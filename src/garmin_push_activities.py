from packages import urllib3
from packages import pymysql
from connectstats import garminapi
import os


def handler(event, context):
    api = garminapi.api()

    api.save_to_cache('cache_activities', event )

    result = {
        'statusCode' : 200,
        'headers' : {
            'Content-Type' : 'application/json'
        }
        #'body'
    }

    return result

