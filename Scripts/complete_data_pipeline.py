#!/usr/bin/env python3
"""
Complete Pharmacy Data Pipeline
==============================

This script orchestrates the entire data extraction and database population process:
1. Classify and organize PDF reports
2. Extract data from all report types
3. Calculate derived metrics
4. Populate the database with complete daily summary data
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

def format_currency(amount: float) -> str:
    """Format amount as currency with commas"""
    if amount is None:
        return "N/A"
    elif amount < 0:
        return f"-R{abs(amount):,.2f}"
    else:
        return f"R{amount:,.2f}"

def load_json_data(filename: str) -> list:
    """Load data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  File not found: {filename}")
        return []

def calculate_basket_size(transactions_total: int, total_products_sold: float) -> float:
    """Calculate average basket size"""
    if transactions_total > 0:
        return round(total_products_sold / transactions_total, 2)
    return 0.0

def combine_all_data() -> Dict[str, Dict[str, Any]]:
    """
    Combine all extracted data into a comprehensive dataset
    Returns a dictionary keyed by (pharmacy, date) with all metrics
    """
    print("🔄 Combining all extracted data...")
    
    # Load all extracted data
    trading_data = load_json_data("trading_summary_extracted_data.json")
    turnover_data = load_json_data("turnover_summary_extracted_data.json")
    transaction_data = load_json_data("transaction_summary_extracted_data.json")
    gross_profit_data = load_json_data("gross_profit_extracted_data.json")
    dispensary_data = load_json_data("dispensary_summary_extracted_data.json")
    
    # Create combined dataset
    combined_data = {}
    
    # Process each data source
    for data_list, data_type in [
        (trading_data, "trading"),
        (turnover_data, "turnover"),
        (transaction_data, "transaction"),
        (gross_profit_data, "gross_profit"),
        (dispensary_data, "dispensary")
    ]:
        for item in data_list:
            pharmacy = item['pharmacy']
            date = item['date']
            key = (pharmacy, date)
            
            if key not in combined_data:
                combined_data[key] = {
                    'pharmacy': pharmacy,
                    'date': date,
                    'trading_summary': {},
                    'turnover_summary': {},
                    'transaction_summary': {},
                    'gross_profit_summary': {},
                    'dispensary_summary': {},
                    'calculated_metrics': {}
                }
            
            # Store the data
            if data_type == "trading":
                combined_data[key]['trading_summary'] = item
            elif data_type == "turnover":
                combined_data[key]['turnover_summary'] = item
            elif data_type == "transaction":
                combined_data[key]['transaction_summary'] = item
            elif data_type == "gross_profit":
                combined_data[key]['gross_profit_summary'] = item
            elif data_type == "dispensary":
                combined_data[key]['dispensary_summary'] = item
    
    # Calculate derived metrics for each pharmacy/date combination
    for key, data in combined_data.items():
        calculated = data['calculated_metrics']
        
        # Get data from different sources
        trading = data.get('trading_summary', {})
        turnover = data.get('turnover_summary', {})
        transaction = data.get('transaction_summary', {})
        gross_profit = data.get('gross_profit_summary', {})
        dispensary = data.get('dispensary_summary', {})
        
        # Calculate basket size
        transactions_total = transaction.get('transactions_total', 0)
        total_products_sold = gross_profit.get('summary_stats', {}).get('total_sales_qty', 0)
        calculated['avg_basket_size'] = calculate_basket_size(transactions_total, total_products_sold)
        
        # Use turnover from turnover summary (as requested)
        calculated['turnover'] = turnover.get('turnover', 0)
        
        # Get other metrics
        calculated['avg_basket_value'] = transaction.get('avg_basket_value', 0)
        calculated['transactions_total'] = transactions_total
        calculated['script_total'] = dispensary.get('script_total', 0)
        calculated['disp_turnover'] = dispensary.get('disp_turnover_excluding_vat', 0)
        calculated['avg_script_value'] = dispensary.get('avg_script_value', 0)
        
        # Stock metrics from trading summary
        calculated['stock_opening'] = trading.get('stock_opening', 0)
        calculated['stock_closing'] = trading.get('stock_closing', 0)
        calculated['purchases'] = trading.get('purchases', 0)
        calculated['adjustments'] = trading.get('adjustments', 0)
        calculated['cost_of_sales'] = trading.get('cost_of_sales', 0)
        calculated['gp_value'] = trading.get('gp_value', 0)
        calculated['gp_percent'] = trading.get('gp_percent', 0)
        
        # Payment methods from turnover summary
        calculated['sales_cash'] = turnover.get('sales_cash', 0)
        calculated['sales_account'] = turnover.get('sales_account', 0)
        calculated['sales_cod'] = turnover.get('sales_cod', 0)
    
    return combined_data

def display_complete_summary(combined_data: Dict[str, Dict[str, Any]]):
    """Display a complete summary of all extracted and calculated data"""
    print("\n" + "="*80)
    print("📊 COMPLETE DATA PIPELINE SUMMARY")
    print("="*80)
    
    for key, data in combined_data.items():
        pharmacy, date = key
        calculated = data['calculated_metrics']
        
        print(f"\n🏪 {pharmacy} - {date}")
        print("-" * 60)
        
        # Financial metrics
        print(f"💰 Financial Metrics:")
        print(f"   • Turnover: {format_currency(calculated['turnover'])}")
        print(f"   • Gross Profit: {format_currency(calculated['gp_value'])} ({calculated['gp_percent']:.2f}%)")
        print(f"   • Cost of Sales: {format_currency(calculated['cost_of_sales'])}")
        print(f"   • Purchases: {format_currency(calculated['purchases'])}")
        
        # Transaction metrics
        print(f"🛒 Transaction Metrics:")
        print(f"   • Total Transactions: {calculated['transactions_total']:,}")
        print(f"   • Average Basket Value: {format_currency(calculated['avg_basket_value'])}")
        print(f"   • Average Basket Size: {calculated['avg_basket_size']} items")
        
        # Script metrics
        print(f"💊 Script Metrics:")
        print(f"   • Total Scripts: {calculated['script_total']:,}")
        print(f"   • Dispensary Turnover: {format_currency(calculated['disp_turnover'])}")
        print(f"   • Average Script Value: {format_currency(calculated['avg_script_value'])}")
        
        # Stock metrics
        print(f"📦 Stock Metrics:")
        print(f"   • Opening Stock: {format_currency(calculated['stock_opening'])}")
        print(f"   • Closing Stock: {format_currency(calculated['stock_closing'])}")
        print(f"   • Adjustments: {format_currency(calculated['adjustments'])}")
        
        # Payment methods
        print(f"💳 Payment Methods:")
        print(f"   • Cash Sales: {format_currency(calculated['sales_cash'])}")
        print(f"   • Account Sales: {format_currency(calculated['sales_account'])}")
        print(f"   • COD Sales: {format_currency(calculated['sales_cod'])}")

def create_database_insert_statements(combined_data: Dict[str, Dict[str, Any]]) -> List[str]:
    """Create SQL INSERT statements for the database"""
    insert_statements = []
    
    for key, data in combined_data.items():
        pharmacy, date = key
        calculated = data['calculated_metrics']
        
        # Create INSERT statement
        sql = f"""
-- {pharmacy} - {date}
INSERT INTO daily_summary (
    pharmacy_id, report_date, turnover, gp_percent, gp_value, cost_of_sales, purchases,
    avg_basket_value, avg_basket_size, transactions_total, script_total, avg_script_value,
    disp_turnover, stock_opening, stock_closing, adjustments, sales_cash, sales_cod, sales_account
) VALUES (
    (SELECT id FROM pharmacies WHERE pharmacy_code = '{pharmacy}'),
    '{date}',
    {calculated['turnover']},
    {calculated['gp_percent']},
    {calculated['gp_value']},
    {calculated['cost_of_sales']},
    {calculated['purchases']},
    {calculated['avg_basket_value']},
    {calculated['avg_basket_size']},
    {calculated['transactions_total']},
    {calculated['script_total']},
    {calculated['avg_script_value']},
    {calculated['disp_turnover']},
    {calculated['stock_opening']},
    {calculated['stock_closing']},
    {calculated['adjustments']},
    {calculated['sales_cash']},
    {calculated['sales_cod']},
    {calculated['sales_account']}
) ON CONFLICT (pharmacy_id, report_date) DO UPDATE SET
    turnover = EXCLUDED.turnover,
    gp_percent = EXCLUDED.gp_percent,
    gp_value = EXCLUDED.gp_value,
    cost_of_sales = EXCLUDED.cost_of_sales,
    purchases = EXCLUDED.purchases,
    avg_basket_value = EXCLUDED.avg_basket_value,
    avg_basket_size = EXCLUDED.avg_basket_size,
    transactions_total = EXCLUDED.transactions_total,
    script_total = EXCLUDED.script_total,
    avg_script_value = EXCLUDED.avg_script_value,
    disp_turnover = EXCLUDED.disp_turnover,
    stock_opening = EXCLUDED.stock_opening,
    stock_closing = EXCLUDED.stock_closing,
    adjustments = EXCLUDED.adjustments,
    sales_cash = EXCLUDED.sales_cash,
    sales_cod = EXCLUDED.sales_cod,
    sales_account = EXCLUDED.sales_account;
"""
        insert_statements.append(sql)
    
    return insert_statements

def run_complete_pipeline(classified_pdfs_dir="temp_classified_pdfs"):
    """
    Main function to run the complete data pipeline
    """
    # Define the base directory for classified PDFs
    base_dir = Path(classified_pdfs_dir)

    print("\n" + "="*80)
    print("🚀 STARTING COMPLETE DATA PIPELINE")
    print("="*80)
    
    # --- Step 1: Run all data extractions from the classified files ---
    print("\n--- Step 1: Running all data extractions ---")
    
    # Trading Summary
    print("\nExtracting Trading Summary data...")
    from extract_trading_summary import process_all_trading_summaries
    process_all_trading_summaries(str(base_dir))
    
    # Turnover Summary
    print("\nExtracting Turnover Summary data...")
    from extract_turnover_summary import process_all_turnover_summaries
    process_all_turnover_summaries(str(base_dir))
    
    # Transaction Summary
    print("\nExtracting Transaction Summary data...")
    from extract_transaction_summary import process_all_transaction_summaries
    process_all_transaction_summaries(str(base_dir))
    
    # Gross Profit Report
    print("\nExtracting Gross Profit data...")
    from extract_gross_profit import process_all_gross_profit_reports
    process_all_gross_profit_reports(str(base_dir))
    
    # Dispensary Summary
    print("\nExtracting Dispensary Summary data...")
    from extract_dispensary_summary import process_all_dispensary_summaries
    process_all_dispensary_summaries(str(base_dir))
    
    print("\n--- All extractions completed ---")
    
    # --- Step 2: Combine all data ---
    print("\n--- Step 2: Combining all data ---")
    combined_data = combine_all_data()
    
    # --- Step 3: Display summary ---
    print("\n--- Step 3: Displaying complete summary ---")
    display_complete_summary(combined_data)
    
    # --- Step 4: Create database insert statements ---
    print("\n--- Step 4: Creating database insert statements ---")
    insert_statements = create_database_insert_statements(combined_data)
    
    # --- Step 5: Save SQL statements to file ---
    print("\n--- Step 5: Saving SQL statements to file ---")
    sql_file = "complete_database_inserts.sql"
    with open(sql_file, 'w') as f:
        f.write("-- Complete Database Insert Statements\n")
        f.write("-- Generated by Pharmacy Data Pipeline\n")
        f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for sql in insert_statements:
            f.write(sql + "\n")
    
    print(f"✅ SQL statements saved to: {sql_file}")
    
    # --- Step 6: Save combined data to file ---
    print("\n--- Step 6: Saving combined data to JSON file ---")
    with open('complete_pipeline_data.json', 'w') as f:
        # Convert tuple keys to string keys for JSON compatibility
        json.dump({f"{k[0]}_{k[1]}": v for k, v in combined_data.items()}, f, indent=2, default=str)
    
    print("✅ Combined data saved to complete_pipeline_data.json")
    print("\n🎉 COMPLETE DATA PIPELINE FINISHED SUCCESSFULLY!")

if __name__ == "__main__":
    run_complete_pipeline()