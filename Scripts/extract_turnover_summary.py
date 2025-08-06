import fitz  # PyMuPDF
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import json

def extract_turnover_summary_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract turnover summary data from a PDF file
    
    Returns a dictionary with the extracted data that matches the database schema:
    - turnover: Total turnover (Nett Exclusive) - This will override trading summary turnover
    - sales_cash: Cash sales (Nett Exclusive)
    - sales_account: Account sales (Nett Exclusive)  
    - sales_cod: COD sales (Nett Exclusive)
    """
    
    doc = fitz.open(pdf_path)
    text = ""
    
    # Extract text from all pages
    for page_num in range(len(doc)):
        text += doc[page_num].get_text()
    
    doc.close()
    
    # Initialize result dictionary
    result = {
        'turnover': None,
        'sales_cash': None,
        'sales_account': None,
        'sales_cod': None
    }
    
    # Define regex patterns for each field (focusing on Nett Excl column - 3rd number)
    # Format: Gross + Disc = Nett + VAT = Nett Count Average
    #         [1st]  [2nd]  [3rd] [4th]  [5th] [6th] [7th]
    patterns = {
        'turnover': [
            # Match TOTAL TURNOVER line with 3rd number (Nett Exclusive)
            r'\*\*\s*TOTAL TURNOVER\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2}[-]?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'TURNOVER SUMMARY.*?(\d{1,3}(?:,\d{3})*\.\d{2})\s+Nett\s+\(Exclusive\)'
        ],
        'sales_cash': [
            # Match CASH TOTALS line with 3rd number (Nett Exclusive)
            r'\*\*\s*CASH TOTALS\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2}[-]?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'sales_account': [
            # Match STANDARD ACCOUNTS line with 3rd number (Nett Exclusive)
            r'\*\*\s*STANDARD ACCOUNTS\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2}[-]?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'sales_cod': [
            # Match C.O.D. ACCOUNTS line with 3rd number (Nett Exclusive)
            r'\*\*\s*C\.O\.D\.\s*ACCOUNTS\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2}[-]?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
        ]
    }
    
    # Extract each field using regex patterns
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if field == 'turnover' and len(match.groups()) == 1:
                        # Special case for TURNOVER SUMMARY line
                        value_str = match.group(1).replace(',', '')
                    else:
                        # Use the 3rd group (Nett Exclusive value)
                        value_str = match.group(3).replace(',', '')
                    
                    # Handle negative values
                    if '-' in value_str:
                        value_str = value_str.replace('-', '')
                        result[field] = -float(value_str)
                    else:
                        result[field] = float(value_str)
                    break  # Stop after first successful match for this field
                except (ValueError, IndexError):
                    continue
    
    return result

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
        r'FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s*-\s*(\d{4})/(\d{1,2})/(\d{1,2})'
    ]
    
    date_str = None
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            # Use the end date (last 3 values)
            if len(match.groups()) == 6:
                year, month, day = match.group(4), match.group(5), match.group(6)
            else:
                year, month, day = match.group(1), match.group(2), match.group(3)
            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            break
    
    return pharmacy_name, date_str

def format_currency(amount: float) -> str:
    """Format amount as currency with commas"""
    if amount is None:
        return "N/A"
    elif amount < 0:
        return f"-R{abs(amount):,.2f}"
    else:
        return f"R{amount:,.2f}"

def process_all_turnover_summaries(base_dir: str = "../temp_classified_pdfs"):
    """
    Process all turnover summary files in the classified PDFs directory
    """
    import json
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Directory not found: {base_path}")
        return
    
    # Find all turnover summary files
    turnover_files = list(base_path.rglob("turnover_summary_*.pdf"))
    
    if not turnover_files:
        print("No turnover summary files found")
        return
    
    print(f"Found {len(turnover_files)} turnover summary files")
    
    all_data = []
    
    for pdf_file in turnover_files:
        pharmacy_name, date_str = extract_pharmacy_and_date(str(pdf_file))
        turnover_data = extract_turnover_summary_data(str(pdf_file))
        
        complete_data = {
            'file': pdf_file.name,
            'pharmacy': pharmacy_name,
            'date': date_str,
            **turnover_data
        }
        all_data.append(complete_data)
    
    # Save extracted data to JSON file for the pipeline
    output_file = Path("turnover_summary_extracted_data.json")
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)

if __name__ == "__main__":
    process_all_turnover_summaries() 