# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Forms we gonna need to handle creation and editing of entries

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.api import *
from pyClanSphere.utils import forms
from pyClanSphere.utils.validators import ValidationError, is_not_whitespace_only

from pyClanSphere.plugins.gamesquad.models import Game, Squad

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
