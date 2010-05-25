Translations and documentation
==============================

We have some documentation and localizations to build, if wanted. So let's do so. Feel free to skip this section if you only want to hack on your code.

Compiling translations
----------------------

To get a localized version, compile shipped translations by running::

    # On Mac/Linux
    $ scripts/compile-translations

    # On Win
    C:\pyClanSphere> python scripts\compile-translations

Adding a new translation or updating a current one always requires this step after modifications of the raw file.

Building inline documentation
-----------------------------

As `pyClanSphere` also has a help option in its backend, it is recommended that you also build the documentation for it. You can skip it, if you're fine with a hint upon following that link.

Note that you need docutils for this step. So if you're doing this for the first time, run::

    easy_install docutils

before you go on with building. Otherwise you get an import error,
telling you that docutils package cannot be found. Then compile
docs by running::

    # On Mac/Linux
    $ scripts/build-documentation

    # On Win
    C:\pyClanSphere> python scripts\build-documentation
