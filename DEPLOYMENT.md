# Deployment Guide

## Prerequisites

1. **AWS Account**: Sign up at https://aws.amazon.com
2. **AWS CLI**: Install from https://aws.amazon.com/cli/
3. **SAM CLI**: Install from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
4. **OpenWeatherMap API Key**: Free key from https://openweathermap.org/api

## Option 1: Deploy with AWS SAM (Recommended)

### Step 1: Configure AWS CLI

```bash
aws configure
```

Enter your AWS Access Key ID, Secret Access Key, region (e.g., `us-east-1`), and output format (`json`).

### Step 2: Build the application

```bash
cd C:\GITHUB\golf-handicap-calculator
sam build
```

### Step 3: Deploy

```bash
sam deploy --guided
```

Answer the prompts:
- Stack Name: `golf-handicap-calculator`
- AWS Region: `us-east-1` (or your preferred region)
- Parameter WeatherApiKey: `your_openweathermap_api_key`
- Confirm changes: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Allow function URL public access: `Y`
- Save arguments: `Y`

### Step 4: Get your endpoint URL

After deployment, note the `FunctionUrl` in the outputs. This is what you'll use in your iOS Shortcut.

## Option 2: Manual Lambda Deployment

### Step 1: Package dependencies

```bash
cd C:\GITHUB\golf-handicap-calculator
pip install -r requirements.txt -t package/
cp *.py package/
cd package
```

On Windows PowerShell:
```powershell
Compress-Archive -Path * -DestinationPath ../lambda_function.zip -Force
cd ..
```

### Step 2: Create S3 Bucket (via AWS Console)

1. Go to AWS S3 Console
2. Click "Create bucket"
3. Name: `golf-handicaps-YOUR-ACCOUNT-ID`
4. Region: Same as Lambda
5. Keep default settings
6. Create bucket

### Step 3: Create Lambda Function (via AWS Console)

1. Go to AWS Lambda Console
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `GolfHandicapCalculator`
5. Runtime: Python 3.11
6. Click "Create function"

### Step 4: Upload code

1. In the Lambda function page, go to "Code" tab
2. Click "Upload from" → ".zip file"
3. Upload `lambda_function.zip`
4. Click "Save"

### Step 5: Configure environment variables

1. Go to "Configuration" → "Environment variables"
2. Add:
   - `S3_BUCKET`: Your bucket name
   - `WEATHER_API_KEY`: Your OpenWeatherMap API key

### Step 6: Add S3 permissions

1. Go to "Configuration" → "Permissions"
2. Click on the execution role
3. Add inline policy with S3 full access to your bucket

### Step 7: Create Function URL

1. Go to "Configuration" → "Function URL"
2. Click "Create function URL"
3. Auth type: NONE
4. Configure CORS: Allow all origins
5. Save
6. Copy the Function URL

## Testing

### Test locally first:

```bash
python test_local.py
```

### Test Lambda:

Use the AWS Lambda console "Test" feature with this event:

```json
{
  "scorecard_url": "https://www.tagheuergolf.com/rounds/68C2EE35-519C-4947-B73B-F750C4B3C090"
}
```

Or use curl:

```bash
curl -X POST https://YOUR-FUNCTION-URL \
  -H "Content-Type: application/json" \
  -d '{"scorecard_url": "https://www.tagheuergolf.com/rounds/YOUR-ROUND-ID"}'
```

## Troubleshooting

### Lambda timeout
- Increase timeout in Configuration → General configuration → Timeout (set to 60 seconds)

### Memory issues
- Increase memory in Configuration → General configuration → Memory (set to 512 MB or more)

### Can't access S3
- Check IAM role has S3 permissions
- Verify bucket name in environment variable

### Weather API not working
- Verify API key is correct
- Check you haven't exceeded free tier limits (1000 calls/day)

## Costs

- **Lambda**: Free tier includes 1M requests/month (you'll use ~10/month)
- **S3**: ~$0.023/GB/month (Excel file is <1MB)
- **Data transfer**: Negligible
- **Total**: Essentially **FREE**
