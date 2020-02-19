from packages import urllib3
from packages import pymysql
from connectstats import garminapi
import os
import logging

logging.getLogger().setLevel(logging.INFO)


def handler(event, context):
    statusCode = 200

    try:
        path = event['pathParameters']['proxy']
        stage = event['requestContext']['stage']
    except Exception as e:
        statusCode = 400
        

    if statusCode == 200:
        api = garminapi.api(stage)
        
        if path == 'push/activities':
            table = 'cache_activities'
        elif path == 'push/files':
            table = 'cache_fitfiles'
        if table:
            statusCode = api.save_to_cache(table, event )
        else:
            statusCode = 400

    if statusCode != 200:
        logging.error('malformed event {}'.format(event))

    result = {
        'statusCode' : statusCode,
        'headers' : {
            'Content-Type' : 'application/json'
        },
        'body' : ''
    }

    return result

