# Files to Delete - Safe to Remove

## Test Files (50+)
test_*.py
test_*.txt

## Debug Files
debug_*.py
analyze_*.py
inspect_*.py
verify_*.py (except verify important ones)
check_*.py (mostly debugging)

## Old Processing Scripts
process_*.py (all old batch processing)
load_*.py (except load_credentials.py)
extract_*.py
fetch_*.py (except fetch_year_end_report.py)

## Temporary HTML/Output
*.html
temp_*.zip
*_output.txt
summary_*.txt
output.log

## Old Data/Rounds Files
*_rounds_2025*.txt
andy_rounds*.txt
bruce_rounds*.txt
golf_rounds_export*.json
backup_golf_rounds*.json

## Old Excel Files
handicaps*.xlsx
golf_2025_season*.xlsx

## One-off Scripts
add_monavale_*.py
add_weather_key.py
add_auth_token.py
update_andy_*.py
update_fletcher_*.py
rename_steve.py
fix_goat.py
delete_*_round*.py
save_*.py
show_*.py
display_*.py
compare_*.py
find_*.py
mock_*.py

## Old Deployment
lambda_function.zip
lambda-deployment.zip  
year-end-report.zip
temp_lambda.zip
deploy_year_end_lambda.ps1

## Old Documentation
CLEANUP_GIT_HISTORY.txt (keep CLEAN_GIT_HISTORY.md)
SESSION_*.md (old session notes)
rebuild_log.txt

## Helper scripts you created today
create_new_lambda.py
redeploy_with_new_key.py
search_lambda_regions.py
test_credentials.py
update_openai_key.py
check_aws_permissions.py

Would you like me to create a script to delete all these files?
