from packages import urllib3
from packages import pymysql
from connectstats import res
from connectstats import query
import json
import time
import os
import boto3
import logging

logging.getLogger().setLevel(logging.INFO)

class api:
    def __init__(self,stage='local'):
        self.res = res.resmgr(stage)
        self.userAccessTokenToUser = {}

        
    def send_message_to_queue(self,message):
        """Will trigger a queue event with the cache_id and table info"""

        self.res.send_message(message)

                
    def save_to_cache(self,table,event):
        if 'body' in event:
            body = event['body']
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            logging.info( 'query {}'.format( query ) )
            with self.res.cursor() as cur:
                cur.execute( query, (body, ) )
                lastid = cur.lastrowid
        else:
            logging.error('malformed event {}'.format(event))
            return 400
            
        self.res.commit()
        
        if 'activities' in body or 'activityFiles' in body or 'manuallyUpdatedActivities' in body:
            message = { 'command':'process_push_or_ping',
                       'args':{'cache_id' : lastid, 'table' : table },
                       'stage':self.res.stage
                       }

            self.send_message_to_queue( message )

        return 200

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
            with self.res.cursor() as cur:
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

        isping = 'callbackURL' in row
        
        user = self.garmin_user_for_accessToken( row['userAccessToken'] )
        if user and 'cs_user_id' in user:
            row['cs_user_id'] = user['cs_user_id']
            
        sql,key_val = self.sql_insert_or_update( table, row, ['summaryId','startTimeInSeconds'], key=table_key )
        new_row = key_val is None
        with self.res.cursor() as cur:
            cur.execute( sql, row )
            if not key_val:
                key_val = cur.lastrowid
        if 'json' in row:
            del row['json']
            
        row[table_key] = key_val
        if new_row:
            logging.info( 'inserted {}={}'.format( table_key, key_val) )
        else:
            logging.info( 'updated {}={}'.format( table_key, key_val ) )
        logging.info( row )
        self.res.commit()

        return row

    def garmin_user_for_accessToken(self,accessToken):
        if accessToken in self.userAccessTokenToUser:
            userInfo = self.userAccessTokenToUser[accessToken]
        else:
            query = 'SELECT `cs_user_id`,`userId` FROM `tokens` WHERE `userAccessToken` = %s'
            with self.res.cursor() as cur:
                cur.execute( query, accessToken )
                userInfo = cur.fetchone()
            self.userAccessTokenToUser[accessToken] = userInfo
            
        return userInfo

    def setup_token_id(self,token_id ):
        with self.res.cursor() as cursor:
            cursor.execute( 'SELECT userAccessToken,userAccessTokenSecret FROM tokens WHERE token_id = %s', (token_id, ) )

            row = cursor.fetchone()
        
        self.userAccessToken = row['userAccessToken']
        self.userAccessTokenSecret = row['userAccessTokenSecret']
        
    def setup_access_token(self,access_token ):
        with self.res.cursor() as cursor:
            cursor.execute( "SELECT userAccessToken,userAccessTokenSecret FROM `tokens` WHERE userAccessToken = %s", (access_token, ) )

            row = cursor.fetchone()
        
        self.userAccessToken = row['userAccessToken']
        self.userAccessTokenSecret = row['userAccessTokenSecret']

    def process_callback_url(self,body):
        args = body['args']
        file_id = args['file_id']
        table = args['table']

        with self.res.cursor() as cursor:
            cursor.execute( "SELECT * FROM {} WHERE file_id = {}".format( table, file_id ) )
            row = cursor.fetchone()
        print( row )
        q = query.query(self.res.config)
        self.setup_access_token( row['userAccessToken'] )

        q.setup_tokens(self.userAccessToken,self.userAccessTokenSecret)
        filecontent = q.query_url( row['callbackURL'] )

        filename = 'users/{userId}/assets/{fileType}/{file_id}'.format(**row)
        s3 = boto3.resource('s3')
        object = s3.Object('connectstats.ro-z.net', filename)
        object.put(Body=filecontent)
        logging.info('saved {}'.format(filename))
        
    
    def process_push_or_ping(self,body):
        args = body['args']
        cache_id = args['cache_id']
        cachetable = args['table']

        if cachetable == 'cache_activities':
            table = 'activities'
            tag = 'activities'
            table_key = 'activity_id'
        elif cachetable == 'cache_fitfiles':
            table = 'fitfiles'
            tag = 'activityFiles'
            table_key = 'file_id'
        else:
            return
        
        query = 'SELECT `json` FROM {} WHERE cache_id = {}'.format( cachetable, cache_id )
        logging.info( query )
        with self.res.cursor() as cur:
            cur.execute( query )
            payload = cur.fetchone()

        payload = json.loads( payload['json'] )

        if tag in payload:
            items = payload[tag]
            rows = []
            for item in items:
                row = self.process_garmin_item(item,table,table_key)
                rows += [ row ]
                # update cache map
                mapdata = {'cache_id':cache_id,table_key:row[table_key]}
                sql = self.sql_insert_or_update( '{}_map'.format( cachetable ), mapdata , [table_key])
                with self.res.cursor() as cur:
                    cur.execute( sql, mapdata )
                self.res.commit()

            messages = []
            for row in rows:
                if 'file_id' in row and 'callbackURL' in row:
                    message =  { 'command':'process_callback_url',
                                    'args':{'file_id' : row['file_id'], 'table' : 'fitfiles' },
                                    'stage':self.res.stage
                    }
                    self.res.send_message(message)

    def process_queue_message(self,event,context):
        if 'Records' in event:
            records = event['Records']
            logging.info( 'Processing {} events'.format( len( records ) ) )
            for record in records:
                if 'body' in record and 'messageId' in record:
                    body = json.loads( record['body'] )
                    if 'command' in body:
                        logging.info( 'Processing messageId {}'.format( record['messageId'] ) )
                        if 'stage' in body:
                            self.res.change_stage( body['stage'] )
                        if body['command'] == 'process_push_or_ping':
                            self.process_push_or_ping( body )
                        elif body['command'] == 'process_callback_url':
                            self.process_callback_url( body )
                        else:
                            logging.error('Unkonwn Commmand {}'.format(body))
