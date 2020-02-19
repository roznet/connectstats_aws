from packages import urllib3
from packages import pymysql
from connectstats import garminapi
import os


def handler(event, context):
    statusCode = 200
    try:
        path = event['pathParameters']['proxy']
        (command,arg) = path.split('/')
        stage = event['requestContext']['stage']
    except:
        logging.error('malformed event {}'.format(event))
        statusCode = 400

    if statusCode == 200:
        if command == 'push':
            api = garminapi.api(stage)
            if arg == 'activities':
                table = 'cache_activities'
            elif arg == 'file':
                table = 'cache_fitfiles'
            statusCode = api.save_to_cache(table, event )

    result = {
        'statusCode' : statusCode,
        'headers' : {
            'Content-Type' : 'application/json'
        },
        'body' : ''
    }

    return result

