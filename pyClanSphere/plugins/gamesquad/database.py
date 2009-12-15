# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.database
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Our needed tables are declared here

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.database import db, metadata

games = db.Table('games', metadata,
    db.Column('game_id', db.Integer, primary_key=True),
    db.Column('name', db.String(50))
)

squads = db.Table('squads', metadata,
    db.Column('squad_id', db.Integer, primary_key=True),
    db.Column('game_id', db.ForeignKey('games.game_id')),
    db.Column('name', db.String(50)),
    db.Column('tag', db.String(20))
)

levels = db.Table('levels', metadata,
    db.Column('level_id', db.Integer, primary_key=True),
    db.Column('name', db.String(32))
)

squadmembers = db.Table('squadmembers', metadata,
    db.Column('user_id', db.ForeignKey('users.user_id'), primary_key=True),
    db.Column('squad_id', db.ForeignKey('squads.squad_id'), primary_key=True),
    db.Column('level_id', db.ForeignKey('levels.level_id')),
    db.Column('othertasks', db.String(50))
)

gameaccounts = db.Table('gameaccounts', metadata,
    db.Column('account_id', db.Integer, primary_key=True),
    db.Column('game_id', db.ForeignKey('games.game_id')),
    db.Column('user_id', db.ForeignKey('users.user_id')),
    db.Column('account', db.String(64)),
    db.Column('ingameaccess', db.Boolean)
)

def init_database(app):
    """ This is for inserting our new table"""
    engine = app.database_engine
    metadata.create_all(engine)
