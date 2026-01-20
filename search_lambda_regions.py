"""
Search for Lambda across all regions
"""
import boto3
import os
from load_credentials import load_credentials

load_credentials()

regions = ['us-east-1', 'us-west-2', 'ap-southeast-2', 'eu-west-1', 'ap-northeast-1']

print("Searching for Lambda functions across regions...")
print("=" * 60)

for region in regions:
    print(f"\nChecking {region}...")
    try:
        client = boto3.client('lambda', region_name=region, verify=False)
        functions = client.list_functions()
        if functions['Functions']:
            for f in functions['Functions']:
                print(f"  ✓ Found: {f['FunctionName']}")
        else:
            print(f"  No functions")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
print("If you found your function in a different region, update")
print("the region in your scripts and try again.")
