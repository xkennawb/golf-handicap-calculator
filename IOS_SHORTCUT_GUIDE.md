# iOS Shortcut Setup Guide

This guide will help you create an iOS Shortcut to trigger the golf handicap calculator from your iPhone.

## Overview

The shortcut will:
1. Ask you for the Tag Heuer scorecard URL
2. Send it to your AWS Lambda function
3. Display the results
4. Open WhatsApp with a pre-filled message ready to send

## Prerequisites

- iPhone with iOS 13 or later
- Shortcuts app (pre-installed on iOS)
- AWS Lambda deployed and Function URL obtained

## Step-by-Step Instructions

### Step 1: Create New Shortcut

1. Open the **Shortcuts** app on your iPhone
2. Tap the **+** button (top right) to create a new shortcut
3. Tap "Add Action"

### Step 2: Get URL Input

1. Search for "**Ask for Input**"
2. Add the action
3. Configure:
   - Question: `Paste Tag Heuer Scorecard URL`
   - Input Type: `URL`
   - Default Text: (leave empty)

### Step 3: Call AWS Lambda

1. Search for "**Get Contents of URL**"
2. Add the action
3. Configure:
   - URL: `YOUR_AWS_LAMBDA_FUNCTION_URL`
   - Method: `POST`
   - Headers:
     - Key: `Content-Type`
     - Value: `application/json`
   - Request Body: `JSON`
   - In the JSON field, tap "Add field" and configure:
     ```
     {
       "scorecard_url": "Provided Input"
     }
     ```
   - To add "Provided Input": Long press in the value field → Select "Provided Input" from the variables

### Step 4: Parse Response

1. Search for "**Get Dictionary from Input**"
2. Add the action
3. This will parse the JSON response

### Step 5: Show Results

1. Search for "**Show Alert**"
2. Add the action
3. Configure:
   - Title: `Handicaps Updated! ⛳`
   - Message: Tap in the message field and add these variables from "Dictionary Value":
     - Get `whatsapp_message` from "Contents of URL"
   
   To do this:
   - Long press in the Message field
   - Select "Get Dictionary Value"
   - Type: `whatsapp_message`

### Step 6: Open WhatsApp with Message

1. Search for "**URL**"
2. Add the action
3. In the URL field, type: `whatsapp://send?text=`
4. After the `=`, add the variable:
   - Long press → Get Dictionary Value → `whatsapp_message`
5. Search for "**Open URLs**"
6. Add the action (it will use the URL from the previous step)

### Step 7: Alternative - Copy to Clipboard (Simpler Option)

If WhatsApp integration doesn't work smoothly, replace steps 6 with:

1. Search for "**Copy to Clipboard**"
2. Add the action
3. Configure to copy the `whatsapp_message` variable
4. Search for "**Show Notification**"
5. Add the action with message: `Message copied! Open WhatsApp to paste and send`

### Step 8: Name Your Shortcut

1. Tap the shortcut name at the top
2. Rename to: `⛳ Golf Handicap`
3. Tap "Done"

## Visual Shortcut Flow

```
┌─────────────────────────────┐
│ Ask for Input               │
│ (Tag Heuer URL)            │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Get Contents of URL         │
│ POST to Lambda              │
│ Body: {"scorecard_url": URL}│
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Get Dictionary from Input   │
│ (Parse JSON response)       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Show Alert                  │
│ (Display results)           │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Open WhatsApp               │
│ (Pre-filled message)        │
└─────────────────────────────┘
```

## Adding to Home Screen

1. Open the shortcut
2. Tap the settings icon (•••)
3. Tap "Add to Home Screen"
4. Choose an icon and color
5. Tap "Add"

Now you have a one-tap app icon to run your handicap calculator!

## Adding to Siri

1. Go to Settings → Siri & Search
2. Tap "All Shortcuts"
3. Find "⛳ Golf Handicap"
4. Tap "+" to add phrase
5. Say: "Calculate golf handicaps" or "Update golf scores"

Now you can say "Hey Siri, calculate golf handicaps" and it will run!

## Testing

1. Get a Tag Heuer scorecard URL (e.g., from a recent round)
2. Run the shortcut
3. Paste the URL when prompted
4. Wait for the Lambda to process (5-10 seconds)
5. View the results
6. Share to WhatsApp

## Troubleshooting

### "Cannot Connect to Server"
- Check your Lambda Function URL is correct
- Ensure Lambda is deployed and running
- Check your internet connection

### "Invalid Response"
- Check Lambda logs in AWS CloudWatch
- Test Lambda directly in AWS Console first
- Verify Weather API key is set

### WhatsApp doesn't open
- Use the "Copy to Clipboard" alternative
- Manually open WhatsApp and paste
- Check WhatsApp URL scheme is enabled

### URL encoding issues
- Use the "URL Encode" action before opening WhatsApp
- Add it between the URL creation and Open URLs steps

## Example Shortcut Download

I can't provide a direct download link here, but you can:
1. Follow the steps above to create manually (takes 5 minutes)
2. Share your shortcut with friends once created
3. Or use a shortcut sharing service like RoutineHub.co

## Privacy & Security

⚠️ **Important**: The Lambda Function URL is **public** (no authentication required). Anyone with the URL can use it.

If you want to add authentication:
1. Use AWS API Gateway with API keys
2. Add the API key as a header in the shortcut
3. Or use AWS Cognito for user authentication

For personal use with friends, the public URL is usually fine.

## Next Steps

After your first successful run:
1. Check the S3 bucket for `handicaps.xlsx`
2. Download it to see all your historical data
3. Share the shortcut with your golf buddies
4. Enjoy automated handicap tracking! 🏌️‍♂️
