# -*- coding: utf-8 -*-
"""
    pyClanSphere.database
    ~~~~~~~~~~~~~~~~~~~~~

    This module is a rather complex layer on top of SQLAlchemy 0.4.
    Basically you will never use the `pyClanSphere.database` module except you
    are a core developer, but always the high level
    :mod:`~pyClanSphere.database.db` module which you can import from the
    :mod:`pyClanSphere.api` module.


    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
import os
import sys
import time
import urlparse
from os import path
from datetime import datetime, timedelta
from types import ModuleType
from copy import deepcopy

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.interfaces import ConnectionProxy
from sqlalchemy.orm.interfaces import AttributeExtension
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.util import to_list
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.types import MutableType
from sqlalchemy.ext.associationproxy import association_proxy

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
    provided as `relative_to`.

    Furthermore the engine is created with `convert_unicode` by default.
    """
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

    options = {'convert_unicode': True}

    # alternative pool sizes / recycle settings and more.  These are
    # interpreter wide and not from the config for the following reasons:
    #
    # - system administrators can set it independently from the webserver
    #   configuration via SetEnv and friends.
    # - this setting is deployment dependent should not affect a development
    #   server for the same instance or a development shell
    for key in 'pool_size', 'pool_recycle', 'pool_timeout':
        value = os.environ.get('PYCLANSPHERE_DATABASE_' + key.upper())
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


def attribute_loaded(model, attribute):
    """Returns true if the attribute of the model was already loaded."""
    # XXX: this works but it relys on a specific implementation in
    # SQLAlchemy.  Figure out if SA provides a way to query that information.
    return attribute in model.__dict__


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


class Query(orm.Query):
    """Default query class."""

    def lightweight(self, deferred=None, lazy=None):
        """Send a lightweight query which deferes some more expensive
        things such as comment queries or even text data.
        """
        args = map(db.lazyload, lazy or ()) + map(db.defer, deferred or ())
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


session = orm.scoped_session(lambda: orm.create_session(get_engine(),
                             autoflush=True, autocommit=False),
                             local_manager.get_ident)

# Session.mapper is deprecated in SQL Alchemy 0.5.5 and above´
# New mapper doesn't auto-add, so put together a MapperExtension
# that allows emulating that behaviour (it's added automatically
# unless you specify extenion=... in your mapper() call)
class AutoAddExt(orm.MapperExtension):
    def init_instance(self, mapper, class_, oldinit, instance, args, kwargs):
        session = kwargs.pop('_sa_session', None)
        if session is None:
            session = db.session
        session.add(instance)
        return orm.EXT_CONTINUE

def session_mapper(scoped_session):
    def mapper(cls, *arg, **kw):
        if cls.__init__ is object.__init__:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            cls.__init__ = __init__
        if not hasattr(cls,'query'):
            cls.query = scoped_session.query_property()
        if not 'extension' in kw:
            kw['extension'] = AutoAddExt()
        return orm.mapper(cls, *arg, **kw)
    return mapper

# configure a declarative base.  This is unused in the code but makes it easier
# for plugins to work with the database.
class ModelBase(object):
    """Internal baseclass for `Model`."""
Model = declarative_base(name='Model', cls=ModelBase, mapper=session_mapper(session))

#: create a new module for all the database related functions and objects
sys.modules['pyClanSphere.database.db'] = db = ModuleType('db')
key = value = mod = None
for mod in sqlalchemy, orm:
    for key, value in mod.__dict__.iteritems():
        if key in mod.__all__:
            setattr(db, key, value)
del key, mod, value

#: forward some session methods to the module as well
for name in 'delete', 'save', 'flush', 'execute', 'begin', 'mapper', \
            'commit', 'rollback', 'clear', 'refresh', 'expire', \
            'query_property':
    setattr(db, name, getattr(session, name))

#: and finally hook our own implementations of various objects in
db.Model = Model
db.Query = Query
db.AutoAddExt = AutoAddExt
db.get_engine = get_engine
db.create_engine = create_engine
db.session = session
db.mapper = session_mapper(session)
db.association_proxy = association_proxy
db.attribute_loaded = attribute_loaded
db.AttributeExtension = AttributeExtension

#: called at the end of a request
cleanup_session = session.remove

#: metadata for the core tables and the core table definitions
metadata = db.MetaData()

users = db.Table('users', metadata,
    db.Column('user_id', db.Integer, primary_key=True),
    db.Column('username', db.String(30)),
    db.Column('real_name', db.String(180)),
    db.Column('display_name', db.String(180)),
    db.Column('gender_male', db.Boolean),
    db.Column('birthday', db.DateTime),
    db.Column('height', db.Integer),
    db.Column('address', db.String(250)),
    db.Column('zip', db.Integer),
    db.Column('city', db.String(250)),
    db.Column('country', db.String(200)),
    db.Column('pw_hash', db.String(70)),
    db.Column('email', db.String(250)),
    db.Column('www', db.String(200))
)

groups = db.Table('groups', metadata,
    db.Column('group_id', db.Integer, primary_key=True),
    db.Column('name', db.String(30))
)

group_users = db.Table('group_users', metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.group_id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'))
)

privileges = db.Table('privileges', metadata,
    db.Column('privilege_id', db.Integer, primary_key=True),
    db.Column('name', db.String(50), unique=True)
)

user_privileges = db.Table('user_privileges', metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id')),
    db.Column('privilege_id', db.Integer,
              db.ForeignKey('privileges.privilege_id'))
)

group_privileges = db.Table('group_privileges', metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('groups.group_id')),
    db.Column('privilege_id', db.Integer,
              db.ForeignKey('privileges.privilege_id'))
)

redirects = db.Table('redirects', metadata,
    db.Column('redirect_id', db.Integer, primary_key=True),
    db.Column('original', db.String(200), unique=True),
    db.Column('new', db.String(200))
)

notification_subscriptions = db.Table('notification_subscriptions', metadata,
    db.Column('subscription_id', db.Integer, primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id')),
    db.Column('notification_system', db.String(50)),
    db.Column('notification_id', db.String(100)),
    db.UniqueConstraint('user_id', 'notification_system', 'notification_id')
)

def init_database(engine):
    """This is called from the websetup which explains why it takes an engine
    and not a pyClanSphere application.
    """
    # XXX: consider using something like this for mysql:
    #   cx = engine.connect()
    #   cx.execute('set storage_engine=innodb')
    #   metadata.create_all(cx)
    metadata.create_all(engine)
