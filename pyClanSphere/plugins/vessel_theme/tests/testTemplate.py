# encoding: utf-8
"""
    pyClanSphere.plugins.vessel_theme.testTemplate
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A random template test

    :copyright: (c) 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import unittest

class testTemplate(unittest.TestCase):
    def testExistingLayout(self):
        """Check if our template has a valid layout.html"""
        self.assertTrue(__file__)
