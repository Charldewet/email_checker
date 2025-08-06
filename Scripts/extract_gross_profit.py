import fitz  # PyMuPDF
import re
import pandas as pd
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

def map_department_code(detailed_code: str) -> str:
    """
    Map a 6-character department code to the main 4-character department code
    Examples: BAAC01 -> BAAC, BAAF03 -> BAAF, BBBO02 -> BBBO
    """
    if len(detailed_code) >= 4:
        return detailed_code[:4]
    return detailed_code

def extract_gross_profit_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extract gross profit report data from a PDF file
    
    Returns a dictionary with the extracted data:
    - sales_details: List of sales records with stock codes, descriptions, quantities, values, etc.
    - summary_stats: Summary statistics
    """
    
    doc = fitz.open(pdf_path)
    
    # Step 1: Clean raw lines by removing headers, footers, and subtotal blocks
    cleaned_lines = []
    header_keywords = [
        "REITZ APTEEK", "TLC PHARMACY", "WINTERTON", "PAGE:", "CODE", "DESCRIPTION", "ON HAND", 
        "SALES", "COST", "GROSS", "TURNOVER", "GP%", "QTY", "VALUE", "GROSS PROFIT REPORT"
    ]
    exclusion_keywords = ["MAIN-DEPT", "SUB-DEPT", "TOTAL", "-------", "===", "***"]
    
    for page in doc:
        lines = page.get_text().split("\n")
        for line in lines:
            # Skip header lines
            if any(keyword in line.upper() for keyword in header_keywords):
                continue
            # Skip exclusion lines
            if any(keyword in line.upper() for keyword in exclusion_keywords):
                continue
            # Skip empty or separator lines
            if set(line.strip()) <= {"-", " ", "=", "*"}:
                continue
            # Skip lines that are too short to be data
            if len(line.strip()) < 20:
                continue
            cleaned_lines.append(line.strip())
    
    doc.close()
    
    # Step 2: Define regex pattern to extract structured sales data
    # Pattern for gross profit report lines
    pattern = re.compile(
        r"^([A-Z0-9]{6})\s+([A-Z0-9\-]{4,})\s+(.*?)\s+"
        r"(-?\d+\.\d{3})\s+(-?\d+\.\d{3})\s+(-?\d+\.\d{2})\s+"
        r"(-?\d+\.\d{2})\s+(-?\d+\.\d{2})\s+(-?\d+\.\d{3})\s+(-?\d+\.\d{3})$"
    )
    
    # Alternative pattern for different formatting
    pattern2 = re.compile(
        r"^([A-Z0-9]{6})\s+([A-Z0-9\-]{4,})\s+(.*?)\s+"
        r"(-?\d+\.\d{3})\s+(-?\d+\.\d{3})\s+(-?\d+\.\d{2})\s+"
        r"(-?\d+\.\d{2})\s+(-?\d+\.\d{2})\s+(-?\d+\.\d{3})$"
    )
    
    # Step 3: Extract matched values
    records = []
    for line in cleaned_lines:
        match = pattern.match(line)
        if match:
            dept, stock_code, desc, on_hand, sales_qty, sales_val, sales_cost, gp_val, turnover_pct, gp_pct = match.groups()
            # Map the detailed department code to main department code
            main_dept_code = map_department_code(dept.strip())
            records.append({
                "department_code": main_dept_code,  # Use mapped 4-character code
                "original_department_code": dept.strip(),  # Keep original for reference
                "stock_code": stock_code.strip(),
                "description": desc.strip(),
                "soh": float(on_hand),  # Stock on Hand
                "sales_qty": float(sales_qty),
                "sales_value": float(sales_val),
                "sales_cost": float(sales_cost),
                "gross_profit": float(gp_val),
                "turnover_percent": float(turnover_pct),
                "gross_profit_percent": float(gp_pct)
            })
        else:
            # Try alternative pattern
            match2 = pattern2.match(line)
            if match2:
                dept, stock_code, desc, on_hand, sales_qty, sales_val, sales_cost, gp_val, gp_pct = match2.groups()
                # Map the detailed department code to main department code
                main_dept_code = map_department_code(dept.strip())
                records.append({
                    "department_code": main_dept_code,  # Use mapped 4-character code
                    "original_department_code": dept.strip(),  # Keep original for reference
                    "stock_code": stock_code.strip(),
                    "description": desc.strip(),
                    "soh": float(on_hand),
                    "sales_qty": float(sales_qty),
                    "sales_value": float(sales_val),
                    "sales_cost": float(sales_cost),
                    "gross_profit": float(gp_val),
                    "turnover_percent": None,
                    "gross_profit_percent": float(gp_pct)
                })
    
    # Step 4: Calculate summary statistics
    summary_stats = {
        "total_records": len(records),
        "total_sales_value": sum(record["sales_value"] for record in records),
        "total_sales_cost": sum(record["sales_cost"] for record in records),
        "total_gross_profit": sum(record["gross_profit"] for record in records),
        "total_sales_qty": sum(record["sales_qty"] for record in records),
        "total_soh": sum(record["soh"] for record in records)
    }
    
    if summary_stats["total_sales_value"] > 0:
        summary_stats["overall_gp_percent"] = (summary_stats["total_gross_profit"] / summary_stats["total_sales_value"]) * 100
    else:
        summary_stats["overall_gp_percent"] = 0
    
    return {
        "sales_details": records,
        "summary_stats": summary_stats
    }

def format_currency(amount: float) -> str:
    """Format amount as currency with commas"""
    if amount is None:
        return "N/A"
    elif amount < 0:
        return f"-R{abs(amount):,.2f}"
    else:
        return f"R{amount:,.2f}"

def process_all_gross_profit_reports(base_dir: str = "../temp_classified_pdfs"):
    """
    Process all gross profit report files in the classified PDFs directory
    """
    import json
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"Directory not found: {base_path}")
        return

    gross_profit_files = list(base_path.rglob("gross_profit_report_*.pdf"))

    if not gross_profit_files:
        print("No gross profit report files found")
        return
    
    print(f"Found {len(gross_profit_files)} gross profit report files")

    all_data = []

    for pdf_file in gross_profit_files:
        pharmacy_name, date_str = extract_pharmacy_and_date(str(pdf_file))
        gross_profit_data = extract_gross_profit_data(str(pdf_file))

        complete_data = {
            'file': pdf_file.name,
            'pharmacy': pharmacy_name,
            'date': date_str,
            **gross_profit_data
        }
        all_data.append(complete_data)

    output_file = Path("gross_profit_extracted_data.json")
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)

if __name__ == "__main__":
    process_all_gross_profit_reports() 