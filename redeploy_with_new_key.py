"""
Redeploy Lambda with updated OpenAI API key
This uses update_function_code which you already have permission for
"""
import boto3
import os
from load_credentials import load_credentials

# Load credentials from .env
load_credentials()

# Get OpenAI key from environment
NEW_OPENAI_KEY = os.environ.get('OPENAI_API_KEY')

client = boto3.client('lambda', region_name='ap-southeast-2', verify=False)
function_name = 'golf-handicap-tracker'

print(f"Redeploying {function_name} with new OPENAI_API_KEY...")
print("=" * 60)

# Step 1: Update the code (you have permission for this)
print("\n[1/2] Uploading Lambda code...")
with open('lambda_function.zip', 'rb') as f:
    response = client.update_function_code(
        FunctionName=function_name,
        ZipFile=f.read()
    )
print(f"  ✓ Code uploaded: {response['CodeSha256'][:16]}...")

# Step 2: Try to update environment variables
print("\n[2/2] Updating environment variables...")
try:
    response = client.update_function_configuration(
        FunctionName=function_name,
        Environment={
            'Variables': {
                'OPENAI_API_KEY': NEW_OPENAI_KEY
            }
        }
    )
    print(f"  ✓ OPENAI_API_KEY updated successfully!")
    print(f"  Key starts with: {NEW_OPENAI_KEY[:20]}...")
except Exception as e:
    print(f"  ✗ Could not update environment variable: {e}")
    print("\n" + "=" * 60)
    print("MANUAL STEP REQUIRED:")
    print("=" * 60)
    print("The code is updated but the environment variable needs manual update.")
    print(f"Go to AWS Console and add this environment variable:")
    print(f"  Key: OPENAI_API_KEY")
    print(f"  Value: {NEW_OPENAI_KEY}")

print("\n" + "=" * 60)
print("DEPLOYMENT COMPLETE")
print("=" * 60)
