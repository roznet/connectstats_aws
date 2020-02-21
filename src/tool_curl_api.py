#!/usr/bin/env python3

import pprint
import json
import http
import urllib3
import urllib.parse
import time
import string
import random
import hashlib
import hmac
import re
import mysql.connector
import base64
import argparse
import logging
from connectstats import garminapi
from connectstats import query


class curl_api:

    def __init__(self,args):
        self.args = args

        self.verbose = args.verbose
        if self.verbose:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().setLevel(logging.ERROR)

        api = garminapi.api(args.stage)
        config = api.res.config
        
        self.consumerKey = config['consumerKey']
        self.consumerSecret = config['consumerSecret']

        if args.token:
            api.setup_token_id( args.token )
            self.userAccessToken = api.userAccessToken
            self.userAccessTokenSecret = api.userAccessTokenSecret
        elif args.system and 'serviceKey' in config and 'serviceKeySecret' in config:
            self.userAccessToken = config['serviceKey']
            self.userAccessTokenSecret = config['serviceKeySecret']
        self.query = query.query(api.res.config)
        self.query.verbose = args.verbose

    def query_url(self, accessUrl ):

        if self.verbose:
            print( '> Request {}'.format( accessUrl ) )
        
        self.query.setup_tokens( self.userAccessToken, self.userAccessTokenSecret )
        filecontent = self.query.query_url( self.args.url )
        
        return( filecontent )
        

    def proxy_output(self, path, content):
        parsed = urllib.parse.urlparse( path )
        path = parsed.path
        paths = [x for x in parsed.path.split('/') if x]
        if len(paths)>2:
            stage = paths[0]
            proxypath = '/'.join(paths[2:])
        else:
            stage = args.stage
            proxypath = path

        if parsed.query:
            query_dict = urllib.parse.parse_qs(parsed.query)
            #hack, only take first arguments
            query_dict = {k:v[0] for (k,v) in query_dict.items()}
        else:
            query_dict = {}
            
        jsonobj = json.loads( content )
        return json.dumps( { "path": path,
                                "httpMethod": "GET",
                                "headers": {},
                                "queryStringParameters": query_dict,
                                "pathParameters": {
                                    "proxy": proxypath
                                },
                                "requestContext": {
                                    "stage": stage,
                                },
                                "body": content.decode('utf-8' ),
                                "isBase64Encoded": False
        } ).encode('utf-8')



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser( description='Query ConnectStats API', formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument( 'url' )
    parser.add_argument( '-c', '--config', help='config.php file to use to extract information', default = '../api/config.php' )
    parser.add_argument( '-t', '--token', help='Token id for the access Token Secret (0=no authentification)', default = 0 )
    parser.add_argument( '-g', '--stage', help='Stage to use in the config', default = 'local' )
    parser.add_argument( '-o', '--outfile', help='file to save output' )
    parser.add_argument( '-v', '--verbose', help='verbose output', action='store_true' )
    parser.add_argument( '-p', '--proxy', help='format the output as json from an api proxy with path' )
    parser.add_argument( '-s', '--system', help='Authenticate as a system call', action='store_true' )
    args = parser.parse_args()
    
    req = curl_api(args)
    
    content = req.query_url( args.url )
    if args.proxy:
        content = req.proxy_output(args.proxy,content)
    
    if args.outfile:
        with open( args.outfile, 'wb' ) as of:
            of.write( content )
            if req.verbose:
                logging.info( '> Saved {}'.format( args.outfile ) )
    else:
        print( content.decode('utf-8' ) )

