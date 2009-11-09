# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    This module implements all the views for the gamesquad module.
    
    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os

from werkzeug.exceptions import NotFound, Forbidden

from pyClanSphere import cache
from pyClanSphere.api import *
from pyClanSphere.privileges import CLAN_ADMIN
from pyClanSphere.utils.admin import require_admin_privilege, flash as admin_flash
from pyClanSphere.utils.http import redirect_to
from pyClanSphere.utils.pagination import AdminPagination
from pyClanSphere.views.account import render_account_response
from pyClanSphere.views.admin import render_admin_response, PER_PAGE

from pyClanSphere.plugins.war import forms
from pyClanSphere.plugins.war.models import War, WarMap, warstates, memberstates
from pyClanSphere.plugins.war.privileges import WAR_MANAGE

# Frontend stuff
def war_index(request, page):
    """List wars in frontend"""
    
    data = War.query.get_list(page=page)
    
    return render_response('war_index.html', **data)

def war_detail(request, war_id=None):
    """Show details of a specific war"""
    
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
                           warstates=warstates, memberstates=memberstates)

def warmap_list(request, page):
    """List all entered warmaps"""
    
    data = WarMap.query.get_list(page=page)
    
    return render_response('war_mapindex.html', **data)

def warmap_details(request, warmap_id=None):
    if warmap_id is None:
        raise NotFound()
    warmap = WarMap.query.get(warmap_id)
    if warmap is None:
        raise NotFound()
    
    return render_response('war_mapdetail.html', warmap=warmap)

# Backend stuff

@require_admin_privilege(WAR_MANAGE)
def war_list(request, page):
    """List wars in backend"""
    
    data = War.query.get_list(per_page=PER_PAGE, page=page,
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
            return form.redirect('admin/war_list')
        elif request.form.get('delete') and war:
            return redirect_to('admin/war_delete', war_id=war_id)
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
                return redirect_to('admin/war_edit', war_id=war.id)
            return form.redirect('admin/war_list')
    return render_admin_response('admin/war_edit.html', 'war.wars',
                                    form=form.as_widget())

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
            return form.redirect('admin/war_edit', war_id=war_id)
        elif request.form.get('confirm') and form.validate(request.form):
            warname = str(war.clanname)
            form.delete_war()
            db.commit()
            admin_flash(_('The war %s was deleted successfully') % warname, 'remove')
            return form.redirect('admin/war_list')
    
    return render_admin_response('admin/war_delete.html', 'war.wars',
                                 form=form.as_widget())

@require_admin_privilege(WAR_MANAGE)
def warmap_list(request, page):
    """List warmaps in backend"""
    
    data = WarMap.query.get_list(per_page=PER_PAGE, page=page,
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
            return form.redirect('admin/warmap_list')
        elif request.form.get('delete') and warmap:
            return redirect_to('admin/warmap_delete', warmap_id=warmap_id)
        elif form.validate(request.form):
            if warmap is None:
                warmap = form.make_warmap()
                msg = _('The warmap %s was created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('The war map %s was updated successfully.')
                icon = 'info'
            
            admin_flash(msg % (warmap.name), icon)
            
            db.commit()
            
            mapfile = request.files.get('mapfile')
            if mapfile:
                warmap.place_file(mapfile)
            
            if 'save_and_continue' in request.form:
                return redirect_to('admin/warmap_edit', warmap_id=warmap.id)
            return form.redirect('admin/warmap_list')
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
            return form.redirect('admin/warmap_edit', warmap_id=warmap_id)
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('admin/warmap_edit', warmap_id=warmap_id)
            form.add_invalid_redirect_target('admin/warmap_delete', warmap_id=warmap_id)
            name = str(warmap.name)
            form.delete_warmap()
            db.commit()
            admin_flash(_('The war map %s was deleted successfully') % name, 'remove')
            return form.redirect('admin/warmap_list')
    
    return render_admin_response('admin/warmap_delete.html', 'war.maps',
                                 form=form.as_widget())
