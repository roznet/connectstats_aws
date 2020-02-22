from packages import urllib3
from connectstats import resources

import os
import json
import logging

logging.getLogger().setLevel(logging.INFO)

def test_db():
    res = resources.resources_manager('dev')

    with res.cursor() as cur:
        cur.execute( 'SELECT MAX(`version`) FROM `schema`' )
        row = cur.fetchone()

    logging.info( f'got db version {row}' )

    return row

def test_url():
    status_url = os.environ['CS_ROZNET_STATUS_URL']
    pm = urllib3.PoolManager()
    response =  pm.request('GET', status_url )

    logging.info( f'query {status_url}' )
    return response

def handler(event, context):
        
    logging.info( context )
    logging.info( event )

    test_db()
    
    response = test_url()
    
    body = {'payload':event, 'response':json.loads(response.data) }
    if response.status == 200 :
        return { 'statusCode': 200, 'body' : json.dumps( body ), 'headers':{} }
    else:
        return { 'statusCode': response.status, 'body' : '{}', 'headers':{} }


