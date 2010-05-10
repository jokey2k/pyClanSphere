# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Game / Squad / Member Group Management

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname

from pyClanSphere.api import _, url_for, signals, signal

from pyClanSphere.plugins.gamesquad.database import init_database
from pyClanSphere.plugins.gamesquad.privileges import PLUGIN_PRIVILEGES, GAME_MANAGE, LEVEL_MANAGE
from pyClanSphere.plugins.gamesquad import views

TEMPLATE_FILES = join(dirname(__file__), 'templates')

# Register our used signals
signal('before_game_deleted', """\
Plugins can use this to react to game deletes.  They can't stop
the deleting of the game but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword game: the game to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_squad_deleted', """\
Plugins can use this to react to squad deletes.  They can't stop
the deleting of the squad but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword squad: the squad to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_level_deleted', """\
Plugins can use this to react to level deletes.  They can't stop
the deleting of the level but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword level: the level to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_gameaccount_deleted', """\
Plugins can use this to react to gameaccount deletes.  They can't stop
the deleting of the level but they can delete information in
their own tables or push out new server configurations.

:keyword gameaccount: the gameaccount to be deleted
""")

def add_admin_links(sender, **kwds):
    """Add our views to the admin interface"""

    priv_check = kwds['request'].user.has_privilege

    entries = [('squads', url_for('admin/squad_list'), _(u'Squads'))]

    if priv_check(GAME_MANAGE):
        entries.insert(0,('games', url_for('admin/game_list'), _(u'Games')))

    if priv_check(LEVEL_MANAGE):
        entries.append(('levels', url_for('admin/level_list'), _(u'Levels')))

    kwds['navbar'].insert(1, ('gamesquad', url_for('admin/squad_list'), _(u'Games and Squads'), entries))

def add_account_links(sender, **kwds):
    """Add our views to the account interface"""

    kwds['navbar'].insert(2, ('gameaccounts', url_for('account/gameaccount_list'), _(u'Gameaccounts'),[]))

def setup(app, plugin):
    """Init our needed stuff"""

    # Setup tables
    init_database(app)

    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # Add our template path
    app.add_template_searchpath(TEMPLATE_FILES)

    # Register pages page
    app.add_url_rule('/games/', endpoint='game/index', defaults={'page': 1},
                     view=views.game_index)
    app.add_url_rule('/games/page/<int:page>', endpoint='game/index',
                     view=views.game_index)
    app.add_url_rule('/games/<int:game_id>', endpoint='game/detail',
                     view=views.game_detail)
    app.add_url_rule('/squads/<int:squad_id>', endpoint='squad/detail',
                     view=views.squad_detail)

    # Register our admin views
    # Games
    app.add_url_rule('/games/', prefix='admin', defaults={'page': 1}, endpoint='admin/game_list',
                     view=views.game_list)
    app.add_url_rule('/games/new', prefix='admin', endpoint='admin/game_create',
                     view=views.edit_game)
    app.add_url_rule('/games/<int:game_id>', prefix='admin', endpoint='admin/game_edit',
                     view=views.edit_game)
    app.add_url_rule('/games/<int:game_id>/delete', prefix='admin', endpoint='admin/game_delete',
                     view=views.delete_game)
    # Squads
    app.add_url_rule('/squads/', prefix='admin', defaults={'page': 1}, endpoint='admin/squad_list',
                     view=views.squad_list)
    app.add_url_rule('/squads/new', prefix='admin', endpoint='admin/squad_create',
                     view=views.edit_squad)
    app.add_url_rule('/squads/<int:squad_id>', prefix='admin', endpoint='admin/squad_edit',
                     view=views.edit_squad)
    app.add_url_rule('/squads/<int:squad_id>/delete', prefix='admin', endpoint='admin/squad_delete',
                     view=views.delete_squad)
    # Squadmembers
    app.add_url_rule('/squads/<int:squad_id>/listmembers', prefix='admin', defaults={'page': 1}, endpoint='admin/squad_listmembers',
                     view=views.list_squadmembers)
    app.add_url_rule('/squads/<int:squad_id>/listmembers/page/<int:page>', prefix='admin', endpoint='admin/squad_listmembers')
    app.add_url_rule('/squads/<int:squad_id>/editmember/<int:user_id>', prefix='admin', endpoint='admin/squad_editmember',
                     view=views.edit_squadmember)
    app.add_url_rule('/squads/<int:squad_id>/newmember', prefix='admin', endpoint='admin/squad_newmember',
                     view=views.edit_squadmember)
    app.add_url_rule('/squads/<int:squad_id>/deletemember/<int:user_id>', prefix='admin', endpoint='admin/squad_deletemember',
                     view=views.delete_squadmember)
    # Levels
    app.add_url_rule('/levels/', prefix='admin', defaults={'page': 1}, endpoint='admin/level_list',
                     view=views.level_list)
    app.add_url_rule('/levels/new', prefix='admin', endpoint='admin/level_create',
                     view=views.edit_level)
    app.add_url_rule('/levels/<int:level_id>', prefix='admin', endpoint='admin/level_edit',
                     view=views.edit_level)
    app.add_url_rule('/levels/<int:level_id>/delete', prefix='admin', endpoint='admin/level_delete',
                     view=views.delete_level)

    # admin views
    app.add_url_rule('/gameaccounts/<int:account_id>/delete', prefix='admin', endpoint='admin/gameaccount_delete',
                      view=views.adm_delete_gameaccount)

    # Gameaccounts
    app.add_url_rule('/gameaccounts/', prefix='account', defaults={'page': 1}, endpoint='account/gameaccount_list',
                     view=views.gameaccount_list)
    app.add_url_rule('/gameaccounts/new', prefix='account', endpoint='account/gameaccount_new',
                     view=views.gameaccount_edit)
    app.add_url_rule('/gameaccounts/<int:account_id>', prefix='account', endpoint='account/gameaccount_edit',
                     view=views.gameaccount_edit)
    app.add_url_rule('/gameaccounts/<int:account_id>/delete', prefix='account', endpoint='account/gameaccount_delete',
                     view=views.acc_delete_gameaccount)

    # Add admin views to navigation bar
    signals.modify_admin_navigation_bar.connect(add_admin_links)

    # Add account views to navigation bar
    signals.modify_account_navigation_bar.connect(add_account_links)
