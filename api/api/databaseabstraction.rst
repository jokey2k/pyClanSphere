Database interface
==================

.. currentmodule:: pyClanSphere.database.db

To avoid having to include random sqlalchemy modules all over the place, a central db module is built, which you get for free by asterisk importing the api or explicitely importing it.
In almost any case you just want to use that as all the magic, which is needed to simplify things, are done there already so you don't need to repeat that yourself.

What you need
-------------

Depending on what you are about to do, you need to know what is available and where it should live.

In pyClanSphere, there is a split between doing MetaData work, such as specifying tables and just using mapped classes. To get an idea where to start if you put together something new, take a look at the following sections

Using mapped classes
--------------------

Whenever you want to query for data, use the mapped query attribute::

    # If you want all users
    userlist = User.query.all()
    
    # If you want all users but don't need the birtday (in case you have heavy columns)
    userlist = User.query.defer(User.birthday).all()
    
    # Or finetune with filters
    userlist = User.query.filter(db.and_(db.not_(User.gender),User.height >= 100))\
                   .order_by(db.desc(User.height)).all()

Commonly useful query attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lazyload
.. autofunction:: between
.. autofunction:: defer
.. autofunction:: desc
.. autofunction:: distinct
.. autofunction:: eagerload
.. autofunction:: eagerload_all
.. autofunction:: joinedload
.. autofunction:: joinedload_all
.. autofunction:: noload
.. autofunction:: and_
.. autofunction:: not_
.. autofunction:: or_
.. autofunction:: subqueryload
.. autofunction:: subqueryload_all
.. autofunction:: undefer

Mapper and helpers
------------------


.. autofunction:: mapper
   
   .. note:: We use a prepared mapper, which auto-adds a query attribute to the mapped class and also autoadds new instances to the session, so that they will be committed on next :func:`commit` call without you having to worry about persistence of the data.

.. autofunction:: backref
.. autofunction:: dynamic_loader
.. autofunction:: relationship


MetaData work
-------------

Whenever you need to specify tables (you really should do this in a schema.py), then you might need the following classes

Table and Column
~~~~~~~~~~~~~~~~

.. autoclass:: Table
.. autoclass:: Column

Field Types
~~~~~~~~~~~

.. autoclass:: Boolean
.. autoclass:: Date
.. autoclass:: DateTime
.. autoclass:: Float
.. autoclass:: ForeignKey
.. autoclass:: Integer
.. autoclass:: String
.. autoclass:: Text
.. autoclass:: Time

Database wrapper module
-----------------------

.. warning:: Normally you don't use this directly but just stick to the
   :mod:`pyClanSphere.database.db` module from above, which is also exported via astersik
   import on :mod:`pyClanSphere.api`.

.. automodule:: pyClanSphere.database
   :members:
