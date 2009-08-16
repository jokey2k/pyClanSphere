# -*- coding: utf-8 -*-
"""
    pyClanSphere.views
    ~~~~~~~~~~~~~~~~~~

    This module binds all the endpoints specified in `pyClanSphere.urls` to
    python functions in the view modules.


    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.views import account, admin, core
from pyClanSphere import i18n


#: bind the views to url endpoints
all_views = {
    'core/index':               core.index,
    'core/serve_translations':  i18n.serve_javascript,

    # account views
    'account/index':            account.index,
    'account/login':            account.login,
    'account/logout':           account.logout,
    'account/delete':           account.delete_account,
    'account/about_pyClanSphere':       account.about_pyClanSphere,
    'account/help':             account.help,
    'account/profile':          account.profile,
    'account/notification_settings':
                                account.notification_settings,

    # admin views
    'admin/index':              admin.index,
    'admin/bookmarklet':        admin.bookmarklet,
    'admin/manage_users':       admin.manage_users,
    'admin/new_user':           admin.edit_user,
    'admin/edit_user':          admin.edit_user,
    'admin/delete_user':        admin.delete_user,
    'admin/manage_groups':      admin.manage_groups,
    'admin/new_group':          admin.edit_group,
    'admin/edit_group':         admin.edit_group,
    'admin/delete_group':       admin.delete_group,
    'admin/options':            admin.options,
    'admin/basic_options':      admin.basic_options,
    'admin/urls':               admin.urls,
    'admin/theme':              admin.theme,
    'admin/configure_theme':    admin.configure_theme,
    'admin/plugins':            admin.plugins,
    'admin/remove_plugin':      admin.remove_plugin,
    'admin/cache':              admin.cache,
    'admin/configuration':      admin.configuration,
    'admin/maintenance':        admin.maintenance,
    'admin/information':        admin.information,
    'admin/log':                admin.log,
    'admin/help':               admin.help,
}

#: the privileges for these content types are defined in pyClanSphere.privileges
admin_content_type_handlers = {
}

absolute_url_handlers = []
