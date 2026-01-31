#!/usr/bin/env python3
"""
Test script for Opsera Press Release Scraper
Tests the scraping functionality without writing to Google Sheets
"""

import json
from scraper import OpseraPressReleaseScraper


class TestScraper(OpseraPressReleaseScraper):
    """Test version that doesn't require Google credentials"""

    def __init__(self):
        self.base_url = "https://www.opsera.ai/newsroom"
        self.press_releases = []
        self.seen_links = set()

    def test_scrape_only(self):
        """Test scraping and display results without Google Sheets"""
        print("=" * 60)
        print("Testing Opsera Press Release Scraper (Dry Run)")
        print("=" * 60)
        print("")

        print("Scraping website...")
        self.scrape_press_releases()

        if self.press_releases:
            print(f"\n✓ Successfully scraped {len(self.press_releases)} press releases!\n")
            print("Scraped data:")
            print("-" * 60)

            for i, pr in enumerate(self.press_releases, 1):
                print(f"\n{i}. {pr.get('title', 'No title')}")
                print(f"   Date: {pr.get('date', 'No date')}")
                print(f"   Link: {pr.get('link', 'No link')}")
                if pr.get('description'):
                    desc = pr['description'][:100] + "..." if len(pr.get('description', '')) > 100 else pr.get('description', '')
                    print(f"   Description: {desc}")

            output_file = 'scraped_data.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.press_releases, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Full data saved to: {output_file}")

        else:
            print("\n✗ No press releases found!")
            print("This might mean:")
            print("  - The website structure has changed")
            print("  - The page failed to load")
            print("  - The selectors need to be updated")

        print("\n" + "=" * 60)
        print("Test complete!")
        print("=" * 60)


def main():
    """Run test scraper"""
    scraper = TestScraper()
    scraper.test_scrape_only()


if __name__ == '__main__':
    main()
