# -*- coding: utf-8 -*-
"""
    pyClanSphere.tests.testModels
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Make sure our core models have consistent behaviour

    :copyright: (c) 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import sys
import os
import unittest

from pyClanSphere import models, privileges
from pyClanSphere.tests import pyClanSphereTestCase

class testUserModel(pyClanSphereTestCase):
    def setUp(self):
        pyClanSphereTestCase.setUp(self)
        models.User(u'TestUser', u'TestPass', u'somewhere@home.de', u'TestBenutzer')
        self.db.commit()

    def testAnonymousUser(self):
        """Make sure anonymous user is properly recognized"""

        user = models.User.query.get(1)
        self.assertTrue(isinstance(user, models.User))
        self.assertFalse(isinstance(user, models.AnonymousUser))
        self.assertTrue(user.is_somebody)

        user = models.AnonymousUser()
        self.assertTrue(isinstance(user, models.User))
        self.assertTrue(isinstance(user, models.AnonymousUser))
        self.assertFalse(user.is_somebody)

    def testPermissions(self):
        """Setting different permissions"""

        admin = models.User.query.get(1)
        self.assertTrue(admin.is_somebody)
        self.assertTrue(admin.is_manager)
        self.assertTrue(admin.has_profile_access)
        self.assertTrue(admin.is_admin)

        user = models.User.query.get(2)
        self.assertTrue(user.is_somebody)
        self.assertFalse(user.is_manager)
        self.assertFalse(user.has_profile_access)
        self.assertFalse(user.is_admin)

        priv = privileges.ENTER_ACCOUNT_PANEL
        user.own_privileges.add(priv)
        self.assertFalse(user.is_manager)
        self.assertTrue(user.has_profile_access)
        self.assertFalse(user.is_admin)
        user.own_privileges.remove(priv)
        self.assertFalse(user.is_manager)
        self.assertFalse(user.has_profile_access)
        self.assertFalse(user.is_admin)

        priv = privileges.ENTER_ADMIN_PANEL
        user.own_privileges.add(priv)
        self.assertTrue(user.is_manager)
        self.assertFalse(user.has_profile_access)
        self.assertFalse(user.is_admin)
        user.own_privileges.remove(priv)
        self.assertFalse(user.is_manager)
        self.assertFalse(user.has_profile_access)
        self.assertFalse(user.is_admin)

    def testUserPassword(self):
        """User Password setting and account disabling"""

        user = models.User.query.get(2)
        self.assertFalse(user.disabled)
        self.assertTrue(user.check_password('TestPass'))
        user.disable()
        self.assertFalse(user.check_password('TestPass'))
        self.assertFalse(user.check_password('!'))
        self.assertTrue(user.disabled)
        user.set_password('!')
        self.assertFalse(user.disabled)
        self.assertTrue(user.check_password('!'))

    def testUserQuery(self):
        """User querying"""

        self.assertTrue(models.User.query.count() > 0)

        anon = models.User.query.get_nobody()
        self.assertTrue(isinstance(anon, models.User))
        self.assertTrue(isinstance(anon, models.AnonymousUser))

        userlist = models.User.query.namesort().all()
        self.assertEqual(userlist, [models.User.query.get(1),models.User.query.get(2)])

    def testUserNaming(self):
        """Realname or Username"""

        user = models.User.query.get(2)
        self.assertEqual(user.display_name, 'TestUser')
        user.display_name = '$real_name'
        self.assertEqual(user.display_name, 'TestBenutzer')
        user.display_name = '$username'
        self.assertNotEqual(user.display_name, 'TestBenutzer')
        self.assertEqual(user.display_name, 'TestUser')

    def tearDown(self):
        self.db.delete(models.User.query.get(2))
        self.db.commit()
        pyClanSphereTestCase.tearDown(self)
