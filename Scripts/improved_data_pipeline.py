#!/usr/bin/env python3
"""
Improved Pharmacy Data Pipeline
===============================

This script implements the "keep the largest value" strategy:
1. Processes all classified PDFs from the temp folders
2. Extracts data from all report types
3. Compares new data with existing database values
4. Only keeps the larger values for each metric
5. Updates the database with the best data
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import logging

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/improved_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def format_currency(amount: float) -> str:
    """Format amount as currency with commas"""
    if amount is None or amount == 0:
        return "R0.00"
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
        logger.warning(f"File not found: {filename}")
        return []

def calculate_basket_size(transactions_total: int, total_products_sold: float) -> float:
    """Calculate average basket size"""
    if transactions_total > 0:
        return round(total_products_sold / transactions_total, 2)
    return 0.0

def calculate_basket_value(turnover: float, transactions_total: int) -> float:
    """Calculate average basket value from turnover and transactions"""
    if transactions_total > 0 and turnover > 0:
        return round(turnover / transactions_total, 2)
    return 0.0

class ImprovedDataPipeline:
    def __init__(self):
        """Initialize the improved data pipeline"""
        self.temp_dir = Path("temp_classified_test")
        self.db = None
        self.connect_database()
        
    def connect_database(self):
        """Connect to the database"""
        try:
            from render_database_connection import RenderPharmacyDatabase
            self.db = RenderPharmacyDatabase()
            logger.info("✅ Connected to database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            self.db = None
    
    def get_existing_data(self, pharmacy_code: str, report_date: str) -> Dict[str, Any]:
        """Get existing data from database for comparison"""
        if not self.db:
            return {}
        
        try:
            query = """
            SELECT * FROM daily_summary 
            WHERE pharmacy_id = (SELECT id FROM pharmacies WHERE pharmacy_code = %s)
            AND report_date = %s
            """
            result = self.db.execute_query(query, (pharmacy_code, report_date))
            
            if result:
                return dict(result[0])
            return {}
            
        except Exception as e:
            logger.error(f"Error getting existing data: {e}")
            return {}
    
    def compare_and_keep_largest(self, existing_value: float, new_value: float, field_name: str) -> float:
        """Compare existing and new values, keep the larger one"""
        if existing_value is None or existing_value == 0:
            logger.info(f"  {field_name}: No existing value, using new value: {format_currency(new_value)}")
            return new_value
        
        if new_value > existing_value:
            logger.info(f"  {field_name}: New value {format_currency(new_value)} > existing {format_currency(existing_value)}, keeping new")
            return new_value
        else:
            logger.info(f"  {field_name}: Existing value {format_currency(existing_value)} >= new {format_currency(new_value)}, keeping existing")
            return existing_value
    
    def extract_and_process_all_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract data from all classified PDFs and process with largest value strategy
        """
        logger.info("🔄 Starting data extraction and processing...")
        
        # Import extraction modules
        from extract_trading_summary import process_all_trading_summaries
        from extract_turnover_summary import process_all_turnover_summaries
        from extract_transaction_summary import process_all_transaction_summaries
        from extract_gross_profit import process_all_gross_profit_reports
        from extract_dispensary_summary import process_all_dispensary_summaries
        
        # Run all extractions
        logger.info("Extracting Trading Summary data...")
        process_all_trading_summaries(str(self.temp_dir))
        
        logger.info("Extracting Turnover Summary data...")
        process_all_turnover_summaries(str(self.temp_dir))
        
        logger.info("Extracting Transaction Summary data...")
        process_all_transaction_summaries(str(self.temp_dir))
        
        logger.info("Extracting Gross Profit data...")
        process_all_gross_profit_reports(str(self.temp_dir))
        
        logger.info("Extracting Dispensary Summary data...")
        process_all_dispensary_summaries(str(self.temp_dir))
        
        # Load all extracted data
        trading_data = load_json_data("trading_summary_extracted_data.json")
        turnover_data = load_json_data("turnover_summary_extracted_data.json")
        transaction_data = load_json_data("transaction_summary_extracted_data.json")
        gross_profit_data = load_json_data("gross_profit_extracted_data.json")
        dispensary_data = load_json_data("dispensary_summary_extracted_data.json")
        
        # Combine and process data with aggregation
        combined_data = {}
        
        # Process each data source and aggregate by pharmacy/date
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
                
                # Aggregate data by keeping the highest values
                if data_type == "trading":
                    existing = combined_data[key]['trading_summary']
                    if not existing or item.get('turnover', 0) > existing.get('turnover', 0):
                        combined_data[key]['trading_summary'] = item
                elif data_type == "turnover":
                    existing = combined_data[key]['turnover_summary']
                    if not existing or item.get('turnover', 0) > existing.get('turnover', 0):
                        combined_data[key]['turnover_summary'] = item
                elif data_type == "transaction":
                    existing = combined_data[key]['transaction_summary']
                    if not existing or item.get('transactions_total', 0) > existing.get('transactions_total', 0):
                        combined_data[key]['transaction_summary'] = item
                elif data_type == "gross_profit":
                    existing = combined_data[key]['gross_profit_summary']
                    if not existing or item.get('total_gross_profit', 0) > existing.get('total_gross_profit', 0):
                        combined_data[key]['gross_profit_summary'] = item
                elif data_type == "dispensary":
                    existing = combined_data[key]['dispensary_summary']
                    if not existing or item.get('script_total', 0) > existing.get('script_total', 0):
                        combined_data[key]['dispensary_summary'] = item
        
        # Log the aggregation results
        logger.info("📊 Aggregated data summary:")
        for key, data in combined_data.items():
            pharmacy, date = key
            turnover = data.get('turnover_summary', {}).get('turnover', 0)
            transactions = data.get('transaction_summary', {}).get('transactions_total', 0)
            logger.info(f"  {pharmacy} - {date}: R{turnover:,.2f} turnover, {transactions} transactions")
        
        return combined_data
    
    def calculate_derived_metrics(self, combined_data: Dict[str, Dict[str, Any]]):
        """Calculate derived metrics for each pharmacy/date combination"""
        logger.info("🔄 Calculating derived metrics...")
        
        for key, data in combined_data.items():
            pharmacy, date = key
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
            
            # Use turnover from turnover summary
            calculated['turnover'] = turnover.get('turnover', 0)
            
            # Calculate basket value from turnover and transactions
            calculated['avg_basket_value'] = calculate_basket_value(calculated['turnover'], transactions_total)
            
            # Store other metrics
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
            # Type R sales from turnover summary
            calculated['type_r_sales'] = turnover.get('type_r_sales', 0)
    
    def compare_with_database_and_update(self, combined_data: Dict[str, Dict[str, Any]]):
        """
        Compare new data with existing database data and update with largest values
        """
        logger.info("🔄 Comparing with database and updating with largest values...")
        
        if not self.db:
            logger.error("❌ No database connection available")
            return
        
        for key, data in combined_data.items():
            pharmacy, date = key
            calculated = data['calculated_metrics']
            
            # Skip records with invalid dates
            if not date or date is None:
                logger.warning(f"⚠️ Skipping {pharmacy} - Invalid date (None)")
                continue
                
            logger.info(f"\n🏪 Processing {pharmacy} - {date}")
            
            # Get existing data from database
            existing_data = self.get_existing_data(pharmacy, date)
            
            # Compare and keep largest values for each metric
            final_metrics = {}
            
            # Financial metrics - keep largest
            final_metrics['turnover'] = self.compare_and_keep_largest(
                existing_data.get('turnover', 0), 
                calculated.get('turnover', 0), 
                'Turnover'
            )
            
            final_metrics['gp_value'] = self.compare_and_keep_largest(
                existing_data.get('gp_value', 0), 
                calculated.get('gp_value', 0), 
                'Gross Profit Value'
            )
            
            final_metrics['cost_of_sales'] = self.compare_and_keep_largest(
                existing_data.get('cost_of_sales', 0), 
                calculated.get('cost_of_sales', 0), 
                'Cost of Sales'
            )
            
            final_metrics['purchases'] = self.compare_and_keep_largest(
                existing_data.get('purchases', 0), 
                calculated.get('purchases', 0), 
                'Purchases'
            )
            
            final_metrics['disp_turnover'] = self.compare_and_keep_largest(
                existing_data.get('disp_turnover', 0), 
                calculated.get('disp_turnover', 0), 
                'Dispensary Turnover'
            )
            
            # Transaction metrics - keep largest
            final_metrics['transactions_total'] = self.compare_and_keep_largest(
                existing_data.get('transactions_total', 0), 
                calculated.get('transactions_total', 0), 
                'Total Transactions'
            )
            
            final_metrics['script_total'] = self.compare_and_keep_largest(
                existing_data.get('script_total', 0), 
                calculated.get('script_total', 0), 
                'Total Scripts'
            )
            
            # Stock metrics - keep largest
            final_metrics['stock_opening'] = self.compare_and_keep_largest(
                existing_data.get('stock_opening', 0), 
                calculated.get('stock_opening', 0), 
                'Opening Stock'
            )
            
            final_metrics['stock_closing'] = self.compare_and_keep_largest(
                existing_data.get('stock_closing', 0), 
                calculated.get('stock_closing', 0), 
                'Closing Stock'
            )
            
            # Payment methods - keep largest
            final_metrics['sales_cash'] = self.compare_and_keep_largest(
                existing_data.get('sales_cash', 0), 
                calculated.get('sales_cash', 0), 
                'Cash Sales'
            )
            
            final_metrics['sales_account'] = self.compare_and_keep_largest(
                existing_data.get('sales_account', 0), 
                calculated.get('sales_account', 0), 
                'Account Sales'
            )
            
            final_metrics['sales_cod'] = self.compare_and_keep_largest(
                existing_data.get('sales_cod', 0), 
                calculated.get('sales_cod', 0), 
                'COD Sales'
            )
            
            # Type R sales - keep largest
            final_metrics['type_r_sales'] = self.compare_and_keep_largest(
                existing_data.get('type_r_sales', 0), 
                calculated.get('type_r_sales', 0), 
                'Type R Sales'
            )
            
            # For percentages and averages, use the value from the record with higher turnover
            if final_metrics['turnover'] == calculated.get('turnover', 0):
                # Use new values if turnover is from new data
                final_metrics['gp_percent'] = calculated.get('gp_percent', 0)
                final_metrics['avg_basket_value'] = calculated.get('avg_basket_value', 0)
                final_metrics['avg_basket_size'] = calculated.get('avg_basket_size', 0)
                final_metrics['avg_script_value'] = calculated.get('avg_script_value', 0)
                final_metrics['adjustments'] = calculated.get('adjustments', 0)
            else:
                # Use existing values if turnover is from existing data
                final_metrics['gp_percent'] = existing_data.get('gp_percent', 0)
                final_metrics['avg_basket_value'] = existing_data.get('avg_basket_value', 0)
                final_metrics['avg_basket_size'] = existing_data.get('avg_basket_size', 0)
                final_metrics['avg_script_value'] = existing_data.get('avg_script_value', 0)
                final_metrics['adjustments'] = existing_data.get('adjustments', 0)
            
            # Update database with final metrics
            self.update_database_record(pharmacy, date, final_metrics)
    
    def update_database_record(self, pharmacy: str, date: str, metrics: Dict[str, Any]):
        """Update database record with final metrics"""
        try:
            # Validate date before attempting database operation
            if not date or date is None:
                logger.warning(f"⚠️ Skipping database update for {pharmacy} - Invalid date (None)")
                return
                
            query = """
            INSERT INTO daily_summary (
                pharmacy_id, report_date, turnover, gp_percent, gp_value, cost_of_sales, purchases,
                avg_basket_value, avg_basket_size, transactions_total, script_total, avg_script_value,
                disp_turnover, stock_opening, stock_closing, adjustments, sales_cash, sales_cod, sales_account,
                type_r_sales
            ) VALUES (
                (SELECT id FROM pharmacies WHERE pharmacy_code = %s),
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                sales_account = EXCLUDED.sales_account,
                type_r_sales = EXCLUDED.type_r_sales
            """
            
            params = (
                pharmacy, date,
                metrics['turnover'], metrics['gp_percent'], metrics['gp_value'],
                metrics['cost_of_sales'], metrics['purchases'], metrics['avg_basket_value'],
                metrics['avg_basket_size'], metrics['transactions_total'], metrics['script_total'],
                metrics['avg_script_value'], metrics['disp_turnover'], metrics['stock_opening'],
                metrics['stock_closing'], metrics['adjustments'], metrics['sales_cash'],
                metrics['sales_cod'], metrics['sales_account'], metrics.get('type_r_sales', 0)
            )
            
            self.db.execute_query(query, params)
            logger.info(f"✅ Updated database record for {pharmacy} - {date}")
            # Refresh rollups for this pharmacy/date
            try:
                self.db.refresh_rollups(pharmacy, date)
                logger.info("♻️  Rollups refreshed")
            except Exception as e:
                logger.warning(f"Rollup refresh failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error updating database for {pharmacy} - {date}: {e}")
    
    def display_final_summary(self, combined_data: Dict[str, Dict[str, Any]]):
        """Display final summary of processed data"""
        logger.info("\n" + "="*80)
        logger.info("📊 FINAL PROCESSED DATA SUMMARY")
        logger.info("="*80)
        
        for key, data in combined_data.items():
            pharmacy, date = key
            calculated = data['calculated_metrics']
            
            logger.info(f"\n🏪 {pharmacy} - {date}")
            logger.info("-" * 60)
            
            # Financial metrics
            logger.info(f"💰 Financial Metrics:")
            logger.info(f"   • Turnover: {format_currency(calculated['turnover'])}")
            logger.info(f"   • Gross Profit: {format_currency(calculated['gp_value'])} ({calculated['gp_percent']:.2f}%)")
            logger.info(f"   • Cost of Sales: {format_currency(calculated['cost_of_sales'])}")
            logger.info(f"   • Purchases: {format_currency(calculated['purchases'])}")
            
            # Transaction metrics
            logger.info(f"🛒 Transaction Metrics:")
            logger.info(f"   • Total Transactions: {calculated['transactions_total']:,}")
            logger.info(f"   • Average Basket Value: {format_currency(calculated['avg_basket_value'])}")
            logger.info(f"   • Average Basket Size: {calculated['avg_basket_size']} items")
            
            # Script metrics
            logger.info(f"💊 Script Metrics:")
            logger.info(f"   • Total Scripts: {calculated['script_total']:,}")
            logger.info(f"   • Dispensary Turnover: {format_currency(calculated['disp_turnover'])}")
            logger.info(f"   • Average Script Value: {format_currency(calculated['avg_script_value'])}")
            
            # Stock metrics
            logger.info(f"📦 Stock Metrics:")
            logger.info(f"   • Opening Stock: {format_currency(calculated['stock_opening'])}")
            logger.info(f"   • Closing Stock: {format_currency(calculated['stock_closing'])}")
            logger.info(f"   • Adjustments: {format_currency(calculated['adjustments'])}")
            
            # Payment methods
            logger.info(f"💳 Payment Methods:")
            logger.info(f"   • Cash Sales: {format_currency(calculated['sales_cash'])}")
            logger.info(f"   • Account Sales: {format_currency(calculated['sales_account'])}")
            logger.info(f"   • COD Sales: {format_currency(calculated['sales_cod'])}")
    
    def run_complete_pipeline(self):
        """Run the complete improved data pipeline"""
        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING IMPROVED DATA PIPELINE")
        logger.info("="*80)
        
        try:
            # Step 1: Extract and process all data
            logger.info("\n--- Step 1: Extracting and processing data ---")
            combined_data = self.extract_and_process_all_data()
            
            if not combined_data:
                logger.warning("No data found to process")
                return
            
            # Step 2: Calculate derived metrics
            logger.info("\n--- Step 2: Calculating derived metrics ---")
            self.calculate_derived_metrics(combined_data)
            
            # Step 3: Compare with database and update with largest values
            logger.info("\n--- Step 3: Comparing with database and updating ---")
            self.compare_with_database_and_update(combined_data)
            
            # Step 4: Display final summary
            logger.info("\n--- Step 4: Displaying final summary ---")
            self.display_final_summary(combined_data)
            
            # Step 5: Save processed data to file
            logger.info("\n--- Step 5: Saving processed data ---")
            with open('improved_pipeline_data.json', 'w') as f:
                # Convert tuple keys to string keys for JSON compatibility
                json.dump({f"{k[0]}_{k[1]}": v for k, v in combined_data.items()}, f, indent=2, default=str)
            
            logger.info("✅ Processed data saved to improved_pipeline_data.json")
            logger.info("\n🎉 IMPROVED DATA PIPELINE COMPLETED SUCCESSFULLY!")
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise

def main():
    """Main function"""
    pipeline = ImprovedDataPipeline()
    pipeline.run_complete_pipeline()

if __name__ == "__main__":
    main() 