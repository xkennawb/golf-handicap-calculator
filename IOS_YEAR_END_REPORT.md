# iOS Shortcut: Year End Golf Report

## Overview
This shortcut calls your AWS Lambda function to generate and display the year-end golf season report.

## Setup Instructions

### 1. Deploy the Lambda Function (Already Done! ✅)

**Function is deployed and ready to use:**
- Function Name: `golf-year-end-report`
- Region: `ap-southeast-2`
- Runtime: Python 3.13
- URL: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/`

**To update the function:**
```powershell
# Build package with Lambda-compatible binaries
Remove-Item -Recurse -Force package
New-Item -ItemType Directory -Force -Path package
Copy-Item lambda_year_end_report.py package/
cd package
pip install --platform manylinux2014_x86_64 --target . --implementation cp --python-version 3.13 --only-binary=:all: openai -q
cd ..
Compress-Archive -Path package\* -DestinationPath year-end-report.zip -Force

# Deploy
python -c "import boto3; c = boto3.client('lambda', region_name='ap-southeast-2', verify=False); z = open('year-end-report.zip', 'rb').read(); c.update_function_code(FunctionName='golf-year-end-report', ZipFile=z); print('Updated')"
```

### 2. Function URL (Already Configured! ✅)

**Your Lambda URL:**
```
https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/
```

This URL is public and ready to use in your iOS Shortcut.

### 3. Create iOS Shortcut

**Shortcut Steps:**

1. **Add to Home Screen** - Name: "⛳ Year End Report"

2. **Get Contents of URL**
   - URL: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/`
   - Method: GET
   - Request Body: (none)
   - Headers: (none)

3. **Get Dictionary from Input**
   - Input: Contents of URL

4. **Get Dictionary Value**
   - Key: `summary`
   - Dictionary: Dictionary

5. **Copy to Clipboard**
   - Input: Dictionary Value

6. **Show Notification**
   - Title: "Year End Report Ready"
   - Body: "Report copied to clipboard - paste into WhatsApp"

7. **Open URL**
   - URL: `whatsapp://`
   - (This opens WhatsApp so you can paste the report)

### Optional: Specify Year

To generate a report for a different year:

1. Add **Ask for Input** at the beginning
   - Question: "Which year?"
   - Default Answer: `2025`
   - Input Type: Number

2. Modify **Get Contents of URL**
   - URL: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/?year={AskForInput}`

## Usage

1. Run the shortcut from your home screen
2. The report will be generated and copied to your clipboard
3. WhatsApp will open automatically
4. Navigate to your golf group chat
5. Paste the report
6. Send!

## Troubleshooting

- **"No qualified players" error**: Make sure there are at least 10 rounds played in that year
- **Lambda timeout**: Increase the Lambda timeout to 30 seconds in AWS Console
- **URL not working**: Make sure the Function URL is enabled and has NONE auth type

## Example URLs

- Get current year report: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/`
- Get 2025 report: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/?year=2025`
- Get 2024 report: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/?year=2024`

## Local Testing

You can also generate the report locally and save to file:

```powershell
# Fetch and save report to file
python save_report.py

# Opens: 2025_YEAR_END_REPORT_WHATSAPP.txt
# Ready to copy/paste into WhatsApp
```
