#!/usr/bin/env python3
"""
Render PostgreSQL Database Connection
====================================

This script provides database connection and query functionality for the pharmacy system
deployed on Render with PostgreSQL.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from datetime import datetime, date

class RenderPharmacyDatabase:
    def __init__(self):
        """Initialize database connection using Render environment variables"""
        # Get database URL from environment variable
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Initialize connection
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            print("✅ Connected to Render PostgreSQL database")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    self.conn.commit()
                    return []
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Query execution failed: {e}")
            raise
    
    def get_pharmacy_id_by_code(self, pharmacy_code: str) -> Optional[int]:
        """Get pharmacy_id from pharmacy_code"""
        query = "SELECT id FROM pharmacies WHERE pharmacy_code = %s"
        result = self.execute_query(query, (pharmacy_code,))
        return result[0]['id'] if result else None
    
    def get_pharmacy_code_by_id(self, pharmacy_id: int) -> Optional[str]:
        """Get pharmacy_code from pharmacy_id"""
        query = "SELECT pharmacy_code FROM pharmacies WHERE id = %s"
        result = self.execute_query(query, (pharmacy_id,))
        return result[0]['pharmacy_code'] if result else None

    def refresh_rollups(self, pharmacy_code: str, as_of_date: str) -> None:
        """Refresh monthly and yearly rollups for a pharmacy and date."""
        try:
            # Use SELECT to invoke function and ignore returned rows
            self.execute_query("SELECT refresh_rollups(%s, %s)", (pharmacy_code, as_of_date))
        except Exception as e:
            # Do not fail ingestion on rollup refresh issues
            print(f"⚠️  Warning: rollup refresh failed for {pharmacy_code} {as_of_date}: {e}")
    
    def insert_daily_summary(self, **kwargs) -> bool:
        """Insert or update daily summary data"""
        query = """
        INSERT INTO daily_summary (
            pharmacy_id, report_date, turnover, gp_percent, gp_value, 
            cost_of_sales, purchases, avg_basket_value, avg_basket_size, 
            transactions_total, script_total, avg_script_value, disp_turnover,
            stock_opening, stock_closing, adjustments, sales_cash, 
            sales_cod, sales_account
        ) VALUES (
            (SELECT id FROM pharmacies WHERE pharmacy_code = %s),
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (pharmacy_id, report_date) DO UPDATE SET
            turnover = EXCLUDED.turnover,
            gp_percent = EXCLUDED.gp_percent,
            gp_value = EXCLUDED.gp_value,
            cost_of_sales = EXCLUDED.cost_of_sales,
            purchases = EXCLUDED.purchases,
            avg_basket_value = EXCLUDED.avg_basket_value,
            avg_basket_size = EXCLUDED.avg_basket_size,
            transactions_total = EXCLUDED.transactions_total,
            script_total = EXCLUDED.script_total,
            avg_script_value = EXCLUDED.avg_script_value,
            disp_turnover = EXCLUDED.disp_turnover,
            stock_opening = EXCLUDED.stock_opening,
            stock_closing = EXCLUDED.stock_closing,
            adjustments = EXCLUDED.adjustments,
            sales_cash = EXCLUDED.sales_cash,
            sales_cod = EXCLUDED.sales_cod,
            sales_account = EXCLUDED.sales_account
        """
        
        params = (
            kwargs.get('pharmacy_code'),
            kwargs.get('report_date'),
            kwargs.get('turnover'),
            kwargs.get('gp_percent'),
            kwargs.get('gp_value'),
            kwargs.get('cost_of_sales'),
            kwargs.get('purchases'),
            kwargs.get('avg_basket_value'),
            kwargs.get('avg_basket_size'),
            kwargs.get('transactions_total'),
            kwargs.get('script_total'),
            kwargs.get('avg_script_value'),
            kwargs.get('disp_turnover'),
            kwargs.get('stock_opening'),
            kwargs.get('stock_closing'),
            kwargs.get('adjustments'),
            kwargs.get('sales_cash'),
            kwargs.get('sales_cod'),
            kwargs.get('sales_account')
        )
        
        try:
            self.execute_query(query, params)
            return True
        except Exception as e:
            print(f"❌ Failed to insert daily summary: {e}")
            return False
    
    def insert_sales_details(self, pharmacy_code: str, report_date: str, sales_data: List[Dict]) -> bool:
        """Insert sales details data"""
        if not sales_data:
            return True
        
        # First, ensure the daily_summary record exists
        daily_summary_exists = self.execute_query(
            "SELECT id FROM daily_summary WHERE pharmacy_id = (SELECT id FROM pharmacies WHERE pharmacy_code = %s) AND report_date = %s",
            (pharmacy_code, report_date)
        )
        
        if not daily_summary_exists:
            print(f"❌ Daily summary record not found for {pharmacy_code} on {report_date}")
            return False
        
        # First, delete existing sales details for this pharmacy/date to avoid duplicates
        delete_query = """
        DELETE FROM sales_details 
        WHERE pharmacy_id = (SELECT id FROM pharmacies WHERE pharmacy_code = %s) 
        AND report_date = %s
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(delete_query, (pharmacy_code, report_date))
                print(f"🗑️  Cleared existing sales details for {pharmacy_code} on {report_date}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clear existing sales details: {e}")
        
        # Insert sales details
        query = """
        INSERT INTO sales_details (
            pharmacy_id, report_date, department_code, stock_code, description,
            soh, sales_qty, sales_value, sales_cost, gross_profit, gross_profit_percent
        ) VALUES (
            (SELECT id FROM pharmacies WHERE pharmacy_code = %s),
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        try:
            with self.conn.cursor() as cursor:
                for product in sales_data:
                    params = (
                        pharmacy_code,
                        report_date,
                        product.get('department_code'),
                        product.get('stock_code'),
                        product.get('description'),
                        product.get('soh'),
                        product.get('sales_qty'),
                        product.get('sales_value'),
                        product.get('sales_cost'),
                        product.get('gross_profit'),
                        product.get('gross_profit_percent')
                    )
                    cursor.execute(query, params)
            
            self.conn.commit()
            print(f"✅ Inserted {len(sales_data)} sales detail records for {pharmacy_code}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Failed to insert sales details: {e}")
            return False
    
    def get_top_selling_products(self, pharmacy_code: str, report_date: str, limit: int = 10) -> List[Dict]:
        """Get top selling products for a pharmacy on a specific date"""
        query = """
        SELECT 
            stock_code,
            description,
            sales_qty,
            sales_value,
            gross_profit_percent,
            department_code
        FROM sales_details sd
        JOIN pharmacies p ON sd.pharmacy_id = p.id
        WHERE p.pharmacy_code = %s AND sd.report_date = %s
        ORDER BY sd.sales_qty DESC
        LIMIT %s
        """
        
        return self.execute_query(query, (pharmacy_code, report_date, limit))
    
    def get_pharmacy_performance(self, pharmacy_code: str, start_date: str, end_date: str) -> List[Dict]:
        """Get pharmacy performance data for a date range"""
        query = """
        SELECT 
            report_date,
            turnover,
            gp_percent,
            gp_value,
            transactions_total,
            avg_basket_value,
            avg_basket_size,
            script_total,
            avg_script_value,
            disp_turnover
        FROM daily_summary ds
        JOIN pharmacies p ON ds.pharmacy_id = p.id
        WHERE p.pharmacy_code = %s 
        AND ds.report_date BETWEEN %s AND %s
        ORDER BY ds.report_date
        """
        
        return self.execute_query(query, (pharmacy_code, start_date, end_date))
    
    def get_department_analysis(self, pharmacy_code: str, report_date: str) -> List[Dict]:
        """Get department-level analysis for a pharmacy on a specific date"""
        query = """
        SELECT 
            department_code,
            COUNT(*) as product_count,
            SUM(sales_qty) as total_qty,
            SUM(sales_value) as total_value,
            AVG(gross_profit_percent) as avg_gp_percent
        FROM sales_details sd
        JOIN pharmacies p ON sd.pharmacy_id = p.id
        WHERE p.pharmacy_code = %s AND sd.report_date = %s
        GROUP BY department_code
        ORDER BY total_qty DESC
        """
        
        return self.execute_query(query, (pharmacy_code, report_date))
    
    def get_all_pharmacies(self) -> List[Dict]:
        """Get all pharmacies"""
        return self.execute_query("SELECT * FROM pharmacies ORDER BY name")
    
    def get_available_dates(self, pharmacy_code: str = None) -> List[Dict]:
        """Get available report dates"""
        if pharmacy_code:
            query = """
            SELECT DISTINCT report_date 
            FROM daily_summary ds
            JOIN pharmacies p ON ds.pharmacy_id = p.id
            WHERE p.pharmacy_code = %s
            ORDER BY report_date DESC
            """
            return self.execute_query(query, (pharmacy_code,))
        else:
            query = """
            SELECT DISTINCT report_date 
            FROM daily_summary 
            ORDER BY report_date DESC
            """
            return self.execute_query(query)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.execute_query("SELECT 1 as test")
            return len(result) > 0 and result[0]['test'] == 1
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            # Count pharmacies
            pharmacies = self.execute_query("SELECT COUNT(*) as count FROM pharmacies")
            stats['pharmacies'] = pharmacies[0]['count'] if pharmacies else 0
            
            # Count daily summaries
            summaries = self.execute_query("SELECT COUNT(*) as count FROM daily_summary")
            stats['daily_summaries'] = summaries[0]['count'] if summaries else 0
            
            # Count sales details
            sales = self.execute_query("SELECT COUNT(*) as count FROM sales_details")
            stats['sales_details'] = sales[0]['count'] if sales else 0
            
            # Get date range
            dates = self.execute_query("SELECT MIN(report_date) as min_date, MAX(report_date) as max_date FROM daily_summary")
            if dates:
                stats['date_range'] = {
                    'min_date': dates[0]['min_date'],
                    'max_date': dates[0]['max_date']
                }
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")

def test_render_database():
    """Test function for Render database connection"""
    print("🧪 Testing Render Database Connection")
    print("=" * 50)
    
    try:
        # Initialize database
        db = RenderPharmacyDatabase()
        
        # Test connection
        if db.test_connection():
            print("✅ Database connection test passed")
        else:
            print("❌ Database connection test failed")
            return
        
        # Get database stats
        stats = db.get_database_stats()
        print(f"📊 Database Statistics:")
        print(f"   • Pharmacies: {stats.get('pharmacies', 0)}")
        print(f"   • Daily Summaries: {stats.get('daily_summaries', 0)}")
        print(f"   • Sales Details: {stats.get('sales_details', 0)}")
        if 'date_range' in stats:
            print(f"   • Date Range: {stats['date_range']['min_date']} to {stats['date_range']['max_date']}")
        
        # Get all pharmacies
        pharmacies = db.get_all_pharmacies()
        print(f"\n🏪 Pharmacies in database:")
        for pharmacy in pharmacies:
            print(f"   • {pharmacy['name']} ({pharmacy['pharmacy_code']})")
        
        # Get available dates
        dates = db.get_available_dates()
        print(f"\n📅 Available report dates:")
        for date_record in dates[:5]:  # Show first 5 dates
            print(f"   • {date_record['report_date']}")
        
        db.close()
        print("\n✅ Render database test completed successfully!")
        
    except Exception as e:
        print(f"❌ Render database test failed: {e}")

if __name__ == "__main__":
    test_render_database() 