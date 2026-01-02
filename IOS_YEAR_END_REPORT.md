# iOS Shortcut: Year End Golf Report

## Overview
This shortcut calls your AWS Lambda function to generate and display the year-end golf season report.

## Setup Instructions

### 1. Deploy the Lambda Function

```bash
# Package and deploy the year-end report Lambda
cd c:\GITHUB\golf-handicap-calculator

# Create deployment package
pip install --target ./package boto3
cd package
zip -r ../year-end-report.zip .
cd ..
zip -g year-end-report.zip lambda_year_end_report.py

# Deploy to AWS (you'll need to create this function first)
aws lambda create-function \
  --function-name golf-year-end-report \
  --runtime python3.13 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler lambda_year_end_report.lambda_handler \
  --zip-file fileb://year-end-report.zip \
  --region ap-southeast-2
```

### 2. Create Function URL (if not already done)

```bash
# Create a function URL for easy access from iOS
aws lambda create-function-url-config \
  --function-name golf-year-end-report \
  --auth-type NONE \
  --region ap-southeast-2

# This will return a URL like:
# https://abc123xyz.lambda-url.ap-southeast-2.on.aws/
```

### 3. Create iOS Shortcut

**Shortcut Steps:**

1. **Add to Home Screen** - Name: "⛳ Year End Report"

2. **Get Contents of URL**
   - URL: `https://YOUR-LAMBDA-URL.lambda-url.ap-southeast-2.on.aws/`
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
   - URL: `https://YOUR-LAMBDA-URL.lambda-url.ap-southeast-2.on.aws/?year={AskForInput}`

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

- Get current year report: `https://YOUR-URL.lambda-url.ap-southeast-2.on.aws/`
- Get 2025 report: `https://YOUR-URL.lambda-url.ap-southeast-2.on.aws/?year=2025`
- Get 2024 report: `https://YOUR-URL.lambda-url.ap-southeast-2.on.aws/?year=2024`
