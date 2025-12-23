# AWS Lambda Deployment Instructions

## Prerequisites
- AWS Account
- AWS CLI configured with credentials
- Python 3.11+

## Step 1: Create DynamoDB Table

```bash
aws dynamodb create-table \
    --table-name golf-rounds \
    --attribute-definitions \
        AttributeName=date,AttributeType=S \
    --key-schema \
        AttributeName=date,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

## Step 2: Create IAM Role for Lambda

Create a file `trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Create the role:
```bash
aws iam create-role \
    --role-name golf-lambda-role \
    --assume-role-policy-document file://trust-policy.json
```

Attach policies:
```bash
# CloudWatch Logs
aws iam attach-role-policy \
    --role-name golf-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# DynamoDB access
aws iam attach-role-policy \
    --role-name golf-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

## Step 3: Package Lambda Function

```bash
# Create deployment package directory
mkdir lambda-package
cd lambda-package

# Copy function
cp ../lambda_function.py .
cp ../requirements.txt .

# Install dependencies
pip install -r requirements.txt -t .

# Create zip file
powershell Compress-Archive -Path * -DestinationPath ../lambda-deployment.zip -Force
cd ..
```

## Step 4: Create Lambda Function

Get your role ARN:
```bash
aws iam get-role --role-name golf-lambda-role --query 'Role.Arn' --output text
```

Create the function (replace YOUR_ROLE_ARN):
```bash
aws lambda create-function \
    --function-name golf-handicap-tracker \
    --runtime python3.11 \
    --role YOUR_ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-deployment.zip \
    --timeout 30 \
    --memory-size 512 \
    --region us-east-1
```

## Step 5: Create API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
    --name "Golf Handicap API" \
    --description "API for golf handicap tracking" \
    --region us-east-1
```

Note the API ID from the response, then:

```bash
# Get the root resource ID
aws apigateway get-resources \
    --rest-api-id YOUR_API_ID \
    --region us-east-1

# Create a resource
aws apigateway create-resource \
    --rest-api-id YOUR_API_ID \
    --parent-id ROOT_RESOURCE_ID \
    --path-part "round" \
    --region us-east-1

# Create POST method
aws apigateway put-method \
    --rest-api-id YOUR_API_ID \
    --resource-id RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --region us-east-1

# Link Lambda to API Gateway
aws apigateway put-integration \
    --rest-api-id YOUR_API_ID \
    --resource-id RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:golf-handicap-tracker/invocations \
    --region us-east-1

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
    --function-name golf-handicap-tracker \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:YOUR_ACCOUNT_ID:YOUR_API_ID/*/*" \
    --region us-east-1

# Deploy API
aws apigateway create-deployment \
    --rest-api-id YOUR_API_ID \
    --stage-name prod \
    --region us-east-1
```

Your API endpoint will be:
```
https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/round
```

## Step 6: Initial Data Load

You'll need to load your existing 45 rounds into DynamoDB. Create a script `load_initial_data.py`:

```python
import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('golf-rounds')

# Load your rounds from process_47_rounds_fresh.py
# Extract the rounds_data list and convert to DynamoDB format

rounds = [
    # Copy from your script...
]

for round_data in rounds:
    table.put_item(Item=round_data)
    print(f"Loaded round: {round_data['date']}")

print("Data load complete!")
```

Run it:
```bash
python load_initial_data.py
```

## Step 7: Test the API

Test adding a round:
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/round \
  -H "Content-Type: application/json" \
  -d '{
    "action": "add_round",
    "url": "https://www.tagheuergolf.com/rounds/YOUR_ROUND_URL"
  }'
```

Test getting summary only:
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/round \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_summary"
  }'
```

## Step 8: Update Lambda (when needed)

```bash
# Rebuild package
cd lambda-package
powershell Compress-Archive -Path * -DestinationPath ../lambda-deployment.zip -Force
cd ..

# Update function
aws lambda update-function-code \
    --function-name golf-handicap-tracker \
    --zip-file fileb://lambda-deployment.zip \
    --region us-east-1
```

## iOS Shortcut Configuration

1. Open Shortcuts app on iOS
2. Create new shortcut
3. Add "Get Contents of URL" action
   - URL: `https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/round`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Request Body: JSON
   ```json
   {
     "action": "add_round",
     "url": "[Tag Heuer URL from clipboard or input]"
   }
   ```
4. Add "Get Dictionary from Input" action
5. Add "Get Dictionary Value" for key "summary"
6. Add "Show Result" or "Copy to Clipboard"

Now you can run the shortcut with a Tag Heuer URL and it will:
1. Send URL to Lambda
2. Lambda fetches round data
3. Lambda saves to DynamoDB
4. Lambda returns WhatsApp summary
5. Shortcut displays/copies summary

## Cost Estimate

- Lambda: ~$0.20/month (free tier: 1M requests, 400k GB-seconds)
- DynamoDB: ~$0.25/month (free tier: 25 GB storage, 25 WCU, 25 RCU)
- API Gateway: ~$3.50/month (free tier: 1M requests for 12 months)

Total: ~$4/month (or free with AWS Free Tier)
