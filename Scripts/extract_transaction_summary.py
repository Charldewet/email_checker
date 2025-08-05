import fitz  # PyMuPDF
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import json

def extract_turnover_from_turnover_summary(pharmacy_name: str, date_str: str, base_dir: str = "../temp_classified_pdfs") -> Optional[float]:
    """
    Extract turnover value from turnover summary report for the given pharmacy and date
    """
    base_path = Path(base_dir)
    
    # Look for turnover summary file for this pharmacy and date
    turnover_files = list(base_path.rglob(f"turnover_summary_*.pdf"))
    
    for pdf_file in turnover_files:
        # Check if this file is for the correct pharmacy and date
        doc = fitz.open(str(pdf_file))
        text = doc[0].get_text().upper()
        doc.close()
        
        # Check pharmacy
        if pharmacy_name == "REITZ" and "REITZ" not in text:
            continue
        if pharmacy_name == "TLC WINTERTON" and ("WINTERTON" not in text and "TLC" not in text):
            continue
            
        # Check date
        date_patterns = [
            r'FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})\s*-\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'RANGE.*FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'PERIOD.*FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'DATE FROM\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+DATE TO\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})'
        ]
        
        file_date = None
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 6:
                    year, month, day = match.group(4), match.group(5), match.group(6)
                else:
                    year, month, day = match.group(1), match.group(2), match.group(3)
                file_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                break
        
        if file_date == date_str:
            # Extract turnover from this file
            doc = fitz.open(str(pdf_file))
            text = doc[0].get_text()
            doc.close()
            
            # Look for TOTAL TURNOVER line with 3rd number (Nett Exclusive)
            turnover_pattern = r'\*\*\s*TOTAL TURNOVER\s+(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2}[-]?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
            match = re.search(turnover_pattern, text, re.IGNORECASE)
            
            if match:
                try:
                    turnover_str = match.group(3).replace(',', '')
                    return float(turnover_str)
                except ValueError:
                    continue
    
    return None

def extract_transaction_summary_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract transaction summary data from a PDF file
    
    Returns a dictionary with the extracted data:
    - transactions_total: Total transaction count (sum of all Accno values, excluding PAID OUT)
    - transaction_breakdown: Breakdown by transaction type (excluding PAID OUT)
    - avg_basket_value: Calculated average basket value (turnover / transactions)
    """
    
    doc = fitz.open(pdf_path)
    text = ""
    
    # Extract text from all pages
    for page_num in range(len(doc)):
        text += doc[page_num].get_text()
    
    doc.close()
    
    # Initialize result dictionary
    result = {
        'transactions_total': 0,
        'transaction_breakdown': {},
        'avg_basket_value': None
    }
    
    # Split text into lines and process each line
    lines = text.split('\n')
    total_transactions = 0
    
    for line in lines:
        # Look for lines that contain transaction data
        # Pattern: DOCKET TYPE followed by numbers in the Accno column
        # We're looking for lines that have a docket type and a number in the Accno position
        
        # Common docket types to look for (excluding PAID OUT)
        docket_types = [
            'CASH SALE', 'C.O.D SALE', 'INVOICE', 'CASH REFUND', 
            'CREDIT NOTE', 'RECEIPT', 'RECEIPT COD',
            'SCRIPT', 'SCRIPT REFUND', 'MEDICAL AIDS', 'LEVY DEBITS',
            'LEVY CREDITS'
        ]
        
        for docket_type in docket_types:
            if docket_type in line.upper():
                # Try to extract the Accno value (transaction count)
                # The Accno is typically a number in the 3rd or 4th column
                # Pattern: look for a number after the docket type
                accno_pattern = rf'{docket_type}.*?(\d+)'
                match = re.search(accno_pattern, line, re.IGNORECASE)
                
                if match:
                    try:
                        accno_value = int(match.group(1))
                        total_transactions += accno_value
                        
                        # Store breakdown by docket type
                        if docket_type not in result['transaction_breakdown']:
                            result['transaction_breakdown'][docket_type] = 0
                        result['transaction_breakdown'][docket_type] += accno_value
                        
                        print(f"  Found {docket_type}: {accno_value} transactions")
                    except ValueError:
                        continue
                break
    
    result['transactions_total'] = total_transactions
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
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s*-\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'RANGE.*FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'PERIOD.*FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'DATE FROM\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+DATE TO\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})'
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

def test_transaction_extraction(base_dir: str = "../temp_classified_pdfs"):
    """
    Test transaction summary extraction
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Directory not found: {base_path}")
        return
    
    # Find all transaction summary files
    transaction_files = list(base_path.rglob("transaction_summary_*.pdf"))
    
    if not transaction_files:
        print("No transaction summary files found")
        return
    
    print(f"=== TRANSACTION SUMMARY DATA EXTRACTION TEST ===")
    print(f"Found {len(transaction_files)} transaction summary files\n")
    
    all_data = []
    
    for pdf_file in transaction_files:
        print(f"📄 Processing: {pdf_file.name}")
        
        # Extract pharmacy and date
        pharmacy_name, date_str = extract_pharmacy_and_date(str(pdf_file))
        
        # Extract transaction data
        transaction_data = extract_transaction_summary_data(str(pdf_file))
        
        # Get turnover from turnover summary report
        turnover = extract_turnover_from_turnover_summary(pharmacy_name, date_str, base_dir)
        
        # Calculate average basket value
        if turnover and transaction_data['transactions_total'] > 0:
            avg_basket_value = turnover / transaction_data['transactions_total']
            transaction_data['avg_basket_value'] = avg_basket_value
            transaction_data['turnover'] = turnover
            print(f"  📊 Turnover: {format_currency(turnover)}")
            print(f"  📊 Avg Basket Value: {format_currency(avg_basket_value)}")
        else:
            print(f"  ⚠️  Could not calculate avg basket value (turnover: {format_currency(turnover)}, transactions: {transaction_data['transactions_total']})")
        
        # Combine all data
        complete_data = {
            'file': pdf_file.name,
            'pharmacy': pharmacy_name,
            'date': date_str,
            **transaction_data
        }
        
        all_data.append(complete_data)
        
        # Display formatted results
        print(f"   🏪 Pharmacy: {pharmacy_name}")
        print(f"   📅 Date: {date_str}")
        print(f"   📊 Transaction Summary:")
        print(f"      • Total Transactions: {transaction_data.get('transactions_total', 0)}")
        print(f"   📋 Transaction Breakdown:")
        
        breakdown = transaction_data.get('transaction_breakdown', {})
        if breakdown:
            for docket_type, count in breakdown.items():
                print(f"      • {docket_type}: {count}")
        else:
            print(f"      • No transaction breakdown found")
        
        print(f"   " + "="*50)
        print()
    
    # Save extracted data to JSON file for reference
    output_file = Path("transaction_summary_extracted_data.json")
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    
    print(f"📊 Extracted data saved to: {output_file}")
    print(f"✅ Successfully processed {len(transaction_files)} transaction summary files")

if __name__ == "__main__":
    test_transaction_extraction() 