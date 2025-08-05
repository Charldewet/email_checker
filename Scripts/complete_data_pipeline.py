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

def run_complete_pipeline():
    """Run the complete data pipeline"""
    print("🚀 STARTING COMPLETE PHARMACY DATA PIPELINE")
    print("=" * 60)
    
    # Step 1: Classify and organize PDFs
    print("\n📁 Step 1: Classifying and organizing PDF reports...")
    try:
        from classify_and_organize_pdfs import classify_and_organize_pdfs
        classify_and_organize_pdfs()
        print("✅ PDF classification completed")
    except Exception as e:
        print(f"❌ PDF classification failed: {e}")
        return False
    
    # Step 2: Extract trading summary data
    print("\n📊 Step 2: Extracting trading summary data...")
    try:
        from test_trading_extraction import test_trading_extraction
        test_trading_extraction()
        print("✅ Trading summary extraction completed")
    except Exception as e:
        print(f"❌ Trading summary extraction failed: {e}")
        return False
    
    # Step 3: Extract turnover summary data
    print("\n💰 Step 3: Extracting turnover summary data...")
    try:
        from extract_turnover_summary import test_turnover_extraction
        test_turnover_extraction()
        print("✅ Turnover summary extraction completed")
    except Exception as e:
        print(f"❌ Turnover summary extraction failed: {e}")
        return False
    
    # Step 4: Extract transaction summary data
    print("\n🛒 Step 4: Extracting transaction summary data...")
    try:
        from extract_transaction_summary import test_transaction_extraction
        test_transaction_extraction()
        print("✅ Transaction summary extraction completed")
    except Exception as e:
        print(f"❌ Transaction summary extraction failed: {e}")
        return False
    
    # Step 5: Extract gross profit data
    print("\n📈 Step 5: Extracting gross profit data...")
    try:
        from extract_gross_profit import test_gross_profit_extraction
        test_gross_profit_extraction()
        print("✅ Gross profit extraction completed")
    except Exception as e:
        print(f"❌ Gross profit extraction failed: {e}")
        return False
    
    # Step 6: Extract dispensary summary data
    print("\n💊 Step 6: Extracting dispensary summary data...")
    try:
        from extract_dispensary_summary import test_dispensary_extraction
        test_dispensary_extraction()
        print("✅ Dispensary summary extraction completed")
    except Exception as e:
        print(f"❌ Dispensary summary extraction failed: {e}")
        return False
    
    # Step 7: Combine all data
    print("\n🔄 Step 7: Combining all extracted data...")
    try:
        combined_data = combine_all_data()
        print(f"✅ Data combination completed for {len(combined_data)} pharmacy/date combinations")
    except Exception as e:
        print(f"❌ Data combination failed: {e}")
        return False
    
    # Step 8: Display complete summary
    display_complete_summary(combined_data)
    
    # Step 9: Create database insert statements
    print("\n📝 Step 8: Creating database insert statements...")
    insert_statements = create_database_insert_statements(combined_data)
    
    # Save SQL statements to file
    sql_file = "complete_database_inserts.sql"
    with open(sql_file, 'w') as f:
        f.write("-- Complete Database Insert Statements\n")
        f.write("-- Generated by Pharmacy Data Pipeline\n")
        f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for sql in insert_statements:
            f.write(sql + "\n")
    
    print(f"✅ SQL statements saved to: {sql_file}")
    
    # Step 10: Save combined data to JSON
    print("\n💾 Step 9: Saving combined data...")
    combined_file = "complete_pipeline_data.json"
    
    # Convert tuple keys to strings for JSON serialization
    json_safe_data = {}
    for key, data in combined_data.items():
        pharmacy, date = key
        json_key = f"{pharmacy}_{date}"
        json_safe_data[json_key] = data
    
    with open(combined_file, 'w') as f:
        json.dump(json_safe_data, f, indent=2, default=str)
    print(f"✅ Combined data saved to: {combined_file}")
    
    print("\n🎉 COMPLETE DATA PIPELINE FINISHED SUCCESSFULLY!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = run_complete_pipeline()
    if success:
        print("\n✅ Pipeline completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Pipeline failed!")
        sys.exit(1)