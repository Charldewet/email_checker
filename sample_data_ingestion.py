"""
Sample Data Ingestion Script for Pharmacy Reporting System

This script demonstrates how to:
1. Connect to the database
2. Insert sample pharmacy data
3. Insert sample daily summary reports
4. Insert sample sales details
5. Query and analyze the data
"""

import sys
import os
from datetime import date, timedelta
from decimal import Decimal
import random

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_connection import PharmacyDatabase


def create_sample_data():
    """
    Create sample data for demonstration purposes.
    """
    
    # Initialize database connection
    db = PharmacyDatabase()
    
    print("🚀 Starting sample data ingestion...")
    
    # Test database connection
    if not db.test_connection():
        print("❌ Database connection failed. Please check your connection parameters.")
        return False
    
    print("✅ Database connection successful")
    
    # Step 1: Insert sample pharmacies
    print("\n📋 Inserting sample pharmacies...")
    pharmacies = [
        ("REITZ", "Reitz Pharmacy"),
        ("BLOEM", "Bloemfontein Pharmacy"),
        ("JHB001", "Johannesburg Central Pharmacy"),
        ("CT001", "Cape Town Pharmacy"),
        ("DURBAN", "Durban Pharmacy")
    ]
    
    for code, name in pharmacies:
        pharmacy_id = db.insert_pharmacy(code, name)
        if pharmacy_id:
            print(f"  ✅ {name} ({code}) - ID: {pharmacy_id}")
        else:
            print(f"  ❌ Failed to insert {name}")
    
    # Step 2: Insert sample daily summary data
    print("\n📊 Inserting sample daily summary data...")
    
    # Generate data for the last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    for pharmacy_code in ["REITZ", "BLOEM", "JHB001"]:
        current_date = start_date
        while current_date <= end_date:
            # Generate realistic sample data
            summary_data = {
                'turnover': round(random.uniform(15000, 45000), 2),
                'gp_percent': round(random.uniform(18, 25), 2),
                'gp_value': round(random.uniform(3000, 9000), 2),
                'cost_of_sales': round(random.uniform(12000, 36000), 2),
                'purchases': round(random.uniform(8000, 15000), 2),
                'avg_basket_value': round(random.uniform(85, 150), 2),
                'avg_basket_size': random.randint(3, 8),
                'transactions_total': random.randint(120, 300),
                'script_total': random.randint(80, 200),
                'avg_script_value': round(random.uniform(120, 250), 2),
                'disp_turnover': round(random.uniform(8000, 20000), 2),
                'stock_opening': round(random.uniform(80000, 120000), 2),
                'stock_closing': round(random.uniform(75000, 115000), 2),
                'adjustments': round(random.uniform(-500, 500), 2),
                'sales_cash': round(random.uniform(8000, 20000), 2),
                'sales_cod': round(random.uniform(2000, 8000), 2),
                'sales_account': round(random.uniform(5000, 15000), 2)
            }
            
            if db.insert_daily_summary(pharmacy_code, current_date, summary_data):
                print(f"  ✅ {pharmacy_code} - {current_date}")
            else:
                print(f"  ❌ Failed to insert summary for {pharmacy_code} - {current_date}")
            
            current_date += timedelta(days=1)
    
    # Step 3: Insert sample sales details
    print("\n🛍️ Inserting sample sales details...")
    
    # Sample product data using real department codes
    sample_products = [
        ("PDOB", "PAN001", "Panado 500mg Tablets", 100, 15, 45.50, 35.00, 10.50, 23.08),
        ("PDOB", "DIS001", "Disprin 500mg Tablets", 85, 12, 38.75, 28.50, 10.25, 26.45),
        ("PDOT", "VIT001", "Vitamin C 1000mg", 120, 8, 65.00, 45.00, 20.00, 30.77),
        ("FPBL", "SOAP001", "Hand Soap 500ml", 60, 5, 25.50, 18.00, 7.50, 29.41),
        ("HSNN", "PRO001", "Protein Powder 1kg", 45, 3, 180.00, 120.00, 60.00, 33.33),
        ("MAHD", "THERM001", "Digital Thermometer", 30, 2, 95.00, 65.00, 30.00, 31.58),
        ("FBBB", "BABY001", "Baby Formula 400g", 75, 10, 85.50, 60.00, 25.50, 29.82),
        ("BCCL", "LIP001", "Lip Balm 4.5g", 200, 25, 15.75, 10.50, 5.25, 33.33),
        ("FNHC", "CLEAN001", "Surface Cleaner 750ml", 40, 6, 35.00, 25.00, 10.00, 28.57),
        ("FNCD", "CHOC001", "Dark Chocolate 100g", 150, 20, 22.50, 15.00, 7.50, 33.33)
    ]
    
    # Insert sales details for a few recent days
    for pharmacy_code in ["REITZ", "BLOEM"]:
        for days_ago in range(7):  # Last 7 days
            report_date = end_date - timedelta(days=days_ago)
            
            # Generate random sales data for each product
            sales_data = []
            for dept_code, stock_code, description, base_soh, base_qty, base_value, base_cost, base_gp, base_gp_pct in sample_products:
                # Add some randomness to make data more realistic
                soh = max(0, base_soh + random.randint(-20, 20))
                sales_qty = max(0, base_qty + random.randint(-5, 5))
                sales_value = round(base_value * (sales_qty / base_qty) * random.uniform(0.8, 1.2), 2)
                sales_cost = round(base_cost * (sales_qty / base_qty) * random.uniform(0.8, 1.2), 2)
                gross_profit = sales_value - sales_cost
                gross_profit_percent = round((gross_profit / sales_value * 100) if sales_value > 0 else 0, 2)
                
                sales_data.append({
                    'department_code': dept_code,
                    'stock_code': stock_code,
                    'description': description,
                    'soh': soh,
                    'sales_qty': sales_qty,
                    'sales_value': sales_value,
                    'sales_cost': sales_cost,
                    'gross_profit': gross_profit,
                    'gross_profit_percent': gross_profit_percent
                })
            
            if db.insert_sales_details(pharmacy_code, report_date, sales_data):
                print(f"  ✅ {pharmacy_code} - {report_date} ({len(sales_data)} products)")
            else:
                print(f"  ❌ Failed to insert sales details for {pharmacy_code} - {report_date}")
    
    print("\n✅ Sample data ingestion completed!")
    return True


def demonstrate_queries():
    """
    Demonstrate various database queries and analysis.
    """
    
    print("\n🔍 Demonstrating database queries...")
    
    db = PharmacyDatabase()
    
    # Query 1: Get pharmacy performance for the last 7 days
    print("\n📈 Pharmacy Performance (Last 7 days):")
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    for pharmacy_code in ["REITZ", "BLOEM", "JHB001"]:
        performance = db.get_pharmacy_performance(pharmacy_code, start_date, end_date)
        if performance:
            print(f"\n  {pharmacy_code}:")
            for record in performance:
                print(f"    {record['report_date']}: Turnover R{record['turnover']:.2f}, "
                      f"GP R{record['gp_value']:.2f} ({record['gp_percent']:.1f}%)")
    
    # Query 2: Get top selling products
    print("\n🏆 Top Selling Products (Last 7 days):")
    for pharmacy_code in ["REITZ", "BLOEM"]:
        top_products = db.get_top_selling_products(pharmacy_code, start_date, end_date, limit=5)
        if top_products:
            print(f"\n  {pharmacy_code}:")
            for i, product in enumerate(top_products, 1):
                print(f"    {i}. {product['description']} - "
                      f"Qty: {product['total_sales_qty']}, "
                      f"Value: R{product['total_sales_value']:.2f}")
    
    # Query 3: Get daily summary view
    print("\n📊 Daily Summary Overview:")
    summaries = db.get_daily_summary_view(start_date=start_date, end_date=end_date)
    if summaries:
        for summary in summaries[:5]:  # Show first 5 records
            print(f"  {summary['pharmacy_name']} ({summary['report_date']}): "
                  f"Turnover R{summary['turnover']:.2f}, "
                  f"Transactions: {summary['transactions_total']}")


def main():
    """
    Main function to run the sample data ingestion and demonstration.
    """
    
    print("🏥 Pharmacy Reporting System - Sample Data Setup")
    print("=" * 50)
    
    # Create sample data
    if create_sample_data():
        # Demonstrate queries
        demonstrate_queries()
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Review the sample data in your database")
        print("2. Modify the connection parameters in database_connection.py if needed")
        print("3. Start extracting data from your PDF reports")
        print("4. Use the PharmacyDatabase class to insert your real data")
    else:
        print("\n❌ Setup failed. Please check your database connection and try again.")


if __name__ == "__main__":
    main() 