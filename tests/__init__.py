from nose import SkipTest
import ConfigParser
from sqlalchemy import create_engine


def get_engine(name):
    config = ConfigParser.ConfigParser()
    config.read('setup.cfg')
    try:
        uri = config.get('dburi', name)
    except ConfigParser.NoOptionError:
        raise SkipTest("No database configuration for %s is defined" % name)
    return create_engine(uri)
