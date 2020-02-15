# Setup

These contains my notes as I learn AWS for this project

```
aws iam create-group --group-name roznet_lambda_user_group
aws iam create-user --user-name roznet_lambda_user
aws iam add-user-to-group --user-name roznet_lambda_user --group-name roznet_lambda_user_group
aws iam put-user-policy --user-name roznet_lambda_user --policy-name roznet_lambda_all --policy-document file://roznet_lambda_policy.json
```

## Create profile/keys

Create login profile for user, get access keys and configure new profile with the keys

```
aws iam create-login-profile --username roznet_lambda_user --password 'XXXX'
aws iam create-access-key --user-name roznet_lambda_user
aws configure --profile roznet_lambda_user
export AWS_PROFILE=roznet_lambda_user
```

## Create Function

```
aws lambda create-function --region eu-west-2 --function-name roznet_status --zip-file fileb://roznet_status.zip --role "arn:aws:iam::XXXXXX:role/roznet_lambda_role" --handler roznet_status.handler --runtime python3.8 --profile roznet_lambda_user
```

## Update function

```
zip -q -r zip/roznet_status.zip roznet_status.py packages
aws lambda update-function-code --function-name roznet_status --zip-file fileb://zip/roznet_status.zip --profile roznet_lambda_user
```

## Update Environment variables

```
aws lambda update-function-configuration --function-name my-function --environment "Variables={BUCKET=my-bucket,KEY=file.txt}"
```

## List Functions

```
aws lambda list-functions --profile roznet_lambda_user
```

## Call function

```
aws lambda invoke --function-name quotes-lambda-function --log-type Tail --payload '{"a":1}' outputfile.txt
aws lambda invoke --invocation-type RequestResponse --function-name roznet_status --log-type Tail --payload '{"a":1}' --profile roznet_lambda_user statusout.txt
```

## Database

```
aws rds create-db-instance --db-name garmindev --engine MySQL --db-instance-identifier garmindev --backup-retention-period 3 --db-instance-class db.t2.micro --allocated-storage 5 --no-publicly-accessible --master-username roznet_dbuser --master-user-password XXX
```

## Setup packages

```
pip3 install --target packages urllib3
pip3 freeze --path packages > requirements.txt
pip3 install -r requirements.txt --target packages
```
