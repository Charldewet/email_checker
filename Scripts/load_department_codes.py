#!/usr/bin/env python3
"""
Load Department Codes from CSV
=============================

This script loads all department codes from the Departments.csv file into the Render database.
"""

import os
import csv
import sys
from pathlib import Path
from render_database_connection import RenderPharmacyDatabase

def load_department_codes_from_csv():
    """Load department codes from CSV file into database"""
    print("📋 Loading department codes from CSV file...")
    
    # Path to the CSV file
    csv_file = Path('../Departments/Departments.csv')
    
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Connect to database
    db = RenderPharmacyDatabase()
    
    # Read CSV file
    departments = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                department_code = row.get('Department Code', '').strip()
                department_name = row.get('Department Name', '').strip()
                
                if department_code and department_name:
                    departments.append({
                        'code': department_code,
                        'name': department_name
                    })
        
        print(f"📊 Found {len(departments)} department codes in CSV file")
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False
    
    # Insert departments into database
    success_count = 0
    skipped_count = 0
    
    print("\n🗄️ Inserting department codes into database...")
    
    for dept in departments:
        try:
            # Check if department already exists
            existing = db.execute_query(
                "SELECT department_code FROM department_codes WHERE department_code = %s",
                (dept['code'],)
            )
            
            if existing:
                skipped_count += 1
                print(f"   ⏭️  Skipped: {dept['code']} - {dept['name']} (already exists)")
                continue
            
            # Insert new department
            db.execute_query(
                "INSERT INTO department_codes (department_code, department_name) VALUES (%s, %s)",
                (dept['code'], dept['name'])
            )
            
            success_count += 1
            print(f"   ✅ Added: {dept['code']} - {dept['name']}")
            
        except Exception as e:
            print(f"   ❌ Error inserting {dept['code']}: {e}")
            continue
    
    print(f"\n📊 Insertion Summary:")
    print(f"   ✅ Successfully inserted: {success_count} departments")
    print(f"   ⏭️  Skipped (already exists): {skipped_count} departments")
    print(f"   📋 Total processed: {len(departments)} departments")
    
    # Get updated database statistics
    stats = db.get_database_stats()
    print(f"\n📊 Updated Database Statistics:")
    print(f"   • Department Codes: {stats.get('department_codes', 0)} records")
    
    # Show sample of departments
    print(f"\n📋 Sample Department Codes:")
    sample_depts = db.execute_query(
        "SELECT department_code, department_name FROM department_codes ORDER BY department_code LIMIT 10"
    )
    
    for dept in sample_depts:
        print(f"   • {dept['department_code']}: {dept['department_name']}")
    
    if len(sample_depts) == 10:
        print(f"   ... and {stats.get('department_codes', 0) - 10} more departments")
    
    db.close()
    return True

def verify_department_mapping():
    """Verify that department codes from gross profit reports can be mapped"""
    print("\n🔍 Verifying department code mapping...")
    
    db = RenderPharmacyDatabase()
    
    # Get all department codes from database
    db_depts = db.execute_query("SELECT department_code FROM department_codes")
    db_codes = {dept['department_code'] for dept in db_depts}
    
    print(f"📊 Database has {len(db_codes)} department codes")
    
    # Check mapping for some common codes from gross profit reports
    test_codes = [
        'BAAC', 'BAAB', 'BBGF', 'BCCF', 'FBBC', 'FDAA', 'FNCB', 'FPBS', 'HVLL', 'PDOA'
    ]
    
    print(f"\n🔍 Testing department code mapping:")
    for code in test_codes:
        if code in db_codes:
            dept_name = db.execute_query(
                "SELECT department_name FROM department_codes WHERE department_code = %s",
                (code,)
            )
            if dept_name:
                print(f"   ✅ {code} → {dept_name[0]['department_name']}")
        else:
            print(f"   ❌ {code} → NOT FOUND")
    
    # Check for 4-letter main codes
    main_codes = set()
    for code in db_codes:
        if len(code) == 4:
            main_codes.add(code)
    
    print(f"\n📊 Main Department Codes (4 letters): {len(main_codes)}")
    print(f"📊 Sub-department Codes (6+ letters): {len(db_codes) - len(main_codes)}")
    
    db.close()

def main():
    """Main function"""
    print("📋 Department Codes Database Loader")
    print("=" * 50)
    
    # Load department codes
    if load_department_codes_from_csv():
        print("\n✅ Department codes loaded successfully!")
        
        # Verify mapping
        verify_department_mapping()
        
        print("\n🎉 Department code loading completed!")
        print("\n📋 Next steps:")
        print("1. The database now has all department codes from your CSV")
        print("2. Gross profit reports will be properly mapped to departments")
        print("3. You can run the email monitor to process new reports")
        
    else:
        print("\n❌ Failed to load department codes")

if __name__ == "__main__":
    main() 