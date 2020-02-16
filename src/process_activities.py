from packages import urllib3
from packages import pymysql
from connectstats import garminapi
import os


def handler(event, context):
    api = garminapi.api()

    api.process_cache(event,context)

    

