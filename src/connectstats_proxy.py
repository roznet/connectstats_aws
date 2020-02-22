from connectstats import lambdas

def handler(event, context):
    tasks = {
        'connectstats/status':('connectstats_status',)
        }
    return( lambdas.proxy_handler(event,context,tasks) )
