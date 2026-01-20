# Clean Git History - REQUIRED before making repo public

**WARNING: This rewrites Git history. Only do this if you're the only user of this repo.**

## Option 1: Using git-filter-repo (Recommended)

### Install:
```powershell
pip install git-filter-repo
```

### Remove the compromised file from all history:
```powershell
git filter-repo --path test_openai.py --invert-paths --force
```

### Re-add the cleaned version and push:
```powershell
git add test_openai.py
git commit -m "Add test_openai.py without hardcoded keys"
git push --force
```

## Option 2: Using BFG Repo-Cleaner (Alternative)

### Download BFG:
https://rtyley.github.io/bfg-repo-cleaner/

### Create a file with strings to replace:
Create `passwords.txt` with:
```
AKIA4M3PLP5LPZKHZI7L
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
```

### Run BFG:
```powershell
java -jar bfg.jar --replace-text passwords.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

## After cleaning:

1. Verify credentials are gone:
```powershell
git log --all -S "AKIA4M3PLP5LPZKHZI7L"
```
(Should return no results)

2. Then you can make the repo public safely

## IMPORTANT: 
The old leaked credentials are ALREADY compromised and disabled. This cleanup is just to prevent them from being visible in your public repo history.
