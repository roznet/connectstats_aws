from connectstats import lambdas

def handler(event, context):
    tasks = {
        'push/activities':('garmin_save_to_cache','cache_activities'),
        'push/file':('garmin_save_to_cache','cache_fitfiles'),
        }
    return lambdas.proxy_handler(event,context,tasks)
