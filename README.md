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
- 📊 Calculates 9-hole handicaps per WHS (World Handicap System)
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

### Manual Build

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `config.json` file:

```json
{
  "weather_api_key": "your_openweathermap_api_key",
  "s3_bucket": "your-s3-bucket-name"
}
```

Get a free API key from: https://openweathermap.org/api

### 3. Deploy to AWS Lambda

```bash
# Package dependencies
pip install -r requirements.txt -t package/
cp *.py package/
cd package
zip -r ../lambda_function.zip .
cd ..

# Upload to AWS Lambda via AWS Console or CLI
```

### 4. Setup iOS Shortcut

See `ios-shortcut-instructions.md` for detailed setup.

## Local Testing

```bash
python test_local.py
```

## Usage

1. Play your round of golf
2. Get the Tag Heuer scorecard URL
3. Run iOS Shortcut
4. Paste URL
5. View handicap updates
6. Share to WhatsApp group

## Files

- `scraper.py` - Tag Heuer scorecard scraper
- `weather.py` - Weather API integration
- `handicap.py` - Australian WHS handicap calculator with Stableford
- `excel_handler.py` - Excel spreadsheet management with year stats
- `stats_reporter.py` - Statistics and leaderboard generator
- `lambda_function.py` - AWS Lambda entry point
- `test_local.py` - Local testing script

## License

MIT
