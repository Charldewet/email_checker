#!/usr/bin/env python3
"""
Render Database Setup Script
===========================

This script sets up the complete database schema for the pharmacy system on Render.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def connect_to_render_database():
    """Connect to Render PostgreSQL database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("💡 Please set your Render database URL:")
        print("   export DATABASE_URL='postgresql://user:password@host:port/database'")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        print("✅ Connected to Render PostgreSQL database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def create_database_schema(conn):
    """Create the complete database schema"""
    print("\n🔧 Creating database schema...")
    
    schema_sql = """
    -- Render PostgreSQL Database Setup for Pharmacy Reporting System
    -- This script creates the complete database structure

    -- Step 1: Create Tables

    -- Table: pharmacies
    CREATE TABLE IF NOT EXISTS pharmacies (
        id SERIAL PRIMARY KEY,
        pharmacy_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Table: daily_summary
    CREATE TABLE IF NOT EXISTS daily_summary (
        id SERIAL PRIMARY KEY,
        pharmacy_id INTEGER REFERENCES pharmacies(id) ON DELETE CASCADE,
        report_date DATE NOT NULL,
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        -- Financial metrics
        turnover NUMERIC,
        gp_percent NUMERIC,
        gp_value NUMERIC,
        cost_of_sales NUMERIC,
        purchases NUMERIC,
        
        -- Transaction metrics
        avg_basket_value NUMERIC,
        avg_basket_size NUMERIC,
        transactions_total INTEGER,
        script_total INTEGER,
        avg_script_value NUMERIC,
        
        -- Dispensing metrics
        disp_turnover NUMERIC,
        
        -- Stock metrics
        stock_opening NUMERIC,
        stock_closing NUMERIC,
        adjustments NUMERIC,
        
        -- Payment methods
        sales_cash NUMERIC,
        sales_cod NUMERIC,
        sales_account NUMERIC,

        UNIQUE (pharmacy_id, report_date)
    );

    -- Table: department_codes
    CREATE TABLE IF NOT EXISTS department_codes (
        id SERIAL PRIMARY KEY,
        department_code TEXT UNIQUE NOT NULL,
        department_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Table: sales_details
    CREATE TABLE IF NOT EXISTS sales_details (
        id SERIAL PRIMARY KEY,
        pharmacy_id INTEGER REFERENCES pharmacies(id) ON DELETE CASCADE,
        report_date DATE NOT NULL,

        -- Product information
        department_code TEXT REFERENCES department_codes(department_code) ON DELETE SET NULL,
        stock_code TEXT,
        description TEXT,
        
        -- Stock and sales data
        soh INTEGER, -- Stock on Hand
        sales_qty INTEGER,
        sales_value NUMERIC,
        sales_cost NUMERIC,
        gross_profit NUMERIC,
        gross_profit_percent NUMERIC,

        -- Foreign key constraint to ensure data integrity
        FOREIGN KEY (pharmacy_id, report_date) REFERENCES daily_summary(pharmacy_id, report_date) ON DELETE CASCADE
    );

    -- Step 2: Create Indexes for Performance
    CREATE INDEX IF NOT EXISTS idx_sales_details_pharmacy_date ON sales_details(pharmacy_id, report_date);
    CREATE INDEX IF NOT EXISTS idx_department_code_lookup ON department_codes(department_code);
    CREATE INDEX IF NOT EXISTS idx_daily_summary_pharmacy_date ON daily_summary(pharmacy_id, report_date);
    CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_summary(report_date);
    CREATE INDEX IF NOT EXISTS idx_sales_details_stock_code ON sales_details(stock_code);
    CREATE INDEX IF NOT EXISTS idx_sales_details_department ON sales_details(department_code);
    -- Optional index to speed up latest-first scans
    CREATE INDEX IF NOT EXISTS idx_daily_summary_pharmacy_date_desc ON daily_summary(pharmacy_id, report_date DESC);

    -- Step 3: Insert Sample Data
    INSERT INTO pharmacies (pharmacy_code, name) 
    VALUES 
        ('REITZ', 'Reitz Pharmacy'),
        ('TLC WINTERTON', 'TLC Winterton Pharmacy')
    ON CONFLICT (pharmacy_code) DO NOTHING;

    -- Step 4: Create Views for Easy Querying
    CREATE OR REPLACE VIEW daily_summary_view AS
    SELECT 
        ds.*,
        p.pharmacy_code,
        p.name as pharmacy_name
    FROM daily_summary ds
    JOIN pharmacies p ON ds.pharmacy_id = p.id;

    CREATE OR REPLACE VIEW sales_details_view AS
    SELECT 
        sd.*,
        p.pharmacy_code,
        p.name as pharmacy_name,
        dc.department_name
    FROM sales_details sd
    JOIN pharmacies p ON sd.pharmacy_id = p.id
    LEFT JOIN department_codes dc ON sd.department_code = dc.department_code;

    -- Step 4.1: Pre-aggregations
    CREATE TABLE IF NOT EXISTS monthly_kpis (
        id SERIAL PRIMARY KEY,
        pharmacy_id INTEGER NOT NULL REFERENCES pharmacies(id) ON DELETE CASCADE,
        month_start DATE NOT NULL,
        turnover NUMERIC DEFAULT 0,
        gp_value NUMERIC DEFAULT 0,
        purchases NUMERIC DEFAULT 0,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (pharmacy_id, month_start)
    );

    CREATE INDEX IF NOT EXISTS idx_monthly_kpis_pharmacy_month ON monthly_kpis(pharmacy_id, month_start);

    CREATE TABLE IF NOT EXISTS yearly_kpis (
        id SERIAL PRIMARY KEY,
        pharmacy_id INTEGER NOT NULL REFERENCES pharmacies(id) ON DELETE CASCADE,
        year_start DATE NOT NULL,
        turnover NUMERIC DEFAULT 0,
        gp_value NUMERIC DEFAULT 0,
        purchases NUMERIC DEFAULT 0,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (pharmacy_id, year_start)
    );

    CREATE INDEX IF NOT EXISTS idx_yearly_kpis_pharmacy_year ON yearly_kpis(pharmacy_id, year_start);

    -- Step 5: Create Functions for Common Queries
    CREATE OR REPLACE FUNCTION get_pharmacy_performance(
        p_pharmacy_code TEXT,
        p_start_date DATE,
        p_end_date DATE
    ) RETURNS TABLE (
        report_date DATE,
        turnover NUMERIC,
        gp_percent NUMERIC,
        transactions_total INTEGER,
        avg_basket_value NUMERIC
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            ds.report_date,
            ds.turnover,
            ds.gp_percent,
            ds.transactions_total,
            ds.avg_basket_value
        FROM daily_summary ds
        JOIN pharmacies p ON ds.pharmacy_id = p.id
        WHERE p.pharmacy_code = p_pharmacy_code
        AND ds.report_date BETWEEN p_start_date AND p_end_date
        ORDER BY ds.report_date;
    END;
    $$ LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION get_top_selling_products(
        p_pharmacy_code TEXT,
        p_date DATE,
        p_limit INTEGER DEFAULT 10
    ) RETURNS TABLE (
        stock_code TEXT,
        description TEXT,
        sales_qty INTEGER,
        sales_value NUMERIC,
        gross_profit_percent NUMERIC
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            sd.stock_code,
            sd.description,
            sd.sales_qty,
            sd.sales_value,
            sd.gross_profit_percent
        FROM sales_details sd
        JOIN pharmacies p ON sd.pharmacy_id = p.id
        WHERE p.pharmacy_code = p_pharmacy_code
        AND sd.report_date = p_date
        ORDER BY sd.sales_qty DESC
        LIMIT p_limit;
    END;
    $$ LANGUAGE plpgsql;

    -- Step 7: Ensure gp_percent is computed consistently from gp_value/turnover
    CREATE OR REPLACE FUNCTION compute_gp_percent()
    RETURNS trigger AS $$
    BEGIN
        IF COALESCE(NEW.turnover, 0) = 0 THEN
            NEW.gp_percent := 0;
        ELSE
            NEW.gp_percent := ROUND(100 * COALESCE(NEW.gp_value, 0) / NULLIF(NEW.turnover, 0), 2);
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS daily_summary_compute_gp ON daily_summary;
    CREATE TRIGGER daily_summary_compute_gp
    BEFORE INSERT OR UPDATE OF turnover, gp_value
    ON daily_summary
    FOR EACH ROW
    EXECUTE FUNCTION compute_gp_percent();

    -- One-time backfill to correct existing rows
    UPDATE daily_summary
    SET gp_percent = ROUND(
        CASE WHEN COALESCE(turnover,0) = 0 THEN 0
             ELSE (COALESCE(gp_value,0) / NULLIF(turnover,0)) * 100 END
    , 2);
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)
        conn.commit()
        print("✅ Database schema created successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to create schema: {e}")
        return False

def insert_sample_department_codes(conn):
    """Insert sample department codes"""
    print("\n📋 Inserting sample department codes...")
    
    department_codes = [
        ('BAAC', 'Baby & Child'),
        ('BEAU', 'Beauty'),
        ('COSM', 'Cosmetics'),
        ('DISP', 'Dispensary'),
        ('FOOD', 'Food & Beverages'),
        ('HEAL', 'Health & Wellness'),
        ('HOME', 'Home & Personal Care'),
        ('MEDI', 'Medicines'),
        ('NUTR', 'Nutrition'),
        ('ORAL', 'Oral Care'),
        ('SKIN', 'Skin Care'),
        ('VITA', 'Vitamins & Supplements')
    ]
    
    try:
        with conn.cursor() as cursor:
            for code, name in department_codes:
                cursor.execute(
                    "INSERT INTO department_codes (department_code, department_name) VALUES (%s, %s) ON CONFLICT (department_code) DO NOTHING",
                    (code, name)
                )
        conn.commit()
        print(f"✅ Inserted {len(department_codes)} department codes")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to insert department codes: {e}")
        return False

def test_database_queries(conn):
    """Test database queries"""
    print("\n🧪 Testing database queries...")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Test pharmacies
            cursor.execute("SELECT * FROM pharmacies")
            pharmacies = cursor.fetchall()
            print(f"✅ Found {len(pharmacies)} pharmacies:")
            for pharmacy in pharmacies:
                print(f"   • {pharmacy['name']} ({pharmacy['pharmacy_code']})")
            
            # Test department codes
            cursor.execute("SELECT * FROM department_codes LIMIT 5")
            departments = cursor.fetchall()
            print(f"✅ Found {len(departments)} department codes (showing first 5):")
            for dept in departments:
                print(f"   • {dept['department_code']}: {dept['department_name']}")
            
            # Test views
            cursor.execute("SELECT COUNT(*) as count FROM daily_summary_view")
            daily_count = cursor.fetchone()
            print(f"✅ Daily summary view: {daily_count['count']} records")
            
            cursor.execute("SELECT COUNT(*) as count FROM sales_details_view")
            sales_count = cursor.fetchone()
            print(f"✅ Sales details view: {sales_count['count']} records")
            
        return True
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def get_database_stats(conn):
    """Get database statistics"""
    print("\n📊 Database Statistics:")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Table counts
            tables = ['pharmacies', 'daily_summary', 'department_codes', 'sales_details']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                print(f"   • {table}: {result['count']} records")
            
            # Database size
            cursor.execute("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    pg_size_pretty(pg_total_relation_size('daily_summary')) as daily_size,
                    pg_size_pretty(pg_total_relation_size('sales_details')) as sales_size
            """)
            sizes = cursor.fetchone()
            print(f"   • Database size: {sizes['db_size']}")
            print(f"   • Daily summary size: {sizes['daily_size']}")
            print(f"   • Sales details size: {sizes['sales_size']}")
            
    except Exception as e:
        print(f"❌ Failed to get database stats: {e}")

def main():
    """Main setup function"""
    print("🗄️ Render PostgreSQL Database Setup")
    print("=" * 50)
    
    # Connect to database
    conn = connect_to_render_database()
    if not conn:
        return False
    
    try:
        # Create schema
        if not create_database_schema(conn):
            return False
        
        # Insert sample data
        if not insert_sample_department_codes(conn):
            return False
        
        # Test queries
        if not test_database_queries(conn):
            return False
        
        # Get statistics
        get_database_stats(conn)
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your .env file with the DATABASE_URL")
        print("2. Test the email monitor: python3 test_email_monitor.py")
        print("3. Run the email monitor: python3 email_monitor.py")
        
        return True
        
    finally:
        conn.close()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    main() 