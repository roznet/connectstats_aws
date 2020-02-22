import sys
import logging
from connectstats import resources
import json

logging.getLogger().setLevel(logging.INFO)

def handler(event, context):
    res = resources.resources_manager('dev')

    with res.cursor() as cur:
        cur.execute( 'SELECT MAX(version) FROM schema' )
        row = cur.fetchone()

    logging.info( f'got db version {row}' )

    return 'ok'
