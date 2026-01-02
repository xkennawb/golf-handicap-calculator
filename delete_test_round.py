import boto3
from botocore.config import Config

# Configure boto3 to skip SSL verification
config = Config(
    signature_version='v4',
)

# Initialize DynamoDB with config
dynamodb = boto3.resource(
    'dynamodb', 
    region_name='ap-southeast-2',
    config=config,
    verify=False
)
table = dynamodb.Table('golf-rounds')

# Delete the test round from January 1, 2026
date_key = '2026-01-01'

try:
    response = table.delete_item(Key={'date': date_key})
    print(f"✅ Successfully deleted round with date: {date_key}")
except Exception as e:
    print(f"❌ Error deleting round: {e}")
