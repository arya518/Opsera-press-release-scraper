# Opsera Press Release Scraper

Automatically scrapes press releases from opsera.ai and populates a Google Sheet with the data.

## Features

- Scrapes press releases from opsera.ai/blog
- Extracts title, date, link, category, and description
- Automatically populates a Google Sheet
- Detects and only adds new press releases (avoids duplicates)
- Can be scheduled to run automatically

## Setup Instructions

### Step 1: Install Python Dependencies

```bash
cd opsera-press-scraper
pip install -r requirements.txt
```

### Step 2: Set Up Google Sheets API

#### 2.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Name it something like "Opsera Scraper"

#### 2.2 Enable Google Sheets API

1. In your project, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click "Enable"
4. Also search for and enable "Google Drive API"

#### 2.3 Create Service Account Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Enter a name (e.g., "opsera-scraper-bot")
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

#### 2.4 Download Credentials JSON

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. Click "Create" - this will download a JSON file
6. **Rename this file to `credentials.json`**
7. **Move it to the `opsera-press-scraper` folder**

#### 2.5 Share Google Sheet with Service Account

1. Open the downloaded `credentials.json` file
2. Find the `client_email` field (looks like: `something@project-id.iam.gserviceaccount.com`)
3. Copy this email address
4. Create a new Google Sheet or open an existing one
5. Click "Share" button
6. Paste the service account email
7. Give it "Editor" permissions
8. Click "Send"

**OR** let the script create a new sheet automatically (you'll need to find it in your Google Drive and it will be owned by the service account initially).

### Step 3: Configure the Scraper

Edit [scraper.py](scraper.py) if you want to change settings:

```python
GOOGLE_CREDS_FILE = 'credentials.json'  # Path to credentials
SHEET_NAME = 'Opsera Press Releases'    # Name of your Google Sheet
```

### Step 4: Run the Scraper

```bash
python scraper.py
```

The script will:
1. Scrape all press releases from opsera.ai
2. Create or open the Google Sheet
3. Add new press releases (avoiding duplicates)
4. Format the sheet with headers

## Scheduling Automation

### Option 1: macOS/Linux (cron)

1. Open terminal and type:
```bash
crontab -e
```

2. Add this line to run daily at 9 AM:
```bash
0 9 * * * cd /Users/aryagoyal/opsera-press-scraper && /usr/bin/python3 scraper.py >> scraper.log 2>&1
```

3. Adjust the path to match your setup

### Option 2: Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Name it "Opsera Scraper"
4. Set trigger (e.g., Daily at 9 AM)
5. Action: Start a program
6. Program: `python`
7. Arguments: `scraper.py`
8. Start in: `C:\path\to\opsera-press-scraper`

### Option 3: GitHub Actions (Cloud-based)

Create `.github/workflows/scraper.yml`:

```yaml
name: Scrape Opsera Press Releases

on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run scraper
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
        run: |
          echo "$GOOGLE_CREDENTIALS" > credentials.json
          python scraper.py
```

Then add your `credentials.json` content as a repository secret named `GOOGLE_CREDENTIALS`.

## Google Sheet Structure

The scraper creates a sheet with these columns:

| Title | Date | Link | Category | Description | Scraped On |
|-------|------|------|----------|-------------|------------|
| Press Release Title | 2024-01-15 | https://... | News | Brief description... | 2024-01-29 10:30:00 |

## Troubleshooting

### "Credentials file not found"
Make sure `credentials.json` is in the same folder as `scraper.py`.

### "Permission denied" on Google Sheets
Make sure you've shared the Google Sheet with the service account email from `credentials.json`.

### Chrome/ChromeDriver issues
The script auto-downloads ChromeDriver. If you have issues:
- Make sure Chrome browser is installed
- Try running with `--headless=false` for debugging

### No press releases found
The website structure may have changed. You might need to update the CSS selectors in `_find_articles()` method.

## Customization

### Modify what data is extracted

Edit the `_extract_article_data()` method in [scraper.py](scraper.py) to add or remove fields.

### Filter specific press releases

Edit the `_is_press_release()` method to add filtering logic (e.g., only include posts with "press release" in the title).

### Change scraping frequency

Modify the cron schedule or Task Scheduler frequency.

## Advanced: Debugging Mode

To see what the scraper is doing in real-time, edit [scraper.py](scraper.py) and change:

```python
chrome_options.add_argument("--headless")  # Remove this line
```

This will open a visible Chrome window during scraping.

## Files

- `scraper.py` - Main scraper script
- `requirements.txt` - Python dependencies
- `credentials.json` - Google API credentials (you create this)
- `README.md` - This file

## Support

If the scraper stops working, it's likely because:
1. The opsera.ai website structure changed
2. Google API credentials expired or were revoked
3. Network/firewall issues

For website structure changes, you may need to update the CSS selectors in the code.
