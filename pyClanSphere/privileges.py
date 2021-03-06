# -*- coding: utf-8 -*-
"""
    pyClanSphere.privileges
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module contains a list of builtin privileges.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug.exceptions import Forbidden

from pyClanSphere.database import db
from pyClanSphere.application import get_application, get_request
from pyClanSphere.i18n import lazy_gettext


__all__ = ['DEFAULT_PRIVILEGES', 'Privilege']

DEFAULT_PRIVILEGES = {}


class _Expr(object):

    def iter_privileges(self, cache=None):
        raise NotImplementedError()

    def __and__(self, other):
        return _And(self, other)

    def __or__(self, other):
        return _Or(self, other)

    def __call__(self, privileges):
        return False


class _Bin(_Expr):
    joiner = 'BIN'

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def iter_privileges(self, cache=None):
        if cache is None:
            cache = set()
        for op in self.a, self.b:
            for item in op.iter_privileges(cache):
                yield item

    def __repr__(self):
        return '(%r %s %r)' % (self.a, self.joiner, self.b)


class _And(_Bin):
    joiner = '&'

    def __call__(self, privileges):
        return self.a(privileges) and self.b(privileges)


class _Or(_Bin):
    joiner = '|'

    def __call__(self, privileges):
        return self.a(privileges) or self.b(privileges)


class _Privilege(object):
    """Internal throw-away class used for the association proxy."""

    def __init__(self, name):
        self.name = name

    @property
    def privilege(self):
        return get_application().privileges.get(self.name)


class Privilege(_Expr):

    def __init__(self, name, explanation, privilege_dependencies):
        self.name = name
        self.explanation = explanation
        self.dependencies = privilege_dependencies

    def iter_privileges(self, cache=None):
        if cache is None:
            cache = set([self])
            yield self
        elif self not in cache:
            cache.add(self)
            yield self

    def __call__(self, privileges):
        return self in privileges

    def __repr__(self):
        return self.name


def add_admin_privilege(privilege):
    """If privilege is none, CLAN_ADMIN is returned, otherwise CLAN_ADMIN
    is "or"ed to the expression.
    """
    if privilege is None:
        privilege = CLAN_ADMIN
    elif privilege != CLAN_ADMIN:
        privilege = CLAN_ADMIN | privilege
    return privilege


def bind_privileges(container, privileges, user=None):
    """Binds the privileges to the container.  The privileges can be a list
    of privilege names, the container must be a set.  This is called for
    the HTTP round-trip in the form validation.
    """
    if not user:
        user = get_request().user
    app = get_application()
    notification_types = app.notification_manager.notification_types
    current_map = dict((x.name, x) for x in container)
    currently_attached = set(x.name for x in container)
    new_privileges = set(privileges)

    # remove out-dated privileges
    for name in currently_attached.difference(new_privileges):
        container.remove(current_map[name])
        # remove any privilege dependencies that are not attached to other
        # privileges
        if current_map[name].dependencies:
            for privilege in current_map[name].dependencies.iter_privileges():
                try:
                    container.remove(privilege)
                except KeyError:
                    # privilege probably already removed
                    pass

        # remove notification subscriptions that required the privilege
        # being deleted.
        for notification in user.notification_subscriptions:
            privs = notification_types[notification.notification_id].privileges
            if current_map[name] in privs.iter_privileges():
                db.session.delete(notification)
                break
            for privilege in current_map[name].dependencies:
                if privilege in privs.iter_privileges():
                    db.session.delete(notification)

    # add new privileges
    for name in new_privileges.difference(currently_attached):
        privilege = app.privileges[name]
        container.add(privilege)
        # add dependable privileges
        if privilege.dependencies:
            for privilege in privilege.dependencies.iter_privileges():
                container.add(privilege)


def require_privilege(expr):
    """Requires CLAN_ADMIN privilege or one of the given."""
    def wrapped(f):
        def decorated(request, *args, **kwargs):
            if request.user.has_privilege(expr):
                return f(request, *args, **kwargs)
            raise Forbidden()
        decorated.__name__ = f.__name__
        decorated.__module__ = f.__module__
        decorated.__doc__ = f.__doc__
        return decorated
    return wrapped


def assert_privilege(expr):
    """Like the `require_privilege` decorator but for asserting."""
    if not get_request().user.has_privilege(expr):
        raise Forbidden()


def privilege_attribute(lowlevel_attribute):
    """Returns a proxy attribute for privilege access."""
    def creator_func(privilege):
        if not isinstance(privilege, Privilege):
            raise TypeError('%r is not a privilege object' %
                            type(privilege).__name__)
        priv = _Privilege.query.filter_by(name=privilege.name).first()
        if priv is None:
            priv = _Privilege(privilege.name)
        return priv
    return db.association_proxy(lowlevel_attribute, 'privilege',
                                creator=creator_func)


def _register(name, description, privilege_dependencies=None):
    """Register a new builtin privilege."""
    priv = Privilege(name, description, privilege_dependencies)
    DEFAULT_PRIVILEGES[name] = priv
    globals()[name] = priv
    __all__.append(name)


_register('ENTER_ACCOUNT_PANEL', lazy_gettext(u'can enter user account panel'))
_register('ENTER_ADMIN_PANEL', lazy_gettext(u'can enter admin panel'))
_register('CLAN_ADMIN', lazy_gettext(u'can administer everything'))
