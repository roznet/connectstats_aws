from packages import urllib3
import os
import json
import logging

logging.getLogger().setLevel(logging.INFO)


def handler(event, context):
    status_url = os.environ['CS_ROZNET_STATUS_URL']
    pm = urllib3.PoolManager()
    response =  pm.request('GET', status_url )
        
    logging.info( context )
    logging.info( event )

    info = { 'function_name': context.function_name, 'function_version':context.function_version, 'invoked_function_arn':context.invoked_function_arn }
        
    body = {'payload':event, 'response':json.loads(response.data), 'context':info }
    if response.status == 200 :
        return { 'statusCode': 200, 'body' : json.dumps( body ), 'headers':{} }
    else:
        return { 'statusCode': response.status, 'body' : '{}', 'headers':{} }


