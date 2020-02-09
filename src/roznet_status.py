from packages import urllib3
import os

def handler(event, context):
    pm = urllib3.PoolManager()
    status_url = os.environ['CS_ROZNET_STATUS_URL']
    response = pm.request('GET', 'https://ro-z.net/prod/api/connectstats/status' )
    if response.status == 200 :
        return { 'status': 200, 'response' : response.data, 'url':status_url }
    else:
        return { 'status': response.status, 'response' : 'error', 'url':status_url }


