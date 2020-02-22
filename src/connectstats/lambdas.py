from connectstats import garminapi
import os
import logging

logging.getLogger().setLevel(logging.INFO)

def proxy_handler(event,context,tasks):
    statusCode = 500
    path = None
    
    try:
        path = event['pathParameters']['proxy']
        stage = event['requestContext']['stage']
    except Exception as e:
        logging.error('missing path or stage information in event {}'.format(event))
        statusCode = 400

    response = {'statusCode':statusCode}
    
    if path in tasks:
        (task,args) = tasks[path]

        api = garminapi.api(stage)

        if task and hasattr(api,task):
            logging.info( f'running {task}({args})' )
            response = getattr(api,task)(event, args )
            if 'statusCode' not in response or response['statusCode' ] != 200:
                logging.error( f'failed {task}' )
    else:
        logging.info( f"couldn't map {path} to a task" )
        response = {'statusCode':400}

    if 'statusCode' not in response:
        response['statusCode'] = 500
        
    return response
