# -*- coding: utf-8 -*-
"""
    pyClanSphere.views.account
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements the account views.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug import escape
from werkzeug.exceptions import NotFound, Forbidden

from pyClanSphere.api import *
from pyClanSphere.forms import LoginForm, DeleteAccountForm, EditProfileForm, \
     make_notification_form, DeleteIMAccountForm, EditIMAccountForm, \
     ChangePasswordForm
from pyClanSphere.models import IMAccount
from pyClanSphere.i18n import _, ngettext
from pyClanSphere.privileges import ENTER_ADMIN_PANEL
from pyClanSphere.utils.account import flash, require_account_privilege
from pyClanSphere.utils.http import redirect_back, redirect_to
from pyClanSphere.utils.pagination import AdminPagination


def render_account_response(template_name, _active_menu_item=None, **values):
    """Works pretty much like the normal `render_response` function but
    it emits some events to collect navigation items and injects that
    into the template context. This also gets the flashes messages from
    the user session and injects them into the template context after the
    plugins have provided theirs in the `before-account-response-rendered`
    event.

    The second parameter can be the active menu item if wanted. For example
    ``'account.notifications'`` would show the notifications button in the account
    submenu. If the menu is a standalone menu like the dashboard (no
    child items) you can also just use ``'dashboard'`` to highlight that.
    """
    request = get_request()

    # set up the core navigation bar
    navigation_bar = [
        ('dashboard', url_for('account/index'), _(u'Dashboard'), []),
        ('profile', url_for('account/profile'), _(u'Profile'), [
            ('profile', url_for('account/profile'), _(u'Profile')),
            ('password', url_for('account/password'), _(u'Password'))
        ]),
        ('imaccounts', url_for('account/imaccount_list'), _('IM accounts'), []),
        ('notifications', url_for('account/notification_settings'),
         _(u'Notifications'), [])
    ]

    # add the about items to the navigation bar
    system_items = [
        ('about', url_for('account/about_pyClanSphere'), _(u'About'))
    ]
    if request.user.is_admin:
        # Current documentation is addressed for admins
        system_items.append(('help', url_for('account/help'), _(u'Help')))

    navigation_bar.append(('system', system_items[0][1], _(u'System'),
                           system_items))

    #! allow plugins to extend the navigation bar
    emit_event('modify-account-navigation-bar', request, navigation_bar)

    # find out which is the correct menu and submenu bar
    active_menu = active_submenu = None
    if _active_menu_item is not None:
        p = _active_menu_item.split('.')
        if len(p) == 1:
            active_menu = p[0]
        else:
            active_menu, active_submenu = p
    for id, url, title, subnavigation_bar in navigation_bar:
        if id == active_menu:
            break
    else:
        subnavigation_bar = []


    #! used to flash messages, add links to stylesheets, modify the admin
    #! context etc.
    emit_event('before-account-response-rendered', request, values)

    # the admin variables is pushed into the context after the event was
    # sent so that plugins can flash their messages. If we would emit the
    # event afterwards all flashes messages would appear in the request
    # after the current request.
    values['account'] = {
        'user_can_enter_admin_panel':
                        request.user.has_privilege(ENTER_ADMIN_PANEL),
        'navbar': [{
            'id':       id,
            'url':      url,
            'title':    title,
            'active':   active_menu == id
        } for id, url, title, children in navigation_bar],
        'ctxnavbar': [{
            'id':       id,
            'url':      url,
            'title':    title,
            'active':   active_submenu == id
        } for id, url, title in subnavigation_bar],
        'messages': [{
            'type':     type,
            'msg':      msg
        } for type, msg in request.session.pop('account/flashed_messages', [])],
        'active_pane': _active_menu_item
    }
    return render_response(template_name, **values)


def login(request):
    """Show a login page."""
    if request.user.is_somebody:
        return redirect_to('account/index')
    form = LoginForm()

    if request.method == 'POST' and form.validate(request.form):
        request.login(form['user'], form['permanent'])
        if request.user.is_admin:
            return form.redirect('admin/index')
        return form.redirect('account/index')

    return render_response('account/login.html', form=form.as_widget())


def logout(request):
    """Just logout and redirect to the login screen."""
    request.logout()
    return redirect_back('account/login')


@require_account_privilege()
def about_pyClanSphere(request):
    """Just show the pyClanSphere license and some other legal stuff."""
    return render_account_response('account/about_pyClanSphere.html',
                                   'system.about')


@require_account_privilege(ENTER_ADMIN_PANEL)   # XXX: For now.
def help(req, page=''):
    """Show help page."""
    from pyClanSphere.docs import load_page, get_resource

    rv = load_page(req.app, page)
    if rv is None:
        resource = get_resource(req.app, page)
        if resource is None:
            return render_account_response('admin/help.html', 'system.help',
                                           not_found=True)
        return resource

    parts, is_index = rv
    ends_with_slash = not page or page.endswith('/')
    if is_index and not ends_with_slash:
        return redirect_to('account/help', page=page + '/')
    elif not is_index and ends_with_slash:
        raise NotFound()

    return render_account_response('account/help.html', 'system.help', **parts)


@require_account_privilege()
def index(request):
    """Show account details page"""
    return render_account_response('account/index.html', 'dashboard')


@require_account_privilege()
def profile(request):
    form = EditProfileForm(request.user)
    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('account/index')
        elif request.form.get('delete'):
            return redirect_to('account/delete')
        elif form.validate(request.form):
            form.save_changes()
            db.commit()
            flash(_(u'Your profile was updated successfully.'), 'info')
            return form.redirect('account/index')
    return render_account_response('account/edit_profile.html', 'profile.profile',
                                   form=form.as_widget())


@require_account_privilege()
def delete_account(request):
    form = DeleteAccountForm(request.user)
    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('account/profile')
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('account/profile')
            form.delete_user()
            request.logout()
            db.commit()
            return render_response('account/sorry_to_see_you_go.html')
    return render_account_response('account/delete_account.html', 'profile.profile',
                                   form=form.as_widget())


@require_account_privilege()
def notification_settings(request):
    """Allow the user to change his notification settings."""
    form = make_notification_form(request.user)
    if request.method == 'POST' and form.validate(request.form):
        form.apply()
        db.commit()
        flash(_('Notification settings changed.'), 'configure')
        return form.redirect('account/notification_settings')

    return render_account_response('account/notification_settings.html', 'notifications',
        form=form.as_widget(),
        systems=sorted(request.app.notification_manager.systems.values(),
                       key=lambda x: x.name.lower()),
        notification_types=sorted(
            request.app.notification_manager.types(request.user),
            key=lambda x: x.description.lower()
        )
    )


@require_account_privilege()
def change_password(request):
    """Allow the current user to change his password."""
    form = ChangePasswordForm(request.user)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('account/index')
        if form.validate(request.form):
            form.user.set_password(form['new_password'])
            db.commit()
            flash(_(u'Password changed successfully.'), 'configure')
            return form.redirect('account/index')

    return render_account_response('account/change_password.html','profile.password',
        form=form.as_widget()
    )


@require_account_privilege()
def imaccount_list(request, page):
    """List all registered imaccounts"""

    data = IMAccount.query.get_list(user=request.user, page=page, paginator=AdminPagination)

    return render_account_response('account/imaccount_list.html', 'imaccounts',
                                   **data)

@require_account_privilege()
def imaccount_edit(request, account_id=None):
    """Edit an existing game account or create a new one."""

    imaccount = None
    if account_id is not None:
        imaccount = IMAccount.query.get(account_id)
        if imaccount is None:
            raise NotFound()
        elif imaccount.user != request.user:
            raise Forbidden()
    form = EditIMAccountForm(request.user, imaccount)

    if request.method == 'POST':
        if 'cancel' in request.form:
            return form.redirect('account/imaccount_list')
        elif request.form.get('delete') and imaccount:
            return redirect_to('account/imaccount_delete', account_id=account_id)
        elif form.validate(request.form):
            if imaccount is None:
                imaccount = form.make_imaccount()
                msg = _('IM account %s was added successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _('IM account %s was updated successfully.')
                icon = 'info'
            flash(msg % (escape(imaccount.account)), icon)

            db.commit()
            if 'save_and_continue' in request.form:
                return redirect_to('account/imaccount_edit', account_id=imaccount.id)
            return form.redirect('account/imaccount_list')
    return render_account_response('account/imaccount_edit.html', 'imaccounts',
                                    form=form.as_widget())


@require_account_privilege()
def imaccount_delete(request, account_id):
    """Delete an InGame Account from user-account panel"""

    imaccount = IMAccount.query.get(account_id)
    if imaccount is None:
        raise NotFound()
    if imaccount.user != request.user:
        raise Forbidden()
    form = DeleteIMAccountForm(imaccount)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('account/imaccount_list')
        elif request.form.get('confirm') and form.validate(request.form):
            accountname = str(imaccount.account)
            form.delete_account()
            db.commit()
            flash(_('IM account %s was deleted successfully') % accountname, 'remove')
            return redirect_to('account/imaccount_list')

    return render_account_response('account/imaccount_delete.html', 'imaccounts',
                                   form=form.as_widget())
