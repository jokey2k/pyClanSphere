Creating a development environment
==================================

To avoid breakage with other packages on your system, we use a `virtualenv`_-based
approach here to protect ourselves. If you already have all dependencies installed,
you can skip this section

.. _virtualenv: http://pypi.python.org/pypi/virtualenv

Mac/Linux
---------

After you have cloned the code, step into the directory and initialize
a new virtual python environment. This is recommended, if you are unsure about
having all needed dependencies installed. Otherwise skip this step ::

    $ cd pyClanSphere
    $ ./scripts/setup-virtualenv env

Now you have a virtual environment called “env” in the root of your repository
initialized with all the libraries required for developing on that branch with
the correct version. This name should be used as it is ignored by git so
it doesn't track it.

Make sure to enable it before working on pyClanSphere::

    $ source env/bin/activate

To leave the virtual environment run this command::

    $ deactivate

Check in often and merge often with upstream.  When you're happy with the result,
create a patch(set) and attach it to a ticket in the issue tracker or just fork it
and file a merge request.

Windows
-------

As questions popped up many times, this will also include installing python itself.
So if you're new to all this stuff, it'll put you in a position to start developing
on a clean system.

Installing Python and setuptools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First of all fetch a Python 2.6 or 2.7 MSI Package from the `website`_ and install it.
**DO NOT use Python 3.x**, as our package is not ported yet. 

Now you need a small tool called `easy_install`. As it would be non-trivial for a beginner,
someone packaged it up to make life even more easy. Just download  the `ez_setup.py`_ file and
run it.  (Double clicking should do the trick)

Once you have it done,  it's important to add the `easy_install` command
and other Python scripts to the path. Therefore add the
Python installation's Script folder to the `PATH` variable.

To do that, right-click on your "My Computer" desktop icon and click
"Properties".  On Windows Vista and Windows 7 then click on "Advanced System
settings", on Windows XP click on the "Advanced" tab instead.  Then click
on the "Environment variables" button and double click on the "Path"
variable in the "System variables" section.

There append the path of your Python interpreter's Script folder to the
end of the last (make sure you delimit it from existing values with a
semicolon).  Assuming you are using Python 2.6 on the default path, add
the following value::

    ;C:\Python26;C:\Python26\Scripts

Now that we have proper python support in place, we can start creating our pyClanSphere development environment.

.. _ez_setup.py: http://peak.telecommunity.com/dist/ez_setup.py
.. _website: http://python.org/download

Set up our development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open a command shell (Click Start->Run and enter cmd), then step into the directory and initialize
a new virtual python environment (assuming you cloned to C:\\pyClanSphere)::

    C:\> cd \pyClanSphere
    C:\pyClanSphere> python scripts\setup-virtualenv env

This will now download all the required dependencies and make them ready for use. Afterwards enable your new environment by running::

    C:\pyClanSphere> env\Scripts\activate.bat

The last step is always required after the terminal windows has been closed.
