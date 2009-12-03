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

from pyClanSphere.plugins.gamesquad.database import games, squads, squadmembers, levels, gameaccounts
from pyClanSphere.plugins.gamesquad.privileges import GAME_MANAGE, SQUAD_MANAGE, SQUAD_MANAGE_MEMBERS, LEVEL_MANAGE


class Game(object):
    """Basics for a Game"""

    def __init__(self, name):
        super(Game, self).__init__()
        self.name = name

    def can_edit(self, user=None):
        """Checks if the given user (or current user) can edit this game."""

        if user is None:
            user = get_request().user

        return user.has_privilege(GAME_MANAGE)

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self.name
        )


class SquadQuery(db.Query):
    """Provide better prepared queries"""

    def manageable_squads(self, grouped=False, user=None):
        """Return a dict for the given (or current) user-manageable squads"""

        if user is None:
            user = get_request().user

        squads = [squad for squad in self.all() if squad.can_manage(user)]
        if not grouped:
            return squads
        else:
            grouped_squads = {}
            for squad in squads:
                if squad.game not in grouped_squads:
                    grouped_squads[game] = []
                grouped_squads[game].append(squad)
            return grouped_squads


class Squad(object):
    """Basics for a Squad"""

    query = db.query_property(SquadQuery)

    def __init__(self, game, name, tag=None):
        super(Squad, self).__init__()
        self.game = game
        self.name = name
        self.tag = tag

    @staticmethod
    def can_create(user=None):
        """Checks if the given user (or current user) can create new ones"""

        if user is None:
            user=get_request().user

        return user.has_privilege(SQUAD_MANAGE)

    def can_edit(self, user=None):
        """Checks if the given user (or current user) can edit this
        squad (NOT manage members)."""

        if user is None:
            user = get_request().user

        return user.has_privilege(SQUAD_MANAGE)

    def can_manage(self, user=None):
        """Checks if the given user (or current user) can manage memberships"""

        if user is None:
            user = get_request().user

        return user.has_privilege(SQUAD_MANAGE_MEMBERS)

    def __repr__(self):
        return "<%s (%s, %s)>" % (
            self.__class__.__name__,
            self.name,
            self.game.name
        )

class SquadMemberQuery(db.Query):
    """Provide better prepared queries"""

    def get_list(self, squad, endpoint=None, page=1, per_page=None,
                 url_args=None, raise_if_empty=True, paginator=Pagination):
        """Return a dict with pagination and the current members."""

        if per_page is None:
            per_page = 20

        # send the query
        offset = per_page * (page - 1)
	query_filter = self.filter_by(squad_id=squad.id).order_by(SquadMember.level_id)
        memberlist = query_filter \
                         .offset(offset).limit(per_page).all()

        # if raising exceptions is wanted, raise it
        if raise_if_empty and (page != 1 and not memberlist):
            raise NotFound()

        pagination = paginator(endpoint, page, per_page,
                                query_filter.count(), url_args=url_args)

        return {
            'squad':            squad,
            'squadmembers':     memberlist,
            'pagination':       pagination
        }


class SquadMember(object):
    """Extends user with additional fields"""

    query = db.query_property(SquadMemberQuery)

    def __init__(self, user, squad, level, othertasks=None):
        super(SquadMember, self).__init__()
        self.user = user
        self.squad = squad
        self.level = level
        self.othertasks = othertasks

    def __repr__(self):
        return "<%s (%s, %s)>" % (
            self.__class__.__name__,
            self.user.username,
            self.squad.name
        )

class Level(object):
    """Name Alias for Levels"""

    def __init__(self, name):
        super(Level, self).__init__()
        self.name = name

    def can_edit(self, user=None):
        """Checks if the given user (or current user) can edit this level."""

        if user is None:
            user = get_request().user

        return user.has_privilege(LEVEL_MANAGE)

    def __repr__(self):
        return "<%s (%r, %s)>" % (
            self.__class__.__name__,
            self.id,
            self.name
        )


class GameAccount(object):
    """Basics for a GameAccount"""

    def __init__(self, game=None, user=None, account=None, ingameaccess=False):
        super(GameAccount, self).__init__()
        self.game = game
        self.user = user
        self.account = account
        self.ingameaccess = ingameaccess

    def __repr__(self):
        return "<%s (%s, %s)>" % (
            self.__class__.__name__,
            self.game,
            self.user
        )


db.mapper(Game, games, properties={
    'id':           games.c.game_id
})
db.mapper(Squad, squads, properties={
    'id':           squads.c.squad_id,
    'game':         db.relation(Game, uselist=False, lazy=False,
                                backref=db.backref('squads', lazy='dynamic')
                    ),
    'members':      db.relation(User,
                                secondary=squadmembers, collection_class=set,
                                backref=db.backref('squads')
                    ),
    'squadmembers': db.relation(SquadMember)
})
db.mapper(SquadMember, squadmembers, properties={
    'user':         db.relation(User, uselist=False, lazy=False),
    'squad':        db.relation(Squad, uselist=False, lazy=False),
    'level':        db.relation(Level, uselist=False, lazy=False)
})
db.mapper(Level, levels, properties={
    'id':           levels.c.level_id
})
db.mapper(GameAccount, gameaccounts, properties={
    'id':           gameaccounts.c.account_id,
    'game':         db.relation(Game, uselist=False, lazy=False),
    'user':         db.relation(User, uselist=False, lazy=False,
                                backref=db.backref('gameaccounts')
    )
})
