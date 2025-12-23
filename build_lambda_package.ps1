# Lambda Deployment Package Builder for AWS Lambda
# Builds deployment package with LINUX-compatible binaries
# Always deploys lambda_function.py (the FULL version with AI commentary)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " AWS Lambda Package Builder - Golf Handicap Tracker" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Clean package directory
$packageDir = "lambda_package"
Write-Host "[1/4] Cleaning build directory..." -ForegroundColor Yellow
if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $packageDir | Out-Null
Write-Host "      Done" -ForegroundColor Green

# Install dependencies with LINUX binaries
Write-Host ""
Write-Host "[2/4] Installing dependencies with Linux binaries..." -ForegroundColor Yellow
Write-Host "      Platform: manylinux2014_x86_64, Python: 3.13" -ForegroundColor Gray
pip install requests beautifulsoup4 openai --platform manylinux2014_x86_64 --target $packageDir --only-binary=:all: --python-version 3.13 --quiet
Write-Host "      Done" -ForegroundColor Green

# Copy Lambda function files
Write-Host ""
Write-Host "[3/4] Copying application files..." -ForegroundColor Yellow
Write-Host "      lambda_function.py" -ForegroundColor Gray
Copy-Item lambda_function.py $packageDir\
Write-Host "      handicap.py" -ForegroundColor Gray
Copy-Item handicap.py $packageDir\
Write-Host "      Done" -ForegroundColor Green

# Create zip file
Write-Host ""
Write-Host "[4/4] Creating deployment package..." -ForegroundColor Yellow
if (Test-Path lambda_function.zip) {
    Remove-Item lambda_function.zip
}

Push-Location $packageDir
Compress-Archive -Path * -DestinationPath ..\lambda_function.zip -Force
Pop-Location

$zipSize = (Get-Item lambda_function.zip).Length / 1MB
Write-Host "      lambda_function.zip created" -NoNewline -ForegroundColor Gray
Write-Host " ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Gray

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host " PACKAGE READY FOR DEPLOYMENT" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next step:" -ForegroundColor Cyan
Write-Host "  python upload_lambda.py" -ForegroundColor Yellow
Write-Host ""
