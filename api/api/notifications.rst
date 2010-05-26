Notification System
===================

.. automodule:: pyClanSphere.notifications

Sending a notification
----------------------
.. autoclass:: pyClanSphere.notifications.Notification
.. autoattribute:: pyClanSphere.notifications.send_notification(type, message, user=Ellipsis)
.. autoattribute:: pyClanSphere.notifications.send_notification_template(type, template_name, user=Ellipsis, **context)

Shipped Notification Systems
----------------------------
.. autoclass:: pyClanSphere.notifications.NotificationSystem
   :members:
.. autoclass:: pyClanSphere.notifications.EMailNotificationSystem
