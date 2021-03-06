# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.war.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements all the views for the war module.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os, datetime

from werkzeug.exceptions import NotFound, Forbidden

from pyClanSphere import cache
from pyClanSphere.api import *
from pyClanSphere.privileges import CLAN_ADMIN
from pyClanSphere.utils.admin import require_admin_privilege, flash as admin_flash
from pyClanSphere.utils.http import redirect_to
from pyClanSphere.utils.pagination import AdminPagination
from pyClanSphere.views.account import render_account_response
from pyClanSphere.views.admin import render_admin_response, PER_PAGE
from werkzeug import escape

from pyClanSphere.plugins.war import forms
from pyClanSphere.plugins.war.models import War, WarMap, WarMode, WarResult, warstates, memberstates
from pyClanSphere.plugins.war.privileges import WAR_MANAGE

# Frontend stuff
@cache.response(vary=('user',))
def war_index(request, page):
    """Render war overview.

    Available template variables:

        `wars`:
            list of war objects

        `pagination`:
            a pagination object to render a pagination

    :Template name: ``war_index.html``
    :URL endpoint: ``wars/index``
    """

    data = War.query.get_list('wars/index', page=page)

    return render_response('war_index.html', **data)

@cache.response(vary=('user',))
def war_detail(request, war_id=None):
    """Render a war in detail.

    Available template variables:

        `war`:
            war object to render

    :Template name: ``war_detail.html``
    :URL endpoint: ``wars/detail``
    """

    if war_id is None:
        raise NotFound()

    # mark all detail field eagerload as they're needed in the template either way
    # and lazyload is just sloooow in this case
    query = War.query
    for field in ['mode','orgamember','members','maps']:
        query = query.options(db.eagerload(field))

    war = query.get(war_id)
    if war is None:
        raise NotFound()

    return render_response('war_detail.html', war=war, result=war.result,
                           memberstates=memberstates)

def war_fightus(request):
    """Render form for a fightus request on front page.

    Available template variables:

        `form`:
            war object to render

    :Template name: ``war_fightus.html``
    :URL endpoint: ``wars/fightus``
    """

    form = forms.FightUsForm(None)

    if request.method == 'POST':
        if form.validate(request.form):
            war = form.make_war()
            db.commit()
            return render_response('war_fightus_success.html', form=form.as_widget())

    return render_response('war_fightus.html', form=form.as_widget())

# Backend stuff

@require_admin_privilege(WAR_MANAGE)
def war_list(request, page):
    """List wars in backend"""

    data = War.query.get_list('admin/wars', per_page=PER_PAGE, page=page,
                              paginator=AdminPagination)

    return render_admin_response('admin/war_list.html', 'war.wars',
                                 **data)

@require_admin_privilege(WAR_MANAGE)
def war_edit(request, war_id=None):
    """Edit an existing war or create a new one."""

    war = None
    if war_id is not None:
        war = War.query.get(war_id)
        if war is None:
            raise NotFound()
    form = forms.EditWarForm(war)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/wars')
        elif 'result' in request.form:
            return form.redirect('admin/warresult_edit', war_id=war_id)
        elif request.form.get('delete') and war:
            return redirect_to('admin/wars/delete', war_id=war_id)
        elif form.validate(request.form):
            if war is None:
                war = form.make_war()
                msg = _('The war %s was added successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('The war %s was updated successfully.')
                icon = 'info'
            admin_flash(msg % (war.clanname), icon)

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('admin/wars/edit', war_id=war.id)
            return redirect_to('admin/wars')

    return render_admin_response('admin/war_edit.html', 'war.wars',
                                 form=form.as_widget(), memberstates=memberstates, warstates=warstates)

@require_admin_privilege(WAR_MANAGE)
def war_delete(request, war_id=None):
    war = None
    if war_id is not None:
        war = War.query.get(war_id)
        if war is None:
            raise NotFound()
    form = forms.DeleteWarForm(war)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/wars/edit', war_id=war_id)
        elif request.form.get('confirm') and form.validate(request.form):
            warname = str(war.clanname)
            form.delete_war()
            db.commit()
            admin_flash(_('The war %s was deleted successfully') % warname, 'remove')
            return redirect_to('admin/wars')

    return render_admin_response('admin/war_delete.html', 'war.wars',
                                 form=form.as_widget())

@require_admin_privilege(WAR_MANAGE)
def warmap_list(request, page):
    """List warmaps in backend"""

    data = WarMap.query.get_list('admin/warmaps', per_page=PER_PAGE, page=page,
                                 paginator=AdminPagination)

    return render_admin_response('admin/warmap_list.html', 'war.maps',
                                  **data)

@require_admin_privilege(WAR_MANAGE)
def warmap_edit(request, warmap_id=None):
    """Edit an existing warmap or create a new one."""

    warmap = None
    if warmap_id is not None:
        warmap = WarMap.query.get(warmap_id)
        if warmap is None:
            raise NotFound()
    form = forms.EditWarMapForm(warmap)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/warmaps')
        elif request.form.get('delete') and warmap:
            return redirect_to('admin/warmaps/delete', warmap_id=warmap_id)
        elif form.validate(request.form):
            if warmap is None:
                warmap = form.make_warmap()
                msg = _('Warmap %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('Warmap %s was updated successfully.')
                icon = 'info'
            db.commit()

            mapfile = request.files.get('mapfile')
            if mapfile:
                warmap.place_file(mapfile)
                if form.overwrite_mapname and hasattr(warmap.metadata, 'name'):
                    warmap.name = unicode(warmap.metadata.name)
                    db.commit()
            admin_flash(msg % (warmap.name), icon)

            if 'save_and_continue' in request.form:
                return redirect_to('admin/warmaps/edit', warmap_id=warmap.id)
            return redirect_to('admin/warmaps')
    return render_admin_response('admin/warmap_edit.html', 'war.maps',
                                    form=form.as_widget())

@require_admin_privilege(WAR_MANAGE)
def warmap_delete(request, warmap_id=None):
    warmap = None
    if warmap_id is not None:
        warmap = WarMap.query.get(warmap_id)
        if warmap is None:
            raise NotFound()
    form = forms.DeleteWarMapForm(warmap)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/warmaps/edit', warmap_id=warmap_id)
        elif request.form.get('confirm') and form.validate(request.form):
            name = str(warmap.name)
            form.delete_warmap()
            db.commit()
            admin_flash(_('Warmap %s was deleted successfully') % name, 'remove')
            return redirect_to('admin/warmaps')

    return render_admin_response('admin/warmap_delete.html', 'war.maps',
                                 form=form.as_widget())

@require_admin_privilege(WAR_MANAGE)
def warresult_edit(request, war_id=None):
    war = None
    if war_id is not None:
        war = War.query.get(war_id)
        if war is None:
            raise NotFound()
    else:
        raise NotFound()
    warresult = WarResult.query.get(war_id)
    form = forms.EditWarResultForm(war, warresult)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/wars/edit', war_id=war_id)
        elif request.form.get('delete'):
            if warresult is not None:
                db.delete(warresult)
                db.commit()
                admin_flash(_('The result for %s was deleted successfully') % war.clanname, 'remove')
            return form.redirect('admin/wars/edit', war_id=war_id)
        elif form.validate(request.form):
            if warresult is None:
                warresult = form.make_warresult()
                msg = _('The result for war %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('The result for war %s was updated successfully.')
                icon = 'info'

            admin_flash(msg % (war.clanname), icon)

            db.commit()

            if 'save_and_continue' in request.form:
                return redirect_to('admin/warresult_edit', war_id=war_id)
            return redirect_to('admin/wars')
    return render_admin_response('admin/warresult_edit.html', 'war.wars',
                                    form=form.as_widget())

@require_admin_privilege(WAR_MANAGE)
def warmode_list(request, page):
    """List warmodes in backend"""

    data = WarMode.query.get_list('admin/warmodes', per_page=PER_PAGE, page=page,
                                 paginator=AdminPagination)

    return render_admin_response('admin/warmode_list.html', 'war.modes',
                                  **data)

@require_admin_privilege(WAR_MANAGE)
def warmode_edit(request, warmode_id=None):
    """Edit an existing warmode or create a new one."""

    warmode = None
    if warmode_id is not None:
        warmode = WarMode.query.get(warmode_id)
        if warmode is None:
            raise NotFound()
    form = forms.EditWarModeForm(warmode)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('admin/warmodes')
        elif request.form.get('delete') and warmode:
            return redirect_to('admin/warmodes/delete', warmode_id=warmode_id)
        elif form.validate(request.form):
            if warmode is None:
                warmode = form.make_warmode()
                msg = _('Warmode %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('Warmode %s was updated successfully.')
                icon = 'info'

            admin_flash(msg % (warmode.name), icon)

            db.commit()

            if 'save_and_continue' in request.form:
                return redirect_to('admin/warmodes/edit', warmode_id=warmode.id)
            return redirect_to('admin/warmodes')
    return render_admin_response('admin/warmode_edit.html', 'war.modes',
                                    form=form.as_widget())

@require_admin_privilege(WAR_MANAGE)
def warmode_delete(request, warmode_id=None):
    warmode = None
    if warmode_id is not None:
        warmode = WarMode.query.get(warmode_id)
        if warmode is None:
            raise NotFound()
    form = forms.DeleteWarModeForm(warmode)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/warmodes/edit', warmode_id=warmode_id)
        elif request.form.get('confirm') and form.validate(request.form):
            name = str(warmode.name)
            form.delete_warmode()
            db.commit()
            admin_flash(_('Warmode %s was deleted successfully') % name, 'remove')
            return redirect_to('admin/warmodes')

    return render_admin_response('admin/warmode_delete.html', 'war.modes',
                                 form=form.as_widget())
