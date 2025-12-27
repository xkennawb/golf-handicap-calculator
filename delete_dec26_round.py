import boto3
from decimal import Decimal
import json
import os

# Set AWS credentials
os.environ['AWS_ACCESS_KEY_ID'] = 'REMOVED_AWS_KEY'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'REMOVED_AWS_SECRET'

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2', verify=False)
table = dynamodb.Table('golf-rounds')

def delete_dec26_round():
    """Delete the Dec 26, 2025 round"""
    
    # First, let's see what we have for Dec 26
    response = table.scan(
        FilterExpression='#d = :date',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={':date': '2025-12-26'}
    )
    
    rounds = response.get('Items', [])
    print(f"\nFound {len(rounds)} round(s) for Dec 26, 2025:")
    
    for round_data in rounds:
        print(f"\nRound keys: {round_data.keys()}")
        print(f"Date: {round_data.get('date')}")
        print(f"Course: {round_data.get('course')}")
        print(f"Players: {[p.get('name') for p in round_data.get('players', [])]}")
        print(f"Time UTC: {round_data.get('time_utc')}")
        
        # The primary key is just 'date'
        print(f"\nDeleting round with date: {round_data['date']}...")
        
        try:
            table.delete_item(
                Key={'date': round_data['date']}
            )
            print("✓ Deleted!")
        except Exception as e:
            print(f"Failed to delete: {e}")
    
    # Verify deletion
    response = table.scan(
        FilterExpression='#d = :date',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={':date': '2025-12-26'}
    )
    
    remaining = response.get('Items', [])
    print(f"\n✓ Verification: {len(remaining)} round(s) remaining for Dec 26, 2025")
    
    # Get total count
    response = table.scan(Select='COUNT')
    total = response['Count']
    print(f"✓ Total rounds in database: {total}")

if __name__ == '__main__':
    delete_dec26_round()
