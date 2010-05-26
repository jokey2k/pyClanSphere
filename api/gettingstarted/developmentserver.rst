Creating an instance and starting development server
====================================================

To make it a fullblown test instance, we need a database.
For the sake of simplicity, we use a sqlite3 database as
python ships with support for it by default and we don't
need to mess with a server setup.
::

    # On Mac/Linux
    $ mkdir instance
    $ scripts/server -I instance

    # On Win
    C:\pyClanSphere> mkdir instance
    C:\pyClanSphere> python scripts\server -I instance

Now a development server will be running on localhost, port 4000.

Just open up a browser and continue the `setup`_, remember to use the following database link::

    sqlite://database.db

.. _setup: http://localhost:4000/

Commandline Options
-------------------

Known commandline options for the development server:

Usage: server [options]

-h, --help            show help message and exit
--no-reloader         Disable the reloader
--no-debugger         Disable the debugger
--threaded            Activate multithreading
--profile             Enable the profiler
--mount=MOUNT         If you want to mount the application somewhere outside
                      the URL root.  This is useful for debugging URL
                      generation problems.
-I INSTANCE, --instance=INSTANCE
                      Use the path provided as pyClanSphere instance.
-a HOSTNAME, --hostname=HOSTNAME  bind to given hostname
-p PORT, --port=PORT  bind to given port
