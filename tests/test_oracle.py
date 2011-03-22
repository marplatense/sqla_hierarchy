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
config = ConfigParser.ConfigParser() 
config.read('setup.cfg')
engine = create_engine('oracle://%s' % config.get('dburi', 'ora-db'))
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
    except Exception as generalerror:
        DBSession.rollback()
        raise(HierarchyTestError(generalerror))

class TestHierarchy(object):

    def test1_dialect(self):
        """Hierarchy oracle: check the supported version"""
        db_vendor, db_version = DBSession.bind.name, \
                                DBSession.bind.dialect.server_version_info
        if db_version < supported_db[db_vendor]:
            assert_raises(HierarchyLesserError, DBSession.execute, qry)
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb])) 

    def test2_fk_error(self):
        """Hierarchy oracle: When selecting a table with no fk->pk in the same 
        table, we should raise an error"""
        assert_raises(MissingForeignKey, Hierarchy, DBSession,
                      no_fk_tb, select([no_fk_tb]))

    def test3_execute(self):
        """Hierarchy oracle: just to see if it works"""
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb]))
        rs = DBSession.execute(qry).fetchall()
        ok_(12 == len(rs), 'Test should return 12 rows but instead it returns '
            '%d' %(len(rs)))

    def test4_level_attr(self):
        """Hierarchy oracle: fetching the extra 'level' column"""
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb])) 
        rs = DBSession.execute(qry).fetchall()
        ok_(hasattr(rs[0], 'level') == True, 
            "Fetched row has not got the 'level' extra column")
        # let's check if the level is right
        for ev in rs:
            ok_(ev.level==dummy_values[ev.id][0], 
                "Wrong level for 'item %d'. Expected %d, got %d" %\
                           (ev.id, dummy_values[ev.id][0], ev.level))

    def test5_is_leaf(self):
        """Hierarchy oracle: requesting the extra column 'is_leaf' and getting
        it"""
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb]))
        rs = DBSession.execute(qry).fetchall()
        ok_(hasattr(rs[0], 'is_leaf') == True, 
            "Fetched row has not got the 'is_leaf' extra column")
        # according to our tree, only 5, 7, 10, 11, 12 are leaves
        for every in rs:
            if every.id in (5,7,10,11,12):
                ok_(every.is_leaf == True, 
                    'is_leaf failed. Expected True for %d' \
                               %(every.id))
            else:
                ok_(every.is_leaf == False, 
                    'is_leaf failed. Expected False for %d' \
                               %(every.id))

    def test6_connect_path(self):
        """Hierarchy oracle: if present 'connect_path' in kw, we should return 
        the path using the sep character defined by the user"""
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb])) 
        rs = DBSession.execute(qry).fetchall()
        ok_(hasattr(rs[0], 'connect_path') == True, 
            "Fetched row has not got the 'connect_path' extra column")
        # let's check the paths
        for ev in rs:
            if ev.id == 1:
                ok_(ev.connect_path==[1], 'Failed path with id 1')
            elif ev.id == 2:
                ok_(ev.connect_path==[1,2], 'Failed path with id 2')
            elif ev.id == 3:
                ok_(ev.connect_path==[1,3], 'Failed path with id 3')
            elif ev.id == 4:
                ok_(ev.connect_path==[1,2,4], 'Failed path with id 4')
            elif ev.id == 5:
                ok_(ev.connect_path==[1,3,5], 'Failed path with id 5')
            elif ev.id == 6:
                ok_(ev.connect_path==[1,2,4,6], 'Failed path with id 6')
            elif ev.id == 7:
                ok_(ev.connect_path==[1, 3, 7], 'Failed path with id 7')
            elif ev.id == 8:
                ok_(ev.connect_path==[1, 2, 4, 6, 8], 'Failed path with id 8')
            elif ev.id == 9:
                ok_(ev.connect_path==[1, 3, 9], 'Failed path with id 9')
            elif ev.id == 10:
                ok_(ev.connect_path==[1, 2, 4, 6, 8, 10], 
                    'Failed path with id 10')
            elif ev.id == 11:
                ok_(ev.connect_path==[1, 3, 9, 11], 'Failed path with id 11')
            elif ev.id == 12:
                ok_(ev.connect_path==[1, 2, 4, 6, 8, 12], 
                    'Failed path with id 12')

    def test7_all_together(self):
        """Hierarchy oracle: all together now"""
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb])) 
        rs = DBSession.execute(qry).fetchall()
        ok_(hasattr(rs[0], 'connect_path') == True, 
            "Fetched row has not got the 'connect_path' extra column")
        ok_(hasattr(rs[0], 'level') == True, 
            "Fetched row has not got the 'level' extra column")
        for ev in rs:
            ok_(ev.level==dummy_values[ev.id][0], 
                "Wrong level for 'item %d'. Expected %d, got %d" %\
                (ev.id, dummy_values[ev.id][0], ev.level))
            if ev.id in (5,7,10,11,12):
                ok_(ev.is_leaf == True, 'is_leaf failed. Expected True for %d' \
                    %(ev.id))
            else:
                ok_(ev.is_leaf == False, 
                    'is_leaf failed. Expected False for %d' \
                    %(ev.id))
            if ev.id == 1:
                ok_(ev.connect_path==[1], 'Failed path with id 1')
            elif ev.id == 2:
                ok_(ev.connect_path==[1,2], 'Failed path with id 2')
            elif ev.id == 3:
                ok_(ev.connect_path==[1,3], 'Failed path with id 3')
            elif ev.id == 4:
                ok_(ev.connect_path==[1,2,4], 'Failed path with id 4')
            elif ev.id == 5:
                ok_(ev.connect_path==[1,3,5], 'Failed path with id 5')
            elif ev.id == 6:
                ok_(ev.connect_path==[1,2,4,6], 'Failed path with id 6')
            elif ev.id == 7:
                ok_(ev.connect_path==[1, 3, 7], 'Failed path with id 7')
            elif ev.id == 8:
                ok_(ev.connect_path==[1, 2, 4, 6, 8], 'Failed path with id 8')
            elif ev.id == 9:
                ok_(ev.connect_path==[1, 3, 9], 'Failed path with id 9')
            elif ev.id == 10:
                ok_(ev.connect_path==[1, 2, 4, 6, 8, 10], 
                    'Failed path with id 10')
            elif ev.id == 11:
                ok_(ev.connect_path==[1, 3, 9, 11], 'Failed path with id 11')
            elif ev.id == 12:
                ok_(ev.connect_path==[1, 2, 4, 6, 8, 12], 
                    'Failed path with id 12')

    def test8_where_clause(self):
        """Hierarchy oracle: we pass a where clause, we expect it to be 
        replicated in every subquery"""
        v1 = DBSession.query(Dummy).get(9)
        v2 = DBSession.query(Dummy).get(11)
        v1.active = False
        v2.active = False
        DBSession.flush()
        qry = Hierarchy(DBSession, dummy_tb, select([dummy_tb.c.id],
                                             dummy_tb.c.active==True)) 
        rs = DBSession.execute(qry).fetchall()
        expected = [1,2,3,4,5,6,7,8,10,12]
        real = [v[0] for v in rs]
        real.sort()
        ok_(expected==real, "We expect to get only the active nodes but we get "
                       "everything. Expected: %s, Got: %s" % (expected, real))
