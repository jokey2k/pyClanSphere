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

from pyClanSphere import models

class testModelsTests(unittest.TestCase):
    def testExistingUser(self):
        """Make sure we have at least one valid user"""
        usercount = models.User.query.count()
        self.assertTrue(usercount > 0)

if __name__ == '__main__':
  unittest.main()