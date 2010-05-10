# -*- coding: utf-8 -*-
"""
    pyClanSphere.database
    ~~~~~~~~~~~~~~~~~~~~~

    Our layer on top of SQLAlchemy.
    Simply use the high level :mod:`~pyClanSphere.database.db` module which
    you can import from the :mod:`pyClanSphere.api` module.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
import os
import sys
import time
from os import path
from types import ModuleType
from datetime import datetime

import sqlalchemy
from sqlalchemy import orm, sql
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.exc import ArgumentError, DisconnectionError
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.interfaces import ConnectionProxy
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.interfaces import AttributeExtension
from sqlalchemy.util import to_list

from werkzeug import url_decode
from werkzeug.exceptions import NotFound

from pyClanSphere.utils import local_manager


if sys.platform == 'win32':
    _timer = time.clock
else:
    _timer = time.time


_sqlite_re = re.compile(r'sqlite:(?:(?://(.*?))|memory)(?:\?(.*))?$')


def get_engine():
    """Return the active database engine (the database engine of the active
    application).  If no application is enabled this has an undefined behavior.
    If you are not sure if the application is bound to the active thread, use
    :func:`~pyClanSphere.application.get_application` and check it for `None`.
    The database engine is stored on the application object as `database_engine`.
    """
    from pyClanSphere.application import get_application
    return get_application().database_engine


def create_engine(uri, relative_to=None, debug=False):
    """Create a new engine.  This works a bit like SQLAlchemy's
    `create_engine` with the difference that it automaticaly set's MySQL
    engines to 'utf-8', and paths for SQLite are relative to the path
    provided as `relative_to`. Also hooks in LookLively to catch MySQL's
    weird way of connection termination without termination.

    Furthermore the engine is created with `convert_unicode` by default.
    """

    # This is a good idea in any case
    options = {'convert_unicode': True}

    # special case sqlite.  We want nicer urls for that one.
    if uri.startswith('sqlite:'):
        match = _sqlite_re.match(uri)
        if match is None:
            raise ArgumentError('Could not parse rfc1738 URL')
        database, query = match.groups()
        if database is None:
            database = ':memory:'
        elif relative_to is not None:
            database = path.join(relative_to, database)
        if query:
            query = url_decode(query).to_dict()
        else:
            query = {}
        info = URL('sqlite', database=database, query=query)

    else:
        info = make_url(uri)

        # if mysql is the database engine and no connection encoding is
        # provided we set it to utf-8
        if info.drivername == 'mysql':
            info.query.setdefault('charset', 'utf8')
            options['listeners'] = [LookLively()]


    # alternative pool sizes / recycle settings and more.  These are
    # interpreter wide and not from the config for the following reasons:
    #
    # - system administrators can set it independently from the webserver
    #   configuration via SetEnv and friends.
    # - this setting is deployment dependent should not affect a development
    #   server for the same instance or a development shell
    for key in 'pool_size', 'pool_recycle', 'pool_timeout':
        value = os.environ.get(key.upper())
        if value is not None:
            options[key] = int(value)

    # if debugging is enabled, hook the ConnectionDebugProxy in
    if debug:
        options['proxy'] = ConnectionDebugProxy()

    return sqlalchemy.create_engine(info, **options)

def secure_database_uri(uri):
    """Returns the database uri with confidental information stripped."""
    obj = make_url(uri)
    if obj.password:
        obj.password = '***'
    return unicode(obj).replace(u':%2A%2A%2A@', u':***@', 1)


class ConnectionDebugProxy(ConnectionProxy):
    """Helps debugging the database."""

    def cursor_execute(self, execute, cursor, statement, parameters,
                       context, executemany):
        start = _timer()
        try:
            return execute(cursor, statement, parameters, context)
        finally:
            from pyClanSphere.application import get_request
            from pyClanSphere.utils.debug import find_calling_context
            request = get_request()
            if request is not None:
                request.queries.append((statement, parameters, start,
                                        _timer(), find_calling_context()))


class LookLively(object):
    """Ensures that MySQL connections checked out of the pool are alive.

    Specific to the MySQLdb DB-API.
    """

    def checkout(self, dbapi_con, con_record, con_proxy):
        try:
            try:
                dbapi_con.ping(False)
            except TypeError:
                dbapi_con.ping()
        except dbapi_con.OperationalError, ex:
            if ex.args[0] in (2006, 2013, 2014, 2045, 2055):
                raise DisconnectionError()
            else:
                raise


class Query(orm.Query):
    """Default query class."""

    def lightweight(self, deferred=None, lazy=None, eager=None):
        """Send a lightweight query which deferes some more expensive
        things such as comment queries or even text data yet also
         offers eagerloading externals as well.
        """

        args = map(db.lazyload, lazy or ()) + map(db.defer, deferred or ()) + map(db.eagerload, eager or ())
        return self.options(*args)

    def first(self, raise_if_missing=False):
        """Return the first result of this `Query` or None if the result
        doesn't contain any rows.  If `raise_if_missing` is set to `True`
        a `NotFound` exception is raised if no row is found.
        """
        rv = orm.Query.first(self)
        if rv is None and raise_if_missing:
            raise NotFound()
        return rv


class AutoAddExt(orm.MapperExtension):
    def init_instance(self, mapper, class_, oldinit, instance, args, kwargs):
        session = kwargs.pop('_sa_session', None)
        if session is None:
            session = db.session
        session.add(instance)
        return orm.EXT_CONTINUE


#: get a new session
session = orm.scoped_session(lambda: orm.create_session(get_engine(),
                             autoflush=False, autocommit=False),
                             local_manager.get_ident)

def mapper(cls, *arg, **options):
    """A mapper that hooks in our standard extensions."""

    extensions = to_list(options.pop('extension', None), [])
    extensions.append(AutoAddExt())
    options['extension'] = extensions

    if not hasattr(cls, 'query'):
        cls.query = session.query_property()

    return orm.mapper(cls, *arg, **options)

#: create a new module for all the database related functions and objects
sys.modules['pyClanSphere.database.db'] = db = ModuleType('db')
key = value = mod = None
for mod in sqlalchemy, orm:
    for key, value in mod.__dict__.iteritems():
        if key in mod.__all__:
            setattr(db, key, value)
del key, mod, value

#: forward some session methods to the module as well
for name in 'delete', 'flush', 'execute', 'begin', \
            'commit', 'rollback', 'refresh', 'expire', \
            'query_property':
    setattr(db, name, getattr(session, name))

#: forward some operators too
for name in 'func', 'and_', 'or_', 'not_':
    setattr(db, name, getattr(sql, name))

#: metadata for the core tables and the core table definitions
metadata = db.MetaData()

#: configure a declarative base.  This is unused in the code but makes it easier
#: for plugins to work with the database.
class ModelBase(object):
    """Internal baseclass for `Model`."""
Model = declarative_base(name='Model', metadata=metadata, cls=ModelBase, mapper=mapper)

#: and finally hook our own implementations of various objects in
db.Model = Model
db.Query = Query
db.get_engine = get_engine
db.create_engine = create_engine
db.mapper = mapper
db.session = session
db.association_proxy = association_proxy
db.AttributeExtension = AttributeExtension
db.attribute_mapped_collection = attribute_mapped_collection

#: called at the end of a request
cleanup_session = session.remove

def init_database(engine):
    """This is called from the websetup which explains why it takes an engine
    and not a pyClanSphere application.
    """
    # XXX: consider using something like this for mysql:
    #   cx = engine.connect()
    #   cx.execute('set storage_engine=innodb')
    #   metadata.create_all(cx)
    metadata.create_all(engine)
