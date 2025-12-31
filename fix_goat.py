with open('lambda_function.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the broken emoji character with GOAT emoji
content = content.replace('*\ufffd {current_year} LEADERBOARD:*', '*🐐 {current_year} LEADERBOARD:*')

with open('lambda_function.py', 'w', encoding='utf-8') as f:
    f.write(content)
    
print('✅ Fixed GOAT emoji')
