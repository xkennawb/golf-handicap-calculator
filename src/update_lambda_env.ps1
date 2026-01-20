# Update Lambda Environment Variable for OpenAI API Key
# Usage: .\update_lambda_env.ps1 "your-new-api-key"

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey
)

$FunctionName = "golf-handicap-ios-shortcut"

Write-Host "Updating Lambda function: $FunctionName" -ForegroundColor Cyan

# Get current environment variables
try {
    $config = aws lambda get-function-configuration --function-name $FunctionName --no-verify-ssl | ConvertFrom-Json
    
    if ($config.Environment.Variables) {
        $envVars = $config.Environment.Variables | ConvertTo-Json -Compress
        Write-Host "Current environment variables retrieved" -ForegroundColor Green
    } else {
        $envVars = "{}"
    }
    
    # Parse and update
    $envObj = $envVars | ConvertFrom-Json
    $envObj | Add-Member -NotePropertyName "OPENAI_API_KEY" -NotePropertyValue $ApiKey -Force
    
    # Convert to AWS CLI format
    $envString = ($envObj.PSObject.Properties | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ","
    
    # Update Lambda
    aws lambda update-function-configuration `
        --function-name $FunctionName `
        --environment "Variables={$envString}" `
        --no-verify-ssl | Out-Null
    
    Write-Host "`n✓ Successfully updated OPENAI_API_KEY" -ForegroundColor Green
    Write-Host "  Key starts with: $($ApiKey.Substring(0, 20))..." -ForegroundColor Gray
    
} catch {
    Write-Host "`n✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nManual update via AWS Console:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://ap-southeast-2.console.aws.amazon.com/lambda/home?region=ap-southeast-2#/functions/$FunctionName" -ForegroundColor Gray
    Write-Host "2. Click 'Configuration' tab" -ForegroundColor Gray
    Write-Host "3. Click 'Environment variables'" -ForegroundColor Gray
    Write-Host "4. Click 'Edit'" -ForegroundColor Gray
    Write-Host "5. Update OPENAI_API_KEY with your new key" -ForegroundColor Gray
    Write-Host "6. Click 'Save'" -ForegroundColor Gray
}
