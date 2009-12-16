# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
        categorylist = self.order_by(db.asc(Category.order)) \
                           .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not warlist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'categories':       categorylist,
            'pagination':       pagination,
        }

class Category(db.Model):
    __tablename__ = "board_categories"
    
    query = db.query_property(CategoryQuery)
    
    id = db.Column('category_id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(50))
    order = db.Column('order', db.Integer)

    def __init__(self, name=None, order=0):
        self.name = name
        self.order = order

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
        forumlist = self.order_by([db.asc(Forum.category_id),db.asc(Forum.order)]) \
                           .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not warlist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                self.count(), url_args=url_args)

        return {
            'forums':           forumlist,
            'pagination':       pagination,
        }


class Forum(db.Model):
    __tablename__ = "board_forums"
    
    query = db.query_property(ForumQuery)
    
    id = db.Column('forum_id', db.Integer, primary_key=True)
    category_id = db.Column('category_id', db.ForeignKey('board_categories.category_id'))
    category = db.relation('Category', uselist=False, backref='forums')
    name = db.Column('name', db.String(255))
    topiccount = db.Column('topiccount', db.Integer)
    postcount = db.Column('postcount', db.Integer)
    lastposter_id = db.Column('lastposter_id', db.ForeignKey('users.user_id'))
    lastposter = db.relation(User, uselist=False)
    lasttopic_id = db.Column('lasttopic_id', db.Integer)
    modification_date = db.Column('modification_date', db.DateTime)
    order = db.Column('order', db.Integer)
    allow_anonymous = db.Column('allow_anonymous', db.Boolean)
    is_public = db.Column('is_public', db.Boolean)
    db.ForeignKeyConstraint(['lasttopic_id'],['board_topics.topic_id'], name='boardtopics', use_alter=True)

    def __init__(self, category, name=None, order=0):
        assert category is not None
        self.category = category
        self.name = name
        self.order = order

    def can_edit(self, user=None):
        return True
        
    def refresh(self):
        topics = Topic.query.filter(Topic.forum_id==self.id).order_by(db.desc(Topic.modification_date)).all()
        self.topiccount = len(topics)
        if self.topiccount:
            self.lasttopic = topics[0]
            self.lastposter = self.lasttopic.lastposter
            postcount = 0
            for topic in topics:
                postcount += len(topic.posts)
        else:
            self.lasttopic = self.lastposter = None
            postcount = 0
        self.postcount = postcount
        self.modification_date = datetime.utcnow()

class Topic(db.Model):
    __tablename__ = 'board_topics'
    
    id = db.Column('topic_id', db.Integer, primary_key=True)
    forum_id = db.Column('forum_id', db.ForeignKey('board_forums.forum_id'))
    forum = db.relation('Forum', uselist=False, backref='topics')
    name = db.Column('name', db.String(255))
    author_id = db.Column('author_id', db.ForeignKey('users.user_id'))
    author = db.relation(User, uselist=False, primaryjoin=author_id == User.id)
    postcount = db.Column('postcount', db.Integer)
    lastposter_id = db.Column('lastposter_id', db.ForeignKey('users.user_id'))
    lastposter = db.relation(User, uselist=False, primaryjoin=lastposter_id == User.id)
    modification_date = db.Column('modification_date', db.DateTime)
    is_sticky = db.Column('is_sticky', db.Boolean)
    is_locked = db.Column('is_locked', db.Boolean)
    is_global = db.Column('is_global', db.Boolean)
    is_solved = db.Column('is_solved', db.Boolean)
    is_external = db.Column('is_external', db.Boolean)

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
        
    def refresh(self):
        posts = Post.query.filter(Post.topic_id==self.id).order_by(db.asc(Post.id)).all()
        self.postcount = len(posts)
        if self.postcount:
            lastpost = posts[0]
            self.lastposter = lastpost.author
        else:
            self.lastposter = None
        self.modification_date = datetime.utcnow()

# Now that the topics are there, init the lasttopic mapper in Forum class
Forum.lasttopic = db.relation(Topic, uselist=False)


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


class Post(db.Model):
    __tablename__ = 'board_posts'
    
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


def init_database(app):
    """ This is for inserting our new table"""
    engine = app.database_engine
    db.Model.metadata.create_all(engine)
    

__all__ = ['Category', 'Forum', 'Topic', 'Post']
