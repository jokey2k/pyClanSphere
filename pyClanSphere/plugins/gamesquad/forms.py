# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Forms we gonna need to handle creation and editing of entries

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.api import *
from pyClanSphere.models import User
from pyClanSphere.utils import forms
from pyClanSphere.utils.validators import ValidationError, is_not_whitespace_only

from pyClanSphere.plugins.gamesquad.models import Game, Squad, SquadMember, Level, GameAccount

class _GameBoundForm(forms.Form):
    """Internal baseclass for games bound forms."""

    def __init__(self, game, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.game = game

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.game = self.game
        widget.new = self.game is None
        return widget


class EditGameForm(_GameBoundForm):
    """Edit or create a game."""

    gamename = forms.TextField(lazy_gettext(u'Gamename'), max_length=50,
                                validators=[is_not_whitespace_only()],
                                required=True)

    def __init__(self, game=None, initial=None):
        if game is not None:
            initial = forms.fill_dict(initial,
                gamename=game.name
            )
        _GameBoundForm.__init__(self, game, initial)

    def validate_gamename(self, value):
        query = Game.query.filter_by(name=value)
        if self.game is not None:
            query = query.filter(Game.id != self.game.id)
        if query.first() is not None:
            raise ValidationError(_('This gamename is already in use'))

    def _set_common_attributes(self, game):
        forms.set_fields(game, self.data)

    def make_game(self):
        """A helper function that creates a new game object."""
        game = Game(self.data['gamename'])
        self._set_common_attributes(game)
        self.game = game
        return game

    def save_changes(self):
        """Apply the changes."""
        self.game.name = self.data['gamename']
        self._set_common_attributes(self.game)


class DeleteGameForm(_GameBoundForm):
    """Used to delete a game from the admin panel."""

    action = forms.ChoiceField(lazy_gettext(u'What should pyClanSphere do with squads '
                                            u'assigned to this group?'),
                              choices=[
        ('delete_membership', lazy_gettext(u'Delete game, remove squads')),
        ('relocate', lazy_gettext(u'Move the squads to another game'))
    ], widget=forms.RadioButtonGroup)
    relocate_to = forms.ModelField(Game, 'id', lazy_gettext(u'Relocate squad to'),
                                   widget=forms.SelectBox)

    def __init__(self, game, initial=None):
        self.relocate_to.choices = [('', u'')] + [
            (g.id, g.name) for g in Game.query.filter(Game.id != game.id)
        ]

        _GameBoundForm.__init__(self, game, forms.fill_dict(initial,
            action='delete_membership'))

    def context_validate(self, data):
        if data['action'] == 'relocate' and not data['relocate_to']:
            raise ValidationError(_('You have to select a game which '
                                    'the squad gets assigned to.'))

    def delete_game(self):
        """Deletes a game."""
        if self.data['action'] == 'relocate':
            new_game = Game.query.filter_by(id=self.data['relocate_to'].id).first()
            for squad in self.game.squads:
                new_game.squads.append(squad)
        db.commit()

        emit_event('before-game-deleted', self.game, self.data)
        db.delete(self.game)


class _SquadBoundForm(forms.Form):
    """Internal baseclass for squads bound forms."""

    def __init__(self, squad, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.squad = squad

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.squad = self.squad
        widget.new = self.squad is None
        return widget


class EditSquadForm(_SquadBoundForm):
    """Edit or create a squad."""

    squadname = forms.TextField(lazy_gettext(u'Squadname'), max_length=50,
                                validators=[is_not_whitespace_only()],
                                required=True)
    game = forms.ModelField(Game, 'id', lazy_gettext(u'Belongs to'),
                            widget=forms.SelectBox)
    tag = forms.TextField(lazy_gettext(u'Squad Tag'), max_length=20,
                          validators=[is_not_whitespace_only()])

    def __init__(self, squad=None, initial=None):
        if squad is not None:
            initial = forms.fill_dict(initial,
                squadname=squad.name,
                game=squad.game,
                tag=squad.tag
            )
        _SquadBoundForm.__init__(self, squad, initial)
        self.game.choices = [(game.id, game.name) for game in Game.query.all()]

    def _set_common_attributes(self, squad):
        squad.game = self.data['game']
        forms.set_fields(squad, self.data)

    def make_squad(self):
        """A helper function that creates a new squad object."""
        squad = Squad(self.data['game'], self.data['squadname'])
        self._set_common_attributes(squad)
        self.squad = squad
        return squad

    def save_changes(self):
        """Apply the changes."""

        self.squad.name = self.data['squadname']
        self._set_common_attributes(self.squad)


class DeleteSquadForm(_SquadBoundForm):
    """Used to delete a squad from the admin panel."""

    action = forms.ChoiceField(lazy_gettext(u'What should pyClanSphere do with members '
                                            u'assigned to this squad?'),
                              choices=[
        ('delete_membership', lazy_gettext(u'Delete squad, remove squadmemberships')),
        ('relocate', lazy_gettext(u'Move the members to another squad'))
    ], widget=forms.RadioButtonGroup)
    relocate_to = forms.ModelField(Squad, 'id', lazy_gettext(u'Relocate members to'),
                                   widget=forms.SelectBox)

    def __init__(self, squad, initial=None):
        self.relocate_to.choices = [('', u'')] + [
            (g.id, g.name) for g in Squad.query.filter(Squad.id != squad.id)
        ]

        _SquadBoundForm.__init__(self, squad, forms.fill_dict(initial,
            action='delete_membership'))

    def context_validate(self, data):
        if data['action'] == 'relocate' and not data['relocate_to']:
            raise ValidationError(_('You have to select a squad which '
                                    'the squad gets assigned to.'))

    def delete_squad(self):
        """Deletes a squad."""
        if self.data['action'] == 'relocate':
            new_squad = Squad.query.filter_by(id=self.data['relocate_to'].id).first()
            for squadmember in self.squad.squadmembers:
                if squadmember not in new_squad.squadmembers:
                    squadmember.squad_id = new_squad.squad_id
        db.commit()

        emit_event('before-squad-deleted', self.squad, self.data)
        db.delete(self.squad)


class _SquadMemberBoundForm(forms.Form):
    """Internal baseclass for squadmember bound forms."""

    def __init__(self, squadmember, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.squadmember = squadmember

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.squadmember = self.squadmember
        widget.new = self.squadmember is None
        return widget


class EditSquadMemberForm(_SquadMemberBoundForm):
    """Decide whos in our squad."""

    clanmember = forms.ModelField(User, 'id', lazy_gettext(u'Clanmember'),
                                  widget=forms.SelectBox)
    level = forms.ModelField(Level, 'id', lazy_gettext(u'Level'),
                            widget=forms.SelectBox)
    othertasks = forms.TextField(lazy_gettext(u'Other tasks'), max_length=100,
                                 validators=[is_not_whitespace_only()])

    def __init__(self, squad, squadmember=None, initial=None):
        if squadmember is not None:
            initial = forms.fill_dict(initial,
                clanmember=squadmember.user,
                level=squadmember.level,
                othertasks=squadmember.othertasks
            )
        _SquadMemberBoundForm.__init__(self, squadmember, initial)
        self.squad = squad
        # Need access to squad here, as the member might be new and thus there is no
        # member.squad relation yet.
        self.clanmember.choices = [(user.id, user.display_name) for \
                                   user in User.query.all() if user not in self.squad.members]
        if self.squadmember:
            self.clanmember.choices.insert(0,(squadmember.user.id, squadmember.user.display_name))
        self.level.choices = [(level.id, level.name) for level in Level.query.all()]

    def make_squadmember(self):
        """A helper function that creates new SquadMember objects."""

        squadmember = SquadMember(self.data['clanmember'], self.squad,
                                  self.data['level'], self.data['othertasks'])
        self.new_squadmember = squadmember
        return squadmember

    def _set_common_attributes(self, squadmember):
        squadmember.squad = self.squad
        squadmember.clanmember = self.data['clanmember']
        squadmember.level = self.data['level']
        squadmember.othertasks = self.data['othertasks']

    def save_changes(self):
        """Apply the changes."""

        self._set_common_attributes(self.squadmember)


class DeleteSquadMemberForm(_SquadMemberBoundForm):
    """Used to remove a member from a squad."""

    def delete_member(self):
        """Deletes the user."""
        db.delete(self.squadmember)


class _LevelBoundForm(forms.Form):
    """Internal baseclass for levels bound forms."""

    def __init__(self, level, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.level = level

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.level = self.level
        widget.new = self.level is None
        return widget


class EditLevelForm(_LevelBoundForm):
    """Edit or create a level."""

    levelname = forms.TextField(lazy_gettext(u'Levelname'), max_length=32,
                                validators=[is_not_whitespace_only()],
                                required=True)

    def __init__(self, level=None, initial=None):
        if level is not None:
            initial = forms.fill_dict(initial,
                levelname=level.name
            )
        _LevelBoundForm.__init__(self, level, initial)

    def validate_levelname(self, value):
        query = Level.query.filter_by(name=value)
        if self.level is not None:
            query = query.filter(Level.id != self.level.id)
        if query.first() is not None:
            raise ValidationError(_('This levelname is already in use'))

    def _set_common_attributes(self, level):
        forms.set_fields(level, self.data)

    def make_level(self):
        """A helper function that creates a new level object."""
        level = Level(self.data['levelname'])
        self._set_common_attributes(level)
        self.level = level
        return level

    def save_changes(self):
        """Apply the changes."""
        self.level.name = self.data['levelname']
        self._set_common_attributes(self.level)


class DeleteLevelForm(_LevelBoundForm):
    """Used to delete a level from the admin panel."""

    relocate_to = forms.ModelField(Level, 'id', lazy_gettext(u'Reassign squadmembers to'),
                                   widget=forms.SelectBox)

    def __init__(self, level, initial=None):
        self.relocate_to.choices = [('', u'')] + [
            (g.id, g.name) for g in Level.query.filter(Level.id != level.id)
        ]

        _LevelBoundForm.__init__(self, level, forms.fill_dict(initial,
            action='delete_membership'))

    def context_validate(self, data):
        if not data['relocate_to']:
            raise ValidationError(_('You have to select a level which '
                                    'the squadmembers get assigned to.'))

    def delete_level(self):
        """Deletes a level."""

        new_level = Level.query.filter_by(id=self.data['relocate_to'].id).first()
        for squadmember in SquadMember.query.filter_by(level_id=self.level.id):
            squadmember.level = new_level
        db.commit()

        emit_event('before-level-deleted', self.level, self.data)
        db.delete(self.level)

class _GameAccountBoundForm(forms.Form):
    """Internal baseclass for game account bound forms."""

    def __init__(self, gameaccount, initial=None):
        forms.Form.__init__(self, initial)
        self.app = get_application()
        self.gameaccount = gameaccount

    def as_widget(self):
        widget = forms.Form.as_widget(self)
        widget.gameaccount = self.gameaccount
        return widget


class EditGameAccountForm(_GameAccountBoundForm):
    """Update Players' Game Accounts."""

    game = forms.ModelField(Game, 'id', lazy_gettext(u'Game'),
                                  widget=forms.SelectBox)
    account = forms.TextField(lazy_gettext(u'Account ID'), max_length=100,
                              validators=[is_not_whitespace_only()])

    def __init__(self, user, gameaccount=None, initial=None):
        if gameaccount is not None:
            initial = forms.fill_dict(initial,
                game=gameaccount.game,
                account=gameaccount.account
            )
        _GameAccountBoundForm.__init__(self, gameaccount, initial)
        self.user = user
        self.game.choices = [(game.id, game.name) for game in Game.query.all()]

    def make_gameaccount(self):
        """A helper function that creates new GameAccount objects."""

        gameaccount = GameAccount(self.data['game'], self.user,
                                  self.data['account'])
        self.gameaccount = gameaccount
        return gameaccount

    def context_validate(self, data):
        query = GameAccount.query.filter_by(game_id=data['game'].id).filter_by(account=data['account'])
        if self.gameaccount is not None:
            query = query.filter(GameAccount.id != self.gameaccount.id)
        if query.first() is not None:
            raise ValidationError(_('This account is already registered'))

    def _set_common_attributes(self, gameaccount):
        gameaccount.user = self.user
        gameaccount.game = self.data['game']
        gameaccount.account = self.data['account']

    def save_changes(self):
        """Apply the changes."""

        self._set_common_attributes(self.gameaccount)


class DeleteGameAccountForm(_GameAccountBoundForm):
    """Used to remove a member from a squad."""

    def delete_account(self):
        """Deletes the game account."""
        db.delete(self.gameaccount)
