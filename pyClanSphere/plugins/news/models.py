# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.news.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Required baseclass and query extension to handle our news

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, date

from pyClanSphere.api import *
from pyClanSphere.models import User
from pyClanSphere.utils.text import build_tag_uri
from pyClanSphere.utils.pagination import Pagination

from pyClanSphere.plugins.news.database import newsitems
from pyClanSphere.plugins.news.privileges import NEWS_EDIT, NEWS_PUBLIC

STATUS_DRAFT = 1
STATUS_PUBLISHED = 2

class NewsQuery(db.Query):
    """Add some extra methods to the news model"""

    def published(self, ignore_privileges=False):
        """Return a queryset for only published posts."""

        return self.filter(
            (News.status == STATUS_PUBLISHED) &
            (News.pub_date <= datetime.utcnow())
        )

    def drafts(self, ignore_user=False, user=None):
        """Return a query that returns all drafts for the current user.
        or the user provided or no user at all if `ignore_user` is set.
        """
        if user is None and not ignore_user:
            req = get_request()
            if req and req.user:
                user = req.user
        query = self.filter(News.status == STATUS_DRAFT)
        if user is not None:
            query = query.filter(News.author_id == user.id)
        return query

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination, the current posts, number of pages,
        total posts and all that stuff for further processing.
        """
        if per_page is None:
            app = get_application()
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
        newslist = self.order_by(News.pub_date.desc()) \
                       .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not newslist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args)

        return {
            'pagination':       pagination,
            'newsitems':        newslist
        }

    def get_archive_summary(self, detail='months', limit=None,
                            ignore_privileges=False):
        """Query function to get the archive of the blog. Usually used
        directly from the templates to add some links to the sidebar.
        """
        # XXX: currently we also return months without articles in it.
        # other blog systems do not, but because we use sqlalchemy we have
        # to go with the functionality provided.  Currently there is no way
        # to do date truncating in a database agnostic way.  When this is done
        # ignore_privileges should no longer be a noop
        last = self.filter(News.pub_date != None) \
                   .order_by(News.pub_date.asc()).first()
        now = datetime.utcnow()

        there_are_more = False
        result = []

        if last is not None:
            now = date(now.year, now.month, now.day)
            oldest = date(last.pub_date.year, last.pub_date.month,
                          last.pub_date.day)
            result = [now]

            there_are_more = False
            if detail == 'years':
                now, oldest = [x.replace(month=1, day=1) for x in now, oldest]
                while True:
                    now = now.replace(year=now.year - 1)
                    if now < oldest:
                        break
                    result.append(now)
                else:
                    there_are_more = True
            elif detail == 'months':
                now, oldest = [x.replace(day=1) for x in now, oldest]
                while limit is None or len(result) < limit:
                    if not now.month - 1:
                        now = now.replace(year=now.year - 1, month=12)
                    else:
                        now = now.replace(month=now.month - 1)
                    if now < oldest:
                        break
                    result.append(now)
                else:
                    there_are_more = True
            elif detail == 'days':
                while limit is None or len(result) < limit:
                    now = now - timedelta(days=1)
                    if now < oldest:
                        break
                    result.append(now)
                else:
                    there_are_more = True
            else:
                raise ValueError('detail must be years, months, or days')

        return {
            detail:     result,
            'more':     there_are_more,
            'empty':    not result
        }

    def latest(self, ignore_privileges=False):
        """Filter for the latest n posts."""
        return self.published(ignore_privileges=ignore_privileges).order_by(News.pub_date.desc())

    def date_filter(self, year, month=None, day=None):
        """Filter all the items that match the given date."""
        if month is None:
            return self.filter(
                (News.pub_date >= datetime(year, 1, 1)) &
                (News.pub_date < datetime(year + 1, 1, 1))
            )
        elif day is None:
            return self.filter(
                (News.pub_date >= datetime(year, month, 1)) &
                (News.pub_date < (month == 12 and
                               datetime(year + 1, 1, 1) or
                               datetime(year, month + 1, 1)))
            )
        return self.filter(
            (News.pub_date >= datetime(year, month, day)) &
            (News.pub_date < datetime(year, month, day) +
                             timedelta(days=1))
        )


class News(object):
    """Represents a news post"""

    # Attach query model from above
    query = db.query_property(NewsQuery)

    def __init__(self, title, author, text, pub_date=None,
                 last_update=None, status=STATUS_DRAFT, extra=None):
        super(News, self).__init__()
        self.title = title
        self.author = author
        self.text = text or u''
        self.pub_date = pub_date
        self.status = status

        self.touch_times(pub_date)

        if last_update is not None:
            self.last_update = last_update

    @property
    def is_draft(self):
        """True if not published"""

        return self.status == STATUS_DRAFT

    @property
    def is_public(self):
        """True if post is publicly visible"""

        return (self.status == STATUS_PUBLISHED and \
                self.pub_date <= datetime.utcnow())

    def can_edit(self, user=None):
        """Checks if the given user (or current user) can edit this post."""

        if user is None:
            user = get_request().user

        return user.has_privilege(NEWS_PUBLIC) or \
               (self.status == STATUS_DRAFT and \
               (self.author == user or user.has_privilege(NEWS_EDIT)))

    def can_publish(self, user=None):
        """Checks if the given user (or current user) can publish items."""

        if user is None:
            user = get_request().user

        return user.has_privilege(NEWS_PUBLIC)

    def touch_times(self, pub_date=None):
        """Touches the times for this post.  If the pub_date is given the
        `pub_date` is changed to the given date.  If it's not given the
        current time is assumed if the post status is set to published,
        otherwise it's set to `None`.

        Additionally the `last_update` is always set to now.
        """
        now = datetime.utcnow()
        if pub_date is None and self.status == STATUS_PUBLISHED:
            pub_date = now
        self.pub_date = pub_date
        self.last_update = now


db.mapper(News, newsitems, properties={
    'id':               newsitems.c.news_id,
    'author':           db.relation(User, uselist=False, lazy=False,
                            backref=db.backref('newsitems', lazy='dynamic')
                        )
})
