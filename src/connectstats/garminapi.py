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
        self.db = pymysql.connect( self.config['db_host'], user=self.config['db_username'], passwd=self.config['db_password'],db=self.config['database'], connect_timeout=5,cursorclass=pymysql.cursors.DictCursor)

        self.userAccessTokenToUser = {}

    def trigger_queue(self,table,lastid):
        """Will trigger a queue event with the cache_id and table info"""
        
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

    def dict_to_sql_insert(self,table,data):
        columns = ['`{}`'.format( x ) for x in data.keys()]
        values = ['%({})s'.format( x ) for x in data.keys()]

        return 'INSERT INTO {} ({}) VALUES({})'.format( table, ', '.join( columns ), ', '.join( values ) )
    
    def dict_to_sql_update(self,table,data,keys,where):
        equal = ['`{}`=%({})s'.format( x, x ) for x in data.keys() if x not in keys]

        return 'UPDATE {} SET {} WHERE {}'.format( table, ', '.join( equal ), where )

    def sql_insert_or_update(self,table,data,keys,key=None):
        previous = None
        if len(keys)>0:
            where = ' AND '.join( '`{}` = {}'.format( x, data[x] ) for x in keys )
            with self.db.cursor() as cur:
                sql = 'SELECT {} FROM {} WHERE {}'.format( key if key else keys[0], table, where )
                cur.execute( sql )
                previous = cur.fetchone()
        if previous:
            sql = self.dict_to_sql_update(table,data,keys,where)
            if key:
                sql = (sql, previous[key] )
        else:
            sql = self.dict_to_sql_insert(table,data)
            if key:
                sql = (sql, None )
            
        return sql
            
            
    def process_garmin_item(self,item,table,table_key):
        extract_fields = ['summaryId', 'startTimeInSeconds', 'callbackURL', 'fileType', 'userId', 'userAccessToken']

        data = {}
        row  = {}

        for (key,val) in item.items():
            if key in extract_fields:
                row[key] = val
            else:
                data[key] = val

        user = self.garmin_user_for_accessToken( row['userAccessToken'] )
        if user and 'cs_user_id' in user:
            row['cs_user_id'] = user['cs_user_id']
        row['json'] = json.dumps( data )
        sql,key_val = self.sql_insert_or_update( table, row, ['summaryId','startTimeInSeconds'], key=table_key )
        new_row = key_val is None
        with self.db.cursor() as cur:
            cur.execute( sql, row )
            if not key_val:
                key_val = cur.lastrowid
        del row['json']
        row['activity_id'] = key_val
        if new_row:
            logging.info( 'inserted {}={}'.format( table_key, key_val) )
        else:
            logging.info( 'updated {}={}'.format( table_key, key_val ) )
        logging.info( row )
        self.db.commit()

        return row

    def garmin_user_for_accessToken(self,accessToken):
        if accessToken in self.userAccessTokenToUser:
            userInfo = self.userAccessTokenToUser[accessToken]
        else:
            query = 'SELECT `cs_user_id`,`userId` FROM `tokens` WHERE `userAccessToken` = %s'
            with self.db.cursor() as cur:
                cur.execute( query, accessToken )
                userInfo = cur.fetchone()
            self.userAccessTokenToUser[accessToken] = userInfo
            
        return userInfo

    
    def process_cache_one(self,info):
        cache_id = info['cache_id']
        cachetable = info['table']

        table = 'activities'
        table_key = 'activity_id'
        
        query = 'SELECT `json` FROM {} WHERE cache_id = {}'.format( cachetable, cache_id )
        logging.info( query )
        with self.db.cursor() as cur:
            cur.execute( query )
            payload = cur.fetchone()

        payload = json.loads( payload['json'] )

        tag = 'activities'

        if tag in payload:
            items = payload[tag]
            rows = []
            for item in items:
                row = self.process_garmin_item(item,table,table_key)
                rows += [ row ]
                # update cache map
                mapdata = {'cache_id':cache_id,table_key:row[table_key]}
                sql = self.sql_insert_or_update( '{}_map'.format( cachetable ), mapdata , [table_key])
                with self.db.cursor() as cur:
                    cur.execute( sql, mapdata )
                self.db.commit()

            
    def process_cache(self,event,context):
        """
        
        """
        if 'Records' in event:
            records = event['Records']
            logging.info( 'Processing {} events'.format( len( records ) ) )
            for record in records:
                if 'body' in record and 'messageId' in record:
                    logging.info( 'Processing messageId {}'.format( record['messageId'] ) )
                    body = json.loads( record['body'] )
                    logging.info( body )
                    self.process_cache_one( body )
