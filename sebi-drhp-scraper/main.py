#!/usr/bin/env python3
"""
SEBI DRHP Scraper - Main Application
Scrapes SEBI website for latest DRHP filings, extracts data, and sends via email
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.sebi_scraper import SEBIScraper, DRHPFiling
from src.drhp_parser import DRHPParser, DRHPData
from src.email_sender import EmailSender, EmailConfig


def print_banner():
    """Print application banner"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║               SEBI DRHP Scraper v1.0                          ║
║     Scrape SEBI filings, Extract DRHP data, Send via Email    ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def print_filings_table(filings: list):
    """Print filings in a formatted table"""
    print("\n" + "="*70)
    print("LATEST SEBI DRHP FILINGS")
    print("="*70)
    print(f"{'#':<3} {'Company Name':<40} {'Filing Date':<15}")
    print("-"*70)

    for i, filing in enumerate(filings, 1):
        name = filing.company_name[:38] + ".." if len(filing.company_name) > 40 else filing.company_name
        print(f"{i:<3} {name:<40} {filing.filing_date:<15}")

    print("="*70)


def print_drhp_summary(data: DRHPData):
    """Print DRHP data summary in table format"""
    print("\n" + "="*70)
    print("DRHP SUMMARY")
    print("="*70)

    print(f"""
| Name of Company              | {data.company_name} (The "Company")
|------------------------------|-------------------------------------------
| Business of the Company      |
|   1. Business Model          | {data.business_model[:60]}...
|   2. Main Operations         | {data.main_operations[:60]}...
|   3. Segments                | {data.segments[:60]}...
|   4. Products/Locations      | {data.products_locations[:60]}...
|------------------------------|-------------------------------------------
| Objects of the Issue         |""")

    for i, obj in enumerate(data.objects_of_issue[:3], 1):
        print(f"|   {i}. {obj[:55]}...")

    print(f"""|------------------------------|-------------------------------------------
| Regulation 6(1) or 6(2)      | {data.regulation_type}
|------------------------------|-------------------------------------------
| Issue Type                   | {data.issue_type}
|------------------------------|-------------------------------------------
| Issue Size                   | Fresh Issue: {data.fresh_issue_size}
|                              | OFS: {data.ofs_size}
|------------------------------|-------------------------------------------
| Selling Shareholders         |""")

    for i, sh in enumerate(data.selling_shareholders[:3], 1):
        print(f"|   {i}. {sh['name'][:30]} - {sh['shares']} Shares")

    print(f"""|------------------------------|-------------------------------------------
| Revenue from Operations      | {data.revenue_latest_quarter} (Latest Qtr)
|                              | {data.revenue_current_year} (Current FY)
|                              | {data.revenue_previous_year} (Previous FY)
|------------------------------|-------------------------------------------
| Profit/Loss After Tax        | {data.pat_latest_quarter} (Latest Qtr)
|                              | {data.pat_current_year} (Current FY)
|                              | {data.pat_previous_year} (Previous FY)
|------------------------------|-------------------------------------------
| Book Running Lead Managers   |""")

    for i, brlm in enumerate(data.brlms[:5], 1):
        print(f"|   {i}. {brlm}")

    print("="*70)


def save_output(data: DRHPData, filings: list, output_dir: str):
    """Save extracted data to JSON file"""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"drhp_report_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    output = {
        "generated_at": datetime.now().isoformat(),
        "latest_filings": [
            {
                "company_name": f.company_name,
                "filing_date": f.filing_date,
                "document_link": f.document_link
            }
            for f in filings
        ],
        "drhp_data": data.to_dict()
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Report saved to: {filepath}")
    return filepath


def run_scraper(
    num_filings: int = 3,
    download_drhp: bool = True,
    send_email: bool = False,
    recipient_email: Optional[str] = None,
    headless: bool = True,
    output_dir: str = "./output",
    download_dir: str = "./downloads"
):
    """
    Main scraper function

    Args:
        num_filings: Number of latest filings to fetch
        download_drhp: Whether to download the DRHP PDF
        send_email: Whether to send results via email
        recipient_email: Email recipient (required if send_email is True)
        headless: Run browser in headless mode
        output_dir: Directory for output files
        download_dir: Directory for downloaded PDFs
    """
    print_banner()

    # Initialize scraper
    scraper = SEBIScraper(headless=headless, download_dir=download_dir)

    try:
        # Step 1: Get latest filings
        print("\n[STEP 1] Fetching latest SEBI DRHP filings...")
        filings = scraper.get_latest_filings(count=num_filings)

        if not filings:
            print("[ERROR] Could not fetch any filings from SEBI website")
            print("[TIP] The website may be temporarily unavailable or blocking requests")
            return None

        print_filings_table(filings)

        # Step 2: Download latest DRHP
        pdf_path = None
        if download_drhp and filings:
            print("\n[STEP 2] Downloading latest DRHP document...")
            pdf_path = scraper.download_drhp(filings[0])

            if pdf_path:
                print(f"[SUCCESS] DRHP downloaded: {pdf_path}")
            else:
                print("[WARN] Could not download DRHP. Will try alternative sources...")

        # Step 3: Parse DRHP
        drhp_data = None
        if pdf_path and os.path.exists(pdf_path):
            print("\n[STEP 3] Extracting data from DRHP...")
            parser = DRHPParser(pdf_path)
            drhp_data = parser.parse()
            print_drhp_summary(drhp_data)
        else:
            print("\n[STEP 3] Creating placeholder DRHP data...")
            # Create placeholder data from filing info
            drhp_data = DRHPData(
                company_name=filings[0].company_name if filings else "Unknown",
                business_model="Please refer to the DRHP document for details",
                main_operations="Please refer to the DRHP document for details",
                segments="Please refer to the DRHP document for details",
                products_locations="Please refer to the DRHP document for details",
                objects_of_issue=["Please refer to the DRHP document for details"],
                regulation_type="Please refer to the DRHP document",
                issue_type="Please refer to the DRHP document",
            )

        # Step 4: Save output
        print("\n[STEP 4] Saving report...")
        report_path = save_output(drhp_data, filings, output_dir)

        # Step 5: Send email
        if send_email:
            print("\n[STEP 5] Sending email...")

            if not recipient_email:
                recipient_email = os.getenv("EMAIL_RECIPIENT")

            if not recipient_email:
                print("[ERROR] No recipient email specified. Use --email flag or set EMAIL_RECIPIENT in .env")
                return drhp_data

            sender_email = os.getenv("EMAIL_SENDER")
            sender_password = os.getenv("EMAIL_PASSWORD")

            if not sender_email or not sender_password:
                print("[ERROR] Email credentials not configured in .env file")
                print("[TIP] Copy .env.example to .env and fill in your credentials")
                return drhp_data

            config = EmailConfig(
                sender_email=sender_email,
                sender_password=sender_password,
                smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                smtp_port=int(os.getenv("SMTP_PORT", "587"))
            )

            email_sender = EmailSender(config)

            filings_summary = [
                {"company_name": f.company_name, "filing_date": f.filing_date}
                for f in filings
            ]

            subject = f"SEBI DRHP Report - {drhp_data.company_name} - {datetime.now().strftime('%Y-%m-%d')}"

            success = email_sender.send_email(
                recipient_email=recipient_email,
                subject=subject,
                drhp_data=drhp_data,
                attachment_path=pdf_path,
                filings_summary=filings_summary
            )

            if success:
                print(f"[SUCCESS] Email sent to {recipient_email}")
            else:
                print("[ERROR] Failed to send email")

        print("\n" + "="*70)
        print("SCRAPING COMPLETE!")
        print("="*70)

        return drhp_data

    finally:
        scraper.stop()


def main():
    """CLI entry point"""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Scrape SEBI DRHP filings and extract key information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Basic scrape, show results
  python main.py --email user@example.com # Scrape and send to email
  python main.py --no-download            # Don't download DRHP PDF
  python main.py --filings 5              # Get latest 5 filings
  python main.py --no-headless            # Show browser window
        """
    )

    parser.add_argument(
        '--filings', '-f',
        type=int,
        default=3,
        help='Number of latest filings to fetch (default: 3)'
    )

    parser.add_argument(
        '--email', '-e',
        type=str,
        help='Send results to this email address'
    )

    parser.add_argument(
        '--no-download',
        action='store_true',
        help='Skip downloading DRHP PDF'
    )

    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Show browser window (not headless)'
    )

    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./output',
        help='Directory for output files (default: ./output)'
    )

    parser.add_argument(
        '--download-dir', '-d',
        type=str,
        default='./downloads',
        help='Directory for downloaded PDFs (default: ./downloads)'
    )

    parser.add_argument(
        '--parse-pdf', '-p',
        type=str,
        help='Parse an existing DRHP PDF file instead of scraping'
    )

    args = parser.parse_args()

    # If parsing existing PDF
    if args.parse_pdf:
        if not os.path.exists(args.parse_pdf):
            print(f"[ERROR] File not found: {args.parse_pdf}")
            sys.exit(1)

        print_banner()
        print(f"\n[INFO] Parsing existing PDF: {args.parse_pdf}")

        parser_obj = DRHPParser(args.parse_pdf)
        data = parser_obj.parse()
        print_drhp_summary(data)

        if args.email:
            load_dotenv()
            sender_email = os.getenv("EMAIL_SENDER")
            sender_password = os.getenv("EMAIL_PASSWORD")

            if sender_email and sender_password:
                config = EmailConfig(sender_email=sender_email, sender_password=sender_password)
                email_sender = EmailSender(config)
                email_sender.send_email(
                    recipient_email=args.email,
                    subject=f"DRHP Report - {data.company_name}",
                    drhp_data=data,
                    attachment_path=args.parse_pdf
                )
        return

    # Run the scraper
    run_scraper(
        num_filings=args.filings,
        download_drhp=not args.no_download,
        send_email=bool(args.email),
        recipient_email=args.email,
        headless=not args.no_headless,
        output_dir=args.output_dir,
        download_dir=args.download_dir
    )


if __name__ == "__main__":
    main()
