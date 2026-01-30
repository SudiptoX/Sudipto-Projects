"""
DRHP PDF Parser
Extracts key information from Draft Red Herring Prospectus documents
"""

import re
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import pdfplumber
from PyPDF2 import PdfReader


@dataclass
class DRHPData:
    """Data class containing extracted DRHP information"""
    company_name: str = ""
    business_model: str = ""
    main_operations: str = ""
    segments: str = ""
    products_locations: str = ""
    objects_of_issue: List[str] = field(default_factory=list)
    regulation_type: str = ""  # 6(1) or 6(2)
    issue_type: str = ""  # Fresh issue, OFS, etc.
    fresh_issue_size: str = ""
    ofs_size: str = ""
    selling_shareholders: List[Dict[str, str]] = field(default_factory=list)
    revenue_latest_quarter: str = ""
    revenue_current_year: str = ""
    revenue_previous_year: str = ""
    pat_latest_quarter: str = ""
    pat_current_year: str = ""
    pat_previous_year: str = ""
    brlms: List[str] = field(default_factory=list)
    registrar: str = ""
    listing_exchanges: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "company_name": self.company_name,
            "business_of_company": {
                "business_model": self.business_model,
                "main_operations": self.main_operations,
                "segments": self.segments,
                "products_locations": self.products_locations
            },
            "objects_of_issue": self.objects_of_issue,
            "regulation_type": self.regulation_type,
            "issue_type": self.issue_type,
            "issue_size": {
                "fresh_issue": self.fresh_issue_size,
                "ofs": self.ofs_size
            },
            "selling_shareholders": self.selling_shareholders,
            "financials": {
                "revenue": {
                    "latest_quarter": self.revenue_latest_quarter,
                    "current_year": self.revenue_current_year,
                    "previous_year": self.revenue_previous_year
                },
                "pat": {
                    "latest_quarter": self.pat_latest_quarter,
                    "current_year": self.pat_current_year,
                    "previous_year": self.pat_previous_year
                }
            },
            "brlms": self.brlms,
            "registrar": self.registrar,
            "listing_exchanges": self.listing_exchanges
        }


class DRHPParser:
    """Parser for DRHP PDF documents"""

    def __init__(self, pdf_path: str):
        """
        Initialize the DRHP Parser

        Args:
            pdf_path: Path to the DRHP PDF file
        """
        self.pdf_path = pdf_path
        self.text_content = ""
        self.pages_text = []

    def extract_text(self, max_pages: int = 150) -> str:
        """
        Extract text from PDF

        Args:
            max_pages: Maximum number of pages to process

        Returns:
            Extracted text content
        """
        print(f"[INFO] Extracting text from PDF: {self.pdf_path}")

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = min(len(pdf.pages), max_pages)
                print(f"[INFO] Processing {total_pages} pages...")

                for i, page in enumerate(pdf.pages[:max_pages]):
                    try:
                        text = page.extract_text() or ""
                        self.pages_text.append(text)
                        self.text_content += text + "\n\n"

                        if (i + 1) % 20 == 0:
                            print(f"[INFO] Processed {i + 1}/{total_pages} pages...")

                    except Exception as e:
                        print(f"[WARN] Error on page {i + 1}: {e}")
                        continue

            print(f"[INFO] Text extraction complete. Total characters: {len(self.text_content)}")

        except Exception as e:
            print(f"[ERROR] Failed to extract PDF text: {e}")
            # Fallback to PyPDF2
            self._extract_with_pypdf2(max_pages)

        return self.text_content

    def _extract_with_pypdf2(self, max_pages: int):
        """Fallback text extraction using PyPDF2"""
        try:
            reader = PdfReader(self.pdf_path)
            for i, page in enumerate(reader.pages[:max_pages]):
                text = page.extract_text() or ""
                self.pages_text.append(text)
                self.text_content += text + "\n\n"
        except Exception as e:
            print(f"[ERROR] PyPDF2 extraction also failed: {e}")

    def parse(self) -> DRHPData:
        """
        Parse the DRHP and extract all required information

        Returns:
            DRHPData object with extracted information
        """
        if not self.text_content:
            self.extract_text()

        data = DRHPData()

        # Extract each field
        data.company_name = self._extract_company_name()
        data.business_model = self._extract_business_model()
        data.main_operations = self._extract_main_operations()
        data.segments = self._extract_segments()
        data.products_locations = self._extract_products_locations()
        data.objects_of_issue = self._extract_objects_of_issue()
        data.regulation_type = self._extract_regulation_type()
        data.issue_type = self._extract_issue_type()
        data.fresh_issue_size, data.ofs_size = self._extract_issue_size()
        data.selling_shareholders = self._extract_selling_shareholders()
        data.revenue_latest_quarter, data.revenue_current_year, data.revenue_previous_year = self._extract_revenue()
        data.pat_latest_quarter, data.pat_current_year, data.pat_previous_year = self._extract_pat()
        data.brlms = self._extract_brlms()
        data.registrar = self._extract_registrar()
        data.listing_exchanges = self._extract_exchanges()

        return data

    def _extract_company_name(self) -> str:
        """Extract company name from DRHP"""
        patterns = [
            r'DRAFT RED HERRING PROSPECTUS.*?([A-Z][A-Z\s&\.]+(?:LIMITED|LTD|PRIVATE LIMITED|PVT\.?\s*LTD))',
            r'(?:of|for)\s+([A-Z][A-Za-z\s&\.]+(?:LIMITED|LTD|PRIVATE LIMITED))',
            r'^([A-Z][A-Z\s&\.]+(?:LIMITED|LTD))\s*$',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content[:5000], re.MULTILINE | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                if len(name) > 5 and len(name) < 100:
                    return name

        return "Company Name Not Found"

    def _extract_business_model(self) -> str:
        """Extract business model description"""
        patterns = [
            r'(?:Our Company|The Company|We are)\s+(?:is\s+)?(?:a|an|engaged in|primarily)\s+(.{100,500}?)(?:\.|We|Our)',
            r'Business\s+Overview[:\s]+(.{100,500}?)(?:\n\n|Our Company)',
            r'About\s+(?:Our|the)\s+Company[:\s]+(.{100,500}?)(?:\n\n)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE | re.DOTALL)
            if match:
                return self._clean_text(match.group(1))

        return "Business model information not found"

    def _extract_main_operations(self) -> str:
        """Extract main operations"""
        patterns = [
            r'(?:principal|main|primary)\s+(?:business|operations?|activities?)\s+(?:include|comprise|are|is)\s+(.{50,300}?)(?:\.|We)',
            r'engaged\s+in\s+(?:the\s+)?(.{50,300}?)(?:\.|We|Our)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))

        return "Operations information not found"

    def _extract_segments(self) -> str:
        """Extract business segments"""
        patterns = [
            r'(?:business\s+)?segments?\s+(?:include|comprise|are)[:\s]+(.{50,400}?)(?:\n\n|Our|The Company)',
            r'(?:operating|reportable)\s+segments?[:\s]+(.{50,400}?)(?:\n\n)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE | re.DOTALL)
            if match:
                return self._clean_text(match.group(1))

        return "Segment information not found"

    def _extract_products_locations(self) -> str:
        """Extract products and locations"""
        patterns = [
            r'(?:products?|services?)\s+(?:include|offered|portfolio)[:\s]+(.{50,400}?)(?:\n\n|Our)',
            r'(?:operations?\s+in|presence\s+in|located\s+in)\s+(.{30,200}?)(?:\.|We)',
        ]

        results = []
        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE)
            if match:
                results.append(self._clean_text(match.group(1)))

        return "; ".join(results) if results else "Products/locations information not found"

    def _extract_objects_of_issue(self) -> List[str]:
        """Extract objects of the issue"""
        objects = []

        patterns = [
            r'OBJECTS\s+OF\s+THE\s+(?:ISSUE|OFFER)(.{200,2000}?)(?:BASIS\s+FOR|ISSUE\s+STRUCTURE|The\s+main\s+objects)',
            r'Objects\s+of\s+the\s+Issue[:\s]+(.{200,2000}?)(?:Basis\s+for|Issue\s+Structure)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE | re.DOTALL)
            if match:
                objects_text = match.group(1)

                # Extract bullet points or numbered items
                items = re.findall(r'(?:[\u2022\u2023\u25cf\u25e6\u25aa\u25ab•●○]\s*|(?:\d+\.|\([a-z]\)|\([0-9]\))\s*)([^\n]+)', objects_text)
                if items:
                    objects = [self._clean_text(item) for item in items[:5]]
                else:
                    # Just get first few sentences
                    sentences = re.split(r'[.;]', objects_text)
                    objects = [self._clean_text(s) for s in sentences[:3] if len(s.strip()) > 20]
                break

        return objects if objects else ["Objects of issue not found"]

    def _extract_regulation_type(self) -> str:
        """Extract whether it's Regulation 6(1) or 6(2)"""
        if re.search(r'Regulation\s*6\s*\(\s*2\s*\)', self.text_content, re.IGNORECASE):
            return "6(2)"
        elif re.search(r'Regulation\s*6\s*\(\s*1\s*\)', self.text_content, re.IGNORECASE):
            return "6(1)"

        # Check for QIB allocation percentage (75% indicates 6(2))
        if re.search(r'(?:75|seventy.?five)\s*%?\s*.*?(?:QIB|Qualified\s+Institutional)', self.text_content, re.IGNORECASE):
            return "6(2)"

        return "Not determined"

    def _extract_issue_type(self) -> str:
        """Extract issue type (Fresh Issue, OFS, or both)"""
        has_fresh = bool(re.search(r'fresh\s+issue', self.text_content, re.IGNORECASE))
        has_ofs = bool(re.search(r'offer\s+for\s+sale|OFS', self.text_content, re.IGNORECASE))

        if has_fresh and has_ofs:
            return "Fresh Issue and Offer for Sale"
        elif has_fresh:
            return "Fresh Issue"
        elif has_ofs:
            return "Offer for Sale (OFS)"
        else:
            return "Issue type not determined"

    def _extract_issue_size(self) -> tuple:
        """Extract issue size for fresh issue and OFS"""
        fresh_size = ""
        ofs_size = ""

        # Fresh issue patterns
        fresh_patterns = [
            r'fresh\s+issue\s+(?:of\s+)?(?:up\s+to\s+)?(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(?:crore|million|lakh)',
            r'fresh\s+issue\s+(?:of\s+)?(?:up\s+to\s+)?([\d,\.]+)\s*(?:equity\s+)?shares',
        ]

        for pattern in fresh_patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE)
            if match:
                fresh_size = f"Up to {match.group(1)} {self._get_unit(match.group(0))}"
                break

        # OFS patterns
        ofs_patterns = [
            r'offer\s+for\s+sale\s+(?:of\s+)?(?:up\s+to\s+)?(?:₹|Rs\.?|INR)?\s*([\d,\.]+)\s*(?:crore|million|lakh)',
            r'offer\s+for\s+sale\s+(?:of\s+)?(?:up\s+to\s+)?([\d,\.]+)\s*(?:equity\s+)?shares',
            r'OFS\s+(?:of\s+)?(?:up\s+to\s+)?([\d,\.]+)',
        ]

        for pattern in ofs_patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE)
            if match:
                ofs_size = f"Up to {match.group(1)} {self._get_unit(match.group(0))}"
                break

        return fresh_size or "N/A", ofs_size or "N/A"

    def _get_unit(self, text: str) -> str:
        """Determine the unit from text"""
        text_lower = text.lower()
        if 'crore' in text_lower:
            return 'crore'
        elif 'million' in text_lower:
            return 'million'
        elif 'lakh' in text_lower:
            return 'lakh'
        elif 'share' in text_lower:
            return 'Equity Shares'
        return ''

    def _extract_selling_shareholders(self) -> List[Dict[str, str]]:
        """Extract selling shareholders details"""
        shareholders = []

        # Find the selling shareholders section
        section_pattern = r'(?:Selling|Promoter)\s+Shareholders?(.{500,3000}?)(?:Objects\s+of|Public\s+Issue|Book\s+Running)'
        section_match = re.search(section_pattern, self.text_content, re.IGNORECASE | re.DOTALL)

        if section_match:
            section_text = section_match.group(1)

            # Extract individual shareholders
            shareholder_pattern = r'([A-Z][A-Za-z\s\.]+(?:Holdings?|Ventures?|Capital|Limited|LLP|LLC)?)\s*[-–:]\s*([\d,\.]+)\s*(?:Equity\s+)?Shares?'
            matches = re.findall(shareholder_pattern, section_text, re.IGNORECASE)

            for name, shares in matches[:10]:  # Limit to 10 shareholders
                shareholders.append({
                    "name": self._clean_text(name),
                    "shares": shares.strip()
                })

        return shareholders if shareholders else [{"name": "Selling shareholders not found", "shares": "N/A"}]

    def _extract_revenue(self) -> tuple:
        """Extract revenue from operations"""
        latest_q = current_fy = previous_fy = "N/A"

        # Look for financial summary section
        patterns = [
            r'Revenue\s+from\s+[Oo]perations?\s*[\n:]+(.{100,1000}?)(?:Other\s+Income|Total\s+Income|Profit)',
            r'(?:Total\s+)?Revenue[:\s]+(?:₹|Rs\.?)?\s*([\d,\.]+)\s*(?:crore|million)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE | re.DOTALL)
            if match:
                numbers = re.findall(r'(?:₹|Rs\.?)?\s*([\d,]+\.?\d*)\s*(?:crore|million|lakh)?', match.group(1))
                if len(numbers) >= 3:
                    latest_q = f"₹ {numbers[0]} million"
                    current_fy = f"₹ {numbers[1]} million"
                    previous_fy = f"₹ {numbers[2]} million"
                elif len(numbers) >= 1:
                    current_fy = f"₹ {numbers[0]} million"
                break

        return latest_q, current_fy, previous_fy

    def _extract_pat(self) -> tuple:
        """Extract Profit/Loss After Tax"""
        latest_q = current_fy = previous_fy = "N/A"

        patterns = [
            r'(?:Profit|Loss)\s*(?:/\s*(?:Profit|Loss))?\s+[Aa]fter\s+[Tt]ax\s*[\n:]+(.{100,500}?)(?:Earnings|Basic|Diluted)',
            r'(?:Net\s+)?(?:Profit|Loss)\s+for\s+the\s+(?:year|period)[:\s]+(?:₹|Rs\.?)?\s*([\d,\.]+)',
            r'PAT[:\s]+(?:₹|Rs\.?)?\s*([\d,\.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE | re.DOTALL)
            if match:
                numbers = re.findall(r'(?:₹|Rs\.?)?\s*\(?([\d,]+\.?\d*)\)?', match.group(1) if len(match.groups()) > 0 else match.group(0))
                if len(numbers) >= 3:
                    latest_q = f"₹ {numbers[0]} million"
                    current_fy = f"₹ {numbers[1]} million"
                    previous_fy = f"₹ {numbers[2]} million"
                elif len(numbers) >= 1:
                    current_fy = f"₹ {numbers[0]} million"
                break

        return latest_q, current_fy, previous_fy

    def _extract_brlms(self) -> List[str]:
        """Extract Book Running Lead Managers"""
        brlms = []

        patterns = [
            r'BOOK\s+RUNNING\s+LEAD\s+MANAGERS?(.{200,2000}?)(?:REGISTRAR|SYNDICATE)',
            r'BRLMs?[:\s]+(.{100,1000}?)(?:Registrar|Legal)',
            r'Lead\s+Managers?[:\s]+(.{100,1000}?)(?:Registrar)',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE | re.DOTALL)
            if match:
                section = match.group(1)

                # Extract company names (typically end with Limited, Ltd, etc.)
                names = re.findall(r'([A-Z][A-Za-z\s&]+(?:Limited|Ltd|LLP|LLC|Co\.|Company|Capital|Securities|Advisors?))', section)
                brlms = list(set([self._clean_text(name) for name in names]))[:10]
                break

        return brlms if brlms else ["BRLMs not found"]

    def _extract_registrar(self) -> str:
        """Extract Registrar to the Issue"""
        patterns = [
            r'REGISTRAR\s+TO\s+THE\s+(?:ISSUE|OFFER)[:\s]+([A-Z][A-Za-z\s&]+(?:Limited|Ltd))',
            r'Registrar[:\s]+([A-Z][A-Za-z\s&]+(?:Limited|Ltd))',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.text_content, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))

        return "Registrar not found"

    def _extract_exchanges(self) -> str:
        """Extract listing exchanges"""
        if re.search(r'BSE\s+and\s+NSE|NSE\s+and\s+BSE', self.text_content, re.IGNORECASE):
            return "BSE and NSE"
        elif re.search(r'\bBSE\b', self.text_content):
            return "BSE"
        elif re.search(r'\bNSE\b', self.text_content):
            return "NSE"

        return "Exchanges not found"

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Remove common artifacts
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        return text


def main():
    """Test the parser"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python drhp_parser.py <path_to_drhp.pdf>")
        return

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    parser = DRHPParser(pdf_path)
    data = parser.parse()

    print("\n" + "="*60)
    print("EXTRACTED DRHP DATA")
    print("="*60)

    print(f"\nCompany: {data.company_name}")
    print(f"Business Model: {data.business_model[:200]}...")
    print(f"Regulation: {data.regulation_type}")
    print(f"Issue Type: {data.issue_type}")
    print(f"Fresh Issue: {data.fresh_issue_size}")
    print(f"OFS: {data.ofs_size}")
    print(f"\nObjects of Issue:")
    for i, obj in enumerate(data.objects_of_issue, 1):
        print(f"  {i}. {obj}")
    print(f"\nBRLMs: {', '.join(data.brlms)}")


if __name__ == "__main__":
    main()
