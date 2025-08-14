#!/usr/bin/env python3
"""
Test New API Endpoints
======================

This script tests the new top products endpoints locally to ensure they work
before deploying to Render.
"""

import requests
import json
from datetime import datetime

def test_local_endpoints():
    """Test the new endpoints locally"""
    
    base_url = "http://localhost:5000"  # Local Flask development server
    
    print("🧪 Testing new API endpoints locally...")
    print("=" * 50)
    
    # Test 1: Database connection test
    print("\n1️⃣ Testing database connection...")
    try:
        response = requests.get(f"{base_url}/api/db_test", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data.get('message', 'Success')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 2: Top products by value (using pharmacy code)
    print("\n2️⃣ Testing top products by value endpoint...")
    try:
        response = requests.get(
            f"{base_url}/api/stock/top_products_by_value_pharmacy/REITZ/2025-08-06",
            params={'limit': 5},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {len(data.get('products', []))} products")
            print(f"   📊 Total sales value: R{data.get('summary', {}).get('total_sales_value', 0):,.2f}")
            
            # Show first product
            if data.get('products'):
                first_product = data['products'][0]
                print(f"   🥇 Top product: {first_product.get('description', 'Unknown')[:40]}...")
                print(f"      Sales value: R{first_product.get('sales_value', 0):,.2f}")
        else:
            print(f"   ❌ Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: System status
    print("\n3️⃣ Testing system status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System status: {data.get('status', 'Unknown')}")
            if 'database' in data:
                db_info = data['database']
                print(f"   📊 Pharmacies: {db_info.get('total_pharmacies', 0)}")
                print(f"   📊 Daily summaries: {db_info.get('total_daily_summaries', 0)}")
                print(f"   📊 Sales records: {db_info.get('total_sales_records', 0)}")
        else:
            print(f"   ❌ Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")

def test_render_endpoints():
    """Test the endpoints on Render (if accessible)"""
    
    base_url = "https://email-checker-c5lw.onrender.com"
    
    print("\n🌐 Testing Render API endpoints...")
    print("=" * 50)
    
    # Test 1: Simple health check
    print("\n1️⃣ Testing Render health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Service: {data.get('service', 'Unknown')}")
            print(f"   ✅ Status: {data.get('status', 'Unknown')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 2: Database test
    print("\n2️⃣ Testing Render database connection...")
    try:
        response = requests.get(f"{base_url}/api/db_test", timeout=15)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data.get('message', 'Success')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Render testing completed!")

def main():
    """Main function"""
    
    print("🚀 API Endpoint Testing Suite")
    print("=" * 50)
    
    # Test local endpoints first
    test_local_endpoints()
    
    # Then test Render endpoints
    test_render_endpoints()
    
    print("\n💡 Next Steps:")
    print("   1. If local tests pass, your endpoints are working correctly")
    print("   2. If Render tests fail, there may be a deployment issue")
    print("   3. Deploy the updated code to Render to enable the new endpoints")
    print("   4. Use the new endpoints to get top products data via API")

if __name__ == "__main__":
    main() 