# -*- coding: utf-8 -*-
"""
    pyClanSphere.api
    ~~~~~~~~

    Module for plugins and core. Star import this to get
    access to all the important helper functions.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere.application import (
    # Event handling
    emit_event, iter_listeners,

    # Request/Response
    Response, get_request, url_for, shared_url, add_link, add_meta,
    add_script, add_header_snippet,

    # Template helpers
    render_template, render_response,

    # Appliation helpers
    get_application
)

# Database
from pyClanSphere.database import db

# Privilege support
from pyClanSphere.privileges import require_privilege

# Cache
from pyClanSphere import cache

# Gettext
from pyClanSphere.i18n import gettext, ngettext, lazy_gettext, lazy_ngettext, _

# Plugin syste
from pyClanSphere.pluginsystem import SetupError


__all__ = list(x for x in locals() if x == '_' or not x.startswith('_'))
