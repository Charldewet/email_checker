#!/usr/bin/env python3
"""
Insert Extracted Data to Render Database
========================================

This script inserts the extracted pharmacy data into the Render PostgreSQL database.
"""

import os
import json
from render_database_connection import RenderPharmacyDatabase

def insert_data_to_database():
    """Insert extracted data into the database"""
    print("🗄️ Inserting extracted data into Render database...")
    
    # Connect to database
    db = RenderPharmacyDatabase()
    
    # Load the combined data
    with open('complete_pipeline_data.json', 'r') as f:
        data = json.load(f)
    
    print(f"📊 Found {len(data)} pharmacy/date combinations to insert")
    
    success_count = 0
    for key, pharmacy_data in data.items():
        try:
            # Extract pharmacy and date
            pharmacy = pharmacy_data.get('pharmacy')
            date = pharmacy_data.get('date')
            
            print(f"\n🏪 Processing: {pharmacy} - {date}")
            
            # Prepare data for insertion
            insert_data = {
                'pharmacy_code': pharmacy,
                'report_date': date,
                'turnover': None,
                'gp_percent': None,
                'gp_value': None,
                'cost_of_sales': None,
                'purchases': None,
                'avg_basket_value': None,
                'avg_basket_size': None,
                'transactions_total': None,
                'script_total': None,
                'avg_script_value': None,
                'disp_turnover': None,
                'stock_opening': None,
                'stock_closing': None,
                'adjustments': None,
                'sales_cash': None,
                'sales_cod': None,
                'sales_account': None
            }
            
            # Extract trading summary data
            if 'trading_summary' in pharmacy_data:
                trading = pharmacy_data['trading_summary']
                insert_data.update({
                    'turnover': trading.get('turnover'),
                    'gp_percent': trading.get('gp_percent'),
                    'gp_value': trading.get('gp_value'),
                    'cost_of_sales': trading.get('cost_of_sales'),
                    'purchases': trading.get('purchases'),
                    'stock_opening': trading.get('stock_opening'),
                    'stock_closing': trading.get('stock_closing'),
                    'adjustments': trading.get('adjustments')
                })
            
            # Extract turnover summary data (overrides trading summary turnover)
            if 'turnover_summary' in pharmacy_data:
                turnover = pharmacy_data['turnover_summary']
                print(f"   📊 Turnover Summary Data: {turnover}")
                insert_data.update({
                    'turnover': turnover.get('turnover'),
                    'sales_cash': turnover.get('sales_cash'),
                    'sales_account': turnover.get('sales_account'),
                    'sales_cod': turnover.get('sales_cod'),
                    'type_r_sales': turnover.get('type_r_sales')
                })
            
            # Extract transaction summary data
            if 'transaction_summary' in pharmacy_data:
                transaction = pharmacy_data['transaction_summary']
                print(f"   📊 Transaction Summary Data: {transaction}")
                insert_data.update({
                    'transactions_total': transaction.get('transactions_total'),
                    'avg_basket_value': transaction.get('avg_basket_value')
                })
            
            # Extract dispensary summary data
            if 'dispensary_summary' in pharmacy_data:
                dispensary = pharmacy_data['dispensary_summary']
                print(f"   📊 Dispensary Summary Data: {dispensary}")
                insert_data.update({
                    'script_total': dispensary.get('script_total'),
                    'disp_turnover': dispensary.get('disp_turnover_excluding_vat'),
                    'avg_script_value': dispensary.get('avg_script_value')
                })
            
            # Log what we're about to insert
            print(f"   🗄️ Final insert data: turnover={insert_data.get('turnover')}, pharmacy_code={insert_data.get('pharmacy_code')}")
            
            # Calculate average basket size if we have the data
            if 'gross_profit' in pharmacy_data and insert_data['transactions_total']:
                gross_profit = pharmacy_data['gross_profit']
                total_qty = gross_profit.get('total_sales_qty', 0)
                if total_qty and insert_data['transactions_total']:
                    insert_data['avg_basket_size'] = total_qty / insert_data['transactions_total']
            
            # Insert the data
            if db.insert_daily_summary(**insert_data):
                success_count += 1
                print(f"✅ Successfully inserted data for {pharmacy} - {date}")
                # Refresh pre-aggregations (MTD/YTD)
                try:
                    db.refresh_rollups(pharmacy, date)
                    print("   ♻️  Rollups refreshed")
                except Exception as e:
                    print(f"   ⚠️  Rollup refresh skipped/failed: {e}")
                
                # Print summary of inserted data
                print(f"   💰 Turnover: R{insert_data['turnover']:,.2f}" if insert_data['turnover'] else "   💰 Turnover: N/A")
                print(f"   🛒 Transactions: {insert_data['transactions_total']}" if insert_data['transactions_total'] else "   🛒 Transactions: N/A")
                print(f"   💊 Scripts: {insert_data['script_total']}" if insert_data['script_total'] else "   💊 Scripts: N/A")
            else:
                print(f"❌ Failed to insert data for {pharmacy} - {date}")
        
        except Exception as e:
            print(f"❌ Error processing {key}: {e}")
            continue
    
    print(f"\n🎉 Database insertion completed!")
    print(f"✅ Successfully inserted {success_count}/{len(data)} records")
    
    # Get database statistics
    stats = db.get_database_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   • Pharmacies: {stats.get('pharmacies', 0)}")
    print(f"   • Daily Summaries: {stats.get('daily_summaries', 0)}")
    print(f"   • Sales Details: {stats.get('sales_details', 0)}")
    
    db.close()

def test_database_queries():
    """Test some database queries"""
    print("\n🧪 Testing database queries...")
    
    db = RenderPharmacyDatabase()
    
    try:
        # Test getting pharmacy performance
        print("\n📊 Pharmacy Performance Data:")
        performance = db.get_pharmacy_performance('REITZ', '2025-08-04', '2025-08-04')
        if performance:
            for record in performance:
                print(f"   • REITZ - {record['report_date']}: R{record['turnover']:,.2f} turnover, {record['transactions_total']} transactions")
        
        performance = db.get_pharmacy_performance('TLC WINTERTON', '2025-08-04', '2025-08-04')
        if performance:
            for record in performance:
                print(f"   • TLC WINTERTON - {record['report_date']}: R{record['turnover']:,.2f} turnover, {record['transactions_total']} transactions")
        
        # Test getting available dates
        print("\n📅 Available Report Dates:")
        dates = db.get_available_dates()
        for date_record in dates:
            print(f"   • {date_record['report_date']}")
        
        print("\n✅ Database queries working correctly!")
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
    
    db.close()

def main():
    """Main function"""
    print("🗄️ Pharmacy Data Database Insertion")
    print("=" * 50)
    
    # Insert data
    insert_data_to_database()
    
    # Test queries
    test_database_queries()
    
    print("\n🎉 All operations completed successfully!")

if __name__ == "__main__":
    main() 