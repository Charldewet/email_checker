import fitz  # PyMuPDF
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import json

# Import the extraction functions from our other scripts
from test_trading_extraction import extract_trading_summary_data, extract_pharmacy_and_date
from extract_turnover_summary import extract_turnover_summary_data

def format_currency(amount: float) -> str:
    """Format amount as currency with commas"""
    if amount is None:
        return "N/A"
    elif amount < 0:
        return f"-R{abs(amount):,.2f}"
    else:
        return f"R{amount:,.2f}"

def combine_report_data(base_dir: str = "../temp_classified_pdfs"):
    """
    Combine data from trading and turnover summary reports to show final database entries
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Directory not found: {base_path}")
        return
    
    # Find all report files
    trading_files = list(base_path.rglob("trading_summary_*.pdf"))
    turnover_files = list(base_path.rglob("turnover_summary_*.pdf"))
    
    print(f"=== COMBINED DATABASE DATA PREVIEW ===")
    print(f"Found {len(trading_files)} trading summary files")
    print(f"Found {len(turnover_files)} turnover summary files\n")
    
    # Group files by pharmacy and date
    combined_data = {}
    
    # Process trading summary files first (base data)
    for pdf_file in trading_files:
        pharmacy_name, date_str = extract_pharmacy_and_date(str(pdf_file))
        key = f"{pharmacy_name}_{date_str}"
        
        if key not in combined_data:
            combined_data[key] = {
                'pharmacy': pharmacy_name,
                'date': date_str,
                'source_files': []
            }
        
        # Extract trading data
        trading_data = extract_trading_summary_data(str(pdf_file))
        combined_data[key].update(trading_data)
        combined_data[key]['source_files'].append(f"Trading: {pdf_file.name}")
    
    # Process turnover summary files (override turnover and add payment method data)
    for pdf_file in turnover_files:
        pharmacy_name, date_str = extract_pharmacy_and_date(str(pdf_file))
        key = f"{pharmacy_name}_{date_str}"
        
        if key not in combined_data:
            combined_data[key] = {
                'pharmacy': pharmacy_name,
                'date': date_str,
                'source_files': []
            }
        
        # Extract turnover data
        turnover_data = extract_turnover_summary_data(str(pdf_file))
        
        # Override turnover value and add payment method data
        combined_data[key].update(turnover_data)
        combined_data[key]['source_files'].append(f"Turnover: {pdf_file.name}")
    
    # Display combined results
    for key, data in combined_data.items():
        print(f"🏪 {data['pharmacy']} - {data['date']}")
        print(f"   📁 Source Files: {', '.join(data['source_files'])}")
        print()
        
        print(f"   💰 Financial Summary:")
        print(f"      • Turnover (from Turnover Summary): {format_currency(data.get('turnover'))}")
        print(f"      • Cash Sales:                       {format_currency(data.get('sales_cash'))}")
        print(f"      • Account Sales:                    {format_currency(data.get('sales_account'))}")
        print(f"      • COD Sales:                        {format_currency(data.get('sales_cod'))}")
        print()
        
        print(f"   📊 Stock & Trading Data (from Trading Summary):")
        print(f"      • Opening Stock:                    {format_currency(data.get('stock_opening'))}")
        print(f"      • Closing Stock:                    {format_currency(data.get('stock_closing'))}")
        print(f"      • Purchases:                        {format_currency(data.get('purchases'))}")
        print(f"      • Adjustments:                      {format_currency(data.get('adjustments'))}")
        print(f"      • Cost of Sales:                    {format_currency(data.get('cost_of_sales'))}")
        print(f"      • Gross Profit:                     {format_currency(data.get('gp_value'))}")
        print(f"      • GP Percentage:                    {data.get('gp_percent', 'N/A')}%")
        print()
        
        print(f"   " + "="*60)
        print()
    
    # Save combined data to JSON
    output_file = Path("combined_database_data.json")
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=2, default=str)
    
    print(f"📊 Combined data saved to: {output_file}")
    
    # Show database table structure preview
    print(f"\n=== DATABASE TABLE PREVIEW ===")
    print(f"The following data will be inserted into the 'daily_summary' table:")
    print()
    
    for key, data in combined_data.items():
        print(f"INSERT INTO daily_summary (pharmacy_id, report_date, ...) VALUES (")
        print(f"  pharmacy_id_for_{data['pharmacy']},")
        print(f"  '{data['date']}',")
        print(f"  {data.get('turnover', 'NULL')},           -- turnover (from turnover summary)")
        print(f"  {data.get('gp_percent', 'NULL')},         -- gp_percent")
        print(f"  {data.get('gp_value', 'NULL')},           -- gp_value")
        print(f"  {data.get('cost_of_sales', 'NULL')},      -- cost_of_sales")
        print(f"  {data.get('purchases', 'NULL')},          -- purchases")
        print(f"  {data.get('stock_opening', 'NULL')},      -- stock_opening")
        print(f"  {data.get('stock_closing', 'NULL')},      -- stock_closing")
        print(f"  {data.get('adjustments', 'NULL')},        -- adjustments")
        print(f"  {data.get('sales_cash', 'NULL')},         -- sales_cash")
        print(f"  {data.get('sales_account', 'NULL')},      -- sales_account")
        print(f"  {data.get('sales_cod', 'NULL')}           -- sales_cod")
        print(f");")
        print()

if __name__ == "__main__":
    combine_report_data() 