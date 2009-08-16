# -*- coding: utf-8 -*-
"""
    pyClanSphere.models
    ~~~~~~~~~~~

    The core models and query helper functions.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from math import log
from datetime import date, datetime, timedelta
from urlparse import urljoin

from werkzeug.exceptions import NotFound

from pyClanSphere.database import users, groups, group_users, \
     privileges, user_privileges, group_privileges, \
     notification_subscriptions, db
from pyClanSphere.utils.text import gen_slug, gen_timestamped_slug, build_tag_uri, \
     increment_string
from pyClanSphere.utils.pagination import Pagination
from pyClanSphere.utils.crypto import gen_pwhash, check_pwhash
from pyClanSphere.utils.http import make_external_url
from pyClanSphere.privileges import Privilege, _Privilege, privilege_attribute, \
     add_admin_privilege, ENTER_ADMIN_PANEL, CLAN_ADMIN
from pyClanSphere.application import get_application, get_request, url_for

from pyClanSphere.i18n import to_clan_timezone

class UserQuery(db.Query):
    """Add some extra query methods to the user object."""

    def get_nobody(self):
        return AnonymousUser()

    def authors(self):
        return self.filter_by(is_author=True)
                

class User(object):
    """Represents an user.

    If you change something on this model, even default values, keep in mind
    that the websetup does not use this model to create the admin account
    because at that time the pyClanSphere system is not yet ready. Also update
    the code in `pyClanSphere.websetup.WebSetup.start_setup`.
    """

    query = db.query_property(UserQuery)
    is_somebody = True

    def __init__(self, username, password, email, real_name=u'',
                 gender_male=True, birthday=date(1970,1,1), height=0,
                 address=u'', zip=0, city=u'', country=u'', www=u''):
        super(User, self).__init__()
        self.username = username
        if password is not None:
            self.set_password(password)
        else:
            self.disable()
        self.display_name = u'$username'
        self.email = email
        self.real_name = real_name
        self.gender_male = gender_male
        self.birthday = birthday
        self.height = height
        self.address = address
        self.zip = zip
        self.city = city
        self.country = country
        self.www = www

    @property
    def is_manager(self):
        return self.has_privilege(ENTER_ADMIN_PANEL)

    @property
    def is_admin(self):
        return self.has_privilege(CLAN_ADMIN)

    def _set_display_name(self, value):
        self._display_name = value

    def _get_display_name(self):
        from string import Template
        return Template(self._display_name).safe_substitute(
            username=self.username,
            real_name=self.real_name
        )

    display_name = property(_get_display_name, _set_display_name)
    own_privileges = privilege_attribute('_own_privileges')

    @property
    def privileges(self):
        """A read-only set with all privileges."""
        result = set(self.own_privileges)
        for group in self.groups:
            result.update(group.privileges)
        return frozenset(result)

    def has_privilege(self, privilege):
        """Check if the user has a given privilege.  If the user has the
        CLAN_ADMIN privilege he automatically has all the other privileges
        as well.
        """
        return add_admin_privilege(privilege)(self.privileges)

    def set_password(self, password):
        self.pw_hash = gen_pwhash(password)

    def check_password(self, password):
        if self.pw_hash == '!':
            return False
        return check_pwhash(self.pw_hash, password)

    def disable(self):
        self.pw_hash = '!'

    @property
    def disabled(self):
        return self.pw_hash == '!'

    def get_url_values(self):
        return self.www or '#'

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.username
        )


class Group(object):
    """Wraps the group table."""

    def __init__(self, name):
        self.name = name

    privileges = privilege_attribute('_privileges')

    def has_privilege(self, privilege):
        return add_admin_privilege(privilege)(self.privileges)

    def get_url_values(self):
        return 'admin/edit_group', {'group_id': self.id}

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.name
        )


class AnonymousUser(User):
    """Fake model for anonymous users."""
    id = -1
    is_somebody = is_author = False
    display_name = 'Nobody'
    real_name = description = username = ''
    own_privileges = privileges = property(lambda x: frozenset())

    def __init__(self):
        pass

    def __nonzero__(self):
        return False

    def check_password(self, password):
        return False


class NotificationSubscription(object):
    """NotificationSubscriptions are part of the notification system.
    An `NotificationSubscription` object expresses that the user the interest
    belongs to _is interested in_ the occurrence of a certain kind of event.
    That data is then used to inform the user once such an interesting event
    occurs. The NotificationSubscription also knows via what notification
    system the user wants to be notified.
    """

    def __init__(self, user, notification_system, notification_id):
        self.user = user
        self.notification_system = notification_system
        self.notification_id = notification_id

    def __repr__(self):
        return "<%s (%s, %r, %r)>" % (
            self.__class__.__name__,
            self.user,
            self.notification_system,
            self.notification_id
        )


# connect the tables.
db.mapper(User, users, properties={
    'id':               users.c.user_id,
    'display_name':     db.synonym('_display_name', map_column=True),
    '_own_privileges':  db.relation(_Privilege, lazy=True,
                                    secondary=user_privileges,
                                    collection_class=set,
                                    cascade='all, delete')
})
db.mapper(Group, groups, properties={
    'id':               groups.c.group_id,
    'users':            db.dynamic_loader(User, backref=db.backref('groups', lazy=True),
                                          query_class=UserQuery,
                                          secondary=group_users),
    '_privileges':      db.relation(_Privilege, lazy=True,
                                    secondary=group_privileges,
                                    collection_class=set,
                                    cascade='all, delete')
})
db.mapper(_Privilege, privileges, properties={
    'id':               privileges.c.privilege_id,
})
db.mapper(NotificationSubscription, notification_subscriptions, properties={
    'id':               notification_subscriptions.c.subscription_id,
    'user':             db.relation(User, uselist=False, lazy=False,
                            backref=db.backref('notification_subscriptions',
                                               lazy='dynamic'
                            )
                        )
})
