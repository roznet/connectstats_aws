#!/bin/zsh

## grab file from local host
./tool_curl_api.py -o test/garmin_proxy_test_f.json -v -t=2 'http://localhost/prod/api/connectstats/search?token_id=1&backfill_file=1' -p /local/garmin/push/file
## grab activities from local host
./tool_curl_api.py -o test/garmin_proxy_test_a.json -v -t=2 'http://localhost/prod/api/connectstats/search?token_id=1&backfill_activities=1' -p /local/garmin/push/file

# process the two files
./aws.zsh test garmin_proxy.py test/garmin_proxy_test_a.json
./aws.zsh test process_queue_message.py out/message_0.json

./aws.zsh test garmin_proxy.py test/garmin_proxy_test_f.json 
./aws.zsh test process_queue_message.py out/message_0.json
# file has an extra step to download the asset
./aws.zsh test process_queue_message.py out/message_0.json 
