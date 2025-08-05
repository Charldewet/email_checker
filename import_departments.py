"""
Import Department Codes from CSV

This script imports the real department codes from the Departments.csv file
into the pharmacy reporting database.
"""

import csv
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_connection import PharmacyDatabase


def read_departments_csv(csv_file_path: str) -> list:
    """
    Read department codes from CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        List of tuples (department_code, department_name)
    """
    departments = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                dept_code = row['Department Code'].strip()
                dept_name = row['Department Name'].strip()
                
                # Skip empty rows
                if dept_code and dept_name:
                    departments.append((dept_code, dept_name))
        
        print(f"✅ Read {len(departments)} departments from CSV")
        return departments
        
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return []


def import_departments_to_database(departments: list) -> bool:
    """
    Import departments into the database.
    
    Args:
        departments: List of (code, name) tuples
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db = PharmacyDatabase()
        
        # Test connection
        if not db.test_connection():
            print("❌ Database connection failed")
            return False
        
        # Import departments
        success = db.insert_department_codes(departments)
        
        if success:
            print(f"✅ Successfully imported {len(departments)} departments")
            return True
        else:
            print("❌ Failed to import departments")
            return False
            
    except Exception as e:
        print(f"❌ Error importing departments: {e}")
        return False


def display_department_summary(departments: list):
    """
    Display a summary of the departments being imported.
    
    Args:
        departments: List of (code, name) tuples
    """
    print(f"\n📋 Department Import Summary:")
    print(f"   Total departments: {len(departments)}")
    
    # Show first 10 departments as preview
    print(f"\n   Preview (first 10):")
    for i, (code, name) in enumerate(departments[:10], 1):
        print(f"   {i:2d}. {code} - {name}")
    
    if len(departments) > 10:
        print(f"   ... and {len(departments) - 10} more departments")
    
    # Show some interesting categories
    categories = {
        'Beauty & Skincare': [dept for code, dept in departments if code.startswith('BA')],
        'Fragrance': [dept for code, dept in departments if code.startswith('BP')],
        'Baby Care': [dept for code, dept in departments if code.startswith('FB')],
        'FMCG': [dept for code, dept in departments if code.startswith('FD')],
        'Health & Nutrition': [dept for code, dept in departments if code.startswith('HS')],
        'Medical': [dept for code, dept in departments if code.startswith('MA')],
        'OTC Medicines': [dept for code, dept in departments if code.startswith('PD')],
        'Surgical': [dept for code, dept in departments if code.startswith('NA') or code.startswith('OA')],
        'Footwear': [dept for code, dept in departments if code.startswith('SA') or code.startswith('SB')],
        'Services': [dept for code, dept in departments if code.startswith('ZA')]
    }
    
    print(f"\n   Categories by department code:")
    for category, dept_list in categories.items():
        if dept_list:
            print(f"   {category}: {len(dept_list)} departments")


def main():
    """
    Main function to import departments.
    """
    print("🏥 Pharmacy Department Import Tool")
    print("=" * 50)
    
    # Find the CSV file
    csv_paths = [
        "Departments/Departments.csv",
        "Departments.csv",
        "./Departments/Departments.csv"
    ]
    
    csv_file = None
    for path in csv_paths:
        if Path(path).exists():
            csv_file = path
            break
    
    if not csv_file:
        print("❌ Departments.csv file not found!")
        print("   Please ensure the file is in one of these locations:")
        for path in csv_paths:
            print(f"   - {path}")
        return False
    
    print(f"📁 Found CSV file: {csv_file}")
    
    # Read departments from CSV
    departments = read_departments_csv(csv_file)
    
    if not departments:
        print("❌ No departments found in CSV file")
        return False
    
    # Display summary
    display_department_summary(departments)
    
    # Confirm import
    print(f"\n⚠️  This will replace any existing department codes in the database.")
    response = input("   Continue with import? (y/n): ").lower().strip()
    
    if response not in ['y', 'yes']:
        print("❌ Import cancelled")
        return False
    
    # Import to database
    print(f"\n🔄 Importing departments to database...")
    success = import_departments_to_database(departments)
    
    if success:
        print(f"\n🎉 Department import completed successfully!")
        print(f"\n📊 You can now use these department codes when importing sales data.")
        print(f"   Example: Use 'PDOA' for 'OTC STOMACH' products")
        
        # Show some examples
        print(f"\n💡 Example department codes:")
        example_depts = [
            ('PDOA', 'OTC STOMACH'),
            ('PDOB', 'OTC ANALGESICS'),
            ('PDOT', 'VITAMINS AND MINERALS'),
            ('BAAA', 'ANTI AGEING'),
            ('FBBB', 'BABY FOODS'),
            ('MAHR', 'PAIN RELIEF')
        ]
        
        for code, name in example_depts:
            print(f"   {code} - {name}")
            
    else:
        print(f"\n❌ Department import failed!")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nImport interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Import failed with error: {e}")
        sys.exit(1) 