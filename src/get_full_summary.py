import requests
import json
import urllib3

urllib3.disable_warnings()

headers = {'X-Auth-Token': 'HnB9_VsxLXQVVQqNXi2ilSyY0hPQDJ9EcEt-mVoGej0'}
r = requests.get('https://wgrf7ptkhss36vmv7zph4aqzxy0spsff.lambda-url.ap-southeast-2.on.aws/', headers=headers, verify=False)
data = r.json()

print("Response:", json.dumps(data, indent=2))
if 'summary' in data:
    print(data['summary'])
    print(f"\n\nTotal rounds in database: {data['rounds_count']}")
else:
    print("Error in response:", data)
