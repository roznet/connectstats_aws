from packages import urllib3
from packages import pymysql
from connectstats import resources
from connectstats import query
import json
import time
import os
import boto3
import logging

logging.getLogger().setLevel(logging.INFO)

class api:
    def __init__(self,stage='local'):
        self.res = resources.resources_manager(stage)
        self.userAccessTokenToUser = {}

        
    def send_message_to_queue(self,message):
        """Will trigger a queue event with the cache_id and table info"""

        self.res.send_message(message)

    def rest_empty_response(self,statusCode):
        return {
            'statusCode' : statusCode,
            'headers' : {
                'Content-Type' : 'application/json'
            },
            'body' : ''
        }

    def connectstats_status(self,event,args):
        return {
            'statusCode' : statusCode,
            'headers' : {
                'Content-Type' : 'application/json'
            },
            'body' : event
        }

    
    def garmin_save_to_cache(self,event,table):
        if 'body' in event:
            body = event['body']
            query = 'INSERT INTO {} (`started_ts`,`json`) VALUES(FROM_UNIXTIME({}),%s)'.format( table, time.time() )
            logging.info( 'query {}'.format( query ) )
            with self.res.cursor() as cur:
                cur.execute( query, (body, ) )
                lastid = cur.lastrowid
        else:
            logging.error('malformed event {}'.format(event))
            return self.rest_empty_response(400)
            
        self.res.commit()
        
        if 'activities' in body or 'activityFiles' in body or 'manuallyUpdatedActivities' in body or 'file' in body:
            message = { 'queue_task':'queue_task_push_or_ping',
                        'args':{'cache_id' : lastid, 'table' : table },
                        'stage':self.res.stage
            }

            self.send_message_to_queue( message )

        return self.rest_empty_response(200)

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
            
            
    def garmin_process_push_or_ping_item(self,item,table,table_key):
        extract_fields = ['summaryId', 'startTimeInSeconds', 'callbackURL', 'fileType', 'userId', 'userAccessToken']

        data = {}
        row  = {}

        for (key,val) in item.items():
            if key in extract_fields:
                row[key] = val
            else:
                data[key] = val

        if 'callbackURL' in row:
            
            isping = True
        else:
            isping = False
            row['json'] = json.dumps( data )
            
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
            logging.info( f'inserted {table_key}={key_val}' )
        else:
            logging.info( f'updated {table_key}={key_val}' )
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
        '''
        Setup token secret for api call for a given token_id
        '''
        
        with self.res.cursor() as cursor:
            cursor.execute( 'SELECT userAccessToken,userAccessTokenSecret FROM tokens WHERE token_id = %s', (token_id, ) )

            row = cursor.fetchone()
        
        self.userAccessToken = row['userAccessToken']
        self.userAccessTokenSecret = row['userAccessTokenSecret']
        
    def setup_access_token(self,access_token ):
        '''
        Setup token secret for api call matching a userAccessToken
        '''
        with self.res.cursor() as cursor:
            cursor.execute( "SELECT userAccessToken,userAccessTokenSecret FROM `tokens` WHERE userAccessToken = %s", (access_token, ) )

            row = cursor.fetchone()
            
        self.userAccessToken = row['userAccessToken']
        self.userAccessTokenSecret = row['userAccessTokenSecret']

    def queue_task_callback_url(self,body):
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

        userId = row['userId']
        fileType = row['fileType'].lower()
        filename = f'users/{userId}/assets/{fileType}/{file_id}.{fileType}'
        self.res.save_file(filename,filecontent)
    
    def queue_task_push_or_ping(self,body):
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
            logging.error(f"don't know how to process table {cachetable}")
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
                row = self.garmin_process_push_or_ping_item(item,table,table_key)
                rows += [ row ]
                # update cache map
                mapdata = {'cache_id':cache_id,table_key:row[table_key]}
                sql = self.sql_insert_or_update( '{}_map'.format( cachetable ), mapdata , [table_key])
                with self.res.cursor() as cur:
                    cur.execute( sql, mapdata )
                self.res.commit()

                sql = f'UPDATE {cachetable} SET processed_ts = FROM_UNIXTIME({time.time()}) WHERE cache_id = {cache_id}'
                with self.res.cursor() as cur:
                    cur.execute( sql )
                self.res.commit()

            messages = []
            for row in rows:
                if 'file_id' in row and 'callbackURL' in row:
                    message =  { 'queue_task':'queue_task_callback_url',
                                 'args':{'file_id' : row['file_id'], 'table' : 'fitfiles' },
                                 'stage':self.res.stage
                    }
                    self.res.send_message(message)
        else:
            logging.error(f'Unable to find {tag} in message body')

    def process_queue_message(self,event,context):
        if 'Records' in event:
            records = event['Records']
            logging.info( 'Processing {} events'.format( len( records ) ) )
            for record in records:
                if 'body' in record and 'messageId' in record:
                    body = json.loads( record['body'] )
                    if 'queue_task' in body:
                        logging.info( 'Processing messageId {}'.format( record['messageId'] ) )
                        if 'stage' in body:
                            self.res.change_stage( body['stage'] )

                        task = body['queue_task']

                        if task.startswith('queue_task_') and hasattr(self, task):
                            logging.info( f'starting task {task}' )
                            getattr(self,task)( body )
                        else:
                            logging.error('Unknown Commmand {}'.format(body))
                    else:
                        logging.error(f'Missing queue_task {body}')
                else:
                    logging.error(f'missing body in {record}')
                    
