#!/usr/bin/env python3
"""
Top Selling Products Query
==========================

This script queries the database to find the top-selling products for each pharmacy
based on sales quantity from the gross profit reports.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

def load_gross_profit_data() -> List[Dict]:
    """Load gross profit data from JSON files"""
    try:
        with open("gross_profit_extracted_data.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Gross profit data not found. Please run the data pipeline first.")
        return []

def analyze_top_selling_products(data: List[Dict], top_n: int = 10) -> Dict[str, List[Dict]]:
    """
    Analyze top selling products for each pharmacy
    
    Args:
        data: List of gross profit data dictionaries
        top_n: Number of top products to return
    
    Returns:
        Dictionary with pharmacy as key and list of top products as value
    """
    pharmacy_products = {}
    
    for report in data:
        pharmacy = report['pharmacy']
        date = report['date']
        sales_details = report.get('sales_details', [])
        
        if pharmacy not in pharmacy_products:
            pharmacy_products[pharmacy] = []
        
        # Add all products for this pharmacy
        for product in sales_details:
            product_info = {
                'pharmacy': pharmacy,
                'date': date,
                'department_code': product.get('department_code', ''),
                'stock_code': product.get('stock_code', ''),
                'description': product.get('description', ''),
                'sales_qty': product.get('sales_qty', 0),
                'sales_value': product.get('sales_value', 0),
                'sales_cost': product.get('sales_cost', 0),
                'gross_profit': product.get('gross_profit', 0),
                'gross_profit_percent': product.get('gross_profit_percent', 0)
            }
            pharmacy_products[pharmacy].append(product_info)
    
    # Sort products by sales quantity for each pharmacy
    top_products = {}
    for pharmacy, products in pharmacy_products.items():
        # Sort by sales quantity (descending)
        sorted_products = sorted(products, key=lambda x: x['sales_qty'], reverse=True)
        top_products[pharmacy] = sorted_products[:top_n]
    
    return top_products

def display_top_selling_products(top_products: Dict[str, List[Dict]], top_n: int = 10):
    """Display top selling products in a formatted way"""
    print(f"\n{'='*100}")
    print(f"🏆 TOP {top_n} SELLING PRODUCTS BY QUANTITY")
    print(f"{'='*100}")
    
    for pharmacy, products in top_products.items():
        print(f"\n🏪 {pharmacy}")
        print("-" * 100)
        print(f"{'Rank':<4} {'Stock Code':<12} {'Description':<40} {'Qty':<6} {'Value':<12} {'GP %':<8}")
        print("-" * 100)
        
        for i, product in enumerate(products, 1):
            description = product['description'][:38] + "..." if len(product['description']) > 40 else product['description']
            print(f"{i:<4} {product['stock_code']:<12} {description:<40} {product['sales_qty']:<6.0f} "
                  f"R{product['sales_value']:<10.2f} {product['gross_profit_percent']:<7.2f}%")
        
        # Calculate summary statistics
        total_qty = sum(p['sales_qty'] for p in products)
        total_value = sum(p['sales_value'] for p in products)
        avg_gp_percent = sum(p['gross_profit_percent'] for p in products) / len(products) if products else 0
        
        print("-" * 100)
        print(f"📊 Top {top_n} Summary: {total_qty:.0f} items, R{total_value:,.2f} value, {avg_gp_percent:.2f}% avg GP")

def analyze_by_department(top_products: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """Analyze top products by department"""
    department_analysis = {}
    
    for pharmacy, products in top_products.items():
        if pharmacy not in department_analysis:
            department_analysis[pharmacy] = {}
        
        for product in products:
            dept = product['department_code']
            if dept not in department_analysis[pharmacy]:
                department_analysis[pharmacy][dept] = {
                    'total_qty': 0,
                    'total_value': 0,
                    'product_count': 0,
                    'products': []
                }
            
            dept_data = department_analysis[pharmacy][dept]
            dept_data['total_qty'] += product['sales_qty']
            dept_data['total_value'] += product['sales_value']
            dept_data['product_count'] += 1
            dept_data['products'].append(product)
    
    return department_analysis

def display_department_analysis(department_analysis: Dict[str, Dict]):
    """Display department analysis"""
    print(f"\n{'='*100}")
    print(f"📊 DEPARTMENT ANALYSIS - TOP SELLING PRODUCTS")
    print(f"{'='*100}")
    
    for pharmacy, departments in department_analysis.items():
        print(f"\n🏪 {pharmacy}")
        print("-" * 100)
        print(f"{'Department':<10} {'Products':<10} {'Total Qty':<12} {'Total Value':<15} {'Avg Qty/Product':<15}")
        print("-" * 100)
        
        # Sort departments by total quantity
        sorted_depts = sorted(departments.items(), key=lambda x: x[1]['total_qty'], reverse=True)
        
        for dept_code, dept_data in sorted_depts:
            avg_qty = dept_data['total_qty'] / dept_data['product_count'] if dept_data['product_count'] > 0 else 0
            print(f"{dept_code:<10} {dept_data['product_count']:<10} {dept_data['total_qty']:<12.0f} "
                  f"R{dept_data['total_value']:<14.2f} {avg_qty:<15.2f}")

def create_sql_queries(top_products: Dict[str, List[Dict]]) -> str:
    """Create SQL queries for database analysis"""
    sql_queries = []
    
    for pharmacy, products in top_products.items():
        # Create a query to find top products for this pharmacy
        sql = f"""
-- Top selling products for {pharmacy}
SELECT 
    sd.department_code,
    sd.stock_code,
    sd.description,
    sd.sales_qty,
    sd.sales_value,
    sd.gross_profit,
    sd.gross_profit_percent,
    p.name as pharmacy_name,
    ds.report_date
FROM sales_details sd
JOIN daily_summary ds ON sd.pharmacy_id = ds.pharmacy_id AND sd.report_date = ds.report_date
JOIN pharmacies p ON sd.pharmacy_id = p.id
WHERE p.pharmacy_code = '{pharmacy}'
ORDER BY sd.sales_qty DESC
LIMIT 10;
"""
        sql_queries.append(sql)
    
    return "\n".join(sql_queries)

def save_analysis_results(top_products: Dict[str, List[Dict]], department_analysis: Dict[str, Dict]):
    """Save analysis results to files"""
    
    # Save top products to JSON
    with open("top_selling_products.json", 'w') as f:
        json.dump(top_products, f, indent=2, default=str)
    
    # Save department analysis to JSON
    with open("department_analysis.json", 'w') as f:
        json.dump(department_analysis, f, indent=2, default=str)
    
    # Create CSV files for each pharmacy
    for pharmacy, products in top_products.items():
        df = pd.DataFrame(products)
        csv_filename = f"top_products_{pharmacy.replace(' ', '_')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"📊 Saved: {csv_filename}")
    
    # Create SQL queries file
    sql_queries = create_sql_queries(top_products)
    with open("top_products_queries.sql", 'w') as f:
        f.write("-- Top Selling Products Database Queries\n")
        f.write("-- Generated by Pharmacy Data Analysis\n\n")
        f.write(sql_queries)
    
    print(f"📊 Saved: top_selling_products.json")
    print(f"📊 Saved: department_analysis.json")
    print(f"📊 Saved: top_products_queries.sql")

def main():
    """Main function to run the top selling products analysis"""
    print("🔍 ANALYZING TOP SELLING PRODUCTS")
    print("=" * 60)
    
    # Load data
    data = load_gross_profit_data()
    if not data:
        return
    
    print(f"📊 Loaded data for {len(data)} reports")
    
    # Analyze top selling products
    top_n = 10  # Number of top products to analyze
    top_products = analyze_top_selling_products(data, top_n)
    
    # Display results
    display_top_selling_products(top_products, top_n)
    
    # Analyze by department
    department_analysis = analyze_by_department(top_products)
    display_department_analysis(department_analysis)
    
    # Save results
    save_analysis_results(top_products, department_analysis)
    
    print(f"\n✅ Analysis complete! Check the generated files for detailed results.")

if __name__ == "__main__":
    main()