# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Required baseclass and query extension to handle our entries

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime, date

from pyClanSphere.api import *
from pyClanSphere.models import User
from pyClanSphere.utils.text import build_tag_uri
from pyClanSphere.utils.pagination import Pagination

from pyClanSphere.plugins.gamesquad.database import games, squads, squadmembers, levels


class Game(object):
    """Basics for a Game"""

    def __init__(self, name):
        super(Game, self).__init__()
        self.name = name

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self.name
        )


class Squad(object):
    """Basics for a Squad"""

    def __init__(self, game, name, tag=None):
        super(Squad, self).__init__()
        self.game = game
        self.name = name
        self.tag = tag

    def __repr__(self):
        return "<%s (%s, %s)>" % (
            self.__class__.__name__,
            self.name,
            self.game.name
        )


class SquadMember(object):
    """Extends user with additional fields"""

    def __init__(self, user, squad, level, othertasks=None):
        super(SquadMember, self).__init__()
        self.user = user
        self.squad = squad
        self.level = level        
        self.othertasks = othertasks


class Level(object):
    """Name Alias for Levels"""

    def __init__(self, name):
        super(Level, self).__init__()
        self.name = name

    def __repr__(self):
        return "<%s (%r, %s)>" % (
            self.__class__.__name__,
            self.id,
            self.name
        )


db.mapper(Game, games, properties={
    'id':           games.c.game_id
})
db.mapper(Squad, squads, properties={
    'id':           squads.c.squad_id,
    'game':         db.relation(Game, uselist=False, lazy=False,
                                backref=db.backref('squads', lazy='dynamic')
                    ),
    'members':      db.relation(User, lazy=True,
                                secondary=squadmembers, collection_class=set,
                                backref=db.backref('squads')
                    )
})
db.mapper(SquadMember, squadmembers, properties={
    'user':         db.relation(User, uselist=False, lazy=False),
    'squad':        db.relation(Squad, uselist=False, lazy=False),
    'level':        db.relation(Level, uselist=False, lazy=False)
})
db.mapper(Level, levels, properties={
    'id':           levels.c.level_id
})