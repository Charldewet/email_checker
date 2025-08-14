#!/usr/bin/env python3
"""
Extract Top 20 Products by Sales Value
=====================================

This script extracts the top 20 products by sales value for REITZ pharmacy 
for the most recent available date in the pipeline data.
"""

import json
from typing import List, Dict, Any
from datetime import datetime

def find_most_recent_date(data_file: str, pharmacy: str) -> str:
    """Find the most recent date available in the pipeline data for a specific pharmacy"""
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    dates = []
    for key in data.keys():
        if key.startswith(f"{pharmacy}_"):
            # Extract date from key like "REITZ_2025-08-06"
            date_str = key.split("_", 1)[1]
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_obj)
            except ValueError:
                continue
    
    if not dates:
        raise ValueError(f"No dates found for pharmacy {pharmacy}")
    
    # Return the most recent date
    most_recent = max(dates)
    return most_recent.strftime("%Y-%m-%d")

def extract_top_products(data_file: str, pharmacy: str, date: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Extract top products by sales value for a specific pharmacy and date.
    
    Args:
        data_file: Path to the complete pipeline data JSON file
        pharmacy: Pharmacy code to filter by
        date: Date to filter by
        limit: Number of top products to return
    
    Returns:
        List of product dictionaries sorted by sales value
    """
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Find the specific pharmacy/date combination
    key = f"{pharmacy}_{date}"
    if key not in data:
        print(f"❌ No data found for {pharmacy} on {date}")
        return []
    
    pharmacy_data = data[key]
    
    # Extract sales details
    if 'gross_profit_summary' not in pharmacy_data or 'sales_details' not in pharmacy_data['gross_profit_summary']:
        print(f"❌ No sales details found for {pharmacy} on {date}")
        return []
    
    sales_details = pharmacy_data['gross_profit_summary']['sales_details']
    
    # Filter products with sales value > 0
    products = [p for p in sales_details if p.get('sales_value', 0) > 0]
    
    # Sort by sales value (descending)
    products.sort(key=lambda x: x.get('sales_value', 0), reverse=True)
    
    # Return top N products
    return products[:limit]

def main():
    """Main function to extract and display top products"""
    
    data_file = "complete_pipeline_data.json"
    pharmacy = "REITZ"
    
    try:
        # Find the most recent date available
        most_recent_date = find_most_recent_date(data_file, pharmacy)
        print(f"🔍 Extracting top products from pipeline data...")
        print(f"📅 Most recent date available: {most_recent_date}")
        
        # Extract top products for the most recent date
        top_products = extract_top_products(data_file, pharmacy, most_recent_date)
        
        if not top_products:
            print(f"❌ No products found for {pharmacy} on {most_recent_date}")
            return
        
        # Display results
        print(f"\n🏆 TOP 20 PRODUCTS BY SALES VALUE")
        print(f"🏪 Pharmacy: {pharmacy}")
        print(f"📅 Date: {most_recent_date}")
        print("=" * 80)
        
        # Header
        print(f"{'Rank':<4} {'Sales Value':<12} {'Product Description':<50} {'Dept':<6} {'Qty':<6} {'GP %':<8}")
        print("-" * 80)
        
        total_sales = 0
        total_products = len(top_products)
        
        for i, product in enumerate(top_products, 1):
            sales_value = product.get('sales_value', 0)
            description = product.get('description', 'N/A')[:48]
            dept = product.get('department_code', 'N/A')
            qty = product.get('sales_qty', 0)
            gp_percent = product.get('gross_profit_percent', 0)
            
            # Format sales value with R prefix
            formatted_value = f"R{sales_value:,.2f}"
            
            print(f"{i:<4} {formatted_value:<12} {description:<50} {dept:<6} {qty:<6} {gp_percent:<8.1f}")
            
            total_sales += sales_value
        
        # Summary
        print("-" * 80)
        print(f"📊 Total Sales Value: R{total_sales:,.2f}")
        print(f"📦 Total Products: {total_products}")
        print(f"📈 Average Sales Value: R{total_sales/total_products:,.2f}")
        print(f"🔥 Highest Sales Value: R{top_products[0].get('sales_value', 0):,.2f}")
        print(f"💧 Lowest Sales Value: R{top_products[-1].get('sales_value', 0):,.2f}")
        
        # Department analysis
        dept_sales = {}
        for product in top_products:
            dept = product.get('department_code', 'N/A')
            sales = product.get('sales_value', 0)
            dept_sales[dept] = dept_sales.get(dept, 0) + sales
        
        print(f"\n💡 INSIGHTS:")
        print(f"🏷️  Top Departments by Sales:")
        sorted_depts = sorted(dept_sales.items(), key=lambda x: x[1], reverse=True)
        for dept, sales in sorted_depts[:5]:
            print(f"   • {dept}: R{sales:,.2f}")
        
        # High margin products
        high_margin = [p for p in top_products if p.get('gross_profit_percent', 0) > 40]
        if high_margin:
            print(f"\n💰 High Margin Products (>40% GP):")
            for product in high_margin[:3]:
                desc = product.get('description', 'N/A')[:40]
                gp = product.get('gross_profit_percent', 0)
                print(f"   • {desc}... ({gp:.1f}% GP)")
        
    except FileNotFoundError:
        print(f"❌ Error: {data_file} not found")
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {data_file}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 