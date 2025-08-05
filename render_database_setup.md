# 🗄️ Render PostgreSQL Database Setup Guide

## Overview
This guide will help you set up a persistent PostgreSQL database on Render for the pharmacy reporting system.

## Prerequisites
- Render account (free tier available)
- Git repository with your pharmacy system code

## Step 1: Create PostgreSQL Database on Render

### 1.1 Access Render Dashboard
1. Go to [render.com](https://render.com)
2. Sign up or log in to your account
3. Click "New +" and select "PostgreSQL"

### 1.2 Configure Database
```
Database Name: pharmacy_reports
User: pharmacy_user
Region: Choose closest to your users
PostgreSQL Version: 15 (latest stable)
Plan: Free (for testing) or Starter ($7/month for production)
```

### 1.3 Database Configuration
- **Name**: `pharmacy_reports`
- **Database**: `pharmacy_reports`
- **User**: `pharmacy_user`
- **Plan**: 
  - **Free**: 1GB storage, 5 connections (good for testing)
  - **Starter**: 1GB storage, 10 connections ($7/month)
  - **Standard**: 10GB storage, 25 connections ($25/month)
  - **Pro**: 100GB storage, 100 connections ($100/month)

## Step 2: Environment Configuration

### 2.1 Get Connection Details
After creating the database, Render will provide:
- **Internal Database URL**: `postgresql://pharmacy_user:password@host:port/pharmacy_reports`
- **External Database URL**: `postgresql://pharmacy_user:password@host:port/pharmacy_reports`

### 2.2 Environment Variables
Set these in your application:
```bash
DATABASE_URL=postgresql://pharmacy_user:password@host:port/pharmacy_reports
DB_HOST=your-render-host
DB_PORT=5432
DB_NAME=pharmacy_reports
DB_USER=pharmacy_user
DB_PASSWORD=your-password
```

## Step 3: Database Schema Setup

### 3.1 Create Database Setup Script
Create `render_database_setup.sql` with your schema:

```sql
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
```

## Step 4: Database Connection Setup

### 4.1 Update Database Connection Script
Update your `database_connection.py`:

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional

class PharmacyDatabase:
    def __init__(self):
        # Get database URL from environment variable
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Parse connection details
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
    
    def get_top_selling_products(self, pharmacy_code: str, date: str, limit: int = 10) -> List[Dict]:
        """Get top selling products for a pharmacy on a specific date"""
        query = """
        SELECT 
            stock_code,
            description,
            sales_qty,
            sales_value,
            gross_profit_percent
        FROM sales_details sd
        JOIN pharmacies p ON sd.pharmacy_id = p.id
        WHERE p.pharmacy_code = %s AND sd.report_date = %s
        ORDER BY sd.sales_qty DESC
        LIMIT %s
        """
        
        return self.execute_query(query, (pharmacy_code, date, limit))
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")
```

## Step 5: Deployment Configuration

### 5.1 Create render.yaml (Optional)
```yaml
services:
  - type: web
    name: pharmacy-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: pharmacy-reports
          property: connectionString
```

### 5.2 Requirements.txt
```
psycopg2-binary==2.9.7
flask==2.3.3
flask-cors==4.0.0
python-dotenv==1.0.0
```

## Step 6: Testing the Setup

### 6.1 Test Connection
```python
from database_connection import PharmacyDatabase

# Test connection
db = PharmacyDatabase()
print("✅ Database connection successful!")

# Test query
result = db.execute_query("SELECT * FROM pharmacies")
print(f"Found {len(result)} pharmacies")

db.close()
```

## Step 7: Scaling Considerations

### 7.1 Performance Optimization
- **Connection pooling**: Use PgBouncer for connection management
- **Indexing**: Ensure proper indexes on frequently queried columns
- **Query optimization**: Use EXPLAIN ANALYZE to optimize slow queries
- **Caching**: Implement Redis for frequently accessed data

### 7.2 Monitoring
- **Render Dashboard**: Monitor database performance
- **Query logs**: Enable query logging for optimization
- **Backup monitoring**: Ensure backups are running successfully

## Step 8: Security Best Practices

### 8.1 Environment Variables
- Never commit database credentials to version control
- Use Render's environment variable management
- Rotate passwords regularly

### 8.2 Network Security
- Use SSL connections (enabled by default on Render)
- Restrict database access to your application only
- Use connection pooling to limit concurrent connections

## Cost Estimation

### Free Tier (Testing)
- **Storage**: 1GB
- **Connections**: 5 concurrent
- **Cost**: $0/month
- **Suitable for**: Development and testing

### Starter Plan (Small Production)
- **Storage**: 1GB
- **Connections**: 10 concurrent
- **Cost**: $7/month
- **Suitable for**: Small pharmacy chains (1-5 locations)

### Standard Plan (Medium Production)
- **Storage**: 10GB
- **Connections**: 25 concurrent
- **Cost**: $25/month
- **Suitable for**: Medium pharmacy chains (5-20 locations)

### Pro Plan (Large Production)
- **Storage**: 100GB
- **Connections**: 100 concurrent
- **Cost**: $100/month
- **Suitable for**: Large pharmacy chains (20+ locations)

## Next Steps

1. **Create Render account** and PostgreSQL database
2. **Update database connection** script with Render credentials
3. **Deploy your application** to Render
4. **Test the connection** and data insertion
5. **Monitor performance** and scale as needed

This setup will give you a robust, scalable database solution that can grow with your pharmacy system! 🚀 