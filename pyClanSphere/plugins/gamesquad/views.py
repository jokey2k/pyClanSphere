# -*- coding: utf-8 -*-
"""
    pyClanSphere.plugins.gamesquad.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements all the views for the gamesquad module.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from os.path import exists
from time import asctime, gmtime, time
from datetime import date

from werkzeug import escape
from werkzeug.exceptions import NotFound, Forbidden

from pyClanSphere import cache
from pyClanSphere.database import db
from pyClanSphere.application import url_for, render_response, emit_event, \
     Response, get_application
from pyClanSphere.i18n import _
from pyClanSphere.privileges import assert_privilege
from pyClanSphere.utils.redirects import lookup_redirect

from pyClanSphere.plugins.gamesquad.models import Game, Squad, SquadMember, Level

# Public views

@cache.response()
def game_index(req):
    """Render the most recent posts.

    Available template variables:

        `newsitems`:
            a list of post objects we want to display

        `pagination`:
            a pagination object to render a pagination

    :Template name: ``index.html``
    :URL endpoint: ``news/index``
    """
    
    data = Game.query.all()

    return render_response('game_index.html', games=data)
