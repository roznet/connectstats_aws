#!/bin/zsh

command=${1?:"Command not specified"}
aws_cmd=aws

name=${2?:"function name not specified"}
name=${name:r}

case $command in
		create)
				aws iam list-roles > out/roles.json
				role_arn=`jq -j '.Roles[] | select ( .RoleName == "roznet_lambda_vpc_role") | .Arn' out/roles.json`
				source_function=garmin_push_activities
				aws lambda get-function-configuration --function-name ${source_function} > out/${source_function}_config.json
				jq -c '.VpcConfig | del(.VpcId)' out/${source_function}_config.json > out/${name}_vpc_config.json
				rm -f connectstats/*~
				zip -q -r zip/${name}.zip ${name}.py packages connectstats config.json
				$aws_cmd lambda create-function --region eu-west-2 --function-name ${name} --zip-file fileb://zip/${name}.zip --role "${role_arn}" --handler ${name}.handler --runtime python3.8 --vpc-config file://out/${name}_vpc_config.json
				;;
		update)
				zip -q -r zip/${name}.zip ${name}.py packages connectstats config.json
				$aws_cmd lambda update-function-code --region eu-west-2 --function-name ${name} --zip-file fileb://zip/${name}.zip --profile roznet_lambda_user
				;;
		test)
				testsuffix=${3:-"test"}
				testname=test/${name}_test.py
				if [ -f ${testsuffix} ]; then
						testinput=${testsuffix}
				else
						testinput=test/${name}_${testsuffix}.json
				fi
				echo 'import json' > $testname
				echo "import ${name}" >> $testname
				if [ -f ${testinput} ]; then
						echo "test input file: $testinput"
						echo "with open( '${testinput}', 'r' ) as f:" >> $testname
						echo "  event=json.load(f)" >> $testname
				else
						echo "no test input file: ${testinput}"
						echo "event={}" >> $testname
				fi
				echo "${name}.handler(event,{})" >> $testname
				cat $testname | python3 
				;;
		createapi)
				aws apigateway get-rest-apis > out/rest_apis.json
				api_id=`jq -j '.items[] | select(.name=="connectstats") | .id' out/rest_apis.json`
				if [ -z "${api_id}" ]; then
						echo "Creating api"
						$aws_cmd apigateway create-rest-api --name connectstats > out/connectstats_api.json
						api_id=`jq -j '.id' out/connectstats_api.json`
				fi
				aws apigateway get-resources --rest-api-id $api_id > out/connectstats_resources.json
				parent_id=`jq -j '.items[] | select( .path == "/") | .id' out/connectstats_resources.json`
				if [ -z "$parent_id" ]; then
						echo 'No parent id'
						exit
				fi
				resource_id=`jq -j ".items[] | select( .path == \"/${name}\") | .id" out/connectstats_resources.json`
				if [ -z "${resource_id}" ]; then
						$aws_cmd apigateway create-resource --rest-api-id $api_id --path-part ${name} --parent-id ${parent_id} 
						aws apigateway get-resources --rest-api-id $api_id > out/connectstats_resources.json
						resource_id=`jq -j ".items[] | select( .path == \"/${name}\") | .id" out/connectstats_resources.json`
				fi
				aws sts get-caller-identity > out/identity.json
				account_id=`jq -j '.Account' out/identity.json`
				region=`aws configure get region`
				method=POST
				stage=test
				$aws_cmd apigateway put-method --rest-api-id ${api_id} --resource-id ${resource_id} --http-method ${method} --authorization-type NONE
				$aws_cmd apigateway put-integration --rest-api-id $api_id --resource-id $resource_id --http-method ${method} --type AWS --integration-http-method ${method} --uri "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${region}:${account_id}:function:${name}/invocations"
				$aws_cmd apigateway put-method-response --rest-api-id $api_id --resource-id $resource_id --http-method ${method} --status-code 200 --response-models application/json=Empty
				$aws_cmd apigateway put-integration-response --rest-api-id $api_id --resource-id $resource_id --http-method ${method} --status-code 200 --response-templates application/json=""
				$aws_cmd create-deployment --rest-api-id $api_id --stage-name $stage
				$aws_cmd lambda add-permission --function-name ${name} --statement-id apigateway-${stage} --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${region}:${account_id}:${api_id}/*/POST/${name}"
				$aws_cmd lambda add-permission --function-name ${name} --statement-id apigateway-${stage} --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${region}:${account_id}:${api_id}/${stage}/POST/${name}"


esac				
							 
