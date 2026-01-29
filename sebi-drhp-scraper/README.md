# SEBI DRHP Scraper

A Python application to scrape SEBI (Securities and Exchange Board of India) website for latest DRHP (Draft Red Herring Prospectus) filings, extract key information, and send formatted reports via email.

## Features

- **Scrape SEBI Filings**: Fetches latest DRHP filings from SEBI website using Selenium (bypasses anti-scraping measures)
- **Download DRHP PDFs**: Automatically downloads DRHP documents
- **Extract Key Data**: Parses DRHP PDFs to extract:
  - Company name and business details
  - Objects of the issue
  - Regulation type (6(1) or 6(2))
  - Issue type and size (Fresh Issue / OFS)
  - Selling shareholders
  - Financial data (Revenue, PAT)
  - Book Running Lead Managers
- **Email Reports**: Send formatted HTML reports via email with PDF attachment

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Chrome browser installed
- Gmail account (for email functionality)

### Setup

1. **Clone/Navigate to the project directory**
   ```bash
   cd sebi-drhp-scraper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure email (optional)**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_RECIPIENT=recipient@example.com
   ```

   > **Note**: For Gmail, you need to use an App Password, not your regular password.
   > Generate one at: https://myaccount.google.com/apppasswords

## Usage

### Basic Usage

```bash
# Scrape latest 3 filings and display results
python main.py

# Get latest 5 filings
python main.py --filings 5

# Scrape and send to email
python main.py --email your_email@example.com

# Show browser window (not headless)
python main.py --no-headless

# Skip downloading DRHP PDF
python main.py --no-download
```

### Parse Existing PDF

```bash
# Parse an already downloaded DRHP PDF
python main.py --parse-pdf /path/to/drhp.pdf

# Parse and send via email
python main.py --parse-pdf /path/to/drhp.pdf --email user@example.com
```

### All Options

```
usage: main.py [-h] [--filings FILINGS] [--email EMAIL] [--no-download]
               [--no-headless] [--output-dir OUTPUT_DIR]
               [--download-dir DOWNLOAD_DIR] [--parse-pdf PARSE_PDF]

Options:
  --filings, -f      Number of latest filings to fetch (default: 3)
  --email, -e        Send results to this email address
  --no-download      Skip downloading DRHP PDF
  --no-headless      Show browser window (not headless)
  --output-dir, -o   Directory for output files (default: ./output)
  --download-dir, -d Directory for downloaded PDFs (default: ./downloads)
  --parse-pdf, -p    Parse an existing DRHP PDF file instead of scraping
```

## Output Format

The extracted data is formatted as follows:

| Field | Description |
|-------|-------------|
| Name of Company | Company name (The "Company") |
| Business of the Company | 1. Business Model<br>2. Main Operations<br>3. Segments<br>4. Products/Locations |
| Objects of the Issue | Top 3 points from DRHP |
| Regulation 6(1) or 6(2) | ICDR regulation type |
| Issue Type | Fresh Issue / Offer for Sale |
| Issue Size | Fresh Issue amount + OFS shares |
| Selling Shareholders | List with share counts |
| Revenue from Operations | Latest Quarter, Current FY, Previous FY |
| Profit/Loss After Tax | Latest Quarter, Current FY, Previous FY |
| Book Running Lead Managers | List of BRLMs |

## Project Structure

```
sebi-drhp-scraper/
├── main.py              # Main application entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # This file
├── src/
│   ├── __init__.py
│   ├── sebi_scraper.py  # SEBI website scraper (Selenium)
│   ├── drhp_parser.py   # DRHP PDF parser
│   └── email_sender.py  # Email functionality
├── downloads/           # Downloaded DRHP PDFs
└── output/              # Generated JSON reports
```

## Troubleshooting

### SEBI Website Blocking

If the SEBI website is blocking requests:
1. Try running without headless mode: `python main.py --no-headless`
2. Add delays between requests
3. Try at different times (website may be under maintenance)

### Chrome/ChromeDriver Issues

The application uses `webdriver-manager` to automatically download the correct ChromeDriver. If you face issues:
1. Ensure Google Chrome is installed
2. Update Chrome to the latest version
3. Clear the webdriver cache: `rm -rf ~/.wdm`

### Email Not Sending

1. Ensure you're using an App Password for Gmail (not regular password)
2. Check if "Less secure app access" is enabled (if not using App Password)
3. Verify SMTP settings in `.env`

### PDF Parsing Issues

If PDF parsing returns incomplete data:
1. Some DRHPs have non-standard formatting
2. Scanned PDFs may not have extractable text
3. Try downloading the PDF manually and use `--parse-pdf` option

## License

MIT License

## Disclaimer

This tool is for educational and informational purposes only. Always verify data from official SEBI sources before making any investment decisions. The extracted data may not be 100% accurate due to varying DRHP formats.
