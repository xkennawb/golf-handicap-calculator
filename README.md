# Golf Handicap Calculator

Automated golf handicap tracking system using World Handicap System (WHS).

---

## 🚀 Quick Start

**New to this project? Start here:**
1. Follow [Installation](#installation) below to set up AWS and deploy
2. Read [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment options
3. See [IOS_SHORTCUTS.md](IOS_SHORTCUTS.md) for iOS Shortcut setup
4. Read [START_HERE.md](START_HERE.md) for development overview

---

## Installation

### Prerequisites

- **AWS Account** - Sign up at https://aws.amazon.com
- **Python 3.11+** - Download from https://www.python.org
- **Git** - Download from https://git-scm.com

### Step 1: Clone Repository

```bash
git clone https://github.com/xkennawb/golf-handicap-calculator.git
cd golf-handicap-calculator
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure AWS Credentials

Create a `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
OPENAI_API_KEY=sk-your-key-here  # Optional, for AI commentary
```

**⚠️ Security**: The `.env` file is gitignored. Never commit credentials to Git.

### Step 4: Deploy to AWS Lambda

```powershell
# Build Lambda package with Linux-compatible binaries
.\build_lambda_package.ps1

# Deploy to AWS
python upload_lambda.py
```

The script will create:
- Lambda function: `golf-handicap-tracker`
- DynamoDB table: `golf-rounds`
- Function URL for iOS Shortcut access

### Step 5: Set Up iOS Shortcut

See [IOS_SHORTCUTS.md](IOS_SHORTCUTS.md) for complete iOS Shortcut configuration.

### Optional: Enable AI Commentary

1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Set monthly budget limit to $1 (prevents overcharges)
3. Add to Lambda environment variable `OPENAI_API_KEY`

See [DEPLOYMENT.md](DEPLOYMENT.md#optional-ai-commentary-setup) for detailed instructions.

---

## Features

- 🏌️ Scrapes Tag Heuer Golf scorecards from URL
- 🌤️ Fetches weather data for course location and date (Open-Meteo API, free)
- 🤖 AI-powered commentary with OpenAI (witty banter about each round)
- 📊 Calculates 9-hole handicaps per WHS Australia (World Handicap System)
- 🎯 Tracks Stableford and Gross scores for each round
- 📈 Season statistics for each player:
  - Average Stableford score
  - Handicap index and course handicap
  - Week-over-week handicap changes
  - Personal best scores (Stableford and Gross)
- 🏆 Season leaderboard with rankings
- 📱 iOS Shortcut integration for easy submission
- 💬 WhatsApp-formatted summaries (mobile-optimized)
- 🗄️ DynamoDB storage (AWS)
- 📅 **Year-End Reports** (NEW Jan 2026):
  - Comprehensive season review with AI commentary
  - Quarterly lead change tracking
  - Awards and season highlights
  - WhatsApp-ready format

---

## Architecture

**iPhone → iOS Shortcut → AWS Lambda → DynamoDB → Returns Summary → Share to WhatsApp**

**Weekly Summaries:**
- **Frontend**: iOS Shortcuts (POST scorecard URL)
- **Backend**: AWS Lambda `golf-handicap-tracker` (Python 3.13)
- **Database**: DynamoDB table `golf-rounds`
- **AI**: OpenAI GPT-4o-mini
- **Weather**: Open-Meteo API (free, no key needed)

**Year-End Reports:**
- **Lambda**: `golf-year-end-report` (Python 3.13)
- **URL**: `https://fgx264nnprn7d4havgkn5mlcim0zttjt.lambda-url.ap-southeast-2.on.aws/`
- **AI**: Enhanced commentary with quarterly analysis
- **Output**: WhatsApp-formatted season review

---

## Build & Deploy

### Quick Deploy
```powershell
.\build_lambda_package.ps1
python upload_lambda.py
```

**Important**: Build script uses `--platform manylinux2014_x86_64` to get Linux-compatible binaries for AWS Lambda.

### Local Testing

Test changes locally before deploying:

```powershell
# View current summary
chcp 65001 >$null; python display_summary.py

# Test specific round
python check_db.py
```

---

## Project Structure

### Root Directory
- `build_lambda_package.ps1` - Build script for Lambda deployment (with Linux binaries)
- `upload_lambda.py` - Upload script for AWS Lambda
- `README.md`, `LICENSE` - Documentation and licensing

### src/ Directory (Source Code)
- `src/lambda_function.py` - AWS Lambda entry point (1575 lines, includes all features)
- `src/handicap.py` - Australian WHS handicap calculator with Stableford
- `src/weather.py`, `src/golf_system.py` - Supporting modules

## WhatsApp Summary Format

**Optimized for mobile viewing** (as of Dec 31, 2025):

1. **TODAY'S RESULTS** - Compact tables with rankings
2. **DECEMBER BOARD** - Monthly leaderboard with season emojis and trends (📈📉➡️)
3. **🐐 LEADERBOARD** - Season standings with qualified players only (10+ rounds after June)
4. **⚠️ Not Qualified** - Separate section for <10 rounds (after June only)
5. **PLAYER STATS** - Alphabetical by first name, country flags, emoji bullets (🎯📊🏆📈)
6. **AI COMMENTARY** - Weather + banter + handicap changes + predictions

**Recent Changes**:
- Changed "2025 LEADERBOARD" to "🐐 LEADERBOARD" (no year, GOAT emoji)
- Split qualified (10+ rounds) and non-qualified (<10 rounds) players after June
- Player stats now sorted alphabetically by first name
- Added country flags before player names (🏴󠁧󠁢󠁥󠁮󠁧󠁿🇦🇺🇳🇿)
- Removed Performance Trends and FUN STATS for cleaner mobile display
- Standardized all table underlines to 25 characters
- AI mentions significant handicap changes (>0.05)
- Year-over-year comparison disabled (can be re-enabled later)

## License

GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
