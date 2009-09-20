# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements all the views for the gamesquad module.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from os.path import exists
from time import asctime, gmtime, time
from datetime import date

from werkzeug import escape
from werkzeug.exceptions import NotFound, Forbidden

from pyClanSphere import cache
from pyClanSphere.database import db
from pyClanSphere.application import url_for, render_response, emit_event, \
     Response, get_application
from pyClanSphere.i18n import _
from pyClanSphere.privileges import assert_privilege
from pyClanSphere.utils.admin import flash, require_admin_privilege
from pyClanSphere.utils.pagination import AdminPagination
from pyClanSphere.utils.http import redirect_to
from pyClanSphere.utils.redirects import lookup_redirect
from pyClanSphere.views.admin import render_admin_response, PER_PAGE

from pyClanSphere.plugins.gamesquad.forms import DeleteGameForm, EditGameForm, \
     DeleteSquadForm, EditSquadForm, EditSquadMemberForm, DeleteSquadMemberForm, \
     EditLevelForm, DeleteLevelForm
from pyClanSphere.plugins.gamesquad.models import Game, Squad, SquadMember, Level
from pyClanSphere.plugins.gamesquad.privileges import GAME_MANAGE, SQUAD_MANAGE, SQUAD_MANAGE_MEMBERS, LEVEL_MANAGE

#
# Public views
#

@cache.response(vary=('user',))
def game_index(req):
    """Render the most recent posts.

    Available template variables:

        `games`:
            list of known games

    :Template name: ``index.html``
    :URL endpoint: ``news/index``
    """
    
    data = Game.query.all()

    return render_response('game_index.html', games=data)

@cache.response(vary=('user',))
def game_detail(req, game_id=None):
    """Show a game in detail.

    Available template variables:

        `game`:
            selected game

    :Template name: ``index.html``
    :URL endpoint: ``news/index``
    """

    data = Game.query.get(game_id)
    if data is None:
        raise NotFound()

    return render_response('game_detail.html', game=data)

@cache.response(vary=('user',))
def squad_detail(req, squad_id=None):
    """Show a game in detail.

    Available template variables:

        `squad`:
            selected squad object

    :Template name: ``index.html``
    :URL endpoint: ``news/index``
    """

    data = Squad.query.get(squad_id)
    if data is None:
        raise NotFound()

    return render_response('squad_detail.html', squad=data)

#
# Admin views
#

# game stuff

@require_admin_privilege()
def game_list(request, page):
    """Show all games in a list."""

    games = Game.query.limit(PER_PAGE).offset(PER_PAGE * (page - 1)).all()
    pagination = AdminPagination('admin/game_list', page, PER_PAGE,
                                 Game.query.count())
    if not games and page != 1:
        raise NotFound()
    return render_admin_response('admin/game_list.html', 'gamesquad.games',
                                 games=games, pagination=pagination)

@require_admin_privilege(GAME_MANAGE)
def edit_game(request, game_id=None):
    """Edit an existing game or create a new one."""
    
    game = None
    if game_id is not None:
        game = Game.query.get(game_id)
        if game is None:
            raise NotFound()
    form = EditGameForm(game)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/game_list')
        elif request.form.get('delete') and game:
            return redirect_to('admin/game_delete', game_id=game.id)
        elif form.validate(request.form):
            if game is None:
                game = form.make_game()
                msg = _('The game %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('The game %s was updated successfully.')
                icon = 'info'
            flash(msg % (escape(game.name)), icon)

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('admin/game_edit', game_id=game.id)
            return form.redirect('admin/game_list')
    return render_admin_response('admin/game_edit.html', 'gamesquad.games',
                                 form=form.as_widget())

@require_admin_privilege(GAME_MANAGE)
def delete_game(request, game_id):
    """Deletes a game."""

    game = Game.query.get(game_id)
    if game is None:
        raise NotFound()
    form = DeleteGameForm(game)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/game_edit', game_id=game.id)
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('admin/game_edit', game_id=game.id)
            gamename = str(game.name)
            form.delete_game()
            db.commit()
            flash(_('The game %s was deleted successfully') % gamename, 'remove')
            return form.redirect('admin/game_list')

    return render_admin_response('admin/game_delete.html', 'gamesquad.games',
                                 form=form.as_widget())

# squad stuff

@require_admin_privilege()
def squad_list(request, page):
    """Show all squads in a list."""

    squads = Squad.query.limit(PER_PAGE).offset(PER_PAGE * (page - 1)).all()
    pagination = AdminPagination('admin/squad_list', page, PER_PAGE,
                                 Squad.query.count())
    if not squads and page != 1:
        raise NotFound()
    return render_admin_response('admin/squad_list.html', 'gamesquad.squads',
                                 squads=squads, pagination=pagination)

@require_admin_privilege(SQUAD_MANAGE)
def edit_squad(request, squad_id=None):
    """Edit an existing squad or create a new one."""
    
    squad = None
    if squad_id is not None:
        squad = Squad.query.get(squad_id)
        if squad is None:
            raise NotFound()
    form = EditSquadForm(squad)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/squad_list')
        elif request.form.get('delete') and squad:
            return redirect_to('admin/squad_delete', squad_id=squad.id)
        elif form.validate(request.form):
            if squad is None:
                squad = form.make_squad()
                msg = _('The squad %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('The squad %s was updated successfully.')
                icon = 'info'
            flash(msg % (escape(squad.name)), icon)

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('admin/squad_edit', squad_id=squad.id)
            return form.redirect('admin/squad_list')
    return render_admin_response('admin/squad_edit.html', 'gamesquad.squads',
                                 form=form.as_widget())

@require_admin_privilege(SQUAD_MANAGE)
def delete_squad(request, squad_id):
    """Deletes a squad."""

    squad = Squad.query.get(squad_id)
    if squad is None:
        raise NotFound()
    form = DeleteSquadForm(squad)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/squad_edit', squad_id=squad.id)
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('admin/squad_edit', squad_id=squad.id)
            squadname = str(squad.name)
            form.delete_squad()
            db.commit()
            flash(_('%s was deleted successfully') % squadname, 'remove')
            return form.redirect('admin/squad_list')

    return render_admin_response('admin/squad_delete.html', 'gamesquad.squads',
                                 form=form.as_widget())

# squad member stuff

@require_admin_privilege()
def list_squadmembers(request, squad_id=None):
    """Show Squadmemberships"""
    
    if squad_id is None:
        raise NotFound()
    squad = Squad.query.get(squad_id)
    if squad is None:
        raise NotFound()

    data = SquadMember.query.get_list(squad)

    return render_admin_response('admin/squad_listmembers.html', 'gamesquad.squads',
                                 **data)

@require_admin_privilege(SQUAD_MANAGE_MEMBERS)
def edit_squadmember(request, squad_id=None, user_id=None):
    """Edit Squadmemberships"""

    if squad_id is None:
        raise NotFound()
    squad = Squad.query.get(squad_id)
    if squad is None:
        raise NotFound()

    squadmember = None
    if user_id is not None:
        squadmember = SquadMember.query.get((user_id,squad_id))
        if squadmember is None:
            raise NotFound()
    form = EditSquadMemberForm(squad, squadmember)
    
    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/squad_listmembers', squad_id=squad_id)
        elif request.form.get('delete') and user_id is not None:
            return redirect_to('admin/squad_deletemember', squad_id=squad_id, user_id=user_id)
        elif form.validate(request.form):
            if squadmember is None:
                squadmember = form.make_squadmember()
                msg = _('The squadmember %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('The squadmember %s was updated successfully.')
                icon = 'info'

            flash(msg % (escape(squadmember.user.display_name)),icon)

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('admin/squad_editmember', squad_id=squad_id,
                                   user_id=squadmember.user.id)
            return form.redirect('admin/squad_listmembers', squad_id=squad_id)
    return render_admin_response('admin/squad_editmember.html', 'gamesquad.squads',
                                 form=form.as_widget(), squad=squad, squadmember=squadmember)


@require_admin_privilege(SQUAD_MANAGE_MEMBERS)
def delete_squadmember(request, squad_id=None, user_id=None):
    """Remove Member from Squad"""

    if squad_id is None or user_id is None:
        raise NotFound()
    member = SquadMember.query.get((user_id, squad_id))
    if member is None:
        raise NotFound()
    form = DeleteSquadMemberForm(member)
    
    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/squad_editmember', squad_id=squad_id, user_id=user_id)
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('admin/squad_editmember', squad_id=squad_id, user_id=user_id)
            membername = str(member.user.display_name)
            squadname = str(member.squad.name)
            form.delete_member()
            db.commit()
            flash(_('Member %s removed from %s') % (membername,  squadname), 'remove')
            return form.redirect('admin/squad_listmembers', squad_id=squad_id)

    return render_admin_response('admin/squad_deletemember.html', 'gamesquad.squads',
                                 form=form.as_widget())

# level stuff

@require_admin_privilege(LEVEL_MANAGE)
def level_list(request, page):
    """Show all games in a list."""

    levels = Level.query.limit(PER_PAGE).offset(PER_PAGE * (page - 1)).all()
    pagination = AdminPagination('admin/level_list', page, PER_PAGE,
                                 Level.query.count())
    if not levels and page != 1:
        raise NotFound()
    return render_admin_response('admin/level_list.html', 'gamesquad.levels',
                                 levels=levels, pagination=pagination)

@require_admin_privilege(LEVEL_MANAGE)
def edit_level(request, level_id=None):
    """Edit an existing level or create a new one."""
    
    level = None
    if level_id is not None:
        level = Level.query.get(level_id)
        if level is None:
            raise NotFound()
    form = EditLevelForm(level)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/level_list')
        elif request.form.get('delete') and level:
            return redirect_to('admin/level_delete', level_id=level_id)
        elif form.validate(request.form):
            if level is None:
                level = form.make_level()
                msg = _('The level %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('The level %s was updated successfully.')
                icon = 'info'
            flash(msg % (escape(level.name)), icon)

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('admin/level_edit', level_id=level.id)
            return form.redirect('admin/level_list')
    return render_admin_response('admin/level_edit.html', 'levelsquad.levels',
                                 form=form.as_widget())

@require_admin_privilege(LEVEL_MANAGE)
def delete_level(request, level_id):
    """Deletes a level."""

    level = Level.query.get(level_id)
    if level is None:
        raise NotFound()
    form = DeleteLevelForm(level)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/level_edit', level_id=level.id)
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('admin/level_edit', level_id=level.id)
            levelname = str(level.name)
            form.delete_level()
            db.commit()
            flash(_('The level %s was deleted successfully') % levelname, 'remove')
            return form.redirect('admin/level_list')

    return render_admin_response('admin/level_delete.html', 'levelsquad.levels',
                                 form=form.as_widget())

