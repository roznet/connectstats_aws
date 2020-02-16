from packages import urllib3
from packages import pymysql
import json
import time
import os
import boto3

class api:
    def __init__(self):
        configfile = open( 'config.json', 'r' )
        fullconfig = json.load( configfile )
        self.config = fullconfig['test']
        self.db = pymysql.connect( self.config['db_host'], user=self.config['db_username'], passwd=self.config['db_password'],db=self.config['database'], connect_timeout=5)


    def trigger_queue(self,table,lastid):
        print( 'sanding {} {}'.format( table, lastid ) )
        
        sqs = boto3.resource('sqs')

        # Get the queue
        queue = sqs.get_queue_by_name(QueueName='connectstats')

        data={'cache_id' : lastid, 'table' : table }
            
        response = queue.send_message(
            MessageBody=json.dumps( data )
        )

        print(response.get('MessageId'))
        
    def save_to_cache(self,table,event):
        if( 'payload' in event and 'body' in event['payload'] ):
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            with self.db.cursor() as cur:
                cur.execute( query, (event['payload']['body'], ) )
                lastid = cur.lastrowid
        else:
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            with self.db.cursor() as cur:
                cur.execute( query, (json.dumps( event ), ) )
                lastid = cur.lastrowid
                
        self.db.commit()
        
        self.trigger_queue(table, lastid )

    def process_activities(self,event,context):
        print( json.dumps(  event ) )
            
        
