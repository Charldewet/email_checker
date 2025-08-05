import fitz  # PyMuPDF
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import json

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

def format_currency(amount: float) -> str:
    """Format amount as currency with commas"""
    return f"R{amount:,.2f}" if amount is not None else "N/A"

def test_trading_extraction(base_dir: str = "../temp_classified_pdfs"):
    """
    Test trading summary extraction without database
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Directory not found: {base_path}")
        return
    
    # Find all trading summary files
    trading_files = list(base_path.rglob("trading_summary_*.pdf"))
    
    if not trading_files:
        print("No trading summary files found")
        return
    
    print(f"=== TRADING SUMMARY DATA EXTRACTION TEST ===")
    print(f"Found {len(trading_files)} trading summary files\n")
    
    all_data = []
    
    for pdf_file in trading_files:
        print(f"📄 Processing: {pdf_file.name}")
        
        # Extract pharmacy and date
        pharmacy_name, date_str = extract_pharmacy_and_date(str(pdf_file))
        
        # Extract trading data
        trading_data = extract_trading_summary_data(str(pdf_file))
        
        # Combine all data
        complete_data = {
            'file': pdf_file.name,
            'pharmacy': pharmacy_name,
            'date': date_str,
            **trading_data
        }
        
        all_data.append(complete_data)
        
        # Display formatted results
        print(f"   🏪 Pharmacy: {pharmacy_name}")
        print(f"   📅 Date: {date_str}")
        print(f"   💰 Financial Summary:")
        print(f"      • Turnover (Sales):     {format_currency(trading_data.get('turnover'))}")
        print(f"      • Opening Stock:        {format_currency(trading_data.get('stock_opening'))}")
        print(f"      • Closing Stock:        {format_currency(trading_data.get('stock_closing'))}")
        print(f"      • Purchases:            {format_currency(trading_data.get('purchases'))}")
        print(f"      • Adjustments:          {format_currency(trading_data.get('adjustments'))}")
        print(f"      • Cost of Sales:        {format_currency(trading_data.get('cost_of_sales'))}")
        print(f"      • Gross Profit:         {format_currency(trading_data.get('gp_value'))}")
        print(f"      • GP Percentage:        {trading_data.get('gp_percent', 'N/A')}%")
        print(f"   " + "="*50)
        print()
    
    # Save extracted data to JSON file for reference
    output_file = Path("trading_summary_extracted_data.json")
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    
    print(f"📊 Extracted data saved to: {output_file}")
    print(f"✅ Successfully processed {len(trading_files)} trading summary files")

if __name__ == "__main__":
    test_trading_extraction() 