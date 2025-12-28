# Golf Handicap Calculator

Automated golf handicap tracking system using World Handicap System (WHS).

---

## 🚀 Quick Start

**New to this project? Start here:**
1. Read [START_HERE.md](START_HERE.md) for overview
2. Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for technical details
3. Check session files for recent changes

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
- 💬 WhatsApp-formatted summaries
- 🗄️ DynamoDB storage (AWS)

---

## Architecture

**iPhone → iOS Shortcut → AWS Lambda → DynamoDB → Returns Summary → Share to WhatsApp**

- **Frontend**: iOS Shortcuts (POST scorecard URL)
- **Backend**: AWS Lambda (Python 3.13)
- **Database**: DynamoDB table `golf-rounds`
- **AI**: OpenAI GPT-4o-mini
- **Weather**: Open-Meteo API (free, no key needed)

---

## Build & Deploy

### Quick Deploy
```powershell
.\build_lambda_package.ps1
python upload_lambda.py
```

**Important**: Build script uses `--platform manylinux2014_x86_64` to get Linux-compatible binaries for AWS Lambda.

### Configure Environment Variables

**OpenAI API Key**: Set `OPENAI_API_KEY` in AWS Lambda environment variables for AI commentary.

**Weather**: Uses Open-Meteo API (free, no key required).

**Auth Token**: Set `AUTH_TOKEN` in Lambda environment variables for securing the endpoint.

### Setup iOS Shortcut

See [IOS_SHORTCUT_POST_ROUND.md](IOS_SHORTCUT_POST_ROUND.md) for detailed setup.

## Local Testing

```powershell
chcp 65001 >$null; python display_summary.py
```

## Usage

1. Play your round of golf
2. Get the Tag Heuer scorecard URL
3. Run iOS Shortcut
4. Paste URL
5. View handicap updates
6. Share to WhatsApp group

## Files

- `lambda_function.py` - AWS Lambda entry point (1658 lines, includes all features)
- `handicap.py` - Australian WHS handicap calculator with Stableford
- `weather.py` - Open-Meteo weather API integration
- `excel_handler.py` - Excel spreadsheet management (legacy)
- `stats_reporter.py` - Statistics and leaderboard generator (legacy)
- `build_lambda_package.ps1` - Build script for Lambda deployment
- `upload_lambda.py` - Upload script for AWS Lambda

## License

MIT
