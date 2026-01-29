"""
SEBI DRHP Filings Scraper
Uses Selenium for browser automation to bypass anti-scraping measures
"""

import os
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


@dataclass
class DRHPFiling:
    """Data class for DRHP filing information"""
    company_name: str
    filing_date: str
    document_link: str
    details_link: str = ""
    document_type: str = "DRHP"


class SEBIScraper:
    """Scraper for SEBI Public Issues / DRHP Filings"""

    SEBI_FILINGS_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15&smid=10"
    SEBI_BASE_URL = "https://www.sebi.gov.in"

    def __init__(self, headless: bool = True, download_dir: str = "./downloads"):
        """
        Initialize the SEBI Scraper

        Args:
            headless: Run browser in headless mode (no GUI)
            download_dir: Directory to save downloaded PDFs
        """
        self.headless = headless
        self.download_dir = os.path.abspath(download_dir)
        self.driver = None

        # Ensure download directory exists
        os.makedirs(self.download_dir, exist_ok=True)

    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # PDF download settings
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 0,
        })

        # Exclude automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Initialize driver with WebDriver Manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Execute CDP commands to mask automation
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """
        })

        return driver

    def start(self):
        """Start the browser session"""
        if self.driver is None:
            self.driver = self._setup_driver()
            print("[INFO] Browser session started")

    def stop(self):
        """Stop the browser session"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("[INFO] Browser session closed")

    def get_latest_filings(self, count: int = 3) -> List[DRHPFiling]:
        """
        Fetch the latest DRHP filings from SEBI website

        Args:
            count: Number of latest filings to retrieve

        Returns:
            List of DRHPFiling objects
        """
        self.start()
        filings = []

        try:
            print(f"[INFO] Navigating to SEBI filings page...")
            self.driver.get(self.SEBI_FILINGS_URL)

            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            # Additional wait for dynamic content
            time.sleep(3)

            # Parse the page content
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find the filings table - SEBI uses various table structures
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')

                for row in rows[1:]:  # Skip header row
                    if len(filings) >= count:
                        break

                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        filing = self._parse_filing_row(cols)
                        if filing:
                            filings.append(filing)

                if filings:
                    break

            # Alternative: Try to find links directly if table parsing fails
            if not filings:
                filings = self._parse_filings_alternative(soup, count)

            print(f"[INFO] Found {len(filings)} filings")

        except TimeoutException:
            print("[ERROR] Page load timeout - SEBI website may be slow or blocking")
        except Exception as e:
            print(f"[ERROR] Failed to fetch filings: {str(e)}")

        return filings[:count]

    def _parse_filing_row(self, cols) -> Optional[DRHPFiling]:
        """Parse a single row from the filings table"""
        try:
            # Extract text from columns
            texts = [col.get_text(strip=True) for col in cols]

            # Find links in the row
            links = []
            for col in cols:
                for a in col.find_all('a', href=True):
                    links.append(a['href'])

            # Try to identify company name and date
            company_name = ""
            filing_date = ""
            doc_link = ""

            for text in texts:
                # Check if it's a date (various formats)
                date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})', text)
                if date_match:
                    filing_date = date_match.group(1)
                elif len(text) > 10 and not text.isdigit():
                    # Likely company name
                    if not company_name:
                        company_name = text

            # Get document link
            for link in links:
                if '.pdf' in link.lower() or 'attachdocs' in link.lower():
                    doc_link = link if link.startswith('http') else self.SEBI_BASE_URL + link
                    break

            if company_name:
                return DRHPFiling(
                    company_name=company_name,
                    filing_date=filing_date or "N/A",
                    document_link=doc_link or "",
                    details_link=links[0] if links else ""
                )

        except Exception as e:
            print(f"[DEBUG] Row parsing error: {e}")

        return None

    def _parse_filings_alternative(self, soup: BeautifulSoup, count: int) -> List[DRHPFiling]:
        """Alternative parsing method using div/list structures"""
        filings = []

        # Look for common listing patterns
        listing_containers = soup.find_all(['div', 'ul'], class_=re.compile(r'list|filing|item', re.I))

        for container in listing_containers:
            items = container.find_all(['li', 'div', 'a'])

            for item in items:
                if len(filings) >= count:
                    break

                text = item.get_text(strip=True)
                link = item.get('href') or (item.find('a', href=True) or {}).get('href', '')

                if text and len(text) > 20:
                    # Extract date from text
                    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})', text)
                    filing_date = date_match.group(1) if date_match else "N/A"

                    # Clean company name
                    company_name = re.sub(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+\w+\s+\d{4}', '', text).strip()

                    if company_name and len(company_name) > 5:
                        filings.append(DRHPFiling(
                            company_name=company_name[:100],
                            filing_date=filing_date,
                            document_link=link if link.startswith('http') else self.SEBI_BASE_URL + link if link else "",
                            details_link=""
                        ))

        return filings

    def download_drhp(self, filing: DRHPFiling) -> Optional[str]:
        """
        Download the DRHP PDF document

        Args:
            filing: DRHPFiling object with document link

        Returns:
            Path to downloaded file or None if failed
        """
        if not filing.document_link:
            print(f"[WARN] No document link for {filing.company_name}")
            return None

        self.start()

        try:
            print(f"[INFO] Downloading DRHP for {filing.company_name}...")

            # Navigate to the document
            self.driver.get(filing.document_link)
            time.sleep(5)  # Wait for download to start

            # Find the downloaded file
            files = os.listdir(self.download_dir)
            pdf_files = [f for f in files if f.endswith('.pdf')]

            if pdf_files:
                # Get the most recent file
                latest_file = max(
                    [os.path.join(self.download_dir, f) for f in pdf_files],
                    key=os.path.getctime
                )

                # Rename to company name
                safe_name = re.sub(r'[^\w\s-]', '', filing.company_name)[:50]
                new_name = os.path.join(self.download_dir, f"{safe_name}_DRHP.pdf")

                if os.path.exists(latest_file) and latest_file != new_name:
                    os.rename(latest_file, new_name)
                    print(f"[INFO] Downloaded: {new_name}")
                    return new_name

                return latest_file

        except Exception as e:
            print(f"[ERROR] Failed to download DRHP: {str(e)}")

        return None

    def get_filing_details_page(self, filing: DRHPFiling) -> Optional[str]:
        """
        Get the HTML content of the filing details page

        Args:
            filing: DRHPFiling object

        Returns:
            HTML content as string or None
        """
        if not filing.details_link:
            return None

        self.start()

        try:
            url = filing.details_link if filing.details_link.startswith('http') else self.SEBI_BASE_URL + filing.details_link
            self.driver.get(url)

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(2)
            return self.driver.page_source

        except Exception as e:
            print(f"[ERROR] Failed to get details page: {str(e)}")

        return None


def main():
    """Test the scraper"""
    scraper = SEBIScraper(headless=True)

    try:
        # Get latest 3 filings
        filings = scraper.get_latest_filings(count=3)

        print("\n" + "="*60)
        print("LATEST SEBI DRHP FILINGS")
        print("="*60)

        for i, filing in enumerate(filings, 1):
            print(f"\n{i}. {filing.company_name}")
            print(f"   Date: {filing.filing_date}")
            print(f"   Link: {filing.document_link or 'N/A'}")

        # Download the latest DRHP
        if filings:
            print("\n[INFO] Attempting to download latest DRHP...")
            pdf_path = scraper.download_drhp(filings[0])
            if pdf_path:
                print(f"[SUCCESS] DRHP saved to: {pdf_path}")

    finally:
        scraper.stop()


if __name__ == "__main__":
    main()
