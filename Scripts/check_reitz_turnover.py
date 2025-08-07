#!/usr/bin/env python3
"""
Check Reitz Turnover Data
=========================

This script uses the database API endpoints to query turnover data for Reitz pharmacy.
"""

import os
import sys
from datetime import datetime
import requests
from flask import Flask

# Add Scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from render_database_connection import RenderPharmacyDatabase
from api_endpoints import register_all_endpoints

def create_test_app():
    """Create a test Flask app with API endpoints for direct database queries"""
    app = Flask(__name__)
    
    try:
        db = RenderPharmacyDatabase()
        register_all_endpoints(app, db)
        print("✅ API endpoints registered successfully")
        return app, db
    except Exception as e:
        print(f"❌ Failed to create test app: {e}")
        return None, None

def check_reitz_turnover_direct(db):
    """Query Reitz turnover data directly from database"""
    print("\n" + "="*60)
    print("🏪 REITZ TURNOVER DATA - DIRECT DATABASE QUERY")
    print("="*60)
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Checking for date: {today}")
    
    # Get pharmacy ID for REITZ
    pharmacy_id = db.get_pharmacy_id_by_code('REITZ')
    if not pharmacy_id:
        print("❌ REITZ pharmacy not found in database")
        return
    
    print(f"🏪 Pharmacy ID for REITZ: {pharmacy_id}")
    
    # Query latest turnover data
    print("\n🔍 Querying latest turnover data...")
    query = """
    SELECT 
        ds.report_date,
        ds.turnover,
        ds.gp_value,
        ds.gp_percent,
        ds.transactions_total,
        ds.avg_basket_value,
        ds.script_total,
        ds.disp_turnover,
        p.pharmacy_code,
        p.name as pharmacy_name
    FROM daily_summary ds
    JOIN pharmacies p ON ds.pharmacy_id = p.id
    WHERE ds.pharmacy_id = %s 
    ORDER BY ds.report_date DESC 
    LIMIT 5
    """
    
    try:
        results = db.execute_query(query, (pharmacy_id,))
        
        if not results:
            print("❌ No turnover data found for REITZ")
            return
        
        print(f"\n📊 Found {len(results)} recent records:")
        print("-" * 60)
        
        for i, record in enumerate(results):
            print(f"\n📅 Record {i+1}: {record['report_date']}")
            print(f"   💰 Turnover: R{record['turnover']:,.2f}" if record['turnover'] else "   💰 Turnover: N/A")
            print(f"   📈 GP Value: R{record['gp_value']:,.2f}" if record['gp_value'] else "   📈 GP Value: N/A")
            print(f"   📊 GP %: {record['gp_percent']:.2f}%" if record['gp_percent'] else "   📊 GP %: N/A")
            print(f"   🛒 Transactions: {record['transactions_total']:,}" if record['transactions_total'] else "   🛒 Transactions: N/A")
            print(f"   💳 Avg Basket: R{record['avg_basket_value']:,.2f}" if record['avg_basket_value'] else "   💳 Avg Basket: N/A")
            print(f"   💊 Scripts: {record['script_total']:,}" if record['script_total'] else "   💊 Scripts: N/A")
            print(f"   🏥 Disp Turnover: R{record['disp_turnover']:,.2f}" if record['disp_turnover'] else "   🏥 Disp Turnover: N/A")
            
            # Check if this is today's data
            if record['report_date'].strftime('%Y-%m-%d') == today:
                print("   ✅ THIS IS TODAY'S DATA!")
            
        # Check specifically for today's data
        print(f"\n🔍 Checking specifically for today's data ({today})...")
        today_query = """
        SELECT 
            ds.report_date,
            ds.turnover,
            ds.gp_value,
            ds.gp_percent,
            ds.transactions_total,
            ds.avg_basket_value,
            ds.script_total,
            ds.disp_turnover
        FROM daily_summary ds
        WHERE ds.pharmacy_id = %s 
        AND ds.report_date = %s
        """
        
        today_results = db.execute_query(today_query, (pharmacy_id, today))
        
        if today_results:
            record = today_results[0]
            print("\n🎉 TODAY'S TURNOVER DATA FOUND!")
            print("=" * 40)
            print(f"📅 Date: {record['report_date']}")
            print(f"💰 Turnover: R{record['turnover']:,.2f}" if record['turnover'] else "💰 Turnover: N/A")
            print(f"📈 GP Value: R{record['gp_value']:,.2f}" if record['gp_value'] else "📈 GP Value: N/A")
            print(f"📊 GP %: {record['gp_percent']:.2f}%" if record['gp_percent'] else "📊 GP %: N/A")
            print(f"🛒 Transactions: {record['transactions_total']:,}" if record['transactions_total'] else "🛒 Transactions: N/A")
            print(f"💳 Avg Basket: R{record['avg_basket_value']:,.2f}" if record['avg_basket_value'] else "💳 Avg Basket: N/A")
            print(f"💊 Scripts: {record['script_total']:,}" if record['script_total'] else "💊 Scripts: N/A")
            print(f"🏥 Disp Turnover: R{record['disp_turnover']:,.2f}" if record['disp_turnover'] else "🏥 Disp Turnover: N/A")
        else:
            print(f"❌ No data found for today ({today})")
            print("💡 Latest available data shown above")
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")

def check_available_dates(db):
    """Check what dates have data available for Reitz"""
    print("\n" + "="*60)
    print("📅 AVAILABLE DATES FOR REITZ")
    print("="*60)
    
    pharmacy_id = db.get_pharmacy_id_by_code('REITZ')
    if not pharmacy_id:
        print("❌ REITZ pharmacy not found in database")
        return
    
    query = """
    SELECT 
        report_date,
        turnover,
        upload_time
    FROM daily_summary
    WHERE pharmacy_id = %s
    ORDER BY report_date DESC
    """
    
    try:
        results = db.execute_query(query, (pharmacy_id,))
        
        if not results:
            print("❌ No data found for REITZ")
            return
        
        print(f"📊 Found data for {len(results)} dates:")
        print("-" * 40)
        
        for record in results:
            print(f"📅 {record['report_date']} - R{record['turnover']:,.2f} - Uploaded: {record['upload_time']}")
            
    except Exception as e:
        print(f"❌ Error querying available dates: {e}")

def main():
    """Main function to check Reitz turnover data"""
    print("🚀 Starting Reitz Turnover Check...")
    
    # Create test app with database connection
    app, db = create_test_app()
    
    if not db:
        print("❌ Failed to connect to database")
        return
    
    # Check available dates first
    check_available_dates(db)
    
    # Check turnover data
    check_reitz_turnover_direct(db)
    
    print("\n✅ Reitz turnover check completed!")

if __name__ == "__main__":
    main() 