#!/usr/bin/env python3
"""
Improved Pharmacy Pipeline Orchestrator
=======================================

This script orchestrates the complete improved pharmacy data pipeline:
1. Runs the improved classification to process emails from last 2 days
2. Runs the improved data pipeline with "keep largest value" strategy
3. Provides comprehensive logging and error handling
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_improved_classification():
    """Run the improved classification process"""
    logger.info("🔄 Starting improved classification process...")
    
    try:
        from improved_classify_and_organize import ImprovedPDFClassifier
        
        classifier = ImprovedPDFClassifier()
        success = classifier.process_emails_and_classify(days=2)
        
        if success:
            classifier.display_summary()
            logger.info("✅ Classification process completed successfully!")
            return True
        else:
            logger.error("❌ Classification process failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in classification process: {e}")
        return False

def run_improved_data_pipeline():
    """Run the improved data pipeline"""
    logger.info("🔄 Starting improved data pipeline...")
    
    try:
        from improved_data_pipeline import ImprovedDataPipeline
        
        pipeline = ImprovedDataPipeline()
        pipeline.run_complete_pipeline()
        
        logger.info("✅ Data pipeline completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in data pipeline: {e}")
        return False

def cleanup_temp_files():
    """Clean up temporary files after processing"""
    logger.info("🧹 Cleaning up temporary files...")
    
    try:
        # Remove extracted data JSON files
        json_files = [
            "trading_summary_extracted_data.json",
            "turnover_summary_extracted_data.json", 
            "transaction_summary_extracted_data.json",
            "gross_profit_extracted_data.json",
            "dispensary_summary_extracted_data.json"
        ]
        
        for json_file in json_files:
            if os.path.exists(json_file):
                os.remove(json_file)
                logger.info(f"Removed: {json_file}")
        
        logger.info("✅ Cleanup completed!")
        
    except Exception as e:
        logger.warning(f"⚠️ Cleanup warning: {e}")

def main():
    """Main orchestrator function"""
    logger.info("\n" + "="*80)
    logger.info("🚀 STARTING IMPROVED PHARMACY PIPELINE ORCHESTRATOR")
    logger.info("="*80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Run improved classification
    logger.info("\n" + "-"*60)
    logger.info("STEP 1: IMPROVED CLASSIFICATION")
    logger.info("-"*60)
    
    classification_success = run_improved_classification()
    
    if not classification_success:
        logger.error("❌ Classification failed. Stopping pipeline.")
        return False
    
    # Step 2: Run improved data pipeline
    logger.info("\n" + "-"*60)
    logger.info("STEP 2: IMPROVED DATA PIPELINE")
    logger.info("-"*60)
    
    pipeline_success = run_improved_data_pipeline()
    
    if not pipeline_success:
        logger.error("❌ Data pipeline failed.")
        return False
    
    # Step 3: Cleanup
    logger.info("\n" + "-"*60)
    logger.info("STEP 3: CLEANUP")
    logger.info("-"*60)
    
    cleanup_temp_files()
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("🎉 IMPROVED PHARMACY PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("="*80)
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 