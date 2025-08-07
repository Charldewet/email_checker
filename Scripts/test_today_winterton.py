#!/usr/bin/env python3
"""
Test Today's Winterton Processing
=================================

This script tests the processing of today's Winterton PDFs to see why they're not being extracted.
"""

import os
import sys
from pathlib import Path
import shutil

# Add Scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def test_today_winterton_processing():
    """Test processing of today's Winterton PDFs"""
    print("🔍 Testing Today's Winterton Processing")
    print("=" * 50)
    
    # Set environment variables
    os.environ['DATABASE_URL'] = 'postgresql://pharmacy_user:PzL1HpYNaYOrmcfImjeZm8LitHTd4d7F@dpg-d28vb1muk2gs73frrns0-a.oregon-postgres.render.com/pharmacy_reports'
    os.environ['REITZ_GMAIL_USERNAME'] = 'dmr.tlc.reitz@gmail.com'
    os.environ['REITZ_GMAIL_APP_PASSWORD'] = 'dkcj ixgf vhkf jupx'
    
    # Step 1: Copy today's Winterton PDFs to a test directory
    print("\n📁 Step 1: Setting up test files...")
    
    test_dir = Path("test_today_winterton")
    test_dir.mkdir(exist_ok=True)
    
    # Copy today's Winterton PDFs
    today_winterton_pdfs = [
        "temp_debug_pdfs/20250807_112033_918_20250807-09h02m01s-Complete.pdf",
        "temp_debug_pdfs/20250807_112035_919_20250807-09h05m43s-Complete.pdf", 
        "temp_debug_pdfs/20250807_112038_920_20250807-09h35m49s-Complete.pdf"
    ]
    
    for pdf_path in today_winterton_pdfs:
        if Path(pdf_path).exists():
            shutil.copy2(pdf_path, test_dir)
            print(f"   ✅ Copied: {pdf_path}")
        else:
            print(f"   ❌ Not found: {pdf_path}")
    
    # Step 2: Run classification
    print("\n🔍 Step 2: Running classification...")
    try:
        from classify_and_organize_pdfs import classify_and_organize_pdfs
        classify_and_organize_pdfs(str(test_dir), "temp_classified_pdfs_test")
        print("   ✅ Classification completed")
    except Exception as e:
        print(f"   ❌ Classification failed: {e}")
        return
    
    # Step 3: Check what was classified
    print("\n📊 Step 3: Checking classification results...")
    classified_dir = Path("temp_classified_pdfs_test")
    if classified_dir.exists():
        for date_folder in classified_dir.iterdir():
            if date_folder.is_dir():
                print(f"   📅 Date folder: {date_folder.name}")
                for pharmacy_folder in date_folder.iterdir():
                    if pharmacy_folder.is_dir():
                        print(f"      🏪 Pharmacy: {pharmacy_folder.name}")
                        for file in pharmacy_folder.glob("*.pdf"):
                            print(f"         📄 File: {file.name}")
    else:
        print("   ❌ No classified directory found")
    
    # Step 4: Run deduplication
    print("\n🔄 Step 4: Running deduplication...")
    try:
        from email_monitor import PharmacyEmailMonitor
        monitor = PharmacyEmailMonitor()
        monitor.keep_latest_versions("temp_classified_pdfs_test")
        print("   ✅ Deduplication completed")
    except Exception as e:
        print(f"   ❌ Deduplication failed: {e}")
    
    # Step 5: Check final results
    print("\n📊 Step 5: Checking final results...")
    if classified_dir.exists():
        for date_folder in classified_dir.iterdir():
            if date_folder.is_dir():
                print(f"   📅 Date folder: {date_folder.name}")
                for pharmacy_folder in date_folder.iterdir():
                    if pharmacy_folder.is_dir():
                        print(f"      🏪 Pharmacy: {pharmacy_folder.name}")
                        files = list(pharmacy_folder.glob("*.pdf"))
                        if files:
                            for file in files:
                                print(f"         📄 File: {file.name}")
                        else:
                            print(f"         ❌ No files found")
    else:
        print("   ❌ No classified directory found")
    
    # Step 6: Run complete pipeline
    print("\n🚀 Step 6: Running complete pipeline...")
    try:
        from complete_data_pipeline import run_complete_pipeline
        run_complete_pipeline("temp_classified_pdfs_test")
        print("   ✅ Complete pipeline completed")
    except Exception as e:
        print(f"   ❌ Complete pipeline failed: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_today_winterton_processing() 