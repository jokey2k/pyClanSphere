Signals
=======

All listed signals can be connected to functions with the following layout::

    def my_receiver(sender, **parameters):
        do_something(parameters['param1'])
        return someting

    my_signal.connect(my_receiver)

Parameters dictionary will then contain parameters given below. If the result is expected, needed return argument will be shown as well.

.. automodule:: pyClanSphere.signals
   :members:

Frontend rendering
------------------
.. autoattribute:: pyClanSphere.signals.before_render_template
.. autoattribute:: pyClanSphere.signals.before_widget_rendered
.. autoattribute:: pyClanSphere.signals.after_widget_rendered
.. autoattribute:: pyClanSphere.signals.before_contents_rendered
.. autoattribute:: pyClanSphere.signals.after_contents_rendered
.. autoattribute:: pyClanSphere.signals.frontpage_context_collect
.. autoattribute:: pyClanSphere.signals.frontpage_content_rendered
.. autoattribute:: pyClanSphere.signals.public_profile_rendered

Backend rendering
-----------------
.. autoattribute:: pyClanSphere.signals.before_account_contents_rendered
.. autoattribute:: pyClanSphere.signals.after_account_contents_rendered
.. autoattribute:: pyClanSphere.signals.before_admin_contents_rendered
.. autoattribute:: pyClanSphere.signals.after_admin_contents_rendered
.. autoattribute:: pyClanSphere.signals.before_account_response_rendered
.. autoattribute:: pyClanSphere.signals.before_admin_response_rendered

User logging in/out
-------------------
.. autoattribute:: pyClanSphere.signals.user_logged_in
.. autoattribute:: pyClanSphere.signals.before_user_logout
.. autoattribute:: pyClanSphere.signals.after_user_logout

User handling
-------------
.. autoattribute:: pyClanSphere.signals.before_group_deleted
.. autoattribute:: pyClanSphere.signals.before_user_deleted

Interface modifications
-----------------------
.. autoattribute:: pyClanSphere.signals.modify_account_navigation_bar
.. autoattribute:: pyClanSphere.signals.modify_admin_navigation_bar

Request handling
----------------
.. autoattribute:: pyClanSphere.signals.after_request_setup
.. autoattribute:: pyClanSphere.signals.before_response_processed
.. autoattribute:: pyClanSphere.signals.before_metadata_assembled

Service handling
----------------
.. autoattribute:: pyClanSphere.signals.before_xml_service_called
.. autoattribute:: pyClanSphere.signals.after_xml_service_called
.. autoattribute:: pyClanSphere.signals.before_json_service_called
.. autoattribute:: pyClanSphere.signals.after_json_service_called
.. autoattribute:: pyClanSphere.signals.after_bbcode_initialized

General application stuff
-------------------------
.. autoattribute:: pyClanSphere.signals.cloak_insecure_configuration_var
.. autoattribute:: pyClanSphere.signals.application_setup_done

Creating your own signal
------------------------

As noted above, just import :meth:`signal`

.. autoattribute:: pyClanSphere.signals.signal(name, doc=None)

