"""
Email Sender Module
Sends formatted DRHP data via email
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from dataclasses import dataclass

from .drhp_parser import DRHPData


@dataclass
class EmailConfig:
    """Email configuration"""
    sender_email: str
    sender_password: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587


class EmailSender:
    """Send formatted DRHP reports via email"""

    def __init__(self, config: EmailConfig):
        """
        Initialize Email Sender

        Args:
            config: EmailConfig object with SMTP settings
        """
        self.config = config

    def format_drhp_table(self, data: DRHPData) -> str:
        """
        Format DRHP data as HTML table

        Args:
            data: DRHPData object

        Returns:
            HTML formatted table string
        """
        # Format business of company
        business_html = f"""
        1. <b>Business Model:</b> {data.business_model}<br>
        2. <b>Main Operations:</b> {data.main_operations}<br>
        3. <b>Segments:</b> {data.segments}<br>
        4. <b>Products/Locations:</b> {data.products_locations}
        """

        # Format objects of issue
        objects_html = "<br>".join([f"{i}. {obj}" for i, obj in enumerate(data.objects_of_issue[:3], 1)])

        # Format selling shareholders
        shareholders_html = "<br>".join([
            f"{i}. {sh['name']} - {sh['shares']} Equity Shares"
            for i, sh in enumerate(data.selling_shareholders[:5], 1)
        ])

        # Format BRLMs
        brlms_html = "<br>".join([f"{i}. {brlm}" for i, brlm in enumerate(data.brlms, 1)])

        # Format issue size
        issue_size_html = ""
        if data.fresh_issue_size != "N/A":
            issue_size_html += f"Fresh Issue: {data.fresh_issue_size}<br>"
        if data.ofs_size != "N/A":
            issue_size_html += f"Offer for Sale: {data.ofs_size}"

        html_table = f"""
        <html>
        <head>
            <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                    vertical-align: top;
                }}
                th {{
                    background-color: #4472C4;
                    color: white;
                    font-weight: bold;
                    width: 30%;
                }}
                td {{
                    background-color: #f9f9f9;
                }}
                tr:nth-child(even) td {{
                    background-color: #E9EBF5;
                }}
                .header {{
                    background-color: #2F5496;
                    color: white;
                    text-align: center;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 15px;
                }}
            </style>
        </head>
        <body>
            <h2 style="color: #2F5496;">DRHP Summary Report</h2>
            <p>Generated from SEBI DRHP Filing</p>

            <table>
                <tr>
                    <th>Name of Company</th>
                    <td><b>{data.company_name}</b> (The "Company")</td>
                </tr>
                <tr>
                    <th>Business of the Company</th>
                    <td>{business_html}</td>
                </tr>
                <tr>
                    <th>Objects of the Issue</th>
                    <td>{objects_html}</td>
                </tr>
                <tr>
                    <th>Regulation 6(1) or 6(2)</th>
                    <td>{data.regulation_type}</td>
                </tr>
                <tr>
                    <th>Issue Type</th>
                    <td>{data.issue_type}</td>
                </tr>
                <tr>
                    <th>Issue Size</th>
                    <td>{issue_size_html}</td>
                </tr>
                <tr>
                    <th>Details of Selling Shareholders</th>
                    <td>{shareholders_html}</td>
                </tr>
                <tr>
                    <th>Revenue from Operations</th>
                    <td>
                        {data.revenue_latest_quarter} (Latest Quarter)<br>
                        {data.revenue_current_year} (Current Year March)<br>
                        {data.revenue_previous_year} (Previous Year March)
                    </td>
                </tr>
                <tr>
                    <th>Profit/Loss After Tax</th>
                    <td>
                        {data.pat_latest_quarter} (Latest Quarter)<br>
                        {data.pat_current_year} (Current Year March)<br>
                        {data.pat_previous_year} (Previous Year March)
                    </td>
                </tr>
                <tr>
                    <th>Book Running Lead Managers (BRLMs)</th>
                    <td>{brlms_html}</td>
                </tr>
            </table>

            <br>
            <p style="color: #666; font-size: 12px;">
                This report was automatically generated by SEBI DRHP Scraper.<br>
                Data extracted from the official Draft Red Herring Prospectus.
            </p>
        </body>
        </html>
        """

        return html_table

    def format_drhp_plain_text(self, data: DRHPData) -> str:
        """
        Format DRHP data as plain text table

        Args:
            data: DRHPData object

        Returns:
            Plain text formatted table
        """
        objects_text = "\n".join([f"   {i}. {obj}" for i, obj in enumerate(data.objects_of_issue[:3], 1)])
        shareholders_text = "\n".join([
            f"   {i}. {sh['name']} - {sh['shares']} Equity Shares"
            for i, sh in enumerate(data.selling_shareholders[:5], 1)
        ])
        brlms_text = "\n".join([f"   {i}. {brlm}" for i, brlm in enumerate(data.brlms, 1)])

        text = f"""
================================================================================
                           DRHP SUMMARY REPORT
================================================================================

| Name of Company              | {data.company_name} (The "Company")
|------------------------------|------------------------------------------------
| Business of the Company      | 1. Business Model: {data.business_model[:100]}...
|                              | 2. Main Operations: {data.main_operations[:100]}...
|                              | 3. Segments: {data.segments[:100]}...
|                              | 4. Products/Locations: {data.products_locations[:100]}...
|------------------------------|------------------------------------------------
| Objects of the Issue         |
{objects_text}
|------------------------------|------------------------------------------------
| Regulation 6(1) or 6(2)      | {data.regulation_type}
|------------------------------|------------------------------------------------
| Issue Type                   | {data.issue_type}
|------------------------------|------------------------------------------------
| Issue Size                   | Fresh Issue: {data.fresh_issue_size}
|                              | Offer for Sale: {data.ofs_size}
|------------------------------|------------------------------------------------
| Selling Shareholders         |
{shareholders_text}
|------------------------------|------------------------------------------------
| Revenue from Operations      | {data.revenue_latest_quarter} (Latest Quarter)
|                              | {data.revenue_current_year} (Current Year March)
|                              | {data.revenue_previous_year} (Previous Year March)
|------------------------------|------------------------------------------------
| Profit/Loss After Tax        | {data.pat_latest_quarter} (Latest Quarter)
|                              | {data.pat_current_year} (Current Year March)
|                              | {data.pat_previous_year} (Previous Year March)
|------------------------------|------------------------------------------------
| Book Running Lead Managers   |
{brlms_text}
================================================================================

Generated by SEBI DRHP Scraper
        """

        return text

    def send_email(
        self,
        recipient_email: str,
        subject: str,
        drhp_data: DRHPData,
        attachment_path: Optional[str] = None,
        filings_summary: Optional[List[dict]] = None
    ) -> bool:
        """
        Send DRHP report via email

        Args:
            recipient_email: Recipient email address
            subject: Email subject
            drhp_data: DRHPData object to format and send
            attachment_path: Optional path to PDF attachment
            filings_summary: Optional list of latest filings summary

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Add filings summary if provided
            filings_html = ""
            if filings_summary:
                filings_html = """
                <h3 style="color: #2F5496;">Latest 3 SEBI DRHP Filings</h3>
                <table style="border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background-color: #4472C4; color: white;">
                        <th style="border: 1px solid #ddd; padding: 8px;">#</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">Company Name</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">Filing Date</th>
                    </tr>
                """
                for i, filing in enumerate(filings_summary, 1):
                    filings_html += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">{i}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{filing.get('company_name', 'N/A')}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{filing.get('filing_date', 'N/A')}</td>
                    </tr>
                    """
                filings_html += "</table><hr>"

            # Create HTML body
            html_body = f"""
            <html>
            <body>
                {filings_html}
                {self.format_drhp_table(drhp_data)}
            </body>
            </html>
            """

            # Create plain text body
            plain_body = self.format_drhp_plain_text(drhp_data)

            # Attach both versions
            part1 = MIMEText(plain_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Attach PDF if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
                print(f"[INFO] Attached PDF: {attachment_path}")

            # Send email
            print(f"[INFO] Connecting to SMTP server: {self.config.smtp_server}:{self.config.smtp_port}")

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.sendmail(
                    self.config.sender_email,
                    recipient_email,
                    msg.as_string()
                )

            print(f"[SUCCESS] Email sent to {recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("[ERROR] SMTP Authentication failed. Check email/password.")
            print("[TIP] For Gmail, use an App Password: https://myaccount.google.com/apppasswords")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP error: {str(e)}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to send email: {str(e)}")
            return False


def main():
    """Test email functionality"""
    from dotenv import load_dotenv
    load_dotenv()

    # Create test data
    test_data = DRHPData(
        company_name="Test Company Limited",
        business_model="Test business model description",
        main_operations="Manufacturing and distribution",
        segments="Segment A, Segment B",
        products_locations="Products in India",
        objects_of_issue=["Expansion of business", "Working capital", "General corporate purposes"],
        regulation_type="6(2)",
        issue_type="Fresh Issue and Offer for Sale",
        fresh_issue_size="Up to 500 crore",
        ofs_size="Up to 1,00,00,000 Equity Shares",
        selling_shareholders=[{"name": "Promoter A", "shares": "50,00,000"}],
        revenue_latest_quarter="₹ 1,000.00 million",
        revenue_current_year="₹ 3,500.00 million",
        revenue_previous_year="₹ 2,800.00 million",
        pat_latest_quarter="₹ 100.00 million",
        pat_current_year="₹ 350.00 million",
        pat_previous_year="₹ 280.00 million",
        brlms=["ICICI Securities Limited", "Axis Capital Limited", "Kotak Mahindra Capital"],
    )

    config = EmailConfig(
        sender_email=os.getenv("EMAIL_SENDER", ""),
        sender_password=os.getenv("EMAIL_PASSWORD", ""),
    )

    if not config.sender_email or not config.sender_password:
        print("[ERROR] Email credentials not configured in .env file")
        print("\nPlain text preview:")
        sender = EmailSender(config)
        print(sender.format_drhp_plain_text(test_data))
        return

    sender = EmailSender(config)
    recipient = os.getenv("EMAIL_RECIPIENT", config.sender_email)

    sender.send_email(
        recipient_email=recipient,
        subject="Test DRHP Report",
        drhp_data=test_data,
    )


if __name__ == "__main__":
    main()
