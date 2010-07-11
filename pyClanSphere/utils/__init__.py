"""
    pyClanSphere.utils
    ~~~~~~~~~~~~~~~~~~

    This package implements various functions used all over the code.

    :copyright: (c) 2009 - 2010 by the pyClanSphere Team,
                see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os

try:
    from simplejson import dumps as dump_json, loads as load_json
except ImportError:
    from json import dumps as dump_json, loads as load_json

from werkzeug import url_quote, Local, LocalManager, ClosingIterator

# load dynamic constants
from pyClanSphere._dynamic import *


# our local stuff
local = Local()
local_manager = LocalManager([local])
