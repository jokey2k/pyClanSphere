# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.bulletin_board.database
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Our needed tables are declared here (now)

    :copyright: (c) 2009-2010 by the pyClanSphere Team, see AUTHORS for details
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from pyClanSphere.database import db, metadata

# Mapping these out from db module to increases readability further down
for var in ['Table', 'Column', 'String', 'Integer', 'Boolean', 'DateTime', 'ForeignKey', 'Text']:
    globals()[var] = getattr(db,var)

board_categories = Table('board_categories', metadata,
    Column('category_id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('ordering', Integer)
)

board_forums = Table('board_forums', metadata,
    Column('forum_id', Integer, primary_key=True),
    Column('category_id', ForeignKey('board_categories.category_id')),
    Column('name', String(50)),
    Column('description', String(255)),
    Column('ordering', Integer),
    Column('allow_anonymous', Boolean),
    Column('is_public', Boolean),
    Column('is_public', Boolean),
    Column('topiccount', Integer),
    Column('postcount', Integer),
    Column('modification_date', DateTime),
    Column('lasttopic_id', Integer, ForeignKey('board_topics.topic_id', name="forum_lasttopic", use_alter=True)),
    Column('lastpost_id', Integer, ForeignKey('board_posts.post_id', name="forum_lastpost", use_alter=True))
)

board_topics = Table('board_topics', metadata,
    Column('topic_id', Integer, primary_key=True),
    Column('forum_id', ForeignKey('board_forums.forum_id')),
    Column('name', String(255)),
    Column('date', DateTime, default=datetime.utcnow()),
    Column('author_id', ForeignKey('users.user_id')),
    Column('author_str', String(40)),
    Column('is_sticky', Boolean),
    Column('is_locked', Boolean),
    Column('is_global', Boolean),
    Column('is_solved', Boolean),
    Column('is_external', Boolean),
    Column('lastpost_id', Integer, ForeignKey('board_posts.post_id', name="topic_lastpost", use_alter=True)),
    Column('postcount', Integer),
    Column('modification_date', DateTime)
)

board_posts = Table('board_posts', metadata,
    Column('post_id', Integer, primary_key=True),
    Column('topic_id', ForeignKey('board_topics.topic_id')),
    Column('text', Text),
    Column('author_id', ForeignKey('users.user_id')),
    Column('author_str', String(40)),
    Column('date', DateTime, default=datetime.utcnow()),
    Column('ip', String(40)),
)

def init_database(app):
    """ This is for inserting our new table"""
    engine = app.database_engine
    metadata.create_all(engine)

__all__ = ['board_categories', 'board_forums', 'board_topics', 'board_posts']
