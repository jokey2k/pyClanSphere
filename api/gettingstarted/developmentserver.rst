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