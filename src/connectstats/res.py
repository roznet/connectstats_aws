from packages import urllib3
from packages import pymysql
from connectstats import filequeue
import json
import time
import os
import boto3
import logging

logging.getLogger().setLevel(logging.INFO)

class resmgr:
    def __init__(self,stage='local'):
        configfile = open( 'config.json', 'r' )
        self.fullconfig = json.load( configfile )
        
        self.config = self.fullconfig[stage]
        self.stage = stage

        self.dbs = {}
        self.queues = {}

    def change_stage(self,stage):
        if stage in self.fullconfig and stage != self.stage:
            logging.info('switched to stage {}'.format( stage ) )
            self.config = self.fullconfig[stage]
            self.stage = stage
        
    def db(self):
        if self.stage not in self.dbs:
            logging.info( 'connecting to mysql[{}] {} as {}'.format(self.stage, self.config['db_host'], self.config['db_username']))
            self.dbs[self.stage] = pymysql.connect( self.config['db_host'], user=self.config['db_username'], passwd=self.config['db_password'],db=self.config['database'], connect_timeout=5,cursorclass=pymysql.cursors.DictCursor)
            
        return self.dbs[self.stage] 
    
    def cursor(self):
        return self.db().cursor()

    def commit(self):
        self.db().commit()

    def queue(self):
        if self.stage not in self.queues:
            if 'sqs_queue_url' in self.config:
                url = self.config['sqs_queue_url']
                if url:
                    sqs = boto3.resource('sqs')
                    if sqs:
                        logging.info( 'Connected sqs[{}] {}'.format( stage, sqs ) )
                        # Get the queue
                        self.queues[self.stage] = sqs.Queue(url)
            elif 'file_queue_path' in self.config:
                self.queues[self.stage] = filequeue.filequeue(self.config['file_queue_path'])
                    
        return self.queues[self.stage]

    def send_message(self,data):
        queue = self.queue()
        
        response = queue.send_message(
            MessageBody=json.dumps( data )
        )
        if response:
            logging.info('message sent {}'.format(response.get('MessageId')))
        else:
            logging.error('Could not send message')
        return response
