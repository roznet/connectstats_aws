from packages import urllib3
from packages import pymysql
import json
import time
import os
import boto3
import logging

logging.getLogger().setLevel(logging.INFO)

class api:
    def __init__(self):
        configfile = open( 'config.json', 'r' )
        fullconfig = json.load( configfile )
        self.config = fullconfig['test']
        logging.info( 'connecting to {} as {}'.format(self.config['db_host'], self.config['db_username']))
        self.db = pymysql.connect( self.config['db_host'], user=self.config['db_username'], passwd=self.config['db_password'],db=self.config['database'], connect_timeout=5)

    def trigger_queue(self,table,lastid):
        url = self.config['sqs_queue_url']
        logging.info( 'sending {}:{} to {}'.format( table, lastid, url ) )
        
        sqs = boto3.resource('sqs')
        if sqs:
            logging.info( 'got sqs {}'.format( sqs ) )
            # Get the queue
            queue = sqs.Queue(url)
            
            if queue:
                logging.info( 'received queue {}'.format( queue ) )

                data={'cache_id' : lastid, 'table' : table }

                response = queue.send_message(
                    MessageBody=json.dumps( data )
                )
                if response:
                    logging.info('message sent {}'.format(response.get('MessageId')))
                else:
                    logging.error('Could not send message')
                    
            else:
                logging.error( 'Could not get queue {}'.format( url ) )
        else:
            logging.error( 'Could not get sqs resource' )

        
    def save_to_cache(self,table,event):
        if( 'payload' in event and 'body' in event['payload'] ):
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            logging.info( 'query {}'.format( query ) )
            with self.db.cursor() as cur:
                cur.execute( query, (event['payload']['body'], ) )
                lastid = cur.lastrowid
        else:
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            logging.info( 'query {}'.format( query ) )
            with self.db.cursor() as cur:
                cur.execute( query, (json.dumps( event ), ) )
                lastid = cur.lastrowid
                
        self.db.commit()
        
        if 'activities' in event or 'activityFiles' in event or 'manuallyUpdatedActivities' in event:
            self.trigger_queue(table, lastid )

    def process_activities(self,event,context):
        logging.info( 'received event {}'.format( event ) )
