#!/usr/bin/env python3
"""
Check Latest Reitz Turnover
===========================

This script queries the deployed database to find the latest turnover data for Reitz pharmacy.
"""

import os
import sys
from datetime import datetime
from render_database_connection import RenderPharmacyDatabase

def main():
    """Check the latest turnover for Reitz pharmacy"""
    try:
        # Initialize database connection
        print("🔌 Connecting to Render PostgreSQL database...")
        db = RenderPharmacyDatabase()
        
        # Query for the latest Reitz turnover data
        query = """
        SELECT 
            p.pharmacy_code,
            p.name as pharmacy_name,
            ds.report_date,
            ds.turnover,
            ds.gp_percent,
            ds.gp_value,
            ds.cost_of_sales,
            ds.transactions_total,
            ds.avg_basket_value,
            ds.upload_time
        FROM daily_summary ds
        JOIN pharmacies p ON ds.pharmacy_id = p.id
        WHERE p.pharmacy_code = 'REITZ'
        ORDER BY ds.report_date DESC
        LIMIT 1
        """
        
        print("📊 Querying latest Reitz turnover data...")
        result = db.execute_query(query)
        
        if not result:
            print("❌ No turnover data found for Reitz pharmacy")
            return
        
        # Display the results
        data = result[0]
        print("\n" + "="*60)
        print("🏪 REITZ PHARMACY - LATEST TURNOVER DATA")
        print("="*60)
        print(f"Pharmacy Code:     {data['pharmacy_code']}")
        print(f"Pharmacy Name:     {data['pharmacy_name']}")
        print(f"Report Date:       {data['report_date']}")
        print(f"Upload Time:       {data['upload_time']}")
        print("\n💰 FINANCIAL SUMMARY:")
        print(f"Turnover:          R{data['turnover']:,.2f}" if data['turnover'] else "Turnover:          Not available")
        print(f"Gross Profit:      R{data['gp_value']:,.2f} ({data['gp_percent']:.1f}%)" if data['gp_value'] and data['gp_percent'] else "Gross Profit:      Not available")
        print(f"Cost of Sales:     R{data['cost_of_sales']:,.2f}" if data['cost_of_sales'] else "Cost of Sales:     Not available")
        print(f"Transactions:      {data['transactions_total']:,.0f}" if data['transactions_total'] else "Transactions:      Not available")
        print(f"Avg Basket Value:  R{data['avg_basket_value']:,.2f}" if data['avg_basket_value'] else "Avg Basket Value:  Not available")
        print("="*60)
        
        # Also show the last 5 dates for context
        print("\n📅 RECENT TURNOVER HISTORY:")
        history_query = """
        SELECT 
            ds.report_date,
            ds.turnover
        FROM daily_summary ds
        JOIN pharmacies p ON ds.pharmacy_id = p.id
        WHERE p.pharmacy_code = 'REITZ'
        AND ds.turnover IS NOT NULL
        ORDER BY ds.report_date DESC
        LIMIT 5
        """
        
        history = db.execute_query(history_query)
        if history:
            for record in history:
                print(f"{record['report_date']}: R{record['turnover']:,.2f}")
        else:
            print("No recent turnover history found")
        
        print("\n✅ Query completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 