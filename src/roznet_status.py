from packages import urllib3
import os

def handler(event, context):
    pm = urllib3.PoolManager()
    status_url = os.environ['CS_ROZNET_STATUS_URL']
    response = pm.request('GET', status_url )
    if response.status == 200 :
        return { 'statusCode': 200, 'body' : response.data, 'headers':{} }
    else:
        return { 'statusCode': response.status, 'body' : '{}', 'headers':{} }


