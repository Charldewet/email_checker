#!/usr/bin/env python3
"""
Get Top Products via API
========================

This script demonstrates how to use the new API endpoints to get top products
by sales value for REITZ pharmacy on August 6th, 2025.
"""

import requests
import json
from datetime import datetime

def get_top_products_via_api(pharmacy_code="REITZ", date="2025-08-06", limit=20):
    """
    Get top products by sales value using the new API endpoint.
    
    Args:
        pharmacy_code: Pharmacy code (e.g., 'REITZ')
        date: Date in YYYY-MM-DD format
        limit: Number of top products to return
    
    Returns:
        Dictionary containing products and summary data
    """
    
    # API endpoint URL
    base_url = "https://email-checker-c5lw.onrender.com"
    endpoint = f"/api/stock/top_products_by_value_pharmacy/{pharmacy_code}/{date}"
    
    # Parameters
    params = {'limit': limit}
    
    print(f"🔍 Fetching top {limit} products for {pharmacy_code} on {date}...")
    print(f"🌐 API Endpoint: {base_url}{endpoint}")
    print("=" * 60)
    
    try:
        # Make API request
        response = requests.get(
            f"{base_url}{endpoint}",
            params=params,
            timeout=30
        )
        
        # Check response status
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - API may be slow or unresponsive")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def display_top_products(data):
    """Display the top products in a formatted table."""
    
    if not data or 'products' not in data:
        print("❌ No product data received")
        return
    
    products = data['products']
    summary = data.get('summary', {})
    
    print(f"\n🏆 TOP {len(products)} PRODUCTS BY SALES VALUE")
    print(f"🏪 Pharmacy: {data.get('pharmacy_code', 'Unknown')}")
    print(f"📅 Date: {data.get('date', 'Unknown')}")
    print("=" * 80)
    
    # Header
    print(f"{'Rank':<4} {'Sales Value':<12} {'Product Description':<50} {'Dept':<6} {'Qty':<4} {'GP %':<6}")
    print("-" * 80)
    
    for i, product in enumerate(products, 1):
        sales_value = product.get('sales_value', 0)
        description = product.get('description', 'Unknown')
        department = product.get('department_code', 'N/A')
        quantity = product.get('sales_qty', 0)
        gp_percent = product.get('gross_profit_percent', 0)
        
        # Truncate description if too long
        if len(description) > 47:
            description = description[:44] + "..."
        
        print(f"{i:<4} R{sales_value:<11,.2f} {description:<50} {department:<6} {quantity:<4} {gp_percent:<6.1f}%")
    
    print("-" * 80)
    
    # Summary statistics
    if summary:
        print(f"📊 Total Sales Value: R{summary.get('total_sales_value', 0):,.2f}")
        print(f"📦 Total Products: {summary.get('product_count', 0)}")
        print(f"📈 Average Sales Value: R{summary.get('average_sales_value', 0):,.2f}")
        print(f"🔥 Highest Sales Value: R{summary.get('highest_sales_value', 0):,.2f}")
        print(f"💧 Lowest Sales Value: R{summary.get('lowest_sales_value', 0):,.2f}")

def test_api_endpoints():
    """Test various API endpoints to check service health."""
    
    base_url = "https://email-checker-c5lw.onrender.com"
    
    print("🧪 Testing API Service Health...")
    print("=" * 40)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"🏥 Health Check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Service: {data.get('service', 'Unknown')}")
            print(f"   ✅ Status: {data.get('status', 'Unknown')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: Database test
    try:
        response = requests.get(f"{base_url}/api/db_test", timeout=15)
        print(f"🗄️ Database Test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data.get('message', 'Success')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print()

def main():
    """Main function"""
    
    print("🚀 Pharmacy Top Products API Demo")
    print("=" * 50)
    
    # First test API health
    test_api_endpoints()
    
    # Then get top products
    data = get_top_products_via_api(
        pharmacy_code="REITZ",
        date="2025-08-06",
        limit=20
    )
    
    if data:
        display_top_products(data)
        
        print(f"\n💡 API Usage Examples:")
        print(f"   • Get top 10 products: GET /api/stock/top_products_by_value_pharmacy/REITZ/2025-08-06?limit=10")
        print(f"   • Get top 50 products: GET /api/stock/top_products_by_value_pharmacy/REITZ/2025-08-06?limit=50")
        print(f"   • Different pharmacy: GET /api/stock/top_products_by_value_pharmacy/TLC%20WINTERTON/2025-08-06")
        print(f"   • Different date: GET /api/stock/top_products_by_value_pharmacy/REITZ/2025-08-05")
        
    else:
        print("\n❌ Failed to retrieve data from API")
        print("💡 Possible issues:")
        print("   1. API service is down or slow")
        print("   2. Database connection issues")
        print("   3. No data available for the specified date")
        print("   4. API endpoint not yet deployed")

if __name__ == "__main__":
    main() 