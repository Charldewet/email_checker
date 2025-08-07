#!/usr/bin/env python3
"""
Test Comparison Logic - Verify the "keep largest value" logic
"""

import os
import logging
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_comparison.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_comparison_logic():
    """Test the comparison logic directly"""
    logger.info("🧪 TESTING COMPARISON LOGIC")
    logger.info("="*50)
    
    try:
        from improved_data_pipeline import ImprovedDataPipeline
        
        # Create pipeline instance
        pipeline = ImprovedDataPipeline()
        
        # Test the comparison function directly
        logger.info("Testing compare_and_keep_largest function:")
        
        # Test case 1: New value is larger
        result1 = pipeline.compare_and_keep_largest(1000, 2000, "Test Turnover")
        logger.info(f"Result 1: {result1}")
        
        # Test case 2: Existing value is larger
        result2 = pipeline.compare_and_keep_largest(3000, 2000, "Test Turnover")
        logger.info(f"Result 2: {result2}")
        
        # Test case 3: No existing value
        result3 = pipeline.compare_and_keep_largest(0, 1500, "Test Turnover")
        logger.info(f"Result 3: {result3}")
        
        logger.info("✅ Comparison logic test completed")
        
    except Exception as e:
        logger.error(f"❌ Comparison logic test failed: {e}")

def test_database_comparison():
    """Test the database comparison for today's data"""
    logger.info("\n🧪 TESTING DATABASE COMPARISON")
    logger.info("="*50)
    
    try:
        from improved_data_pipeline import ImprovedDataPipeline
        from render_database_connection import RenderPharmacyDatabase
        
        # Create instances
        pipeline = ImprovedDataPipeline()
        db = RenderPharmacyDatabase()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"📅 Testing for date: {today}")
        
        # Get existing data for REITZ today
        existing_data = pipeline.get_existing_data("REITZ", today)
        logger.info(f"📊 Existing data for REITZ today: {existing_data}")
        
        # Test with a new value
        new_turnover = 33564.49  # This is what we extracted
        existing_turnover = existing_data.get('turnover', 0)
        
        logger.info(f"💰 Existing turnover: R{existing_turnover:,.2f}")
        logger.info(f"💰 New turnover: R{new_turnover:,.2f}")
        
        # Test the comparison
        final_turnover = pipeline.compare_and_keep_largest(
            existing_turnover, 
            new_turnover, 
            'Turnover'
        )
        
        logger.info(f"🎯 Final turnover: R{final_turnover:,.2f}")
        
        if final_turnover == new_turnover:
            logger.info("✅ New value should replace existing value")
        else:
            logger.info("✅ Existing value should be kept")
            
    except Exception as e:
        logger.error(f"❌ Database comparison test failed: {e}")

def test_pipeline_step():
    """Test the specific pipeline step that should be working"""
    logger.info("\n🧪 TESTING PIPELINE STEP")
    logger.info("="*50)
    
    try:
        from improved_data_pipeline import ImprovedDataPipeline
        
        # Create pipeline instance
        pipeline = ImprovedDataPipeline()
        
        # Create test data
        test_data = {
            ('REITZ', '2025-08-07'): {
                'pharmacy': 'REITZ',
                'date': '2025-08-07',
                'calculated_metrics': {
                    'turnover': 33564.49,
                    'transactions_total': 68,
                    'gp_value': 3409.85,
                    'cost_of_sales': 0,
                    'purchases': 0,
                    'disp_turnover': 0,
                    'script_total': 0,
                    'stock_opening': 0,
                    'stock_closing': 0,
                    'sales_cash': 0,
                    'sales_account': 0,
                    'sales_cod': 0,
                    'gp_percent': 0,
                    'avg_basket_value': 0,
                    'avg_basket_size': 0,
                    'avg_script_value': 0,
                    'adjustments': 0
                }
            }
        }
        
        logger.info("🔄 Testing compare_with_database_and_update with test data")
        pipeline.compare_with_database_and_update(test_data)
        
        logger.info("✅ Pipeline step test completed")
        
    except Exception as e:
        logger.error(f"❌ Pipeline step test failed: {e}")

def main():
    """Main test function"""
    logger.info("🚀 STARTING COMPARISON TESTS")
    logger.info("="*50)
    
    test_comparison_logic()
    test_database_comparison()
    test_pipeline_step()
    
    logger.info("\n✅ ALL TESTS COMPLETED")

if __name__ == "__main__":
    main() 