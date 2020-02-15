#!/bin/zsh

command=${1?:"Command not specified"}
aws_cmd=aws

case $command in
		create)
				name=${2?:"function name not specified"}
				role_arn=`jq -j '.lambda_role' config.json`
				zip -q -r zip/${name}.zip ${name}.py packages connectstats config.json
				$aws_cmd lambda create-function --region eu-west-2 --function-name ${name} --zip-file fileb://zip/${name}.zip --role "${role_arn}" --handler ${name}.handler --runtime python3.8 --profile roznet_lambda_user
				;;
		update)
				name=${2?:"function name not specified"}
				zip -q -r zip/${name}.zip ${name}.py packages connectstats config.json
				$aws_cmd lambda update-function-code --region eu-west-2 --function-name ${name} --zip-file fileb://zip/${name}.zip --profile roznet_lambda_user
				;;
		createapi)
				aws apigateway get-rest-apis > out/rest_apis.json
				api_id=`jq -j '.items[] | select(.name=="connectstats") | .id' out/rest_apis.json`
				if [ -z "${api_id}" ]; then
						echo "Creating api"
						$aws_cmd apigateway create-rest-api --name connectstats > out/connectstats_api.json
						api_id=`jq -j '.id' out/connectstats_api.json`
				fi
				name=${2?:"function name not specified"}
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
							 
