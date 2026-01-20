import boto3
from botocore.config import Config

# Configure boto3 to skip SSL verification
config = Config(signature_version='v4')

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb', 
    region_name='ap-southeast-2',
    config=config,
    verify=False
)
table = dynamodb.Table('golf-rounds')

# Scan for all rounds in 2026
print("Scanning for 2026 rounds...")
response = table.scan()
rounds = response.get('Items', [])

# Filter for 2026 rounds
rounds_2026 = [r for r in rounds if r['date'].startswith('2026')]

if not rounds_2026:
    print("✅ No 2026 rounds found - database is clean!")
else:
    print(f"Found {len(rounds_2026)} rounds from 2026:")
    for round_data in rounds_2026:
        print(f"  - {round_data['date']}")
    
    print("\nDeleting all 2026 rounds...")
    
    deleted_count = 0
    for round_data in rounds_2026:
        try:
            table.delete_item(Key={'date': round_data['date']})
            print(f"  ✅ Deleted: {round_data['date']}")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ Error deleting {round_data['date']}: {e}")
    
    print(f"\n✅ Successfully deleted {deleted_count} rounds from 2026")
