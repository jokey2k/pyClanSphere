# -*- coding: utf-8 -*-
"""
    _make-setup-virtualenv.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Execute this file to regenerate the `setup-virtualenv` script.

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
from virtualenv import create_bootstrap_script


FILENAME = 'setup-virtualenv'
CODE = '''
import os
import sys
from subprocess import call

REQUIREMENTS = [
    'Werkzeug>=0.6',
    'Jinja2>=2.4',
    'SQLAlchemy>=0.6.0',
    'pytz',
    'Babel>=0.9.5',
    'webdepcompress',
    'translitcodec',
    'Blinker>=1.0'
]

# for python 2.4/2.5 we want simplejson installed too.
if sys.version_info < (2, 6):
    REQUIREMENTS.append('simplejson')

def install(home_dir, *args, **kw):
    static_deps = kw.pop('static_deps', False)
    if kw:
        raise TypeError('too many keyword arguments')
    env = None
    if static_deps:
        env = dict(os.environ.items())
        env['STATIC_DEPS'] = 'true'
    call([os.path.join(home_dir, 'bin', 'easy_install')] + list(args), env=env)

def after_install(options, home_dir):
    site_packages = os.path.normpath(os.path.join(home_dir, 'lib', 'python%%d.%%d'
        %% sys.version_info[:2], 'site-packages'))
    for requirement in REQUIREMENTS:
        install(home_dir, requirement)
'''

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__) or '.')
    f = file(FILENAME, 'w')
    try:
        f.write(create_bootstrap_script(CODE % {
            'pyClanSphere_path':    os.path.normpath(os.path.join('..', 'pyClanSphere'))
        }))
    finally:
        f.close()
    os.chmod(FILENAME, 0755)
