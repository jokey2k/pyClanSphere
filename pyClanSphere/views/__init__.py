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
    'core/service_rsd':         core.service_rsd,
    'core/json_service':        core.json_service,
    'core/xml_service':         core.xml_service,

    # account views
    'account/index':            account.index,
    'account/login':            account.login,
    'account/logout':           account.logout,
    'account/lost_password':    account.lost_password,
    'account/reset_password':   account.reset_password,
    'account/delete':           account.delete_account,
    'account/about_pyClanSphere':       account.about_pyClanSphere,
    'account/help':             account.help,
    'account/profile':          account.profile,
    'account/password':         account.change_password,
    'account/notification_settings':
                                account.notification_settings,
    'account/imaccount_list':   account.imaccount_list,
    'account/imaccount_new':    account.imaccount_edit,
    'account/imaccount_edit':   account.imaccount_edit,
    'account/imaccount_delete': account.imaccount_delete,

    # admin views
    'admin/index':              admin.index,
    'admin/manage_users':       admin.manage_users,
    'admin/new_user':           admin.edit_user,
    'admin/edit_user':          admin.edit_user,
    'admin/delete_user':        admin.delete_user,
    'admin/delete_imaccount':   admin.delete_imaccount,
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
    'admin/recaptcha':          admin.recaptcha,
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
