"""
PostgreSQL Database Connection and Operations for Pharmacy Reporting System

This module provides a clean interface for connecting to the pharmacy reports database
and performing common operations like inserting data, querying reports, and data analysis.
"""

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection, cursor
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime
import logging
import os
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PharmacyDatabase:
    """
    Main class for managing pharmacy database operations.
    """
    
    def __init__(self, connection_params: Optional[Dict[str, str]] = None):
        """
        Initialize database connection parameters.
        
        Args:
            connection_params: Dictionary with connection parameters
                (host, port, database, user, password)
        """
        self.connection_params = connection_params or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'pharmacy_reports'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            psycopg2 connection object
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, connection: connection):
        """
        Context manager for database cursors.
        
        Args:
            connection: Database connection object
            
        Yields:
            psycopg2 cursor object
        """
        cursor = None
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            yield cursor
        finally:
            if cursor:
                cursor.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    logger.info("Database connection successful")
                    return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_pharmacy_id(self, pharmacy_code: str) -> Optional[int]:
        """
        Get pharmacy ID by pharmacy code.
        
        Args:
            pharmacy_code: Pharmacy code to look up
            
        Returns:
            Pharmacy ID if found, None otherwise
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(
                        "SELECT id FROM pharmacies WHERE pharmacy_code = %s",
                        (pharmacy_code,)
                    )
                    result = cur.fetchone()
                    return result['id'] if result else None
        except Exception as e:
            logger.error(f"Error getting pharmacy ID: {e}")
            return None
    
    def insert_pharmacy(self, pharmacy_code: str, name: str) -> Optional[int]:
        """
        Insert a new pharmacy.
        
        Args:
            pharmacy_code: Unique pharmacy code
            name: Pharmacy name
            
        Returns:
            Pharmacy ID if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(
                        """
                        INSERT INTO pharmacies (pharmacy_code, name)
                        VALUES (%s, %s)
                        ON CONFLICT (pharmacy_code) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                        """,
                        (pharmacy_code, name)
                    )
                    result = cur.fetchone()
                    conn.commit()
                    logger.info(f"Pharmacy {pharmacy_code} inserted/updated successfully")
                    return result['id']
        except Exception as e:
            logger.error(f"Error inserting pharmacy: {e}")
            return None
    
    def insert_daily_summary(self, pharmacy_code: str, report_date: date, 
                           summary_data: Dict[str, Any]) -> bool:
        """
        Insert daily summary data for a pharmacy.
        
        Args:
            pharmacy_code: Pharmacy code
            report_date: Date of the report
            summary_data: Dictionary containing summary metrics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pharmacy_id = self.get_pharmacy_id(pharmacy_code)
            if not pharmacy_id:
                logger.error(f"Pharmacy {pharmacy_code} not found")
                return False
            
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(
                        """
                        INSERT INTO daily_summary (
                            pharmacy_id, report_date, turnover, gp_percent, gp_value,
                            cost_of_sales, purchases, avg_basket_value, avg_basket_size,
                            transactions_total, script_total, avg_script_value,
                            disp_turnover, stock_opening, stock_closing, adjustments,
                            sales_cash, sales_cod, sales_account
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (pharmacy_id, report_date) 
                        DO UPDATE SET
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
                            sales_account = EXCLUDED.sales_account,
                            upload_time = CURRENT_TIMESTAMP
                        """,
                        (
                            pharmacy_id, report_date,
                            summary_data.get('turnover'),
                            summary_data.get('gp_percent'),
                            summary_data.get('gp_value'),
                            summary_data.get('cost_of_sales'),
                            summary_data.get('purchases'),
                            summary_data.get('avg_basket_value'),
                            summary_data.get('avg_basket_size'),
                            summary_data.get('transactions_total'),
                            summary_data.get('script_total'),
                            summary_data.get('avg_script_value'),
                            summary_data.get('disp_turnover'),
                            summary_data.get('stock_opening'),
                            summary_data.get('stock_closing'),
                            summary_data.get('adjustments'),
                            summary_data.get('sales_cash'),
                            summary_data.get('sales_cod'),
                            summary_data.get('sales_account')
                        )
                    )
                    conn.commit()
                    logger.info(f"Daily summary inserted for {pharmacy_code} on {report_date}")
                    return True
        except Exception as e:
            logger.error(f"Error inserting daily summary: {e}")
            return False
    
    def insert_sales_details(self, pharmacy_code: str, report_date: date,
                           sales_data: List[Dict[str, Any]]) -> bool:
        """
        Insert sales details data for a pharmacy.
        
        Args:
            pharmacy_code: Pharmacy code
            report_date: Date of the report
            sales_data: List of dictionaries containing sales line items
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pharmacy_id = self.get_pharmacy_id(pharmacy_code)
            if not pharmacy_id:
                logger.error(f"Pharmacy {pharmacy_code} not found")
                return False
            
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    # First, ensure daily summary exists
                    cur.execute(
                        "SELECT id FROM daily_summary WHERE pharmacy_id = %s AND report_date = %s",
                        (pharmacy_id, report_date)
                    )
                    if not cur.fetchone():
                        logger.error(f"Daily summary not found for {pharmacy_code} on {report_date}")
                        return False
                    
                    # Insert sales details
                    for item in sales_data:
                        cur.execute(
                            """
                            INSERT INTO sales_details (
                                pharmacy_id, report_date, department_code, stock_code,
                                description, soh, sales_qty, sales_value, sales_cost,
                                gross_profit, gross_profit_percent
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                pharmacy_id, report_date,
                                item.get('department_code'),
                                item.get('stock_code'),
                                item.get('description'),
                                item.get('soh'),
                                item.get('sales_qty'),
                                item.get('sales_value'),
                                item.get('sales_cost'),
                                item.get('gross_profit'),
                                item.get('gross_profit_percent')
                            )
                        )
                    
                    conn.commit()
                    logger.info(f"Sales details inserted for {pharmacy_code} on {report_date}")
                    return True
        except Exception as e:
            logger.error(f"Error inserting sales details: {e}")
            return False
    
    def get_pharmacy_performance(self, pharmacy_code: str, start_date: date, 
                               end_date: date) -> List[Dict[str, Any]]:
        """
        Get pharmacy performance data for a date range.
        
        Args:
            pharmacy_code: Pharmacy code
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of performance records
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(
                        "SELECT * FROM get_pharmacy_performance(%s, %s, %s)",
                        (pharmacy_code, start_date, end_date)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting pharmacy performance: {e}")
            return []
    
    def get_top_selling_products(self, pharmacy_code: str, start_date: date,
                               end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top selling products for a pharmacy in a date range.
        
        Args:
            pharmacy_code: Pharmacy code
            start_date: Start date for analysis
            end_date: End date for analysis
            limit: Number of top products to return
            
        Returns:
            List of top selling products
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(
                        "SELECT * FROM get_top_selling_products(%s, %s, %s, %s)",
                        (pharmacy_code, start_date, end_date, limit)
                    )
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting top selling products: {e}")
            return []
    
    def get_daily_summary_view(self, pharmacy_code: str = None, 
                             start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """
        Get daily summary data with pharmacy details.
        
        Args:
            pharmacy_code: Optional pharmacy code filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of daily summary records
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    query = "SELECT * FROM daily_summary_view WHERE 1=1"
                    params = []
                    
                    if pharmacy_code:
                        query += " AND pharmacy_code = %s"
                        params.append(pharmacy_code)
                    
                    if start_date:
                        query += " AND report_date >= %s"
                        params.append(start_date)
                    
                    if end_date:
                        query += " AND report_date <= %s"
                        params.append(end_date)
                    
                    query += " ORDER BY report_date DESC"
                    
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return []
    
    def insert_department_codes(self, department_codes: List[Tuple[str, str]]) -> bool:
        """
        Insert department codes from a list of tuples (code, name).
        
        Args:
            department_codes: List of (code, name) tuples
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    for code, name in department_codes:
                        cur.execute(
                            """
                            INSERT INTO department_codes (department_code, department_name)
                            VALUES (%s, %s)
                            ON CONFLICT (department_code) DO UPDATE SET department_name = EXCLUDED.department_name
                            """,
                            (code, name)
                        )
                    conn.commit()
                    logger.info(f"Department codes inserted successfully")
                    return True
        except Exception as e:
            logger.error(f"Error inserting department codes: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize database connection
    db = PharmacyDatabase()
    
    # Test connection
    if db.test_connection():
        print("✅ Database connection successful")
        
        # Example: Insert a pharmacy
        pharmacy_id = db.insert_pharmacy("TEST001", "Test Pharmacy")
        if pharmacy_id:
            print(f"✅ Pharmacy inserted with ID: {pharmacy_id}")
        
        # Example: Get pharmacy performance
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        performance = db.get_pharmacy_performance("REITZ", start_date, end_date)
        print(f"✅ Retrieved {len(performance)} performance records")
        
    else:
        print("❌ Database connection failed") 