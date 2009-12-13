# -*- coding: utf-8 -*-
"""
    pyClanSphere.views.admin
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements the admin views. The admin interface is only
    available for admins, editors and authors but not for subscribers. For
    subscribers a simplified account management system exists at /account.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from os import remove, sep as pathsep
from os.path import exists
from urlparse import urlparse

from werkzeug import escape
from werkzeug.exceptions import NotFound, BadRequest, Forbidden

from pyClanSphere.privileges import assert_privilege, require_privilege, CLAN_ADMIN
from pyClanSphere.i18n import _, ngettext
from pyClanSphere.application import get_request, url_for, emit_event, \
     render_response, get_application
from pyClanSphere.database import db, secure_database_uri
from pyClanSphere.models import User, Group, IMAccount
from pyClanSphere.utils import dump_json, load_json
from pyClanSphere.utils.validators import is_valid_email, is_valid_url, check
from pyClanSphere.utils.admin import flash, require_admin_privilege
from pyClanSphere.utils.text import gen_slug
from pyClanSphere.utils.pagination import AdminPagination
from pyClanSphere.utils.http import redirect_back, redirect_to, redirect
from pyClanSphere.i18n import parse_datetime, format_system_datetime, \
     list_timezones, has_timezone, list_languages, has_language
from pyClanSphere.pluginsystem import install_package, InstallationError, \
     SetupError, get_object_name
from pyClanSphere.forms import LoginForm, ChangePasswordForm, PluginForm, \
     LogOptionsForm, BasicOptionsForm, URLOptionsForm, EditUserForm, DeleteUserForm, \
     CacheOptionsForm, EditGroupForm, DeleteGroupForm, ThemeOptionsForm, DeleteImportForm, ExportForm, \
     MaintenanceModeForm, RemovePluginForm, DeleteIMAccountForm, \
     make_config_form, make_notification_form

#: how many posts / comments should be displayed per page?
PER_PAGE = 20


def render_admin_response(template_name, _active_menu_item=None, **values):
    """Works pretty much like the normal `render_response` function but
    it emits some events to collect navigation items and injects that
    into the template context. This also gets the flashes messages from
    the user session and injects them into the template context after the
    plugins have provided theirs in the `before-admin-response-rendered`
    event.

    The second parameter can be the active menu item if wanted. For example
    ``'options.overview'`` would show the overview button in the options
    submenu. If the menu is a standalone menu like the dashboard (no
    child items) you can also just use ``'dashboard'`` to highlight that.
    """
    request = get_request()

    # set up the core navigation bar
    navigation_bar = [
        ('dashboard', url_for('admin/index'), _(u'Dashboard'), [])
    ]

    Access_items = []

    # set up the administration menu bar
    if request.user.has_privilege(CLAN_ADMIN):
        navigation_bar.extend([
            ('users_groups', url_for('admin/manage_users'), _(u'Users and Groups'), [
                ('users', url_for('admin/manage_users'), _(u'Users')),
                ('groups', url_for('admin/manage_groups'), _(u'Groups'))
            ])
        ])
        navigation_bar.extend([
            ('options', url_for('admin/options'), _(u'Options'), [
                ('basic', url_for('admin/basic_options'), _(u'Basic')),
                ('urls', url_for('admin/urls'), _(u'URLs')),
                ('theme', url_for('admin/theme'), _(u'Theme')),
                ('cache', url_for('admin/cache'), _(u'Cache')),
                ('configuration', url_for('admin/configuration'),
                 _(u'Configuration Editor'))
            ])
        ])

    # add the help item to the navigation bar
    system_items = [('help', url_for('admin/help'), _(u'Help'))]

    if request.user.has_privilege(CLAN_ADMIN):
        system_items[0:0] = [
            ('information', url_for('admin/information'),
             _(u'Information')),
            ('maintenance', url_for('admin/maintenance'),
             _(u'Maintenance')),
            ('plugins', url_for('admin/plugins'), _(u'Plugins')),
            ('log', url_for('admin/log'), _('Log'))
        ]

    navigation_bar.append(('system', system_items[0][1], _(u'System'),
                           system_items))

    #! allow plugins to extend the navigation bar
    emit_event('modify-admin-navigation-bar', request, navigation_bar)

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

    # if we are in maintenance_mode the user should know that, no matter
    # on which page he is.
    if request.app.cfg['maintenance_mode'] and \
                                        request.user.has_privilege(CLAN_ADMIN):
        flash(_(u'pyClanSphere is in maintenance mode. Don\'t forget to '
                u'<a href="%s">turn it off again</a> once you finish your '
                u'changes.') % url_for('admin/maintenance'))

    # check for broken plugins if we have the plugin guard enabled
    if request.app.cfg['plugin_guard']:
        plugins_to_deactivate = []
        for plugin in request.app.plugins.itervalues():
            if plugin.active and plugin.setup_error is not None:
                flash(_(u'Could not activate plugin “%(name)s”: %(error)s') % {
                    'name':     plugin.html_display_name,
                    'error':    plugin.setup_error
                })
                plugins_to_deactivate.append(plugin.name)

        if plugins_to_deactivate:
            #TODO: it's quite tricky – it needs at least two reloads to
            #      deactivate the plugin (which is in fact a application reload)
            cfg = request.app.cfg.edit()
            cfg['plugins'] = u', '.join(sorted(set(request.app.cfg['plugins']) - \
                                               set(plugins_to_deactivate)))
            cfg.commit()
            # we change the plugins inline so that the user get somewhat more
            # informations
            request.app.cfg.touch()


    #! used to flash messages, add links to stylesheets, modify the admin
    #! context etc.
    emit_event('before-admin-response-rendered', request, values)

    # the admin variables is pushed into the context after the event was
    # sent so that plugins can flash their messages. If we would emit the
    # event afterwards all flashes messages would appear in the request
    # after the current request.
    values['admin'] = {
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
        } for type, msg in request.session.pop('admin/flashed_messages', [])],
        'active_pane': _active_menu_item
    }
    return render_response(template_name, **values)


@require_admin_privilege()
def index(request):
    """Show the admin interface index page.

    In the future this will be a container page like the main index is.
    """
    return render_admin_response('admin/index.html', 'dashboard')


def bookmarklet(request):
    """Requests to this view are usually triggered by the bookmarklet
    from the edit-post page.  Currently this is a redirect to the new-post
    page with some small modifications but in the future this could be
    expanded to add a wizard or something.
    """
    if request.args['mode'] != 'newpost':
        raise BadRequest()
    body = '%s\n\n<a href="%s">%s</a>' % (
        request.args.get('text', _(u'Text here...')),
        request.args['url'],
        request.args.get('title', _(u'Untitled Page'))
    )
    return redirect_to('admin/new_entry',
        title=request.args.get('title'),
        body=body
    )


def _make_post_dispatcher(action):
    """Creates a new dispatcher for the given content type action.  This
    already checks if the user can enter the admin panel but not if the
    user has the required privileges.
    """
    @require_admin_privilege()
    def func(request, post_id):
        """Dispatch to the request handler for a post."""
        post = Post.query.get(post_id)
        if post is None:
            raise NotFound()
        try:
            handler = request.app.admin_content_type_handlers \
                [post.content_type][action]
        except KeyError:
            raise NotFound()
        return handler(request, post)
    func.__name__ = 'dispatch_post_' + action
    return func


@require_admin_privilege(CLAN_ADMIN)
def manage_users(request, page):
    """Show all users in a list."""
    users = User.query.namesort().limit(PER_PAGE).offset(PER_PAGE * (page - 1)).all()
    pagination = AdminPagination('admin/manage_users', page, PER_PAGE,
                                 User.query.count())
    if not users and page != 1:
        raise NotFound()
    return render_admin_response('admin/manage_users.html', 'users_groups.users',
                                 users=users, pagination=pagination)


@require_admin_privilege(CLAN_ADMIN)
def edit_user(request, user_id=None):
    """Edit a user.  This can also create a user.  If a new user is created
    the dialog is simplified, some unimportant details are left out.
    """
    user = None
    if user_id is not None:
        user = User.query.get(user_id)
        if user is None:
            raise NotFound()
    form = EditUserForm(user)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/manage_users')
        elif request.form.get('delete') and user:
            return redirect_to('admin/delete_user', user_id=user.id)
        elif form.validate(request.form):
            if user is None:
                user = form.make_user()
                msg = _(u'User %s created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _(u'User %s edited successfully.')
                icon = 'info'
            db.commit()
            html_user_detail = u'<a href="%s">%s</a>' % (
                escape(url_for(user)),
                escape(user.username)
            )
            flash(msg % html_user_detail, icon)
            if request.form.get('save'):
                return form.redirect('admin/manage_users')
            return redirect_to('admin/edit_user', user_id=user.id)

    return render_admin_response('admin/edit_user.html', 'users_groups.users',
                                 form=form.as_widget())


@require_admin_privilege(CLAN_ADMIN)
def delete_user(request, user_id):
    """Like all other delete screens just that it deletes a user."""
    user = User.query.get(user_id)
    if user is None:
        raise NotFound()
    form = DeleteUserForm(user)
    if user == request.user:
        flash(_(u'You cannot delete yourself.'), 'error')
        return form.redirect('admin/manage_users')

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/edit_user', user_id=user.id)
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('admin/edit_user', user_id=user.id)
            msg = _(u'User %s removed successfully.') % escape(user.display_name)
            icon = 'remove'
            form.delete_user()
            db.commit()
            flash(msg, icon)
            return form.redirect('admin/manage_users')

    return render_admin_response('admin/delete_user.html', 'users_groups.users',
                                 form=form.as_widget())

@require_admin_privilege(CLAN_ADMIN)
def delete_imaccount(request, account_id, user_id=None):
    """Delete an Instant Messenger Account from admin panel"""

    imaccount = IMAccount.query.get(account_id)
    if imaccount is None:
        raise NotFound()
    form = DeleteIMAccountForm(imaccount)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/edit_user', user_id=imaccount.user.id)
        elif request.form.get('confirm') and form.validate(request.form):
            account = str(imaccount.account)
            user_id = imaccount.user.id
            form.delete_account()
            db.commit()
            flash(_('IM account %s was deleted successfully') % account, 'remove')
            return form.redirect('admin/edit_user', user_id=user_id)

    return render_admin_response('admin/imaccount_delete.html', 'users_groups.users',
                                 form=form.as_widget())

@require_admin_privilege(CLAN_ADMIN)
def manage_groups(request):
    groups = Group.query.all()
    return render_admin_response('admin/manage_groups.html', 'users_groups.groups',
                                 groups=groups)

@require_admin_privilege(CLAN_ADMIN)
def edit_group(request, group_id=None):
    """Edit a Group.  This is used to create a group as well."""
    group = None
    if group_id is not None:
        group = Group.query.get(group_id)
        if group is None:
            raise NotFound()
    form = EditGroupForm(group)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/manage_groups')
        elif request.form.get('delete') and group:
            return redirect_to('admin/delete_group', group_id=group.id)
        elif form.validate(request.form):
            if group is None:
                group = form.make_group()
                msg = _(u'Group %s created successfully.')
                icon = 'add'
            else:
                form.save_changes()
                msg = _(u'Group %s edited successfully.')
                icon = 'info'
            db.commit()
            html_group_detail = u'<a href="%s">%s</a>' % (
                escape(url_for(group)),
                escape(group.name))
            flash(msg % html_group_detail, icon)

            if request.form.get('save'):
                return form.redirect('admin/manage_groups')
            return redirect_to('admin/edit_group', group_id=group.id)

    return render_admin_response('admin/edit_group.html', 'users_groups.groups',
                                 form=form.as_widget())

@require_admin_privilege(CLAN_ADMIN)
def delete_group(request, group_id):
    """Like all other delete screens just that it deletes a group."""
    group = Group.query.get(group_id)
    if group is None:
        raise NotFound()
    form = DeleteGroupForm(group)

    if request.method == 'POST':
        if request.form.get('cancel'):
            return form.redirect('admin/edit_group', group_id=group.id)
        elif request.form.get('confirm') and form.validate(request.form):
            form.add_invalid_redirect_target('admin/edit_group',
                                             group_id=group.id)
            form.delete_group()
            db.commit()
            return form.redirect('admin/manage_groups')

    return render_admin_response('admin/delete_group.html', 'users_groups.groups',
                                 form=form.as_widget())


@require_admin_privilege(CLAN_ADMIN)
def options(request):
    """So far just a redirect page, later it would be a good idea to have
    a page that shows all the links to configuration things in form of
    a simple table.
    """
    return redirect_to('admin/basic_options')


@require_admin_privilege(CLAN_ADMIN)
def basic_options(request):
    """The dialog for basic options such as the site title etc."""
    # flash an altered message if the url is ?altered=true.  For more information
    # see the comment that redirects to the url below.
    if request.args.get('altered') == 'true':
        flash(_(u'Configuration altered successfully.'), 'configure')
        return redirect_to('admin/basic_options')

    form = BasicOptionsForm()

    if request.method == 'POST' and form.validate(request.form):
        form.apply()

        # because the configuration page could change the language and
        # we want to flash the message "configuration changed" in the
        # new language rather than the old.  As a matter of fact we have
        # to wait for pyClanSphere to reload first which is why we do the
        # actual flashing after one reload.
        return redirect_to('admin/basic_options', altered='true')

    return render_admin_response('admin/basic_options.html', 'options.basic',
                                 form=form.as_widget())


@require_admin_privilege(CLAN_ADMIN)
def urls(request):
    """A config page for URL depending settings."""
    form = URLOptionsForm()

    if request.method == 'POST' and form.validate(request.form):
        form.apply()
        db.commit()
        flash(_(u'URL configuration changed.'), 'configure')
        # because the next request could reload the application and move
        # the admin interface we construct the URL to this page by hand.
        return redirect(form['admin_url_prefix'][1:] + '/options/urls')

    return render_admin_response('admin/url_options.html', 'options.urls',
                                 form=form.as_widget())


@require_admin_privilege(CLAN_ADMIN)
def theme(request):
    """Allow the user to select one of the themes that are available."""
    form = ThemeOptionsForm()

    if request.method == 'GET':
        if 'configure' in request.args:
            return redirect_to('admin/configure_theme')
        elif form.validate(request.args):
            new_theme = request.args.get('select')
            if new_theme in request.app.themes:
                request.app.cfg.change_single('theme', new_theme)
                flash(_(u'Theme changed successfully.'), 'configure')
                return redirect_to('admin/theme')

    return render_admin_response('admin/theme.html', 'options.theme',
        themes=sorted(
            request.app.themes.values(),
            key=lambda x: x.name == 'default' or x.display_name.lower()
        ),
        current_theme=request.app.theme,
        form=form.as_widget()
    )


@require_admin_privilege(CLAN_ADMIN)
def configure_theme(request):
    if not request.app.theme.configurable:
        flash(_(u'This theme is not configurable'), 'error')
        return redirect_to('admin/theme')
    return request.app.theme.configuration_page(request)


@require_admin_privilege(CLAN_ADMIN)
def plugins(request):
    """Load and unload plugins and reload pyClanSphere if required."""
    form = PluginForm()

    if request.method == 'POST' and form.validate(request.form):
        form.apply()
        flash(_('Plugin configuration changed'), 'configure')

        new_plugin = request.files.get('new_plugin')
        if new_plugin:
            try:
                plugin = install_package(request.app, new_plugin)
            except InstallationError, e:
                flash(e.message, 'error')
            else:
                flash(_(u'Plugin “%s” added successfully. You can now '
                        u'enable it in the plugin list.') %
                      plugin.html_display_name, 'add')

        return redirect_to('admin/plugins')

    return render_admin_response('admin/plugins.html', 'system.plugins',
        form=form.as_widget(),
        plugins=sorted(request.app.plugins.values(), key=lambda x: x.name)
    )


@require_admin_privilege(CLAN_ADMIN)
def remove_plugin(request, plugin):
    """Remove an inactive, instance installed plugin completely."""
    plugin = request.app.plugins.get(plugin)
    if plugin is None or \
       not plugin.instance_plugin or \
       plugin.active:
        raise NotFound()
    form = RemovePluginForm(plugin)

    if request.method == 'POST' and form.validate(request.form):
        if request.form.get('confirm'):
            try:
                plugin.remove()
            except IOError:
                flash(_(u'Could not remove the plugin “%s” because an '
                        u'IO error occurred. Wrong permissions?') %
                      plugin.html_display_name)
            flash(_(u'The plugin “%s” was removed from the instance '
                    u'successfully.') % escape(plugin.display_name), 'remove')
        return form.redirect('admin/plugins')

    return render_admin_response('admin/remove_plugin.html', 'options.plugins',
        plugin=plugin,
        form=form.as_widget()
    )


@require_admin_privilege(CLAN_ADMIN)
def cache(request):
    """Configure the cache."""
    form = CacheOptionsForm()

    if request.method == 'POST':
        if 'clear_cache' in request.form:
            request.app.cache.clear()
            flash(_(u'The cache was cleared successfully.'), 'configure')
            return redirect_to('admin/cache')
        elif form.validate(request.form):
            form.apply()
            flash(_(u'Cache settings were changed successfully.'), 'configure')
            return redirect_to('admin/cache')

    return render_admin_response('admin/cache.html', 'options.cache',
                                 form=form.as_widget())


@require_admin_privilege(CLAN_ADMIN)
def configuration(request):
    """Advanced configuration editor.  This is useful for development or if a
    plugin doesn't ship an editor for the configuration values.  Because all
    the values are not further checked it could easily be that pyClanSphere is
    left in an unusable state if a variable is set to something bad.  Because
    of this the editor shows a warning and must be enabled by hand.
    """
    form = make_config_form()

    if request.method == 'POST':
        if request.form.get('enable_editor'):
            request.session['ace_on'] = True
        elif request.form.get('disable_editor'):
            request.session['ace_on'] = False
        elif form.validate(request.form):
            form.apply()
            flash(_(u'Configuration updated successfully.'), 'configure')
            return redirect_to('admin/configuration')
        else:
            flash(_(u'Could not save the configuration because the '
                    u'configuration is invalid.'), 'error')

    return render_admin_response('admin/configuration.html',
                                 'options.configuration',
                                 form=form.as_widget(), editor_enabled=
                                 request.session.get('ace_on', False))


@require_admin_privilege(CLAN_ADMIN)
def maintenance(request):
    """Enable / Disable maintenance mode."""
    cfg = request.app.cfg
    form = MaintenanceModeForm()
    if request.method == 'POST' and form.validate(request.form):
        cfg.change_single('maintenance_mode', not cfg['maintenance_mode'])
        if not cfg['maintenance_mode']:
            flash(_(u'Maintenance mode disabled.  The site is now '
                    u'publicly available.'), 'configure')
        return redirect_to('admin/maintenance')

    return render_admin_response('admin/maintenance.html',
                                 'system.maintenance',
        maintenance_mode=cfg['maintenance_mode'],
        form=form.as_widget()
    )


@require_admin_privilege(CLAN_ADMIN)
def information(request):
    """Shows some details about this pyClanSphere installation.  It's useful for
    debugging and checking configurations.  If severe errors in a pyClanSphere
    installation occur it's a good idea to dump this page and attach it to
    a bug report mail.
    """
    from platform import platform
    from sys import version as python_version
    from threading import activeCount
    from jinja2.defaults import DEFAULT_NAMESPACE, DEFAULT_FILTERS
    from pyClanSphere import environment, __version__ as pyClanSphere_version

    export = request.args.get('do') == 'export'
    database_uri = request.app.cfg['database_uri']
    if export:
        database_uri = secure_database_uri(database_uri)

    content_types = {}
    for name, funcs in request.app.admin_content_type_handlers.iteritems():
        if name in content_types:
            for action, func in funcs.iteritems():
                content_types[name][action] = get_object_name(func)
    content_types = sorted(content_types.values(), key=lambda x: x['name'])

    response = render_admin_response('admin/information.html', 'system.information',
        apis=[{
            'name':         name,
            'clan_id':      clan_id,
            'preferred':    preferred,
            'endpoint':     endpoint
        } for name, (clan_id, preferred, endpoint) in request.app.apis.iteritems()],
        endpoints=[{
            'name':         rule.endpoint,
            'rule':         unicode(rule)
        } for rule in sorted(request.app.url_map._rules, key=lambda x: x.endpoint)],
        views=sorted([{
            'endpoint':     endpoint,
            'handler':      get_object_name(view)
        } for endpoint, view
            in request.app.views.iteritems()], key=lambda x: x['endpoint']),
        absolute_url_handlers=[get_object_name(handler) for handler
                               in request.app._absolute_url_handlers],
        content_types=content_types,
        privileges=request.app.list_privileges(),
        servicepoints=sorted([{
            'name':         name,
            'handler':      get_object_name(service)
        } for name, service in request.app._services.iteritems()],
            key=lambda x: x['name']),
        configuration=request.app.cfg.get_public_list(export),
        hosting_env={
            'persistent':       not request.is_run_once,
            'multithreaded':    request.is_multithread,
            'thread_count':     activeCount(),
            'multiprocess':     request.is_multiprocess,
            'wsgi_version':     '.'.join(map(str, request.environ['wsgi.version']))
        },
        plugins=sorted(request.app.plugins.values(), key=lambda x: not x.active and x.name),
        python_version='<br>'.join(map(escape, python_version.splitlines())),
        pyClanSphere_env=environment,
        pyClanSphere_version=pyClanSphere_version,
        template_globals=[name for name, obj in
                          sorted(request.app.template_env.globals.items())
                          if name not in DEFAULT_NAMESPACE],
        template_filters=[name for name, obj in
                          sorted(request.app.template_env.filters.items())
                          if name not in DEFAULT_FILTERS],
        instance_path=request.app.instance_folder,
        database_uri=database_uri,
        platform=platform(),
        export=export
    )

    if export:
        response.headers['Content-Disposition'] = 'attachment; ' \
            'filename="pyClanSphere-environment.html"'

    return response


@require_admin_privilege(CLAN_ADMIN)
def log(request, page):
    page = request.app.log.view().get_page(page)
    form = LogOptionsForm()
    if request.method == 'POST' and form.validate(request.form):
        form.apply()
        flash(_('Log changes saved.'), 'configure')
        return redirect_to('admin/log', page=page.number)
    return render_admin_response('admin/log.html', 'system.log',
                                 page=page, form=form.as_widget())


@require_admin_privilege()
def help(req, page=''):
    """Show help page."""
    from pyClanSphere.docs import load_page, get_resource

    rv = load_page(req.app, page)
    if rv is None:
        resource = get_resource(req.app, page)
        if resource is None:
            return render_admin_response('admin/help_404.html', 'system.help')
        return resource

    parts, is_index = rv
    ends_with_slash = not page or page.endswith('/')
    if is_index and not ends_with_slash:
        return redirect_to('admin/help', page=page + '/')
    elif not is_index and ends_with_slash:
        raise NotFound()

    return render_admin_response('admin/help.html', 'system.help', **parts)

