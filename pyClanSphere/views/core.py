# -*- coding: utf-8 -*-

"""
    pyClanSphere.views.core
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module exports the main index page where plugins can hook in to display their widgets


    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from pyClanSphere import cache
from pyClanSphere.api import *
from pyClanSphere.i18n import _, ngettext

@cache.response()
def index(request):
    """Just show the pyClanSphere license and some other legal stuff."""
    return render_response('index.html')

