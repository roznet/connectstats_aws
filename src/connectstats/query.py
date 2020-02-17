#!/usr/bin/env python3

import pprint
import http
import time
import string
import random
import hashlib
import hmac
import re

from packages import urllib3
from packages import pymysql

import base64
import logging

logging.getLogger().setLevel(logging.INFO)

class query:

    def __init__(self):
        configfile = open( 'config.json', 'r' )
        fullconfig = json.load( configfile )
        self.config = fullconfig['test']
        logging.info( 'connecting to {} as {}'.format(self.config['db_host'], self.config['db_username']))
        
        self.db = pymysql.connect( self.config['db_host'], user=self.config['db_username'], passwd=self.config['db_password'],db=self.config['database'], connect_timeout=5,cursorclass=pymysql.cursors.DictCursor)

        regexp = re.compile("'([a-zA-Z_]+)' +=> +'([-.0-9a-zA-Z_!]+)'," )
        config = dict()

        self.consumerKey = self.config['consumerKey']
        self.consumerSecret = self.config['consumerSecret']

        if 'serviceKey' in self.config and 'serviceKeySecret' in config:
            self.serviceKey = self.config['serviceKey']
            self.serviceKeySecret = self.config['serviceKeySecret']

        self.verbose = True

        
    def setup_token_id(self,token_id ):
        with self.db.cursor() as cursor:
            cursor.execute( 'SELECT userAccessToken,userAccessTokenSecret FROM tokens WHERE token_id = %s', (token_id, ) )

            row = cursor.fetchone()
        
        self.userAccessToken = row['userAccessToken']
        self.userAccessTokenSecret = row['userAccessTokenSecret']

        
    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    def authentification_header(self, accessUrl ):
        if self.userAccessToken is None and not self.args.system:
            if self.verbose:
                print( '> No authentification' )
            return {}
        
        method = "GET"

        parsed = urllib.parse.urlparse( accessUrl )
        get_params = dict( urllib.parse.parse_qsl( parsed.query ) )
        url_base = parsed.scheme + "://" + parsed.netloc + parsed.path
        
        nonce = self.id_generator(16)
        now = str(int(time.time()))

        oauthmethod = "HMAC-SHA1"
        oauthver = "1.0"

        userAccessToken = self.userAccessToken
        userAccessTokenSecret = self.userAccessTokenSecret
        
        if self.verbose:
            print( '> User Authentication: {}'.format( self.userAccessToken ) )

        oauth_params ={"oauth_consumer_key":self.consumerKey,
                       "oauth_token" :userAccessToken,
                       "oauth_nonce":nonce,
                       "oauth_timestamp":now,
                       "oauth_signature_method":oauthmethod,
                       "oauth_version":oauthver}

        all_params = dict(oauth_params)
        all_params.update( get_params )
        all_params_order = sorted(all_params.keys())

        params = '&'.join( [ '{}={}'.format( x, urllib.parse.quote(all_params[x]) )  for x in all_params_order ] )
        base = '&'.join( [ method, urllib.parse.quote(url_base, safe=''), urllib.parse.quote( params ) ] )
        key = '&'.join( [ urllib.parse.quote(self.consumerSecret), urllib.parse.quote(userAccessTokenSecret) ] )

        digest = hmac.new( key.encode('utf-8'), base.encode('utf-8'), hashlib.sha1 ).digest()
        signature = base64.b64encode( digest )

        oauth_params['oauth_signature'] = signature
        oauth_params_order = sorted( oauth_params.keys() )
        header_params = ', '.join( [ '{}="{}"'.format( x, urllib.parse.quote( oauth_params[x] ) ) for x in oauth_params_order] )
        header = 'OAuth {}'.format( header_params )
        headers = {'Authorization': header}
        
        return( headers )

    def query_url(self, accessUrl ):

        if self.verbose:
            print( '> Request {}'.format( accessUrl ) )
        
        headers = self.authentification_header( accessUrl )
        pm = urllib3.PoolManager()

        response = pm.request('GET', accessUrl, headers=headers )

        if response.status == 200:
            contents = response.data
            if self.verbose:
                print( '> Received {} bytes'.format( len(contents) ) )
        else:
            message = http.client.responses[response.status]
            if self.verbose:
                print( '> Error: {} {}'.format( response.status, message ) )
            contents = message.encode( 'utf-8' )
            
        return( contents )
        



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser( description='Query ConnectStats API', formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument( 'url' )
    parser.add_argument( '-c', '--config', help='config.php file to use to extract information', default = '../api/config.php' )
    parser.add_argument( '-t', '--token', help='Token id for the access Token Secret (0=no authentification)', default = 0 )
    parser.add_argument( '-o', '--outfile', help='file to save output' )
    parser.add_argument( '-v', '--verbose', help='verbose output', action='store_true' )
    parser.add_argument( '-s', '--system', help='Authenticate as a system call', action='store_true' )
    args = parser.parse_args()
    
    req = ConnectStatsRequest(args)
    
    content = req.query_url( args.url )
    if args.outfile:
        with open( args.outfile, 'wb' ) as of:
            of.write( content )
            if req.verbose:
                print( '> Saved {}'.format( args.outfile ) )
    else:
        print( content.decode('utf-8' ) )
        
             

