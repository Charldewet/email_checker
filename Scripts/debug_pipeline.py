#!/usr/bin/env python3
"""
Debug Pipeline - Check what data is being extracted and compared
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_json_data(filename: str) -> list:
    """Load data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}")
        return []

def debug_data_extraction():
    """Debug what data is being extracted"""
    logger.info("🔍 DEBUGGING DATA EXTRACTION")
    logger.info("="*50)
    
    # Check what JSON files exist
    json_files = [
        "trading_summary_extracted_data.json",
        "turnover_summary_extracted_data.json", 
        "transaction_summary_extracted_data.json",
        "gross_profit_extracted_data.json",
        "dispensary_summary_extracted_data.json"
    ]
    
    for filename in json_files:
        data = load_json_data(filename)
        logger.info(f"\n📄 {filename}: {len(data)} records")
        
        if data:
            # Show first few records
            for i, record in enumerate(data[:3]):
                logger.info(f"  Record {i+1}: {record.get('pharmacy', 'Unknown')} - {record.get('date', 'No date')}")
                if 'turnover' in record:
                    logger.info(f"    Turnover: R{record.get('turnover', 0):,.2f}")
                if 'transactions_total' in record:
                    logger.info(f"    Transactions: {record.get('transactions_total', 0)}")

def debug_combined_data():
    """Debug the combined data structure"""
    logger.info("\n🔍 DEBUGGING COMBINED DATA")
    logger.info("="*50)
    
    # Load all data
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
    
    logger.info(f"📊 Combined data: {len(combined_data)} pharmacy/date combinations")
    
    for key, data in combined_data.items():
        pharmacy, date = key
        logger.info(f"\n🏪 {pharmacy} - {date}")
        
        # Check what data we have
        turnover = data.get('turnover_summary', {})
        trading = data.get('trading_summary', {})
        transaction = data.get('transaction_summary', {})
        gross_profit = data.get('gross_profit_summary', {})
        dispensary = data.get('dispensary_summary', {})
        
        if turnover:
            logger.info(f"  📈 Turnover: R{turnover.get('turnover', 0):,.2f}")
        if trading:
            logger.info(f"  📦 Trading: GP R{trading.get('gp_value', 0):,.2f}")
        if transaction:
            logger.info(f"  🛒 Transactions: {transaction.get('transactions_total', 0)}")
        if gross_profit:
            logger.info(f"  💰 Gross Profit: {len(gross_profit.get('products', []))} products")
        if dispensary:
            logger.info(f"  💊 Dispensary: {dispensary.get('script_total', 0)} scripts")

def debug_database_connection():
    """Debug database connection and existing data"""
    logger.info("\n🔍 DEBUGGING DATABASE CONNECTION")
    logger.info("="*50)
    
    try:
        from render_database_connection import RenderPharmacyDatabase
        db = RenderPharmacyDatabase()
        
        # Check if we can connect
        logger.info("✅ Database connection successful")
        
        # Check existing data for today
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"📅 Checking existing data for today: {today}")
        
        # Get existing data for REITZ today
        query = """
        SELECT * FROM daily_summary 
        WHERE pharmacy_id = (SELECT id FROM pharmacies WHERE pharmacy_code = 'REITZ')
        AND report_date = %s
        """
        
        result = db.execute_query(query, (today,))
        if result:
            logger.info(f"📊 Found {len(result)} existing records for REITZ today")
            for record in result:
                logger.info(f"  Turnover: R{record[4]:,.2f}, Transactions: {record[10]}")
        else:
            logger.info("📊 No existing records found for REITZ today")
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

def main():
    """Main debug function"""
    logger.info("🚀 STARTING PIPELINE DEBUG")
    logger.info("="*50)
    
    debug_data_extraction()
    debug_combined_data()
    debug_database_connection()
    
    logger.info("\n✅ DEBUG COMPLETED")

if __name__ == "__main__":
    main() 