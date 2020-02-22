#!/bin/zsh

## grab file from local host
./tool_curl_api.py -o test/garmin_proxy_test_api_f.json -v -t=2 'http://localhost/prod/api/connectstats/search?token_id=1&backfill_file=1'
## grab activities from local host
./tool_curl_api.py -o test/garmin_proxy_test_api_a.json -v -t=2 'http://localhost/prod/api/connectstats/search?token_id=1&backfill_activities=1'

# curl to run the test
aws apigateway get-rest-apis > out/rest_apis.json
api_id=`jq -j '.items[] | select(.name=="connectstats") | .id' out/rest_apis.json`
api_url="https://${api_id}.execute-api.eu-west-2.amazonaws.com/dev"
curl -v -d @test/garmin_proxy_test_api_f.json "$api_url/garmin/push/file"
