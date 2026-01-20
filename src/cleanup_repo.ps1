# Cleanup Script - Remove temporary and test files

Write-Host "Repository Cleanup Script" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Patterns to delete
$patterns = @(
    'test_*.py', 'debug_*.py', 'analyze_*.py', 'inspect_*.py',
    'verify_*.py', 'check_*.py', 'process_*.py', 'load_*.py',
    '*.html', '*.zip', '*_output.txt', 'summary_*.txt',
    '*_rounds_2025*.txt', 'andy_rounds*.txt', 'bruce_rounds*.txt',
    '*.json', '*.xlsx', '*.log',
    'add_*.py', 'update_*.py', 'delete_*.py', 'rename_*.py',
    'fix_*.py', 'save_*.py', 'show_*.py', 'mock_*.py',
    'SESSION_*.md', 'CLEANUP_*.txt', '*.txt'
)

# Must keep these
$mustKeep = @(
    'requirements.txt', 'requirements-aws.txt',
    'lambda_function.py', 'handicap.py', 'golf_system.py',
    'scraper.py', 'weather.py', 'stats_reporter.py',
    'excel_handler.py', 'whatsapp_message.py',
    'lambda_year_end_report.py', 'generate_year_end_report.py',
    'create_ios_shortcut.py', 'setup_function_url.py',
    'upload_lambda.py', 'update_lambda_with_openai.py',
    'config.json.example', 'template.yaml', 'trust-policy.json',
    'load_credentials.py', 'cleanup_repo.ps1'
)

# Get files to delete
$toDelete = @()
foreach ($pattern in $patterns) {
    Get-ChildItem -File -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object {
        if ($mustKeep -notcontains $_.Name -and 
            $_.Name -notlike '*_GUIDE.md' -and 
            $_.Name -notlike 'README.md' -and
            $_.Name -notlike 'LICENSE' -and
            $_.Name -notlike 'START_HERE.md' -and
            $_.Name -notlike '*.shortcut') {
            $toDelete += $_
        }
    }
}

$toDelete = $toDelete | Select-Object -Unique

Write-Host "`nFound $($toDelete.Count) files to delete`n"

$toDelete | Select-Object -First 30 | ForEach-Object {
    Write-Host "  - $($_.Name)" -ForegroundColor Gray
}

if ($toDelete.Count -gt 30) {
    Write-Host "  ... and $($toDelete.Count - 30) more"
}

$confirm = Read-Host "`nDelete these files? (yes/no)"

if ($confirm -eq 'yes') {
    $deleted = 0
    foreach ($file in $toDelete) {
        Remove-Item $file.FullName -Force
        $deleted++
    }
    Write-Host "`nDeleted $deleted files!" -ForegroundColor Green
    Write-Host "`nNext: git add -A; git commit -m 'Clean up repo'; git push"
} else {
    Write-Host "`nCancelled" -ForegroundColor Yellow
}
