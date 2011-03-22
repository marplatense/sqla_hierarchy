--------------
SQLA_Hierarchy
--------------

-----------
Description
-----------

Given a Table object and a Select expression, this class will return the information from these objects with some extra columns that will properly denote the hierarchical relation between the rows. The returned Hierarchy object could then be executed and it will return the same Select statement submitted plus the following columns:

- level: the relative level of the row related to its parent
- connect_path: a list with all the ids that compound this part of the hierarchy, from the root node to the current value
- is_leaf: boolean indicating is the particular id is a leaf or not

The resultset will be returned properly ordered by the levels in the hierarchy

Special remarks:

- The selected table must have a self referential foreign key relation, otherwise it will raise MissingForeignKey
- Not every database is supported (at the moment). Check the global var supported_db for an up2date list. Trying to execute Hierarchy with an unsupported db will raise NotImplementedError or HierarchyLesserError or HierarchyGreaterError (check the errors classes docstring for the exact meaning of each of them).
- To prevent the query from returning every node as a different starting node and, therefore, having duplicate values, you can provide the 'starting_node' parameter in the kwargs. The value you must provide is the parent id for the root node you want to start building the hierarchical tree. None has the same meaning as "0" since we perform a coalesce function in the query. By default the system will add a 'starting_node'="0". If you don't want a starting node, pass 'starting_node'=False and the clause will not be added to the query

-------------
Some examples
-------------

First of all, let's set up some imports and variables we will be using ::

    >>> import ConfigParser
    >>> from sqlalchemy import Table, Column, ForeignKey, MetaData, create_engine
    >>> from sqlalchemy import Integer, Unicode, Boolean
    >>> from sqlalchemy import select, and_
    >>> from sqlalchemy.orm import mapper, relationship, scoped_session, sessionmaker
    >>> from sqla_hierarchy import *
    >>> DBSession = scoped_session(sessionmaker())
    >>> metadata = MetaData()
    >>> config = ConfigParser.ConfigParser() 
    >>> config.read('setup.cfg')
    ['setup.cfg']
    >>> engine = create_engine('postgresql://%s' % config.get('dburi', 'pg-db'))
    >>> DBSession.configure(bind=engine)
    >>> metadata.bind = engine

