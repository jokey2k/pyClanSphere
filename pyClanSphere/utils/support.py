# -*- coding: utf-8 -*-
"""
    pyClanSphere.utils.support
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    A support module.  Provides various support methods and helpers.

    :copyright: (c) 2009 by the pyClanSphere Team
                (c) 2009 by Plurk Inc., see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
import unicodedata
from itertools import izip, imap

# imported for the side effects, registers a codec
import translitcodec


_punctuation_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
_missing = object()


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punctuation_re.split(text.lower()):
        word = _punctuation_re.sub(u'', word.encode('translit/long'))
        if word:
            result.append(word)
    return unicode(delim.join(result))


class UIException(Exception):
    """Exceptions that are displayed in the user interface.  The big
    difference to a regular exception is that this exception uses
    an unicode string as message.
    """

    message = None

    def __init__(self, message):
        Exception.__init__(self, message.encode('utf-8'))
        self.message = message

    def __unicode__(self):
        return self.message

    def __str__(self):
        return self.message.encode('utf-8')

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.message)


from pyClanSphere.i18n import _
