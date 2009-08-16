# -*- coding: utf-8 -*-
"""
    _init_pyClanSphere
    ~~~~~~~~~~

    Helper to locate pyClanSphere and the instance folder.
    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from os.path import abspath, join, dirname, pardir, isfile
import sys

# set to None first because the installation replaces this
# with the path to the installed pyClanSphere library.
PYCLANSPHERE_LIB = None

if PYCLANSPHERE_LIB is None:
    PYCLANSPHERE_LIB = abspath(join(dirname(__file__), pardir))

# make sure we load the correct pyClanSphere
sys.path.insert(0, PYCLANSPHERE_LIB)


def find_instance():
    """Find the pyClanSphere instance."""
    instance = None
    if isfile(join('instance', 'pyClanSphere.ini')):
        instance = abspath('instance')
    else:
        old_path = None
        path = abspath('.')
        while old_path != path:
            path = abspath(join(path, pardir))
            if isfile(join(path, 'pyClanSphere.ini')):
                instance = path
                break
            old_path = path
    return instance
