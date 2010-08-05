# -*- coding: utf-8 -*-
"""
    pyClanSphere Test Suite
    ~~~~~~~~~~~~~~~~~~~~~~~

    This is the pyClanSphere test suite. It collects all modules in the pyClanSphere
    package, builds a TestSuite with their doctests and executes them. It also
    collects the tests from the text files in this directory (which are too
    extensive to put them into the code without cluttering it up).
    Plus all python files that start with test* will be added to the TestSuite.

    Please note that coverage reporting and doctest don't play well together
    and your reports will probably miss some of the executed code. Doctest can
    be patched to remove this incompatibility, the patch is at
    http://tinyurl.com/doctest-patch

    :copyright: (c) 2009 by the pyClanSphere Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import sys
import os
from tempfile import mkdtemp
from os.path import join, dirname
from unittest import TestSuite, TextTestRunner
from unittest2 import defaultTestLoader
from doctest import DocTestSuite, DocFileSuite

from pyClanSphere.utils.crypto import gen_pwhash, gen_secret_key, new_iid

try:
    import coverage
except ImportError:
    coverage = None

def create_temporary_instance():
    """Create a sqlite based test instance in a temporary directory"""
    dbname = 'sqlite://database.db'
    instance_folder = mkdtemp(prefix='pyclanspheretest')

    # create database and all tables
    from pyClanSphere.database import db, init_database
    e = db.create_engine(dbname, instance_folder)
    from pyClanSphere.schema import users, user_privileges, privileges
    init_database(e)

    # create admin account
    from pyClanSphere.privileges import CLAN_ADMIN
    user_id = e.execute(users.insert(),
        username=u'TestAdmin',
        pw_hash=gen_pwhash('TestPassWord'),
        email=u'Somewhere@example.com',
        real_name=u'',
        description=u'',
        extra={},
        display_name='$username'
    ).inserted_primary_key[0]

    # insert a privilege for the user
    privilege_id = e.execute(privileges.insert(),
        name=CLAN_ADMIN.name
    ).inserted_primary_key[0]
    e.execute(user_privileges.insert(),
        user_id=user_id,
        privilege_id=privilege_id
    )

    # set up the initial config
    from pyClanSphere.config import Configuration
    config_filename = join(instance_folder, 'pyClanSphere.ini')
    cfg = Configuration(config_filename)
    t = cfg.edit()
    t.update(
        maintenance_mode=False,
        site_url='http://localtest',
        secret_key=gen_secret_key(),
        database_uri=dbname,
        iid=new_iid()
    )
    t.commit()
    
    from pyClanSphere import setup
    from pyClanSphere.upgrades.webapp import WebUpgrades
    instance = setup(instance_folder)
    
    if str(type(instance)) == "<class 'pyClanSphere.upgrades.webapp.WebUpgrades'>":
        # Fast Migration
        from pyClanSphere.upgrades import ManageDatabase
        manage = ManageDatabase(instance)
        upgrade = manage.cmd_upgrade()
        while True:
            try:
                upgrade.next()
            except StopIteration:
                break
        from pyClanSphere._core import _unload_pyClanSphere
        _unload_pyClanSphere()

        instance = setup(instance_folder)
        if str(type(instance)) == "<class 'pyClanSphere.upgrades.webapp.WebUpgrades'>":
            sys.stderr.write('Automatic db migration failed, check your scripts!\n')
            sys.exit(1)
    return instance, instance_folder

def suite(app, modnames=[], return_covermods=False):
    """Generate the test suite.

    First argument is always the instance to use. Use a real one or a temporary.
    The second argument is a list of modules to be tested. If it is empty (which
    it is by default), all sub-modules of the pyClanSphere package are tested.
    If the second argument is True, this function returns two objects: a
    TestSuite instance and a list of the names of the tested modules. Otherwise
    (which is the default) it only returns the former. This is done so that
    this function can be used as setuptools' test_suite.
    """

    # the app object is used for two purposes:
    # 1) plugins are not usable (i.e. not testable) without an initialised app
    # 2) for functions that require an application object as argument, you can
    #    write >>> my_function(app, ...) in the tests
    # The instance directory of this object is located in the tests directory.
    #
    # setup isn't imported at module level because this way coverage
    # can track the whole pyClanSphere imports

    if return_covermods:
        covermods = []
    suite = TestSuite()

    if modnames == []:
        modnames = find_tp_modules()
    test_files = os.listdir(dirname(__file__))
    for modname in modnames:

        # the fromlist must contain something, otherwise the pyClanSphere
        # package is returned, not our module
        try:
            mod = __import__(modname, None, None, [''])
        except ImportError, exc:
            # some plugins can have external dependencies (e.g. creoleparser,
            # pygments) that are not installed on the machine the tests are
            # run on. Therefore, just skip those (with an error message)
            if 'plugins.' in modname:
                if 'versions.' not in modname and 'tests.' not in modname:
                    sys.stderr.write('could not import plugin %s: %s\n' % (modname, exc))
                continue
            else:
                raise
        suites = [DocTestSuite(mod, extraglobs={'app': app})]
        filename = modname[10:] + '.txt'
        if filename in test_files:
            globs = {'app': app}
            globs.update(mod.__dict__)
            suites.append(DocFileSuite(filename, globs=globs))
        for i, subsuite in enumerate(suites):
            # skip modules without any tests
            if subsuite.countTestCases():
                suite.addTest(subsuite)
                if return_covermods and i == 0:
                    covermods.append(mod)
        if 'tests.' in modname:
            suite.addTests(defaultTestLoader.discover(modname))
    
    if return_covermods:
        return suite, covermods
    else:
        return suite


def find_tp_modules():
    """Find all sub-modules of the pyClanSphere package."""
    modules = []
    import pyClanSphere
    base = dirname(pyClanSphere.__file__)
    start = len(dirname(base))
    if base != 'pyClanSphere':
        start += 1

    for path, dirnames, filenames in os.walk(base):
        for filename in filenames:
            if filename.endswith('.py'):
                fullpath = join(path, filename)
                if filename == '__init__.py':
                    stripped = fullpath[start:-12]
                else:
                    stripped = fullpath[start:-3]

                modname = stripped.replace('/', '.')
                modules.append(modname)
    return modules


def main():
    from optparse import OptionParser
    usage = ('Usage: %prog [option] [modules to be tested]\n'
             'Modules names have to be given in the form utils.mail (without '
             'pyClanSphere.)\nIf no module names are given, all tests are run')
    parser = OptionParser(usage=usage)
    parser.add_option('-c', '--coverage', action='store_true', dest='coverage',
                      help='show coverage information (slow!)')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      default=False, help='show which tests are run')
    parser.add_option('--tempinstance', action='store_true', dest='tempinstance',
                      default=False, help='use a temporary sqlite based test instance')
    parser.add_option('--instance', dest='instance',
                      help='instance to use instead of ./instance')

    options, args = parser.parse_args(sys.argv[1:])
    if options.instance and options.tempinstance:
        sys.stderr.write("you can't use a temporary and real instance at the same time!\n")
        sys.exit(1)

    modnames = ['pyClanSphere.' + modname for modname in args]
    if options.coverage:
        if coverage is not None:
            use_coverage = True
        else:
            sys.stderr.write("coverage information requires Ned Batchelder's "
                             "coverage.py to be installed!\n")
            sys.exit(1)
    else:
        use_coverage = False

    # get our instance
    sys.stdout.write("Loading Instance ... ")
    sys.stdout.flush()
    if options.tempinstance:
        instance, instance_folder = create_temporary_instance()
    elif options.instance:
        from pyClanSphere.upgrades.webapp import WebUpgrades
        from pyClanSphere import setup
        instance = setup(options.instance)
        if isinstance(instance, WebUpgrades):
            sys.stderr.write("Please migrate your instance to latest schema first!\n")
            sys.exit(1)
    else:
        from pyClanSphere.upgrades.webapp import WebUpgrades
        from pyClanSphere import setup
        instance_folder = join(dirname(__file__),'../instance')
        sys.stdout.write("Note: Using default instance found at %s\n" % instdir)
        instance = setup(instance_folder)
        if isinstance(instance, WebUpgrades):
            sys.stderr.write("Please migrate your instance to latest schema first!\n")
            sys.exit(1)
    sys.stdout.write("ok\nCollecting tests ... ")
    sys.stdout.flush()
    if use_coverage:
        coverage.erase()
        coverage.start()
        s, covermods = suite(instance, modnames, True)
    else:
        s = suite(instance, modnames)
    sys.stdout.write("ok\n")
    TextTestRunner(verbosity=options.verbose + 1).run(s)
    if use_coverage:
        coverage.stop()
        print '\n\n' + '=' * 25 + ' coverage information ' + '=' * 25
        coverage.report(covermods)
    if options.tempinstance:
        try:
            for root, dirs, files in os.walk(instance_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        except OSError:
            print "Could not remove all tempfiles, please remove", \
                  instance_folder, "yourself"
            pass
if __name__ == '__main__':
    main()
