"""
Create a NEW Lambda function from scratch with OpenAI key pre-configured
"""
import boto3
import os
import json
from load_credentials import load_credentials

load_credentials()

NEW_OPENAI_KEY = os.environ.get('OPENAI_API_KEY')

lambda_client = boto3.client('lambda', region_name='ap-southeast-2', verify=False)
iam_client = boto3.client('iam', verify=False)

print("Creating NEW Lambda function with OpenAI key...")
print("=" * 60)

# Step 1: Check if we need to create an execution role
role_name = 'lambda-golf-handicap-role'
print(f"\n[1/4] Checking IAM role '{role_name}'...")

try:
    role = iam_client.get_role(RoleName=role_name)
    role_arn = role['Role']['Arn']
    print(f"  ✓ Role exists: {role_arn}")
except iam_client.exceptions.NoSuchEntityException:
    print(f"  Creating role...")
    
    # Create role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    role = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    role_arn = role['Role']['Arn']
    print(f"  ✓ Role created: {role_arn}")
    
    # Attach basic Lambda execution policy
    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    )
    print(f"  ✓ Attached AWSLambdaBasicExecutionRole")
    
    # Attach DynamoDB access
    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
    )
    print(f"  ✓ Attached AmazonDynamoDBFullAccess")
    
    print("  ⚠ Waiting 10 seconds for role to propagate...")
    import time
    time.sleep(10)

# Step 2: Read the deployment package
print(f"\n[2/4] Reading deployment package...")
if not os.path.exists('lambda_function.zip'):
    print("  ✗ lambda_function.zip not found!")
    print("  Run: .\\build_lambda_package.ps1")
    exit(1)

with open('lambda_function.zip', 'rb') as f:
    zip_content = f.read()
print(f"  ✓ Package loaded: {len(zip_content) / 1024 / 1024:.2f} MB")

# Step 3: Create the new function
new_function_name = 'golf-handicap-tracker-v2'
print(f"\n[3/4] Creating Lambda function '{new_function_name}'...")

try:
    response = lambda_client.create_function(
        FunctionName=new_function_name,
        Runtime='python3.13',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_content},
        Timeout=30,
        MemorySize=512,
        Environment={
            'Variables': {
                'OPENAI_API_KEY': NEW_OPENAI_KEY
            }
        }
    )
    print(f"  ✓ Function created!")
    print(f"  ARN: {response['FunctionArn']}")
    
except lambda_client.exceptions.ResourceConflictException:
    print(f"  ⚠ Function already exists, updating code and environment...")
    
    # Update code
    lambda_client.update_function_code(
        FunctionName=new_function_name,
        ZipFile=zip_content
    )
    print(f"  ✓ Code updated")
    
    # Update environment
    lambda_client.update_function_configuration(
        FunctionName=new_function_name,
        Environment={
            'Variables': {
                'OPENAI_API_KEY': NEW_OPENAI_KEY
            }
        }
    )
    print(f"  ✓ Environment updated")
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    exit(1)

# Step 4: Create Function URL
print(f"\n[4/4] Creating Function URL...")
try:
    url_config = lambda_client.create_function_url_config(
        FunctionName=new_function_name,
        AuthType='NONE'
    )
    function_url = url_config['FunctionUrl']
    print(f"  ✓ Function URL created!")
    print(f"\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"Your NEW Lambda Function URL:")
    print(f"{function_url}")
    print(f"\nUpdate your iOS Shortcut to use this new URL!")
    
except lambda_client.exceptions.ResourceConflictException:
    # URL already exists, get it
    url_config = lambda_client.get_function_url_config(FunctionName=new_function_name)
    function_url = url_config['FunctionUrl']
    print(f"  ✓ Function URL already exists:")
    print(f"  {function_url}")
    
except Exception as e:
    print(f"  ✗ Error creating Function URL: {e}")
    print(f"  You may need to create it manually in the console")

print("\n" + "=" * 60)
