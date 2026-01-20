import boto3
import os
import json

from load_credentials import load_credentials

load_credentials()

client = boto3.client('lambda', region_name='ap-southeast-2', verify=False)

response = client.invoke(
    FunctionName='golf-handicap-tracker',
    InvocationType='RequestResponse',
    Payload=json.dumps({'action': 'get_summary'})
)

result = json.loads(response['Payload'].read().decode())
body = json.loads(result['body']) if 'body' in result else result

print("=" * 60)
print("GOLF LEADERBOARD STATS")
print("=" * 60)
print(f"\nTotal Rounds: {body.get('rounds_count', 'N/A')}")

# Extract player stats from summary if available
summary = body.get('summary', '')
lines = summary.split('\n')

# Look for season leaderboard section
print("\n2025 SEASON RANKINGS:\n")
in_leaderboard = False
rank = 1
for line in lines:
    if '2025 SEASON LEADERBOARD' in line:
        in_leaderboard = True
        continue
    if in_leaderboard and '0.00 avg' in line:
        print(f"{rank}. {line.strip()}")
        rank += 1
        if rank > 10:
            break

print("\n" + "=" * 60)

