Write-Host "Deploying Year-End Report Lambda..." -ForegroundColor Green

# Create package directory
if (Test-Path package) { Remove-Item -Recurse -Force package }
New-Item -ItemType Directory -Force -Path package | Out-Null

# Install dependencies
Write-Host "Installing dependencies..."
pip install --target ./package --platform manylinux2014_x86_64 --only-binary=:all: openai boto3 -q

# Copy Lambda function
Copy-Item lambda_year_end_report.py package/

# Create zip
Write-Host "Creating deployment package..."
cd package
Compress-Archive -Path * -DestinationPath ../year-end-report.zip -Force
cd ..

# Deploy to Lambda
Write-Host "Uploading to AWS Lambda..."
aws lambda update-function-code `
    --function-name golf-year-end-report `
    --zip-file fileb://year-end-report.zip `
    --region ap-southeast-2

# Set environment variable
Write-Host "Setting OpenAI API key..."
aws lambda update-function-configuration `
    --function-name golf-year-end-report `
    --environment "Variables={OPENAI_API_KEY=REMOVED_OPENAI_KEY}" `
    --region ap-southeast-2

# Get Function URL
Write-Host "`nFunction URL:" -ForegroundColor Green
aws lambda get-function-url-config --function-name golf-year-end-report --region ap-southeast-2 --query 'FunctionUrl' --output text

Write-Host "`nDone! Test with:" -ForegroundColor Green
Write-Host "curl https://YOUR-URL.lambda-url.ap-southeast-2.on.aws/?year=2025"
