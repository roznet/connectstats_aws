import sys
import logging
from packages import pymysql
import json

configfile = open( 'config.json', 'r' )
config = json.load( configfile )

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn = pymysql.connect( config['db_host'], user=config['db_username'], passwd=config['db_password'],db=config['database'], connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")
def handler(event, context):
    """
    This function fetches content from MySQL RDS instance
    """

    item_count = 0

    with conn.cursor() as cur:
        cur.execute("select * from `schema`")
        for row in cur:
            item_count += 1
            logger.info(row)
            #print(row)

    return "Found %d items from RDS MySQL table" %(item_count)
