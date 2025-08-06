import os
import shutil
from pathlib import Path
import fitz  # PyMuPDF
import re
from datetime import datetime

# Define keywords for each report type (copied from Differntiator.py)
REPORT_KEYWORDS = {
    "turnover_summary": ["TOTAL TURNOVER", "GP %", "BASKET VALUE", "TRANSACTIONS"],
    "gross_profit_report": ["GROSS PROFIT", "STOCK CODE", "SALES QTY", "DEPT"],
    "trading_summary": ["OPENING STOCK", "CLOSING STOCK", "PURCHASES", "ADJUSTMENTS"],
    "dispensary_summary": ["SCRIPT STATISTICS", "CLAIMABLE SCRIPTS", "PRIVATE SCRIPTS", "DOCTOR SCRIPT"],
    "transaction_summary": ["INVOICING AUDIT TRAIL"]
}

# Define known pharmacy names
KNOWN_PHARMACIES = ["REITZ", "TLC WINTERTON"]

def extract_pharmacy_name(text):
    """
    Extract pharmacy name from the text
    """
    text_upper = text.upper()
    
    # Look for known pharmacy names (check for partial matches too)
    for pharmacy in KNOWN_PHARMACIES:
        if pharmacy in text_upper:
            return pharmacy
    
    # Special handling for TLC WINTERTON variations
    if "TLC" in text_upper and "WINTERTON" in text_upper:
        return "TLC WINTERTON"
    elif "WINTERTON" in text_upper or "WINTERTO" in text_upper:
        return "TLC WINTERTON"  # Assume it's TLC WINTERTON if WINTERTON or WINTERTO is found
    
    # If no known pharmacy found, try to extract from common patterns
    # Look for patterns like "PHARMACY: [NAME]" or similar
    pharmacy_patterns = [
        r'PHARMACY[:\s]+([A-Z\s]+)',
        r'STORE[:\s]+([A-Z\s]+)',
        r'BRANCH[:\s]+([A-Z\s]+)',
        r'LOCATION[:\s]+([A-Z\s]+)'
    ]
    
    for pattern in pharmacy_patterns:
        match = re.search(pattern, text_upper)
        if match:
            pharmacy_name = match.group(1).strip()
            if len(pharmacy_name) > 2:  # Avoid very short matches
                return pharmacy_name
    
    return "UNKNOWN_PHARMACY"

def extract_date(text):
    """
    Extract date from the text, prioritizing date ranges from reports
    """
    # First, look for date ranges in the format shown in the images
    # Patterns like "FROM: 2025/08/04 TO: 2025/08/04" or "2025/08/04 - 2025/08/04"
    date_range_patterns = [
        r'FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})\s*-\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'RANGE.*FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'PERIOD.*FROM:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+TO:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
        r'DATE FROM\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+DATE TO\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})'
    ]
    
    for pattern in date_range_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Take the last match - use the end date (last 3 values)
            match = matches[-1]
            try:
                if len(match) == 6:  # Full range pattern
                    # Use the end date (last 3 values)
                    year, month, day = match[3], match[4], match[5]
                else:
                    # Fallback to first 3 values
                    year, month, day = match[0], match[1], match[2]
                
                # Format as YYYY-MM-DD
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                continue
    
    # If no date range found, look for single dates in YYYY/MM/DD format
    single_date_patterns = [
        r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',    # YYYY-MM-DD
        r'(\d{1,2})\s+(\w{3})\s+(\d{4})',        # DD MMM YYYY
        r'(\w{3})\s+(\d{1,2})\s+(\d{4})'         # MMM DD YYYY
    ]
    
    for pattern in single_date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Take the last match (most recent/relevant)
            match = matches[-1]
            try:
                if len(match[0]) == 4:  # YYYY format
                    year, month, day = match
                elif len(match[2]) == 4:  # YYYY at end
                    day, month, year = match
                else:
                    # Assume DD/MM/YY format
                    day, month, year = match
                    if len(year) == 2:
                        year = '20' + year
                
                # Convert month name to number if needed
                if month.isalpha():
                    month_names = {
                        'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
                    }
                    month = month_names.get(month.upper(), '01')
                
                # Format as YYYY-MM-DD
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                continue
    
    # If no date found, try to extract from filename
    return None

def classify_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    
    # Extract text from the first 2 pages
    for i in range(min(2, len(doc))):
        text += doc[i].get_text().upper()

    # Determine report type by keyword matches
    scores = {}
    for report_type, keywords in REPORT_KEYWORDS.items():
        scores[report_type] = sum(1 for kw in keywords if kw in text)

    # Get report type with highest score
    best_match = max(scores, key=scores.get)
    if scores[best_match] == 0:
        return "unknown"
    
    return best_match

def classify_and_organize_pdfs():
    """
    Classify PDFs in the Test pdfs folder and save them with appropriate names in a temp folder
    """
    # Define paths
    test_pdfs_dir = Path("../Test pdfs")
    temp_dir = Path("../temp_classified_pdfs")
    
    # Create temp directory if it doesn't exist
    temp_dir.mkdir(exist_ok=True)
    
    # Get all PDF files in the test pdfs directory
    pdf_files = list(test_pdfs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the Test pdfs directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to classify:")
    
    # Classify each PDF and copy to temp directory with appropriate name
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        
        try:
            # Open PDF and extract text
            doc = fitz.open(str(pdf_file))
            text = ""
            for i in range(min(2, len(doc))):
                text += doc[i].get_text()
            doc.close()
            
            # Classify the PDF
            report_type = classify_pdf(str(pdf_file))
            print(f"  Detected report type: {report_type}")
            
            # Extract pharmacy name
            pharmacy_name = extract_pharmacy_name(text)
            print(f"  Detected pharmacy: {pharmacy_name}")
            
            # Extract date
            date_str = extract_date(text)
            if date_str:
                print(f"  Detected date: {date_str}")
            else:
                # Try to extract date from filename
                filename_date = re.search(r'(\d{8})', pdf_file.name)
                if filename_date:
                    date_str = filename_date.group(1)
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    print(f"  Extracted date from filename: {date_str}")
                else:
                    date_str = "UNKNOWN_DATE"
                    print(f"  No date found, using: {date_str}")
            
            # Create folder structure: temp_dir/date/pharmacy/
            date_folder = temp_dir / date_str
            pharmacy_folder = date_folder / pharmacy_name
            pharmacy_folder.mkdir(parents=True, exist_ok=True)
            
            # Create new filename based on classification
            new_filename = f"{report_type}_{pdf_file.name}"
            new_filepath = pharmacy_folder / new_filename
            
            # Copy the file to the appropriate folder
            shutil.copy2(pdf_file, new_filepath)
            print(f"  Saved as: {new_filepath}")
            
        except Exception as e:
            print(f"  Error processing {pdf_file.name}: {str(e)}")
    
    print(f"\nClassification complete! Files saved in: {temp_dir}")
    print("\nSummary of organized files:")
    
    # List all files in organized structure
    for date_folder in temp_dir.iterdir():
        if date_folder.is_dir() and date_folder.name != "__pycache__":
            print(f"\nDate: {date_folder.name}")
            for pharmacy_folder in date_folder.iterdir():
                if pharmacy_folder.is_dir():
                    print(f"  Pharmacy: {pharmacy_folder.name}")
                    for file in pharmacy_folder.glob("*.pdf"):
                        print(f"    - {file.name}")

if __name__ == "__main__":
    classify_and_organize_pdfs() 