import sys
sys.path.insert(0, '.')
from lambda_function_aws import lambda_handler
import json

event = {'request_type': 'whatsapp_summary'}
result = lambda_handler(event, None)
body = json.loads(result['body'])

# Write to file
with open('summary_output.txt', 'w', encoding='utf-8') as f:
    if 'summary' in body:
        f.write(body['summary'])
        print("Summary saved to summary_output.txt")
        print(f"Rounds in database: {body['rounds_count']}")
    else:
        f.write(json.dumps(body, indent=2))
        print("Error response saved to summary_output.txt")
        print(json.dumps(body, indent=2))
