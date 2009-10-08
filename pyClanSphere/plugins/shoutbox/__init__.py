# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.shoutbox
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Plugin implementation description goes here.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from os.path import join, dirname

from pyClanSphere.api import get_application, _, url_for

from pyClanSphere.plugins.shoutbox import views
from pyClanSphere.plugins.shoutbox.database import init_database
from pyClanSphere.plugins.shoutbox.privileges import PLUGIN_PRIVILEGES

TEMPLATE_FILES = join(dirname(__file__), 'templates')

def setup(app, plugin):
    """Init our needed stuff"""

    # Setup tables
    init_database()

    # Add our privileges
    for priv in PLUGIN_PRIVILEGES.values():
        app.add_privilege(priv)

    # Add our templates to the path
    app.add_template_searchpath(TEMPLATE_FILES)
    
    # Register shoutbox widget
    app.add_widget(views.ShoutboxWidget)

    # Shoutbox entry post page
    app.add_url_rule('/shoutbox/new', endpoint='shoutbox/post', 
                     view=views.make_shoutbox_entry)
    app.add_url_rule('/shoutbox/<int:entry_id>/delete', endpoint='shoutbox/delete', 
                     view=views.delete_shoutbox_entry)
