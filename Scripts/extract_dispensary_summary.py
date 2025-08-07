import fitz  # PyMuPDF
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import json

def extract_pharmacy_and_date(pdf_path: str) -> tuple[str, str]:
    """
    Extract pharmacy name and date from the PDF
    Returns tuple of (pharmacy_name, date_string)
    """
    doc = fitz.open(pdf_path)
    text = doc[0].get_text().upper()  # Get first page text
    doc.close()
    
    # Extract pharmacy name
    pharmacy_name = "UNKNOWN"
    if "REITZ" in text:
        pharmacy_name = "REITZ"
    elif "WINTERTON" in text or "TLC" in text:
        pharmacy_name = "TLC WINTERTON"
    
    # Extract date
    date_patterns = [
        r'from:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+to:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s*-\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'range.*from:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+to:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'period.*from:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+to:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'date from\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+date to\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})'
    ]
    
    date_str = None
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Use the end date (last 3 values)
            if len(match.groups()) == 6:
                year, month, day = match.group(4), match.group(5), match.group(6)
            else:
                year, month, day = match.group(1), match.group(2), match.group(3)
            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            break
    
    return pharmacy_name, date_str

def extract_dispensary_summary_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract dispensary summary data from a PDF file
    
    Returns a dictionary with:
    - script_total: Total number of scripts
    - disp_turnover: Dispensary turnover (excluding VAT)
    - avg_script_value: Average script value
    """
    
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    text = text.upper()
    doc.close()
    
    # Extract script total from "NUMBER OF DOCUMENTS DISPENSED" section
    # Look for the TOTAL value in the detailed dispensing statistics
    script_total = None
    
    # Pattern to find the total number of documents dispensed
    script_patterns = [
        r'NUMBER OF DOCUMENTS - DISPENSED.*?(\d+)\s*$',
        r'NUMBER OF DOCUMENTS - DISPENSED.*?TOTAL\s+(\d+)',
        r'DOCTOR.*?TOTAL\s+(\d+).*?PAT/OTC.*?TOTAL\s+(\d+).*?TOTAL\s+(\d+)'
    ]
    
    for pattern in script_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            if len(match.groups()) == 1:
                script_total = int(match.group(1))
            elif len(match.groups()) == 4:
                # If we have doctor + pat/otc + overall total, use the overall total
                script_total = int(match.group(4))
            break
    
    # If regex didn't work, try a simpler approach
    if script_total is None:
        lines = text.split('\n')
        for line in lines:
            if 'NUMBER OF DOCUMENTS - DISPENSED' in line:
                # Split the line and get the last number
                parts = line.split()
                for part in reversed(parts):
                    if part.isdigit():
                        script_total = int(part)
                        break
                break
    

    
    # Extract total revenue from "TOTAL REVENUE" section
    disp_turnover_including_vat = None
    
    # Pattern to find total revenue
    revenue_patterns = [
        r'TOTAL REVENUE\s+([\d,]+\.?\d*)',
        r'TOTAL REVENUE.*?GROSS INCOME\s+([\d,]+\.?\d*)',
        r'TOTAL REVENUE.*?NETT INCOME\s+([\d,]+\.?\d*)'
    ]
    
    for pattern in revenue_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # Remove commas and convert to float
            revenue_str = match.group(1).replace(',', '')
            disp_turnover_including_vat = float(revenue_str)
            break
    
    # Calculate excluding VAT (divide by 1.15)
    disp_turnover_excluding_vat = None
    if disp_turnover_including_vat:
        disp_turnover_excluding_vat = disp_turnover_including_vat / 1.15
    
    # Calculate average script value
    avg_script_value = None
    if script_total and disp_turnover_excluding_vat and script_total > 0:
        avg_script_value = disp_turnover_excluding_vat / script_total
    
    return {
        "script_total": script_total,
        "disp_turnover_including_vat": disp_turnover_including_vat,
        "disp_turnover_excluding_vat": disp_turnover_excluding_vat,
        "avg_script_value": avg_script_value
    }

def format_currency(amount: float) -> str:
    """Format amount as currency with commas"""
    if amount is None:
        return "N/A"
    elif amount < 0:
        return f"-R{abs(amount):,.2f}"
    else:
        return f"R{amount:,.2f}"

def process_all_dispensary_summaries(base_dir: str = "../temp_classified_pdfs"):
    """
    Process all dispensary summary files in the classified PDFs directory
    """
    import json
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"Directory not found: {base_path}")
        return

    dispensary_files = list(base_path.rglob("dispensary_summary_*.pdf"))

    if not dispensary_files:
        print("No dispensary summary files found")
        return

    print(f"Found {len(dispensary_files)} dispensary summary files")

    all_data = []

    for pdf_file in dispensary_files:
        pharmacy_name, date_str = extract_pharmacy_and_date(str(pdf_file))
        dispensary_data = extract_dispensary_summary_data(str(pdf_file))

        complete_data = {
            'file': pdf_file.name,
            'pharmacy': pharmacy_name,
            'date': date_str,
            **dispensary_data
        }
        all_data.append(complete_data)

    output_file = Path("dispensary_summary_extracted_data.json")
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)

if __name__ == "__main__":
    process_all_dispensary_summaries() 