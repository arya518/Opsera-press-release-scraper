# Quick Start Guide

Follow these steps to get your scraper running in 10 minutes!

## Step-by-Step Setup

### 1. Install Dependencies (2 minutes)

```bash
cd opsera-press-scraper
pip install -r requirements.txt
```

### 2. Test the Scraper (1 minute)

Before setting up Google Sheets, verify the scraper works:

```bash
python test_scraper.py
```

This will scrape opsera.ai and save results to `scraped_data.json` without needing Google credentials.

**If this works**, proceed to Step 3. **If it fails**, the website structure may have changed.

### 3. Set Up Google Sheets (5 minutes)

#### Quick Method:

1. Go to: https://console.cloud.google.com/
2. Create a new project
3. Enable "Google Sheets API" and "Google Drive API"
4. Create Service Account credentials:
   - Go to: APIs & Services → Credentials → Create Credentials → Service Account
   - Download JSON key file
   - Rename it to `credentials.json`
   - Put it in the `opsera-press-scraper` folder

5. Copy the service account email from `credentials.json`:
   ```bash
   grep client_email credentials.json
   ```

6. Create a new Google Sheet and share it with that email (Editor access)

### 4. Run the Scraper (30 seconds)

```bash
python scraper.py
```

Or use the helper script:

```bash
./run.sh
```

Check your Google Sheet - it should be populated with press releases!

### 5. Schedule It (Optional - 2 minutes)

#### macOS/Linux:
```bash
crontab -e
```

Add this line (runs daily at 9 AM):
```
0 9 * * * cd /Users/aryagoyal/opsera-press-scraper && python3 scraper.py >> scraper.log 2>&1
```

#### Windows:
Use Task Scheduler to run `scraper.py` daily.

## Troubleshooting

### "No press releases found"
1. Run `python test_scraper.py` first
2. Check `scraped_data.json` to see what was scraped
3. The website might have changed - selectors may need updating

### "credentials.json not found"
Make sure the file is in the `opsera-press-scraper` folder.

### "Permission denied" on Google Sheets
Make sure you shared the sheet with the service account email from `credentials.json`.

## What Gets Scraped?

The scraper extracts:
- **Title**: Press release headline
- **Date**: Publication date
- **Link**: URL to full article
- **Category**: Tags/categories
- **Description**: Brief excerpt
- **Scraped On**: When the scraper ran

## Next Steps

- Check your Google Sheet
- Set up scheduling for automatic updates
- Customize the scraper if needed (see README.md)

## Files Created

After setup, you'll have:
- `credentials.json` - Your Google API credentials (keep secret!)
- `scraped_data.json` - Test output (from test_scraper.py)
- `scraper.log` - Logs from scheduled runs

Need more help? See the full [README.md](README.md)
