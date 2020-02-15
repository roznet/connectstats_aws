from packages import urllib3
import os
import json


def handler(event, context):
    pm = urllib3.PoolManager()
    status_url = os.environ['CS_ROZNET_STATUS_URL']
    response =  pm.request('GET', status_url )

    body = {'payload':event, 'response':json.loads(response.data) }
    if response.status == 200 :
        return { 'statusCode': 200, 'body' : json.dumps( body ), 'headers':{} }
    else:
        return { 'statusCode': response.status, 'body' : '{}', 'headers':{} }


