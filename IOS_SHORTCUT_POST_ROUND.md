# iOS Shortcut - Add Golf Round

## Shortcut Steps Configuration

### Step 1: Ask for Input
- **Action:** Ask for Input
- **Prompt:** "Paste Tag Heuer Golf URL"
- **Input Type:** URL
- **Default Answer:** (leave blank)

---

### Step 2: Get Contents of URL (POST Request)
- **Action:** Get contents of URL
- **URL:** `https://wgrf7ptkhss36vmv7zph4aqzxy0spsff.lambda-url.ap-southeast-2.on.aws/`

**Show More Settings:**
- **Method:** POST
- **Headers:**
  - Add Header: `Content-Type` = `application/json`
- **Request Body:** JSON
- **JSON Content:**
```json
{
  "action": "add_round",
  "url": "Provided Input"
}
```
Note: In the JSON, select "Provided Input" from the variable picker (the magic wand icon)

---

### Step 3: Get Dictionary from Contents of URL
- **Action:** Get dictionary from
- **Input:** Contents of URL

---

### Step 4: Check if Error
- **Action:** If
- **Condition:** Dictionary has key "error"
  - **Then:**
    - Show Alert: "Error"
    - Message: Dictionary Value for "error"
    - Stop shortcut
  - **Otherwise:**
    - Continue to next step

---

### Step 5: Get Summary Value
- **Action:** Get Value
- **Key:** "summary"
- **From:** Dictionary

---

### Step 6: Show/Copy Result
- **Action:** Show Result
- **Input:** Dictionary Value
- Or use: Copy to Clipboard

---

## Quick Setup Text (Copy/Paste this structure)

```
1. Ask for Input
   - Prompt: "Paste Tag Heuer Golf URL"
   - Type: URL

2. Get contents of URL
   - URL: https://wgrf7ptkhss36vmv7zph4aqzxy0spsff.lambda-url.ap-southeast-2.on.aws/
   - Method: POST
   - Headers: Content-Type: application/json
   - Body: {"action": "add_round", "url": "[Provided Input]"}

3. Get dictionary from Contents of URL

4. If Dictionary has key "error"
   - Show Alert: Dictionary["error"]
   - Stop
   
5. Otherwise, Get value for "summary" in Dictionary

6. Copy Dictionary Value to clipboard (or Show Result)
```

---

## Testing

After creating the shortcut, test it by:
1. Run the shortcut
2. Paste a Tag Heuer URL when prompted
3. It should return the updated summary with the new round included

If it's a duplicate date, you'll see: "A round for this date already exists. Duplicate submission prevented."
