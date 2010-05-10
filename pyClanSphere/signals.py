# -*- coding: utf-8 -*-
"""
    pyClanSphere.signals
    ~~~~~~~~~~~~~~~~~~~~

    Signals used in the app, explicitely import :meth:signal if you want to
    add your own signals
    
    Known signals are attributes of this module so they should be straight
    forward on use

    :copyright: (c) 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from blinker import ANY, Namespace

_namespace = Namespace()
_ns_signal = _namespace.signal
def signal(name, doc=None):
    sig = _ns_signal(name, doc)
    globals()[name] = sig
    if name not in __all__: __all__.append(name)

__all__ = ['ANY']

#: Frontend Rendering
signal('before_render_template', """\
Sent right before a template is rendered, the return value is
ignored but the context can be modified in place.

:keyword template_name: name of the template
:keyword stream: True if result is a jinja template stream instead
           of a unicode string
:keyword render_context: current render context
""")
signal('before_widget_rendered', """\
Sent before a widget instance is rendered.

:keyword widget: the widget in question
""")
signal('after_widget_rendered', """\
Sent after widget instance has been rendered.

:keyword widget: the widget in question
""")
signal('before_contents_rendered', """\
Sent right before the contents block is rendered.
""")
signal('after_contents_rendered', """\
Sent right after the contents block is rendered.
""")
signal('frontpage_context_collect', """\
Allow plugins to add their objects to frontpage context. Always
return the context again or it will be empty afterwards.

:keyword context: the current frontpage context
:rtype: (modified) context
""")
signal('frontpage_content_rendered', """\
Allow plugins to append stuff to the frontpage

:rtype: Markup to be added to the frontpage
""")
signal('public_profile_rendered', """\
Extend public profile display with plugins

:rtype: Markup to be added to the profile page
""")

#: Backend rendering
signal('before_account_contents_rendered', """\
Sent right before the contents block of account view is rendered.
""")
signal('after_account_contents_rendered', """\
Sent right after the contents block of account view is rendered.
""")
signal('before_admin_contents_rendered', """\
Sent right before the contents block of admin view is rendered.
""")
signal('after_admin_contents_rendered', """\
Sent right after the contents block of admin view is rendered.
""")
signal('before_account_response_rendered', """\
Used to flash messages, add links to stylesheets, modify the
admin context etc.

:keyword request: current processed request
:keyword values: values passed as keyword to the render function
""")
signal('before_admin_response_rendered', """\
Used to flash messages, add links to stylesheets, modify the
admin context etc.

:keyword request: current processed request
:keyword values: values passed as keyword to the render function
""")

#: User logging in/out
signal('user_logged_in', """\
Sent after successful user login.

:keyword user: the user in question
""")
signal('before_user_logout', """\
Sent before logout is processed.

:keyword user: the user in question
""")
signal('after_user_logout', """\
Sent after user logged out.

:keyword: the user in question
""")

#: User handling
signal('before_group_deleted', """\
Plugins can use this to react to group deletes.  They can't stop
the deleting of the group but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword group: the group to be deleted
:keyword formdata: data of the submitted form
""")
signal('before_user_deleted', """\
Plugins can use this to react to user deletes.  They can't stop
the deleting of the user but they can delete information in
their own tables so that the database is consistent afterwards.

:keyword user: the user to be deleted
:keyword formdata: data of the submitted form
""")

# Interface modifications
signal('modify_account_navigation_bar', """\
allow plugins to extend the navigation bar

:keyword navbar: navigation bar list
:keyword request: current processed request
""")
signal('modify_admin_navigation_bar', """\
allow plugins to extend the navigation bar

:keyword navbar: navigation bar list
:keyword request: current processed request
""")

#: Request handling
signal('after_request_setup', """\
The after-request-setup event can return a response
or modify the request object in place. If we have a
response we just send it, no other modifications are done.

:keyword request: the current processed request
:rtype: (modified) processed request
""")
signal('before_response_processed', """\
Allow plugins to change the response object

:keyword request: the current processed request
:rtype: (modified) processed request
""")
signal('before_metadata_assembled', """\
Sent before the page metadata is assembled with the list of already collected
metadata. You can extend the list in place to add some more html snippets to
the page header.

:keyword result: already assembled metadata
""")

#: Service handling
signal('before_xml_service_called', """\
If this event returns a handler it is called instead of the default
handler.  Useful to intercept certain requests.

:keyword identifier: identifier
:keyword handler: current handler
:rtype: replacement handler or None
""")
signal('after_xml_service_called', """\
Called right after xml callback returned some data with the identifier
of the req method and the result object.  Note that events *have*
to return an object, even if it's just changed in place, otherwise the
return value will be None.

:keyword identifier: identifier
:keyword result: current result object
:rtype: result object
""")
signal('before_json_service_called', """\
If this event returns a handler it is called instead of the default handler.
Useful to intercept certain requests.

:keyword identifier: identifier
:keyword handler: current handler
:rtype: replacement handler or None
""")
signal('after_json_service_called', """\
Called right after json callback returned some data with the identifier
of the req method and the result object.  Note that events *have*
to return an object, even if it's just changed in place, otherwise the
return value will be `null` (None).

:keyword identifier: identifier
:keyword result: current result object
:rtype: result object
""")
signal('after_bbcode_initialized', """\
Allow plugins to add additional bbcodes, hence passing on the current
bbcode parsing instance

:keyword bbcode_parser: current bbcode parser instance
""")

#: General application stuff
signal('cloak_insecure_configuration_var', """\
This event is emitted if the application wants to display a configuration
value publicly. The return value of the listener is used as new value.
A listener should return None if the return value is not used.

:keyword key: the configuration variable
:keyword value: value of the given variable
:rtype: (new) value or None
""")
signal('application_setup_done', """\
Application and all plugins are initialized
""")

