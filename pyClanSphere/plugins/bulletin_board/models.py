# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Models for the board.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime
from operator import attrgetter

from werkzeug import cached_property
from werkzeug.exceptions import NotFound

from pyClanSphere.api import db, get_request
from pyClanSphere.models import User, AnonymousUser
from pyClanSphere.utils.pagination import Pagination

from pyClanSphere.plugins.bulletin_board.privileges import *
from pyClanSphere.plugins.bulletin_board.database import *


class TopicEmpty(Exception):
    """Class used to tell that the given topic has no posts"""
    pass

class CategoryQuery(db.Query):
    """Addon methods for querying categories"""

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination and categories."""

        if per_page is None:
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
        categorylist = self.order_by(db.asc(Category.ordering)) \
                           .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise i
        if raise_if_empty and (page != 1 and not categorylist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'categories':       categorylist,
            'pagination':       pagination,
        }


class Category(object):
    """Representation of a category"""

    query = db.query_property(CategoryQuery)

    def __init__(self, name=None, ordering=0):
        self.name = name
        self.ordering = ordering

    def can_edit(self, user=None):
        return True


class ForumQuery(db.Query):
    """Addon methods for querying forums"""

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination and categories."""

        if per_page is None:
            per_page = 20

        # XXX: this should all be in a one-go in the database as it is much faster
        #      there but works for now

        # retrieve (pre-filtered) forumlist
        offset = per_page * (page - 1)
        forumlist = self.offset(offset).limit(per_page).all()

        # fetch an unique list of categories from selected forums
        categories_temp = [forum.category for forum in forumlist]
        categories = sorted(set(categories_temp), key=attrgetter('ordering'))

        # order by category ordering, then forum ordering
        retlist = []
        for category in categories:
            for forum in self.filter(Forum.category_id==category.id).order_by(Forum.ordering).all():
                retlist.append(forum)

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not retlist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'forums':           retlist,
            'pagination':       pagination,
        }


class Forum(object):
    """Representation of a forum"""

    query = db.query_property(ForumQuery)

    def __init__(self, category, name=None, description=None, ordering=0):
        assert category is not None
        self.category = category
        self.name = name
        self.description = description
        self.ordering = ordering

    def can_edit(self, user=None):
        return True

    def can_see(self, user=None):
        if user is None:
            user = get_request().user
        return self.is_public or user.is_somebody

    def can_create_topic(self, user=None):
        if user is None:
            user = get_request().user
        return self.allow_anonymous or user.is_somebody

    def is_unread(self, user=None):
        if user is None:
            user = get_request().user
        if isinstance(user, AnonymousUser):
            return False

        global_lastread = GlobalLastRead.query.get(user.id)
        if not global_lastread or not self.modification_date:
            return False
        if global_lastread.date > self.modification_date:
            return False

        topics=Topic.query \
               .filter(Topic.modification_date > global_lastread.date) \
               .filter(Topic.forum_id == self.id).all()
        for topic in topics:
            if topic.is_unread(user):
                return True
        return False

    def refresh(self):
        topicfilter = Topic.query.filter(Topic.forum_id==self.id)
        topics = topicfilter.order_by(db.desc(Topic.modification_date)).all()
        self.topiccount = topicfilter.count()
        if self.topiccount:
            lasttopic = topics[0]
            self.lasttopic_id = lasttopic.id
            self.lastpost_id = lasttopic.lastpost.id
            postcount = 0
            for topic in topics:
                postcount += topic.postcount
        else:
            self.lasttopic_id = None
            self.lastpost_id = None
            postcount = 0
        self.postcount = postcount
        self.modification_date = datetime.utcnow()


class TopicQuery(db.Query):
    """Addon methods for querying topics"""

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination and topics."""

        if per_page is None:
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
        stickylist = self.filter(Topic.is_sticky==True) \
                        .order_by(db.desc(Topic.modification_date)).all()
        topiclist = self.filter(db.or_(Topic.is_sticky==False,Topic.is_sticky==None)) \
                        .order_by(db.desc(Topic.modification_date)) \
                        .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise i
        if raise_if_empty and (page != 1 and not topiclist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'stickies':         stickylist,
            'topics':           topiclist,
            'pagination':       pagination,
        }


class AuthorBase(object):
    """Base class for proxying non-authors"""


    def __init__(self):
        # this is just a base class
        raise NotImplemented()

    def _get_author(self):
        if self.author_id == None:
            author = AnonymousUser()
            author.display_name = self.author_str
            return author
        else:
            return User.query.get(self.author_id)

    def _set_author(self, author):
        if author.is_somebody:
            self.author_id = author.id
        else:
            self.author_id = None
            self.author_str = author.display_name

    author = property(_get_author, _set_author)


class Topic(AuthorBase):
    """Representation of a topic"""

    query = db.query_property(TopicQuery)

    def __init__(self, forum, name=None, author=None, date=None, is_sticky=None,
                 is_locked=None, is_global=None, is_solved=None, is_external=None):
        assert forum is not None
        self.forum = forum
        self.name = name
        self.date = date or datetime.utcnow()
        self.author = author
        self.is_sticky = is_sticky
        self.is_solved = is_solved
        self.is_global = is_global
        self.is_locked = is_locked
        self.is_external = is_external

    def can_post(self, user=None):
        if user is None:
            user = request.user
        return not self.is_locked and (user.is_somebody or (self.forum.is_public and self.forum.allow_anonymous))

    def can_see(self, user=None):
        if user is None:
            user = request.user
        return self.is_global or user.is_somebody or self.forum.is_public

    def is_unread(self, user=None):
        if user is None:
            user = get_request().user
        if isinstance(user, AnonymousUser):
            return False

        global_lastread = GlobalLastRead.query.get(user.id)
        if not global_lastread:
            return False
        if global_lastread.date > self.modification_date:
            return False

        local_lastread = LocalLastRead.query.get((user.id,self.id))
        if not local_lastread:
            return True
        if local_lastread.date >= self.modification_date:
            return False

        return True

    def refresh(self):
        """Refresh our lasttopic/lastpost data"""

        postquery = Post.query.filter(Post.topic_id==self.id)
        self.postcount = postquery.count()

        lastpost = postquery.order_by(db.desc(Post.id)).first()
        self.lastpost_id = lastpost.id
        self.modification_date = lastpost.date

    @cached_property
    def pagination(self):
        endpoint = 'board/topic_details'
        per_page = 20
        return Pagination(endpoint, 0, per_page,
                          Post.query.filter(Post.topic_id==self.id).count())

class PostQuery(db.Query):
    """Addon methods for querying posts"""

    def get_list(self, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination and topics."""

        if per_page is None:
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
        postlist = self.order_by(db.asc(Post.date)) \
                       .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise i
        if raise_if_empty and (page != 1 and not postlist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'posts':            postlist,
            'pagination':       pagination,
        }


class Post(AuthorBase):
    """Representation of a post"""

    query = db.query_property(PostQuery)

    def __init__(self, topic, text=None, author=None, date=None, ip=None):
        assert topic is not None
        self.text = text
        self.author = author
        self.date = date
        self.ip = ip
        self.topic = topic

    def can_edit(self, user=None):
        if user is None:
            user = get_request().user
        if not user.is_somebody:
            return
        if not self.author.is_somebody:
            return user.has_privilege(BOARD_MODERATE)
        else:
            return self.author == user or user.has_privilege(BOARD_MODERATE)

    def can_delete(self, user=None):
        if user is None:
            user = get_request().user
        return self.topic.can_see(user) and user.has_privilege(BOARD_MODERATE)


class GlobalLastRead(object):
    """Global Lastread entry"""

    def __init__(self, user, date=None):
        assert user is not None
        self.user = user
        if date:
            self.date = date


class LocalLastRead(object):
    """Per-Topic Lastread entry"""

    def __init__(self, user, topic, date=None):
        assert user is not None
        assert topic is not None
        self.user = user
        self.topic = topic
        if date:
            self.date = date

# Map Classes to tables
db.mapper(Category, board_categories, properties={
    'id':           board_categories.c.category_id
})
db.mapper(Forum, board_forums, properties={
    'id':           board_forums.c.forum_id,
    'category':     db.relation(Category, uselist=False, backref=db.backref('forums', lazy='dynamic')),
    'lasttopic':    db.relation(Topic, uselist=False, primaryjoin=
                                board_forums.c.lasttopic_id==board_topics.c.topic_id),
    'lastpost':     db.relation(Post, uselist=False, primaryjoin=
                                board_forums.c.lastpost_id==board_posts.c.post_id)
})
db.mapper(Topic, board_topics, properties={
    'id':           board_topics.c.topic_id,
    'forum':        db.relation(Forum, uselist=False, backref=db.backref('topics'),
                                primaryjoin=board_topics.c.forum_id==board_forums.c.forum_id),
    'lastpost':     db.relation(Post, uselist=False, primaryjoin=
                                board_topics.c.lastpost_id==board_posts.c.post_id)
})
db.mapper(Post, board_posts, properties={
    'id':           board_posts.c.post_id,
    'topic':        db.relation(Topic, uselist=False, backref=db.backref('posts'),
                                primaryjoin=board_posts.c.topic_id==board_topics.c.topic_id)
})
db.mapper(GlobalLastRead, board_global_lastread, properties={
    'user':         db.relation(User, uselist=False),
})
db.mapper(LocalLastRead, board_local_lastread, properties={
    'user':         db.relation(User, uselist=False),
    'topic':        db.relation(Topic, uselist=False)
})

__all__ = ['Category', 'Forum', 'Topic', 'Post', 'TopicEmpty', 'GlobalLastRead', 'LocalLastRead']
