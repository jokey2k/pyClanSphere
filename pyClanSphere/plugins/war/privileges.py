# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.war.privileges
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains a list of used privileges for the war plugin.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.api import lazy_gettext
from pyClanSphere.privileges import Privilege, ENTER_ADMIN_PANEL

__all__ = ['PLUGIN_PRIVILEGES']

PLUGIN_PRIVILEGES = {}

def _register(name, description, privilege_dependencies=None):
    """Register a new module privilege."""

    priv = Privilege(name, description, privilege_dependencies)
    PLUGIN_PRIVILEGES[name] = priv
    globals()[name] = priv
    __all__.append(name)

_register('WAR_MANAGE', lazy_gettext(u'can manage war-related stuff'), ENTER_ADMIN_PANEL)
