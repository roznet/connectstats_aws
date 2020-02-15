from packages import urllib3
from packages import pymysql
import json
import time
import os

class api:
    def __init__(self):
        configfile = open( 'config.json', 'r' )
        self.config = json.load( configfile )
        print( self.config )
        self.db = pymysql.connect( self.config['db_host'], user=self.config['db_username'], passwd=self.config['db_password'],db=self.config['database'], connect_timeout=5)


    def save_to_cache(self,table,event):
        if( 'payload' in event and 'body' in event['payload'] ):
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            with self.db.cursor() as cur:
                cur.execute( query, (event['payload']['body'], ) )
            self.db.commit()
        else:
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            with self.db.cursor() as cur:
                cur.execute( query, (json.dumps( event ), ) )
            self.db.commit()
            
        
