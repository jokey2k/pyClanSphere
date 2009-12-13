# -*- coding: utf-8 -*-
"""
    pyClanSphere.urls
    ~~~~~~~~~~~~~~~~~

    This module implements a function that creates a list of urls for all
    the core components.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug.routing import Rule, Submount

def make_urls(app):
    """Make the URLs for a new pyClanSphere application."""
    base_urls = [
        Rule('/', endpoint='core/index'),
        Submount(app.cfg['account_url_prefix'], [
            Rule('/', endpoint='account/index'),
            Rule('/login', endpoint='account/login'),
            Rule('/logout', endpoint='account/logout'),
            Rule('/lost_password', endpoint='account/lost_password'),
            Rule('/reset_password/<string(length=36):req_id>', endpoint='account/reset_password'),
            Rule('/delete', endpoint='account/delete'),
            Rule('/profile', endpoint='account/profile'),
            Rule('/password', endpoint='account/password'),
            Rule('/notifications', endpoint='account/notification_settings'),
            Rule('/system/about', endpoint='account/about_pyClanSphere'),
            Rule('/system/help/', endpoint='account/help'),
            Rule('/system/help/<path:page>', endpoint='account/help'),
            Rule('/imaccounts/', endpoint='account/imaccount_list', defaults={'page': 1}),
            Rule('/imaccounts/page/<int:page>', endpoint='account/imaccount_list'),
            Rule('/imaccounts/new', endpoint='account/imaccount_new'),
            Rule('/imaccounts/<int:account_id>', endpoint='account/imaccount_edit'),
            Rule('/imaccounts/<int:account_id>/delete', endpoint='account/imaccount_delete')
        ])
    ]
    admin_urls = [
        Rule('/', endpoint='admin/index'),
        Rule('/_bookmarklet', endpoint='admin/bookmarklet'),
        Rule('/users/', endpoint='admin/manage_users', defaults={'page': 1}),
        Rule('/users/page/<int:page>', endpoint='admin/manage_users'),
        Rule('/users/new', endpoint='admin/new_user'),
        Rule('/users/<int:user_id>', endpoint='admin/edit_user'),
        Rule('/users/<int:user_id>/delete', endpoint='admin/delete_user'),
        Rule('/users/<int:user_id>/imaccount_delete/<int:account_id>', endpoint='admin/delete_imaccount'),
        Rule('/groups/', endpoint='admin/manage_groups'),
        Rule('/groups/new', endpoint='admin/new_group'),
        Rule('/groups/<int:group_id>', endpoint='admin/edit_group'),
        Rule('/groups/<int:group_id>/delete', endpoint='admin/delete_group'),
        Rule('/options/', endpoint='admin/options'),
        Rule('/options/basic', endpoint='admin/basic_options'),
        Rule('/options/urls', endpoint='admin/urls'),
        Rule('/options/theme/', endpoint='admin/theme'),
        Rule('/options/theme/configure', endpoint='admin/configure_theme'),
        Rule('/options/cache', endpoint='admin/cache'),
        Rule('/options/configuration', endpoint='admin/configuration'),
        Rule('/system/', endpoint='admin/information'),
        Rule('/system/maintenance', endpoint='admin/maintenance'),
        Rule('/system/log', defaults={'page': 1}, endpoint='admin/log'),
        Rule('/system/log/page/<int:page>', endpoint='admin/log'),
        Rule('/system/plugins/', endpoint='admin/plugins'),
        Rule('/system/plugins/<plugin>/remove', endpoint='admin/remove_plugin'),
        Rule('/system/help/', endpoint='admin/help'),
        Rule('/system/help/<path:page>', endpoint='admin/help'),
    ]
    other_urls = [
        Rule('/_translations.js', endpoint='core/serve_translations')
    ]

    return [
        Submount('', base_urls),
        Submount(app.cfg['admin_url_prefix'], admin_urls)
    ] + other_urls
