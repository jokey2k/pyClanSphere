"""
    pyClanSphere.plugins.gamesquad.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Required baseclass and query extension to handle our entries

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime, date

from pyClanSphere.api import *
from pyClanSphere.models import User, AnonymousUser
from pyClanSphere.utils.pagination import Pagination

from pyClanSphere.plugins.shoutbox.database import shoutboxentries
from pyClanSphere.plugins.shoutbox.privileges import SHOUTBOX_MANAGE


class ShoutboxEntryQuery(db.Query):
    """Additional query options suitable for our usage"""

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True):
        """Return a dict with pagination, the current posts, number of pages,
        total posts and all that stuff for further processing.
        """
        if per_page is None:
            app = get_application()
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
        shoutboxentries = self.order_by(ShoutboxEntry.postdate.desc()) \
                              .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not newslist):
            raise NotFound()

        pagination = Pagination(endpoint, page, per_page,
                                self.count(), url_args)

        return {
            'pagination':       pagination,
            'entries':          shoutboxentries
        }


class ShoutboxEntry(object):
    """Represents a shoutbox entry"""

    query = db.query_property(ShoutboxEntryQuery)

    def __init__(self, author=u'', user=None, existing_user=False, ip=None, postdate=None, text=u''):
        super(ShoutboxEntry, self).__init__()
        self.ip = ip
        self.text = text
        self.touch_time(postdate)
        if user is not None and user.is_somebody:
            self.set_user(user)
        else:
            self.set_author(author)

    def __repr__(self):
        return "<%s (%s, '%s', %s)>" % (
            self.__class__.__name__,
            self.existing_user,
            self.author,
            self.postdate,
        )

    def can_manage(self, user=None):
        """Check if given (or current) user can manage this entry"""

        if user is None:
            user = get_request().user

        return user.has_privilege(SHOUTBOX_MANAGE)

    def set_author(self, author):
        """Set author to an anonymous name"""

        self.user = None
        self.existing_user = False
        self.author = author

    def set_user(self, user):
        """Set author to an existing user"""

        self.user_id = user.id
        self.existing_user = True
        self.author = user.display_name

    def touch_time(self, date=None):
        """Touches the time for this post.  If the date is given the
        `date` is changed to the given date.  If it's not given the
        current time is assumed.
        """

        if date is None:
            self.postdate = datetime.utcnow()
        else:
            self.postdate = date


db.mapper(ShoutboxEntry, shoutboxentries, properties={
    'id':           shoutboxentries.c.entry_id,
    'user':         db.relation(User, uselist=False, lazy=True,
                                backref=db.backref('shoutboxentries'))
})
