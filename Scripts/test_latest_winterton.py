#!/usr/bin/env python3
"""
Test Latest Winterton Processing
================================

This script tests processing the latest Winterton PDF (11:28:57) specifically.
"""

import os
import sys
from pathlib import Path
import shutil

# Add Scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def test_latest_winterton():
    """Test processing the latest Winterton PDF"""
    print("🔍 Testing Latest Winterton Processing")
    print("=" * 50)
    
    # Set environment variables
    os.environ['DATABASE_URL'] = 'postgresql://pharmacy_user:PzL1HpYNaYOrmcfImjeZm8LitHTd4d7F@dpg-d28vb1muk2gs73frrns0-a.oregon-postgres.render.com/pharmacy_reports'
    
    # Find the latest Winterton PDF (11:28:57)
    source_dir = Path("temp_debug_pdfs")
    latest_pdf = None
    
    for pdf_file in source_dir.glob("*.pdf"):
        if "11h28m57" in pdf_file.name:
            latest_pdf = pdf_file
            break
    
    if not latest_pdf:
        print("❌ Latest Winterton PDF (11:28:57) not found!")
        return
    
    print(f"✅ Found latest Winterton PDF: {latest_pdf.name}")
    
    # Create a test directory with just this PDF
    test_dir = Path("test_latest_winterton")
    test_dir.mkdir(exist_ok=True)
    
    # Copy the latest PDF to test directory
    test_pdf = test_dir / latest_pdf.name
    shutil.copy2(latest_pdf, test_pdf)
    print(f"📄 Copied to: {test_pdf}")
    
    # Run classification on this specific PDF
    print("\n🔍 Running classification...")
    try:
        from classify_and_organize_pdfs import classify_and_organize_pdfs
        classify_and_organize_pdfs(str(test_dir), "temp_classified_latest")
        print("✅ Classification completed!")
        
        # Check what was classified
        classified_dir = Path("temp_classified_latest")
        if classified_dir.exists():
            print("\n📁 Classified files:")
            for pdf in classified_dir.rglob("*.pdf"):
                print(f"   • {pdf}")
                
                # Extract data from this specific PDF
                print(f"\n📊 Extracting data from: {pdf.name}")
                try:
                    from extract_turnover_summary import extract_turnover_summary
                    result = extract_turnover_summary(str(pdf))
                    if result:
                        print(f"   ✅ Turnover: R{result.get('turnover', 0):,.2f}")
                        print(f"   📅 Date: {result.get('date', 'N/A')}")
                        print(f"   🏪 Pharmacy: {result.get('pharmacy', 'N/A')}")
                    else:
                        print("   ❌ No data extracted")
                except Exception as e:
                    print(f"   ❌ Extraction error: {e}")
        else:
            print("❌ No classified files found")
            
    except Exception as e:
        print(f"❌ Classification error: {e}")
    
    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)
    if Path("temp_classified_latest").exists():
        shutil.rmtree("temp_classified_latest")

if __name__ == "__main__":
    test_latest_winterton() 