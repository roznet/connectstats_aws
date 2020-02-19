#!/usr/bin/env python3

import pprint
import http
import time
import string
import random
import hashlib
import hmac
import re
import urllib3
import urllib.parse

from packages import pymysql

import base64
import logging

logging.getLogger().setLevel(logging.INFO)

class query:

    def __init__(self,config):
        self.config = config
        
        self.consumerKey = self.config['consumerKey']
        self.consumerSecret = self.config['consumerSecret']

        self.verbose = True

    def setup_tokens(self,userAccessToken,userAccessTokenSecret):
        self.userAccessToken = userAccessToken
        self.userAccessTokenSecret = userAccessTokenSecret

        
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
        
        
             

