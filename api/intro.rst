Introduction
============

To work on Zine you have to have a Mac running OS X, a BSD system or
Linux.  It's currently not possible to develop on Windows as some of
tools depend on a POSIX environment.  You may have success by using
cygwin, but there's no experience with it yet.

Checking out the Code
---------------------

- ``git://orion7.digital-server.de/pyClanSphere.git`` — the primary repository

Clone the branch using git::

    $ git clone git://orion7.digital-server.de/pyClanSphere.git

    You'll get the master branch initially, may want to switch to another one
    or create your own

Creating a Development Environment
----------------------------------

After you have cloned the code, step into the directory and initialize
a new virtual python environment, if you don't have all the needed tools::

    $ cd pyClanSphere
    $ ./scripts/setup-virtualenv env

Now you have a virtual environment called “env” in the root of your repository
initialized with all the libraries required for developing on that branch with
the correct version.

Make sure to enable it before working on pyClanSphere::

    $ source env/bin/activate

To leave the virtual environment run this command::

    $ deactivate

Check in often and merge often with upstream.  When you're happy with the result,
create a patch(set) and attach it to a ticket in the trac.
