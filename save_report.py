"""
Run this to save the 2025 year-end report to file
"""
import requests
import urllib3
urllib3.disable_warnings()

url = 'https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/?year=2025'
response = requests.get(url, verify=False)
data = response.json()

with open('2025_YEAR_END_REPORT_WHATSAPP.txt', 'w', encoding='utf-8') as f:
    f.write(data['summary'])

print("SUCCESS: Report saved to 2025_YEAR_END_REPORT_WHATSAPP.txt")
