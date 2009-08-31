# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Game / Squad / Member Group Management

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname

from pyClanSphere.api import _, url_for

from pyClanSphere.plugins.gamesquad.database import init_database
from pyClanSphere.plugins.gamesquad.privileges import PLUGIN_PRIVILEGES, GAME_MANAGE, SQUAD_MANAGE
from pyClanSphere.plugins.gamesquad import views

TEMPLATE_FILES = join(dirname(__file__), 'templates')

def add_admin_links(request, navigation_bar):
    """Add our views to the admin interface"""

    priv_check = request.user.has_privilege

    entries = []

    if priv_check(GAME_MANAGE): 
        entries.append(('games', url_for('admin/game_list'), _(u'Games')))

    if priv_check(SQUAD_MANAGE): 
        entries.append(('squads', url_for('admin/squad_list'), _(u'Squads')))

    if entries:
        navigation_bar.extend([
            ('gamesquad', url_for('admin/game_list'), _(u'Games and Squads'), entries)
        ])
    

def setup(app, plugin):
    """Init our needed stuff"""

    # Setup tables
    init_database()

    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # Add our template path
    app.add_template_searchpath(TEMPLATE_FILES)

    # Register pages page
    app.add_url_rule('/games/', endpoint='game/index', 
                     view=views.game_index)
    app.add_url_rule('/games/<int:game_id>', endpoint='game/detail', 
                     view=views.game_detail)
    app.add_url_rule('/squads/<int:squad_id>', endpoint='squad/detail', 
                     view=views.squad_detail)
                         
    # Register news archive along with archive
    # sub-urls to filter by year, month and day
    #app.add_url_rule('/news/archive', endpoint='news/archive',
    #                 view=views.archive)
    #tmp = '/news/'
    #for digits, part in zip((0, 0, 0), ('year', 'month', 'day')):
    #    tmp += '<int(fixed_digits=%d):%s>/' % (digits, part)
    #    app.add_url_rule(tmp, defaults={'page': 1}, endpoint='news/archive')
    #    app.add_url_rule(tmp + 'page/<int:page>', endpoint='news/archive')

    # Register our admin views
    # Games
    app.add_url_rule('/games', prefix='admin', defaults={'page': 1}, endpoint='admin/game_list', 
                     view=views.game_list)
    app.add_url_rule('/games/new', prefix='admin', endpoint='admin/game_create', 
                     view=views.edit_game)
    app.add_url_rule('/games/<int:game_id>', prefix='admin', endpoint='admin/game_edit', 
                     view=views.edit_game)
    app.add_url_rule('/games/<int:game_id>/delete', prefix='admin', endpoint='admin/game_delete', 
                     view=views.delete_game)

    # Squads
    app.add_url_rule('/squads', prefix='admin', defaults={'page': 1}, endpoint='admin/squad_list', 
                     view=views.squad_list)
    app.add_url_rule('/squads/new', prefix='admin', endpoint='admin/squad_create', 
                     view=views.edit_squad)
    app.add_url_rule('/squads/<int:squad_id>', prefix='admin', endpoint='admin/squad_edit', 
                     view=views.edit_squad)
    app.add_url_rule('/squads/<int:squad_id>/memberships', prefix='admin', endpoint='admin/squad_editmemberships', 
                     view=views.edit_squadmemberships)
    app.add_url_rule('/squads/<int:squad_id>/delete', prefix='admin', endpoint='admin/squad_delete', 
                     view=views.delete_squad)
    
    # Add admin views to navigation bar
    app.connect_event('modify-admin-navigation-bar', add_admin_links)
