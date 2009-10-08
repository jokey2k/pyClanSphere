# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.database
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Our needed tables are declared here

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.database import db, metadata

shoutboxentries = db.Table('shoutboxentries', metadata,
    db.Column('entry_id', db.Integer, primary_key=True),
    db.Column('author', db.String(50)),
    db.Column('user_id', db.ForeignKey('users.user_id')),
    db.Column('existing_user', db.Boolean),
    db.Column('ip', db.String(64)),
    db.Column('postdate', db.DateTime),
    db.Column('text', db.String(255))
)

def init_database():
    """ This is for inserting our new table"""
    from pyClanSphere.application import get_application
    engine = get_application().database_engine
    metadata.create_all(engine)
