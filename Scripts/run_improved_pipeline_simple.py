#!/usr/bin/env python3
"""
Simplified Improved Pipeline Runner
==================================

This script provides a simple way to run the improved pipeline
with better error handling and user feedback.
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
        logging.FileHandler('logs/simple_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    logger.info("🔍 Checking environment...")
    
    required_vars = {
        'REITZ_GMAIL_USERNAME': 'Gmail username for email processing',
        'REITZ_GMAIL_APP_PASSWORD': 'Gmail app password for email processing',
        'DATABASE_URL': 'Database connection URL'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        logger.warning("⚠️ Missing environment variables:")
        for var in missing_vars:
            logger.warning(f"   - {var}")
        logger.warning("Some features may not work without these variables.")
        return False
    else:
        logger.info("✅ All environment variables are set.")
        return True

def run_classification():
    """Run the improved classification"""
    logger.info("🔄 Running improved classification...")
    
    try:
        from improved_classify_and_organize import ImprovedPDFClassifier
        
        classifier = ImprovedPDFClassifier()
        success = classifier.process_emails_and_classify(days=2)
        
        if success:
            classifier.display_summary()
            logger.info("✅ Classification completed successfully!")
            return True
        else:
            logger.error("❌ Classification failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in classification: {e}")
        return False

def run_data_pipeline():
    """Run the improved data pipeline"""
    logger.info("🔄 Running improved data pipeline...")
    
    try:
        from improved_data_pipeline import ImprovedDataPipeline
        
        pipeline = ImprovedDataPipeline()
        pipeline.run_complete_pipeline()
        
        logger.info("✅ Data pipeline completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in data pipeline: {e}")
        return False

def check_temp_files():
    """Check if there are files in the temp directory"""
    temp_dir = Path("temp_classified_test")
    
    if not temp_dir.exists():
        logger.info("📁 No temp directory found - classification needed")
        return False
    
    pdf_files = list(temp_dir.rglob("*.pdf"))
    if not pdf_files:
        logger.info("📁 No PDF files found in temp directory - classification needed")
        return False
    
    logger.info(f"📁 Found {len(pdf_files)} PDF files in temp directory")
    for pdf_file in pdf_files:
        logger.info(f"   - {pdf_file}")
    
    return True

def main():
    """Main function with user-friendly interface"""
    print("\n" + "="*80)
    print("🚀 IMPROVED PHARMACY PIPELINE")
    print("="*80)
    print("This pipeline will:")
    print("1. Process emails from the last 2 days")
    print("2. Classify PDF reports by type and pharmacy")
    print("3. Extract data and update database with largest values")
    print("="*80)
    
    # Check environment
    env_ok = check_environment()
    
    # Check if we have existing files
    has_files = check_temp_files()
    
    # Ask user what to do
    if has_files:
        print("\n📁 Found existing classified files in temp_classified_test/")
        choice = input("Do you want to:\n1. Re-run classification (process emails again)\n2. Skip classification (use existing files)\n3. Exit\n\nEnter choice (1-3): ").strip()
        
        if choice == "3":
            print("👋 Exiting...")
            return
        elif choice == "1":
            run_classification()
        elif choice == "2":
            print("⏭️ Skipping classification, using existing files...")
        else:
            print("❌ Invalid choice, exiting...")
            return
    else:
        print("\n📁 No existing files found, running classification...")
        if not run_classification():
            print("❌ Classification failed, exiting...")
            return
    
    # Run data pipeline
    print("\n🔄 Running data pipeline...")
    if run_data_pipeline():
        print("\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("📊 Check the logs for detailed information")
    else:
        print("\n❌ Pipeline failed. Check logs for details.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        print("Check logs for details") 