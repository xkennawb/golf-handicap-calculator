# iOS Shortcuts Guide

Complete guide for all iOS shortcuts used with the Golf Handicap Calculator.

## Prerequisites

- iPhone with iOS 13 or later
- Shortcuts app (pre-installed on iOS)
- AWS Lambda deployed with Function URLs

---

## 1. Add Golf Round Shortcut

This shortcut adds a new round to the system and returns an updated summary.

### Function URL
```
https://wgrf7ptkhss36vmv7zph4aqzxy0spsff.lambda-url.ap-southeast-2.on.aws/
```

### Shortcut Steps

**Step 1: Ask for Input**
- Action: Ask for Input
- Prompt: "Paste Tag Heuer Golf URL"
- Input Type: URL

**Step 2: Get Contents of URL (POST Request)**
- Action: Get contents of URL
- URL: `https://wgrf7ptkhss36vmv7zph4aqzxy0spsff.lambda-url.ap-southeast-2.on.aws/`
- Method: POST
- Headers: `Content-Type: application/json`
- Request Body: JSON
```json
{
  "action": "add_round",
  "url": "Provided Input"
}
```
(Select "Provided Input" from the variable picker)

**Step 3: Get Dictionary from Contents of URL**
- Action: Get dictionary from
- Input: Contents of URL

**Step 4: Check for Errors**
- Action: If
- Condition: Dictionary has key "error"
  - **Then:** Show Alert with Dictionary["error"]
  - **Otherwise:** Continue

**Step 5: Get Summary**
- Action: Get Value
- Key: "summary"
- From: Dictionary

**Step 6: Copy to Clipboard**
- Action: Copy to Clipboard
- Input: Dictionary Value

**Step 7: Open WhatsApp**
- Action: Open URL
- URL: `whatsapp://`

### Usage
1. Run the shortcut
2. Paste Tag Heuer scorecard URL when prompted
3. Summary copies to clipboard
4. WhatsApp opens automatically
5. Paste and send to your golf group

### Error Messages
- "A round for this date already exists" - Duplicate submission prevented
- "Invalid URL" - Check the Tag Heuer URL format

---

## 2. Year End Report Shortcut

Generates the annual golf season report with statistics and leaderboards.

### Function URL
```
https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/
```

### Shortcut Steps (Simple Version)

**Step 1: Get Contents of URL**
- URL: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/`
- Method: GET

**Step 2: Get Dictionary from Input**
- Input: Contents of URL

**Step 3: Get Dictionary Value**
- Key: `summary`
- Dictionary: Dictionary

**Step 4: Copy to Clipboard**
- Input: Dictionary Value

**Step 5: Show Notification**
- Title: "Year End Report Ready"
- Body: "Report copied to clipboard - paste into WhatsApp"

**Step 6: Open WhatsApp**
- URL: `whatsapp://`

### Shortcut Steps (With Year Selection)

Add this at the beginning:

**Step 0: Ask for Input**
- Question: "Which year?"
- Default Answer: `2025`
- Input Type: Number

Then modify Step 1 URL to:
```
https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/?year={AskForInput}
```

### Usage
1. Run the shortcut
2. (Optional) Enter year if prompted
3. Report generates and copies to clipboard
4. WhatsApp opens automatically
5. Paste into golf group chat

---

## 3. General Setup Tips

### Adding to Home Screen
1. Open Shortcuts app
2. Long press on shortcut
3. Select "Details"
4. Tap "Add to Home Screen"
5. Choose icon and name (e.g., "⛳ Add Round", "📊 Year End")

### Alternative to WhatsApp Auto-Open

If automatic WhatsApp opening doesn't work:

Replace the "Open URL" step with:
- **Show Notification**: "Message copied! Open WhatsApp to paste"

Then manually open WhatsApp and paste.

### Sharing Shortcuts

1. Open Shortcuts app
2. Long press on shortcut
3. Select "Share"
4. Send via AirDrop or Messages to other golfers

---

## Troubleshooting

### "Could not connect to server"
- Check internet connection
- Verify Function URL is correct
- Ensure Lambda function is deployed

### "Invalid response"
- Check CloudWatch logs in AWS Console
- Verify Lambda function has correct environment variables
- Test Function URL directly in browser

### WhatsApp not opening
- Check WhatsApp is installed
- Use alternative notification method (see above)
- Try: `whatsapp://send?text=` instead of `whatsapp://`

### Duplicate round error
- Each date can only have one round
- Delete existing round first if needed
- Check date in Tag Heuer URL matches

---

## Advanced: Using Siri

Add Siri phrases to trigger shortcuts:

1. Open Shortcuts app
2. Select your shortcut
3. Tap "Add to Siri"
4. Record phrase like:
   - "Add golf round"
   - "Show year end report"

Then say: "Hey Siri, add golf round"
