#!/usr/bin/env python3
"""
Execute SQL File
===============

This script executes the SQL file to insert today's Winterton data into the database.
"""

import os
import sys

# Add Scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def execute_sql_file():
    """Execute the SQL file to insert today's data"""
    print("🚀 Executing SQL file to insert today's Winterton data...")
    
    # Use DATABASE_URL from environment; ensure it is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not set in environment")
        return
    
    try:
        from render_database_connection import RenderPharmacyDatabase
        db = RenderPharmacyDatabase()
        
        # Read and execute SQL file
        with open('complete_database_inserts.sql', 'r') as f:
            sql_content = f.read()
        
        print("📄 SQL file loaded successfully")
        print(f"📊 SQL file size: {len(sql_content)} characters")
        
        # Execute the SQL
        db.execute_query(sql_content)
        print("✅ SQL executed successfully!")
        
        print("\n🎉 Today's Winterton data has been inserted into the database!")
        print("💡 You can now check the database for today's turnover data.")
        
    except Exception as e:
        print(f"❌ Error executing SQL: {e}")

if __name__ == "__main__":
    execute_sql_file() 