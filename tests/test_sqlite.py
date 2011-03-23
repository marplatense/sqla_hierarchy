# -*- coding: UTF-8 -*-
""""Testing hierarchy dialect in sqlalchemy"""
import ConfigParser
from exceptions import NotImplementedError
from nose.tools import *

from sqlalchemy import Table, Column, ForeignKey, MetaData, create_engine
from sqlalchemy import Integer, Unicode, Boolean
from sqlalchemy import select, and_
from sqlalchemy.orm import mapper, relationship, scoped_session, sessionmaker
from sqla_hierarchy import *

DBSession = scoped_session(sessionmaker())
metadata = MetaData()
engine = create_engine('sqlite://')
DBSession.configure(bind=engine)
metadata.bind = engine

dummy_tb = Table('dummy_hierarchy', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('name', Unicode(10)),
                 Column('parent_id', Integer, ForeignKey('dummy_hierarchy.id'),
                        index=True),
                 Column('active', Boolean, default=True, nullable=False)
                )

class Dummy(object):
    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return "Dummy<%d, %s, %s>" %(self.id, self.name, self.parent_id)

mapper(Dummy, dummy_tb, properties = {
       'parent': relationship(Dummy, remote_side=[dummy_tb.c.id])})

no_fk_tb = Table('no_fk_tb', metadata, 
                 Column('id', Integer, primary_key=True),
                 Column('name', Unicode(10), nullable=False),
                 Column('descrip', Unicode(100))
                )

class NoFk(object):
    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return "NoFk<%d, %s, %s>" %(self.id, self.name, self.descrip)

mapper(NoFk, no_fk_tb)

class HierarchyTestError(Exception):
    pass

dummy_values = {1:(1,None),
                2:(2,1), 3:(2,1),
                4:(3,2), 5:(3,3), 7:(3,3), 9:(3,3),
                6:(4,4), 11:(4,9),
                8:(5,6),
                10:(6,8), 12:(6,8)}

def setup():
    """Create a temporary table.
    This will the final tree:
        1
          2
            4
              6
                8
                  10
                  12 
          3
            5
            7
            9
              11
    """
    dummy_tb.drop(checkfirst=True)
    dummy_tb.create(checkfirst=True)
    xlist = []
    for ev in dummy_values.items():
        xlist.append(Dummy(**{'id':ev[0], 'name':u'item %d' %(ev[0]),
                              'parent_id':ev[1][1]}))
    DBSession.add_all(xlist)
    DBSession.flush()
    try:
        DBSession.commit()
    except Exception, e:
        DBSession.rollback()
        raise(HierarchyTestError(e.args[0]))

class TestHierarchy(object):

    def test1_dialect(self):
        """Hierarchy sqlite: check the supported version"""
        db_vendor, db_version = DBSession.bind.name, \
                                DBSession.bind.dialect.server_version_info
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb])) 
        if db_vendor not in supported_db:
            assert_raises(NotImplementedError, DBSession.execute, qry)
