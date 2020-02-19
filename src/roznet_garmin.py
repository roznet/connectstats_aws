from packages import urllib3
import os
import json
import logging

logging.getLogger().setLevel(logging.INFO)


def handler(event, context):
    logging.info( context )
    logging.info( event )

    info = { 'function_name': context.function_name, 'function_version':context.function_version, 'invoked_function_arn':context.invoked_function_arn }
        
    body = {'garmin': 1,'event':event, 'context':info }
    return { 'statusCode': 200, 'body' : json.dumps( body ), 'headers':{} }


