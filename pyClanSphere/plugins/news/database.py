# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.news.database
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Our needed tables are declared here

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.database import db, metadata

newsitems = db.Table('newsitems', metadata,
    db.Column('news_id', db.Integer, primary_key=True),
    db.Column('pub_date', db.DateTime),
    db.Column('last_update', db.DateTime),
    db.Column('title', db.String(150)),
    db.Column('text', db.Text),
    db.Column('author_id', db.Integer, db.ForeignKey('users.user_id')),
    db.Column('status', db.Integer),
)

def init_database():
    """ This is for inserting our new table"""
    from pyClanSphere.application import get_application
    engine = get_application().database_engine
    metadata.create_all(engine)
