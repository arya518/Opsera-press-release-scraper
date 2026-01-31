#!/usr/bin/env python3
"""
Opsera Press Release Scraper
Scrapes press releases from opsera.ai and populates a Google Sheet
"""

import time
import re
import os
import stat
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials


class OpseraPressReleaseScraper:
    def __init__(self, google_creds_file, sheet_name):
        """
        Initialize the scraper

        Args:
            google_creds_file: Path to Google Service Account JSON credentials
            sheet_name: Name of the Google Sheet to populate
        """
        self.google_creds_file = google_creds_file
        self.sheet_name = sheet_name
        self.base_url = "https://www.opsera.ai/newsroom"
        self.press_releases = []
        self.seen_links = set()

    def setup_driver(self):
        """Set up Selenium WebDriver with Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        driver_path = ChromeDriverManager().install()

        # Fix for Mac ARM: find correct chromedriver binary
        if 'THIRD_PARTY' in driver_path or 'LICENSE' in driver_path or not driver_path.endswith('chromedriver'):
            driver_dir = os.path.dirname(driver_path)
            for root, dirs, files in os.walk(os.path.dirname(driver_dir)):
                if 'chromedriver' in files:
                    potential = os.path.join(root, 'chromedriver')
                    if 'LICENSE' not in potential and 'NOTICE' not in potential:
                        driver_path = potential
                        break

        # Ensure executable
        if os.path.isfile(driver_path):
            os.chmod(driver_path, os.stat(driver_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        print(f"Using ChromeDriver at: {driver_path}")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def scrape_press_releases(self):
        """Scrape all press releases from the website"""
        print(f"Starting scrape of {self.base_url}...")
        driver = self.setup_driver()

        try:
            # Step 1: Get list of all press release links from newsroom (with pagination)
            # Use the Press Release filter - NOTE: uses hash (#) not query param (?)
            filter_url = f"{self.base_url}/#type=press-release"
            driver.get(filter_url)
            print("Waiting for page to load...")
            time.sleep(5)

            newsroom_links = []

            # Handle pagination - 35 press releases = 4 pages (9+9+9+8)
            # Need to click pagination buttons to navigate
            max_pages = 5  # Safety limit
            for page_num in range(1, max_pages + 1):
                print(f"  Scanning page {page_num}...")

                if page_num > 1:
                    # Click on the page number link to navigate
                    try:
                        # Find and click the pagination link for this page
                        page_link = driver.find_element(By.CSS_SELECTOR, f"a[href='#page={page_num}']")
                        driver.execute_script("arguments[0].click();", page_link)
                        time.sleep(3)
                    except Exception as e:
                        print(f"    Could not find page {page_num} link, trying JS navigation...")
                        # Fallback: try updating hash directly and triggering hashchange
                        driver.execute_script(f"""
                            window.location.hash = 'type=press-release&page={page_num}';
                            window.dispatchEvent(new HashChangeEvent('hashchange'));
                        """)
                        time.sleep(3)

                # Scroll to ensure content loads
                driver.execute_script("window.scrollTo(0, 800);")
                time.sleep(2)

                # Extract links from current page
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # Get all newsroom article links, deduplicated
                page_links = set()
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Filter for newsroom article links
                    if '/newsroom/' not in href:
                        continue
                    # Normalize URL
                    if not href.startswith('http'):
                        href = 'https://www.opsera.ai' + href
                    # Skip the main newsroom page
                    if href.rstrip('/') in ['https://opsera.ai/newsroom', 'https://www.opsera.ai/newsroom']:
                        continue
                    # Must have a slug (actual article, not just /newsroom/)
                    parts = href.rstrip('/').split('/')
                    if len(parts) > 4 and parts[-1]:  # Has slug after /newsroom/
                        page_links.add(href)

                # Filter out already seen links
                new_links = [l for l in page_links if l not in self.seen_links]

                # Check if we found any new links
                if not new_links and page_num > 1:
                    print(f"    No new links on page {page_num}, stopping pagination")
                    break

                # Add new links
                for link in new_links:
                    self.seen_links.add(link)
                    newsroom_links.append(link)

                print(f"    Found {len(new_links)} new links (total: {len(newsroom_links)})")

            print(f"Found {len(newsroom_links)} total press release links")

            # Step 2: Visit each press release page to get details
            for i, link in enumerate(newsroom_links, 1):
                print(f"  Scraping {i}/{len(newsroom_links)}: {link[:60]}...")
                try:
                    driver.get(link)
                    time.sleep(2)

                    page_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    press_release = self._extract_press_release_details(page_soup, link)

                    if press_release:
                        self.press_releases.append(press_release)
                except Exception as e:
                    print(f"    Error scraping {link}: {e}")

            print(f"Extracted {len(self.press_releases)} press releases")

        except Exception as e:
            print(f"Error during scraping: {e}")
            raise
        finally:
            driver.quit()

        return self.press_releases

    def _extract_press_release_details(self, soup, url):
        """Extract details from a single press release page"""
        data = {'link': url}

        # Extract title - try multiple selectors
        title_selectors = ['h1', 'h2.entry-title', '.entry-title', 'article h1', 'article h2']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                data['title'] = title_elem.get_text(strip=True)
                break

        if 'title' not in data:
            # Try to extract from URL
            slug = url.rstrip('/').split('/')[-1]
            data['title'] = slug.replace('-', ' ').title()

        # Extract date - look for common patterns
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            r'\d{4}-\d{2}-\d{2}'
        ]

        page_text = soup.get_text()
        data['date'] = ''

        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                data['date'] = self._parse_date(match.group())
                break

        # Also check for time element
        time_elem = soup.find('time')
        if time_elem:
            if time_elem.get('datetime'):
                data['date'] = self._parse_date(time_elem['datetime'])
            elif not data['date']:
                data['date'] = self._parse_date(time_elem.get_text(strip=True))

        # Extract description/first paragraph
        desc_selectors = ['article p', '.entry-content p', 'main p', '.content p']
        for selector in desc_selectors:
            desc_elems = soup.select(selector)
            for desc_elem in desc_elems:
                text = desc_elem.get_text(strip=True)
                if len(text) > 50:  # Skip short paragraphs
                    data['description'] = text[:300] + '...' if len(text) > 300 else text
                    break
            if 'description' in data:
                break

        if 'description' not in data:
            data['description'] = ''

        # Extract category/tags
        data['category'] = 'Press Release'

        return data

    def _parse_date(self, date_string):
        """Parse date string into standardized format"""
        if not date_string:
            return ''

        date_string = date_string.strip()

        # Common date formats
        formats = [
            '%B %d, %Y',      # January 15, 2025
            '%B %d %Y',       # January 15 2025
            '%d %B %Y',       # 15 January 2025
            '%Y-%m-%d',       # 2025-01-15
            '%Y-%m-%dT%H:%M:%S',  # ISO format
            '%Y-%m-%dT%H:%M:%SZ',
            '%b %d, %Y',      # Jan 15, 2025
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return date_string

    def connect_to_google_sheet(self):
        """Connect to Google Sheets using service account credentials"""
        print("Connecting to Google Sheets...")

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = Credentials.from_service_account_file(
            self.google_creds_file,
            scopes=scopes
        )

        client = gspread.authorize(creds)

        try:
            # Try to open by key if it looks like a sheet ID
            if len(self.sheet_name) > 30 and '/' not in self.sheet_name:
                sheet = client.open_by_key(self.sheet_name)
                print(f"Opened sheet by key: {self.sheet_name[:20]}...")
            else:
                sheet = client.open(self.sheet_name)
                print(f"Opened existing sheet: {self.sheet_name}")
        except gspread.SpreadsheetNotFound:
            sheet = client.create(self.sheet_name)
            print(f"Created new sheet: {self.sheet_name}")

        return sheet

    def populate_google_sheet(self, update_existing=False):
        """Populate Google Sheet with scraped data, sorted by date descending, new entries highlighted"""
        if not self.press_releases:
            print("No press releases to populate")
            return 0

        sheet = self.connect_to_google_sheet()
        worksheet = sheet.get_worksheet(0)

        headers = ['Title', 'Date', 'Link', 'Category', 'Description', 'Scraped On', 'Is New']

        # Get existing data
        existing_data = worksheet.get_all_values()
        existing_links = set()
        if existing_data and len(existing_data) > 1:
            # Links are in column 3 (index 2)
            for row in existing_data[1:]:
                if len(row) > 2:
                    existing_links.add(row[2])

        # Prepare all rows with new flag
        all_rows = []
        new_count = 0
        scrape_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for pr in self.press_releases:
            is_new = pr['link'] not in existing_links
            if is_new:
                new_count += 1

            # Parse date for sorting
            date_str = pr.get('date', '')
            if date_str:
                # Extract just the date part (YYYY-MM-DD)
                date_for_sort = date_str[:10] if len(date_str) >= 10 else date_str
            else:
                date_for_sort = '1900-01-01'  # Put items without dates at the end

            row = {
                'title': pr.get('title', ''),
                'date': date_str[:10] if date_str else '',  # Clean date format
                'link': pr.get('link', ''),
                'category': pr.get('category', ''),
                'description': pr.get('description', ''),
                'scraped_on': scrape_time,
                'is_new': 'NEW' if is_new else '',
                'date_for_sort': date_for_sort
            }
            all_rows.append(row)

        # Sort by date descending (newest first)
        all_rows.sort(key=lambda x: x['date_for_sort'], reverse=True)

        # Clear sheet and rewrite with sorted data
        print(f"Writing {len(all_rows)} press releases to sheet (sorted by date, newest first)...")
        worksheet.clear()

        # Write headers
        worksheet.append_row(headers)

        # Write all rows
        rows_to_write = []
        new_row_indices = []  # Track which rows are new (for highlighting)

        for i, row in enumerate(all_rows):
            row_data = [
                row['title'],
                row['date'],
                row['link'],
                row['category'],
                row['description'],
                row['scraped_on'],
                row['is_new']
            ]
            rows_to_write.append(row_data)
            if row['is_new'] == 'NEW':
                new_row_indices.append(i + 2)  # +2 because row 1 is headers, rows are 1-indexed

        if rows_to_write:
            worksheet.append_rows(rows_to_write)

        # Format the sheet
        self._format_sheet(worksheet, new_row_indices)

        print(f"Successfully updated Google Sheet!")
        print(f"  - Total press releases: {len(all_rows)}")
        print(f"  - New entries: {new_count}")

        return new_count

    def _format_sheet(self, worksheet, new_row_indices=None):
        """Apply formatting to the worksheet - headers blue, new rows yellow"""
        try:
            # Format headers - blue background, white bold text
            worksheet.format('A1:G1', {
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                'backgroundColor': {'red': 0.23, 'green': 0.08, 'blue': 0.44}  # Opsera purple
            })

            # Highlight new rows in yellow
            if new_row_indices:
                print(f"  Highlighting {len(new_row_indices)} new entries in yellow...")
                for row_idx in new_row_indices:
                    try:
                        worksheet.format(f'A{row_idx}:G{row_idx}', {
                            'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.6}  # Yellow
                        })
                    except Exception as e:
                        print(f"    Warning: Could not highlight row {row_idx}: {e}")

            # Freeze header row
            worksheet.freeze(rows=1)

            # Auto-resize columns
            worksheet.columns_auto_resize(0, 6)

        except Exception as e:
            print(f"Warning: Could not format sheet: {e}")

    def run(self, update_existing=False):
        """Main execution method"""
        print("=" * 60)
        print("Opsera Press Release Scraper")
        print("=" * 60)

        self.scrape_press_releases()

        if self.press_releases:
            count = self.populate_google_sheet(update_existing=update_existing)
            print(f"\nComplete! Added {count} press releases to Google Sheet")
        else:
            print("\nNo press releases found")


def main():
    """Main entry point"""
    import sys
    import json

    # Support both file-based and environment variable credentials
    GOOGLE_CREDS_FILE = 'credentials.json'
    SHEET_NAME = os.environ.get('SHEET_NAME', '1bkO21snevwTrHFtZidqetV7vSrt1rhp5qFc8EVxiK7E')

    # Check for credentials from environment variable (for GitHub Actions)
    if os.environ.get('GOOGLE_CREDENTIALS'):
        print("Using credentials from environment variable...")
        creds_data = os.environ.get('GOOGLE_CREDENTIALS')
        with open(GOOGLE_CREDS_FILE, 'w') as f:
            f.write(creds_data)
    elif not os.path.exists(GOOGLE_CREDS_FILE):
        print(f"ERROR: Credentials file '{GOOGLE_CREDS_FILE}' not found!")
        print("Please follow the setup instructions in README.md")
        print("Or set GOOGLE_CREDENTIALS environment variable")
        sys.exit(1)

    scraper = OpseraPressReleaseScraper(GOOGLE_CREDS_FILE, SHEET_NAME)
    scraper.run(update_existing=False)


if __name__ == '__main__':
    main()
