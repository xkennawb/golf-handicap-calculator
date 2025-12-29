# AI Commentary Setup Guide

## Step 1: Get OpenAI API Key

1. Go to https://platform.openai.com/signup
2. Create an account (or sign in)
3. Go to https://platform.openai.com/api-keys
4. Click **"Create new secret key"**
5. Give it a name: "Golf Handicap Lambda"
6. **Copy the key** (starts with `sk-...`) - you won't see it again!

## Step 2: Set Usage Limits (IMPORTANT - Prevents Overcharges)

1. In OpenAI dashboard, go to **Settings** → **Limits**
2. Set **Monthly budget limit**: $1.00
3. Enable **Email notification** at 50% and 100%
4. Click **Save**

This ensures you'll never be charged more than $1/month (covers 10,000+ summaries).

## Step 3: Add API Key to AWS Lambda

### Option A: Using AWS Console (Easiest)
1. Go to AWS Console → Lambda
2. Open function: `golf-handicap-tracker`
3. Click **Configuration** tab
4. Click **Environment variables** (left menu)
5. Click **Edit**
6. Click **Add environment variable**
7. Key: `OPENAI_API_KEY`
8. Value: (paste your `sk-...` key)
9. Click **Save**

### Option B: Using AWS CLI
```bash
aws lambda update-function-configuration \
  --function-name golf-handicap-tracker \
  --environment "Variables={OPENAI_API_KEY=sk-your-key-here}" \
  --region ap-southeast-2
```

## Step 4: Update Lambda Package

Run this in your terminal:
```powershell
cd C:\GITHUB\golf-handicap-calculator
python update_lambda_with_openai.py
```

## Step 5: Test It!

Run your iOS Shortcut - the summary should now include AI commentary at the bottom:

```
🎭 AI COMMENTARY:
Andy claims another victory with a solid 16 points, leaving Bruce to 
ponder what could have been. Meanwhile, Hamish's 12 points suggest 
the course had other ideas about his game plan! 😄
```

## Troubleshooting

**No commentary appears:**
- Check CloudWatch logs: `/aws/lambda/golf-handicap-tracker`
- Verify API key is set correctly
- Check OpenAI hasn't hit usage limit

**"OpenAI not available" in logs:**
- Lambda package missing `openai` library
- Re-run the update script

**Want to disable commentary temporarily:**
- Remove the `OPENAI_API_KEY` environment variable
- Lambda will work normally without it

## Costs

- **Per summary**: ~$0.0001 (one hundredth of a cent)
- **52 rounds/year**: ~$0.005 ($1 limit covers 200+ years)
- **Cache**: Requests within 5 minutes use cached commentary (free)

## Security

✅ **Protected by:**
- OpenAI $1/month hard limit
- Lambda 30 second timeout
- 5-minute response cache
- Error handling (fails gracefully)

**Maximum possible loss**: $1/month (even under attack)

---

## AI Commentary Features (Dec 2025)

The AI commentary now includes:

1. **Weather Line**: Factual weather conditions with emojis (☀️🌧️⛅)
2. **Player Banter**: Humorous commentary about all players who played that day
3. **Handicap Changes**: Automatically mentions when players' WHS handicaps change significantly (>0.05)
   - Example: "Fletcher dropped his handicap from 14.7 to 14.0"
4. **Form-Based Predictions**: Identifies next game favorite based on last 5 rounds
5. **Season Summary**: Brief observation about overall standings
6. **Father-Son Awareness**: Correctly identifies Fletcher as Andy's son

The AI is explicitly instructed to:
- Only mention players who actually played
- Be precise about Front 9 vs Back 9 scores
- Mention handicap changes when they occur
- Include predictions about next game favorite
- Announce season champion in late December games
