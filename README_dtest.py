from nose import SkipTest
from tests import get_engine

def setup(mod):
    global engine
    engine = get_engine('pg-db')
