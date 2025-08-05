import fitz  # PyMuPDF
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import sys
import os

# Add the parent directory to the path to import database_connection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_connection import PharmacyDatabase

def extract_trading_summary_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract trading summary data from a PDF file
    
    Returns a dictionary with the extracted data that matches the database schema:
    - stock_opening: Opening stock value
    - stock_closing: Closing stock value  
    - purchases: Purchases value
    - adjustments: Adjustments value
    - cost_of_sales: Cost of sales value
    - gp_value: Gross profit value
    - gp_percent: Gross profit percentage
    - turnover: Sales/turnover value
    """
    
    doc = fitz.open(pdf_path)
    text = ""
    
    # Extract text from all pages
    for page_num in range(len(doc)):
        text += doc[page_num].get_text()
    
    doc.close()
    
    # Initialize result dictionary
    result = {
        'stock_opening': None,
        'stock_closing': None,
        'purchases': None,
        'adjustments': None,
        'cost_of_sales': None,
        'gp_value': None,
        'gp_percent': None,
        'turnover': None
    }
    
    # Define regex patterns for each field
    patterns = {
        'turnover': [
            r'SALES.*?RETAIL.*?(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'SALES.*?STKTRN.*?(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'stock_opening': [
            r'OPENING STOCK.*?(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'OPENING STOCK.*?START DATE.*?(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'purchases': [
            r'PURCHASES.*?(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'\+\s*PURCHASES.*?(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'adjustments': [
            r'ADJUSTMENTS.*?(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'\+\s*ADJUSTMENTS.*?(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'stock_closing': [
            r'CLOSING STOCK.*?(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'CLOSING STOCK.*?END DATE.*?(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'cost_of_sales': [
            r'COST OF SALES.*?(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'COST OF GOODS SOLD.*?(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'gp_value': [
            r'GROSS PROFIT FROM TRADING.*?(\d{1,3}(?:,\d{3})*\.\d{2})',
            r'= GROSS PROFIT FROM TRADING.*?(\d{1,3}(?:,\d{3})*\.\d{2})'
        ],
        'gp_percent': [
            r'GROSS PROFIT AS A PERCENTAGE.*?=\s*(\d+\.\d{2})',
            r'PERCENTAGE OF RETAIL SALES.*?=\s*(\d+\.\d{2})'
        ]
    }
    
    # Extract each field using regex patterns
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    value_str = match.group(1).replace(',', '')
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

def process_trading_summary_file(pdf_path: str, db: PharmacyDatabase) -> bool:
    """
    Process a single trading summary PDF file and insert data into database
    """
    try:
        print(f"Processing: {pdf_path}")
        
        # Extract pharmacy and date
        pharmacy_name, date_str = extract_pharmacy_and_date(pdf_path)
        print(f"  Pharmacy: {pharmacy_name}")
        print(f"  Date: {date_str}")
        
        if not date_str:
            print("  Error: Could not extract date")
            return False
        
        # Extract trading data
        trading_data = extract_trading_summary_data(pdf_path)
        print(f"  Extracted data: {trading_data}")
        
        # Convert date string to date object
        report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Insert or update pharmacy
        pharmacy_id = db.insert_pharmacy(pharmacy_name, pharmacy_name)
        if not pharmacy_id:
            print(f"  Error: Could not insert/get pharmacy {pharmacy_name}")
            return False
        
        # Insert daily summary data (this will update existing record if it exists)
        success = db.insert_daily_summary(pharmacy_name, report_date, trading_data)
        
        if success:
            print(f"  ✅ Successfully inserted trading summary data")
            return True
        else:
            print(f"  ❌ Failed to insert trading summary data")
            return False
            
    except Exception as e:
        print(f"  Error processing {pdf_path}: {str(e)}")
        return False

def process_all_trading_summaries(base_dir: str = "../temp_classified_pdfs"):
    """
    Process all trading summary files in the classified PDFs directory
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Directory not found: {base_path}")
        return
    
    # Initialize database connection
    db = PharmacyDatabase()
    
    # Find all trading summary files
    trading_files = list(base_path.rglob("trading_summary_*.pdf"))
    
    if not trading_files:
        print("No trading summary files found")
        return
    
    print(f"Found {len(trading_files)} trading summary files")
    
    successful = 0
    failed = 0
    
    for pdf_file in trading_files:
        if process_trading_summary_file(str(pdf_file), db):
            successful += 1
        else:
            failed += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(trading_files)}")

if __name__ == "__main__":
    process_all_trading_summaries() 