#!/bin/zsh

## grab file from local host
./tool_curl_api.py -o test/garmin_proxy_test_api_f.json -v -t=2 'http://localhost/prod/api/connectstats/search?token_id=1&backfill_file=1'
## grab activities from local host
./tool_curl_api.py -o test/garmin_proxy_test_api_a.json -v -t=2 'http://localhost/prod/api/connectstats/search?token_id=1&backfill_activities=1'


