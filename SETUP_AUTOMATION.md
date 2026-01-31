# Automatic Weekly Google Sheets Update Setup

This guide will help you set up automatic weekly scraping that updates your Google Sheet without any manual work.

## Step 1: Create Google Service Account (5 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project called "Opsera Scraper"
3. Enable these APIs:
   - Google Sheets API
   - Google Drive API
4. Create Service Account:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **Service Account**
   - Name: `opsera-scraper`
   - Click **Create and Continue** → **Done**
5. Create JSON Key:
   - Click on the service account
   - Go to **Keys** tab
   - **Add Key** → **Create new key** → **JSON**
   - Save the downloaded file as `credentials.json`

## Step 2: Create & Share Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet named: **Opsera Press Releases**
3. Open `credentials.json` and find the `client_email` field
4. Share the spreadsheet with that email (Editor access)

## Step 3: Test Locally First

```bash
cd /Users/aryagoyal/opsera-press-scraper
mv /path/to/downloaded/credentials.json .
python3 scraper.py
```

Check your Google Sheet - it should now have 35 press releases sorted by date!

## Step 4: Set Up GitHub for Automatic Weekly Runs

### 4.1 Create GitHub Repository

```bash
cd /Users/aryagoyal/opsera-press-scraper
git init
git add .
git commit -m "Initial commit: Opsera Press Release Scraper"
```

Then create a new repo on GitHub and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/opsera-press-scraper.git
git branch -M main
git push -u origin main
```

### 4.2 Add Secrets to GitHub

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

   | Secret Name | Value |
   |-------------|-------|
   | `GOOGLE_CREDENTIALS` | Paste the ENTIRE contents of `credentials.json` |
   | `SHEET_NAME` | `Opsera Press Releases` |

### 4.3 Enable GitHub Actions

1. Go to your repo → **Actions** tab
2. Click **I understand my workflows, go ahead and enable them**
3. You should see "Scrape Opsera Press Releases" workflow

### 4.4 Test the Workflow

1. Go to **Actions** → **Scrape Opsera Press Releases**
2. Click **Run workflow** → **Run workflow**
3. Wait for it to complete (takes ~3-5 minutes)
4. Check your Google Sheet for updates!

## How It Works

- **Schedule**: Runs automatically every Monday at 9 AM UTC
- **Sorting**: Press releases are sorted by date (newest first)
- **New Entries**: New press releases are highlighted in yellow
- **No Duplicates**: Only adds new press releases, skips existing ones

## Manual Run

You can trigger a manual run anytime:
1. Go to GitHub → Actions → Scrape Opsera Press Releases
2. Click "Run workflow"

## Changing the Schedule

Edit `.github/workflows/scrape.yml` and modify the cron expression:

```yaml
schedule:
  - cron: '0 9 * * 1'  # Current: Monday 9 AM UTC
```

Common schedules:
- `'0 9 * * 1'` - Every Monday at 9 AM UTC
- `'0 9 * * *'` - Every day at 9 AM UTC
- `'0 9 * * 0'` - Every Sunday at 9 AM UTC
- `'0 9 1 * *'` - First day of every month at 9 AM UTC

## Troubleshooting

### "Credentials not found"
Make sure `GOOGLE_CREDENTIALS` secret contains the full JSON content (not just the path).

### "Permission denied" on Google Sheets
Share the sheet with the service account email from `credentials.json`.

### Workflow fails
Check the Actions logs for detailed error messages.

## Files

```
opsera-press-scraper/
├── scraper.py              # Main scraper
├── test_scraper.py         # Test without Google Sheets
├── app.py                  # Web frontend
├── requirements.txt        # Dependencies
├── credentials.json        # Your Google credentials (don't commit!)
├── .gitignore             # Ignores credentials.json
└── .github/
    └── workflows/
        └── scrape.yml      # GitHub Actions workflow
```
