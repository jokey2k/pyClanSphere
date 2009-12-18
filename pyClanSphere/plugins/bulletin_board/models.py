# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Models for the board.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime

from pyClanSphere.api import db
from pyClanSphere.models import User
from pyClanSphere.utils.pagination import Pagination


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


class Category(db.Model):
    """Representation of a category"""

    __tablename__ = "board_categories"
    query = db.query_property(CategoryQuery)

    # base data
    id = db.Column('category_id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(50))
    ordering = db.Column('ordering', db.Integer)

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

        # send the query
        offset = per_page * (page - 1)
        forumlist = self.order_by([db.asc(Forum.category_id),db.asc(Forum.ordering)]) \
                           .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not forumlist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'forums':           forumlist,
            'pagination':       pagination,
        }


class Forum(db.Model):
    """Representation of a forum"""

    __tablename__ = "board_forums"
    query = db.query_property(ForumQuery)

    # base data
    id = db.Column('forum_id', db.Integer, primary_key=True)
    category_id = db.Column('category_id', db.ForeignKey('board_categories.category_id'))
    category = db.relation('Category', uselist=False, backref=db.backref('forums', lazy='dynamic'))
    name = db.Column('name', db.String(50))
    description = db.Column('description', db.String(255))
    ordering = db.Column('ordering', db.Integer)
    allow_anonymous = db.Column('allow_anonymous', db.Boolean)
    is_public = db.Column('is_public', db.Boolean)

    # quick access
    topiccount = db.Column('topiccount', db.Integer)
    postcount = db.Column('postcount', db.Integer)
    lastposter_id = db.Column('lastposter_id', db.ForeignKey('users.user_id'))
    lastposter = db.relation(User, uselist=False)
    lasttopic_id = db.Column('lasttopic_id', db.Integer)
    modification_date = db.Column('modification_date', db.DateTime)
    db.ForeignKeyConstraint(['lasttopic_id'],['board_topics.topic_id'], name='boardtopics', use_alter=True)

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

    def refresh(self):
        topicfilter = Topic.query.filter(Topic.forum_id==self.id)
        topics = topicfilter.order_by(db.desc(Topic.modification_date)).all()
        self.topiccount = topicfilter.count()
        if self.topiccount:
            lasttopic = topics[0]
            self.lasttopic_id = lasttopic.id
            return
            self.lastposter_id = lasttopic.lastposter.id
            postcount = 0
            for topic in topics:
                postcount += len(topic.posts)
        else:
            self.lasttopic = self.lastposter = None
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
        topiclist = self.order_by(db.desc(Topic.modification_date)) \
                        .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise i
        if raise_if_empty and (page != 1 and not topiclist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'topics':           topiclist,
            'pagination':       pagination,
        }


class Topic(db.Model):
    """Representation of a topic"""

    __tablename__ = 'board_topics'
    query = db.query_property(TopicQuery)

    # base data
    id = db.Column('topic_id', db.Integer, primary_key=True)
    forum_id = db.Column('forum_id', db.ForeignKey('board_forums.forum_id'))
    forum = db.relation('Forum', uselist=False, backref='topics')
    name = db.Column('name', db.String(255))
    author_id = db.Column('author_id', db.ForeignKey('users.user_id'))
    author = db.relation(User, uselist=False, primaryjoin=author_id == User.id)
    date = db.Column('date', db.DateTime)
    is_sticky = db.Column('is_sticky', db.Boolean)
    is_locked = db.Column('is_locked', db.Boolean)
    is_global = db.Column('is_global', db.Boolean)
    is_solved = db.Column('is_solved', db.Boolean)
    is_external = db.Column('is_external', db.Boolean)

    # quick access
    lastposter_id = db.Column('lastposter_id', db.ForeignKey('users.user_id'))
    lastposter = db.relation(User, uselist=False, primaryjoin=lastposter_id == User.id)
    lastpost_id = db.Column('lastpost_id', db.Integer)
    postcount = db.Column('postcount', db.Integer)
    modification_date = db.Column('modification_date', db.DateTime)
    db.ForeignKeyConstraint(['lastpost_id'],['board_posts.post_id'], name='boardposts', use_alter=True)

    def __init__(self, forum, name=None, author=None, is_sticky=None,
                 is_locked=None, is_global=None, is_solved=None, is_external=None):
        assert forum is not None
        self.forum = forum
        self.name = name
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

    def refresh(self):
        """Refresh our lasttopic/lastpost data and do so for our parent forum"""

        posts = Post.query.filter(Post.topic_id==self.id).order_by(db.asc(Post.id)).all()
        self.postcount = len(posts)
        if self.postcount:
            lastpost = posts[0]
            self.lastpost = lastpost
            self.lastposter = lastpost.author
            self.modification_date = lastpost.date
        else:
            self.lastpost = None
            self.lastposter = None
            self.modification_date = None
        self.forum.refresh()


# many to many tables for prefixes
forums_prefix = db.Table('board_forums_prefix', db.Model.metadata,
                         db.Column('forum_id', db.ForeignKey('board_forums.forum_id')),
                         db.Column('prefix_id', db.ForeignKey('board_prefixes'))
                )

topics_prefix = db.Table('board_topics_prefix', db.Model.metadata,
                         db.Column('topic_id', db.ForeignKey('board_topics.topic_id')),
                         db.Column('prefix_id', db.ForeignKey('board_prefixes'))
                )


class Prefix(db.Model):
    __tablename__ = 'board_prefixes'

    id = db.Column('prefix_id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(20))
    forums = db.relation('Forum', secondary=forums_prefix)
    topics = db.relation('Topic', secondary=topics_prefix)


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


class Post(db.Model):
    """Representation of a post"""

    __tablename__ = 'board_posts'
    query = db.query_property(PostQuery)

    # base data
    id = db.Column('post_id', db.Integer, primary_key=True)
    topic_id = db.Column('topic_id', db.ForeignKey('board_topics.topic_id'))
    topic = db.relation('Topic', uselist=False, backref='posts')
    text = db.Column('text', db.Text)
    author_id = db.Column('author_id', db.ForeignKey('users.user_id'))
    author = db.relation(User, uselist=False)
    date = db.Column('date', db.DateTime)
    ip = db.Column('ip', db.String(40))

    def __init__(self, topic, text=None, author=None, date=None, ip=None):
        assert topic is not None
        self.text = text
        self.author = author
        self.date = date
        self.ip = ip
        self.topic = topic


# Add in relations that have circular deps on ini
Forum.lasttopic = db.relation(Topic, uselist=False)
Topic.lastpost = db.relation(Post, uselist=False)


def init_database(app):
    """ This is for inserting our new table"""
    engine = app.database_engine
    db.Model.metadata.create_all(engine)


__all__ = ['Category', 'Forum', 'Topic', 'Post']
