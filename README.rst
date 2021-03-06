--------------
SQLA_Hierarchy
--------------

-----------
Description
-----------

Given a `Table`_ object and a `Select`_ expression, this class will return the information from these objects with some extra columns that will properly denote the hierarchical relation between the rows. The returned Hierarchy object could then be executed and it will return the same Select statement submitted plus the following columns:

- level: the relative level of the row related to its parent
- connect_path: a list with all the ids that compound this part of the hierarchy, from the root node to the current value (**IMPORTANT**: Oracle requires some extra post processing to generate the list)
- is_leaf: boolean indicating is the particular id is a leaf or not

The resultset will be returned properly ordered by the levels in the hierarchy

Special remarks:

- The selected table must have a self referential foreign key relation, otherwise it will raise MissingForeignKey
- Not every database is supported (at the moment). Check the global var supported_db for an up2date list. Trying to execute Hierarchy with an unsupported db will raise NotImplementedError or HierarchyLesserError (check the errors classes docstring for the exact meaning of each of them).
- To prevent the query from returning every node as a different starting node and, therefore, having duplicate values, you can provide the 'starting_node' parameter in the kwargs. The value you must provide is the parent id for the root node you want to start building the hierarchical tree. None has the same meaning as "0" since we perform a coalesce function in the query. By default the system will add a 'starting_node'="0". If you don't want a starting node, pass 'starting_node'=False and the clause will not be added to the query

*Supported databases*:

- PostgreSQL (>=8.4.0)
- Oracle (>=10g)

*Databases we might support on a next version*:

- SQL Server
- DB2

*Databases that we know we cannot support* (because they do not implement recursive):

- MySQL
- SQLite

-------------
Some examples
-------------

First of all, let's set up some imports and variables we will be using ::

    >>> import ConfigParser
    >>> from sqlalchemy import Table, Column, ForeignKey, MetaData, create_engine
    >>> from sqlalchemy import Unicode, select, and_
    >>> from sqlalchemy.orm import mapper, relationship, scoped_session, sessionmaker
    >>> from sqla_hierarchy import *
    >>> DBSession = scoped_session(sessionmaker())
    >>> metadata = MetaData()
    >>> from README_dtest import engine
    >>> DBSession.configure(bind=engine)
    >>> metadata.bind = engine

Let's build some simple table/class to hold boss/employee relation ::

    >>> example_tb = Table('employee', metadata,
    ...                    Column('id', Unicode, primary_key=True),
    ...                    Column('boss', Unicode, ForeignKey('employee.id')))
    >>> class Employee(object):
    ...     def __init__(self, employee, boss=None):
    ...         self.id = employee
    ...         self.boss = boss
    ...     def __repr__(self):
    ...         return "<Employee %s, Boss %s>" % (self.id, self.boss)
    ...
    >>> mapper(Employee, example_tb, properties={  #doctest: +ELLIPSIS
    ...        'parent': relationship(Employee, remote_side=[example_tb.c.id])})
    <Mapper at 0x...; Employee>
    >>> example_tb.drop(checkfirst=True)
    >>> example_tb.create(checkfirst=True)

Add some data ::

    >>> pl = [Employee(u'King Cold', None), Employee(u'Frieza', u'King Cold'),
    ...       Employee(u'Zarbon', u'Frieza'), Employee(u'Dodoria', u'Frieza'),
    ...       Employee(u'Captain Ginyu', u'Frieza'),
    ...       Employee(u'Jeice', u'Captain Ginyu'),
    ...       Employee(u'Burter', u'Captain Ginyu'),
    ...       Employee(u'Recoome', u'Captain Ginyu'),
    ...       Employee(u'Guldo', u'Captain Ginyu'),
    ...       Employee(u'Dr Gero', None), Employee(u'A-16', u'Dr Gero'),
    ...       Employee(u'A-17', u'Dr Gero'), Employee(u'A-18', u'Dr Gero'),
    ...       Employee(u'Cell', u'Dr Gero'), Employee(u'Cell Junior', u'Cell')]
    >>> DBSession.add_all(pl)
    >>> DBSession.commit()

Now let's query some basic relations. First we want a list of bosses and employees using some indentation to visually understand who depends on who ::

    >>> qry = Hierarchy(DBSession, example_tb, select([example_tb]))
    >>> rs = DBSession.execute(qry).fetchall()
    >>> for ev in rs:
    ...     if ev.level == 1:
    ...         print(ev.id)
    ...     else:
    ...         print(" "*2*ev.level+ev.id)
    Dr Gero
        A-16
        A-17
        A-18
        Cell
          Cell Junior
    King Cold
        Frieza
          Captain Ginyu
            Burter
            Guldo
            Jeice
            Recoome
          Dodoria
          Zarbon

Let's take a look at the special attributes sqla_hierachy added ::

    >>> print(rs[0])
    (u'Dr Gero', None, 1, ['Dr Gero'], False)

*Level*: The relative position of this record in the tree. '1' means he/she is the root. The higher the number, the bigger the distance is between the root and the current record ::

    >>> print(rs[0].level)
    1

*Connect Path*: Print the full list of members of this relation: from the root up to the current record::

    >> print(rs[0].connect_path)
    ['Dr Gero']

*Is Leaf*: If is_leaf is True, this record has no more dependents. If False, there are more records that depend on him/her::

    >>> print(rs[0].is_leaf)
    False

Now an example with a record that is a leaf ::

    >>> print(rs[9].level, rs[9].is_leaf)
    (4, True)
    >>> print(rs[9].connect_path)
    ['King Cold', 'Frieza', 'Captain Ginyu', 'Burter']

.. _Table: http://www.sqlalchemy.org/docs/core/schema.html#sqlalchemy.schema.Table
.. _Select: http://www.sqlalchemy.org/docs/core/expression_api.html#sqlalchemy.sql.expression.Select _
