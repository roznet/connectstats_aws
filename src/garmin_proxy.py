from packages import urllib3
from packages import pymysql
from connectstats import garminapi
import os
import logging

logging.getLogger().setLevel(logging.INFO)

def handler(event, context):
    statusCode = 200
    response = {}
    
    try:
        path = event['pathParameters']['proxy']
        stage = event['requestContext']['stage']
    except Exception as e:
        statusCode = 400

    if statusCode == 200:
        api = garminapi.api(stage)
        
        if path == 'push/activities':
            args = 'cache_activities'
            task = 'save_to_cache'
        elif path == 'push/files':
            args = 'cache_fitfiles'
            task = 'save_to_cache'
        else:
            args = None
            task = None
        if task and hasattr(api, task):
            response = getattr(api,task)(event, args )
        else:
            response = {'statusCode':400}

    if 'statusCode' not in response:
        response['statusCode'] = 400

    if response['statusCode'] != 200:
        logging.error('malformed event {}'.format(event))
        
    return response

