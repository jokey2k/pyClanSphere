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
from pyClanSphere.application import Response
from pyClanSphere.models import User
from pyClanSphere.utils import dump_json
from pyClanSphere.utils.xml import generate_rsd, dump_xml, AtomFeed

@cache.response()
def index(request):
    """Just show the pyClanSphere license and some other legal stuff."""
    return render_response('index.html')


#@cache.response()
def profile(request, user_id):
    """Render profile page for given user"""
    user = User.query.get(user_id)
    if not user:
        raise NotFound()
    return render_response('profile.html', user=user)


def json_service(req, identifier):
    """Handle a JSON service req."""
    handler = req.app._services.get(identifier)
    if handler is None:
        raise NotFound()

    #! if this event returns a handler it is called instead of the default
    #! handler.  Useful to intercept certain requests.
    for callback in signals.before_json_service_called.receivers_for(signals.ANY):
        rv = callback(identifier, handler)
        if rv is not None:
            handler = rv
    result = handler(req)

    #! called right after json callback returned some data with the identifier
    #! of the req method and the result object.  Note that events *have*
    #! to return an object, even if it's just changed in place, otherwise the
    #! return value will be `null` (None).
    for callback in signals.after_json_service_called.receivers_for(signals.ANY):
        result = callback(identifier, result)
    return Response(dump_json(result), mimetype='text/javascript')


def xml_service(req, identifier):
    """Handle a XML service req."""
    handler = req.app._services.get(identifier)
    if handler is None:
        raise NotFound()

    #! if this event returns a handler it is called instead of the default
    #! handler.  Useful to intercept certain requests.
    for callback in signals.before_xml_service_called.receivers_for(signals.ANY):
        rv = callback(identifier, handler)
        if rv is not None:
            handler = rv
    result = handler(req)

    #! called right after xml callback returned some data with the identifier
    #! of the req method and the result object.  Note that events *have*
    #! to return an object, even if it's just changed in place, otherwise the
    #! return value will be None.
    for callback in signals.after_xml_service_called.receivers_for(signals.ANY):
        result = callback(identifier, result)
    return Response(dump_xml(result), mimetype='text/xml')


def service_rsd(req):
    """Serves and RSD definition (really simple discovery) so that service
    frontends can query the apis that are available.

    :URL endpoint: ``core/service_rsd``
    """
    return Response(generate_rsd(req.app), mimetype='application/xml')
