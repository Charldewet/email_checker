#!/usr/bin/env python3
"""
Setup script for Pharmacy Reporting System

This script helps automate the setup process and provides helpful instructions.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header():
    """Print a nice header for the setup process."""
    print("🏥 Pharmacy Reporting System - Setup")
    print("=" * 50)
    print()


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True


def check_postgresql():
    """Check if PostgreSQL is available."""
    print("\n🐘 Checking PostgreSQL availability...")
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ PostgreSQL found:", result.stdout.strip())
            return True
        else:
            print("❌ PostgreSQL not found or not accessible")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ PostgreSQL not found. Please install PostgreSQL first.")
        return False


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_env_file():
    """Create .env file if it doesn't exist."""
    print("\n⚙️ Setting up environment configuration...")
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Read the example file
    example_file = Path('env_example.txt')
    if not example_file.exists():
        print("❌ env_example.txt not found")
        return False
    
    # Copy example to .env
    try:
        with open(example_file, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created from template")
        print("⚠️  Please edit .env file with your database credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def setup_database():
    """Provide instructions for database setup."""
    print("\n🗄️ Database Setup Instructions:")
    print("1. Connect to your PostgreSQL instance:")
    print("   psql -U postgres")
    print()
    print("2. Create the database:")
    print("   CREATE DATABASE pharmacy_reports;")
    print("   \\c pharmacy_reports")
    print()
    print("3. Run the setup script:")
    print("   psql -d pharmacy_reports -f database_setup.sql")
    print()
    print("4. Or run this command from the project directory:")
    print("   psql -d pharmacy_reports -f database_setup.sql")
    print()


def test_connection():
    """Test database connection."""
    print("\n🔌 Testing database connection...")
    try:
        from database_connection import PharmacyDatabase
        db = PharmacyDatabase()
        if db.test_connection():
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection failed")
            print("   Please check your .env file and ensure PostgreSQL is running")
            return False
    except ImportError:
        print("❌ Could not import database module")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def run_sample_data():
    """Ask user if they want to run sample data ingestion."""
    print("\n📊 Sample Data Setup:")
    response = input("Would you like to create sample data? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        try:
            print("Running sample data ingestion...")
            subprocess.run([sys.executable, 'sample_data_ingestion.py'], check=True)
            print("✅ Sample data created successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Sample data creation failed: {e}")
    else:
        print("Skipping sample data creation")


def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup completed!")
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Set up the database using the instructions above")
    print("3. Test the connection: python -c \"from database_connection import PharmacyDatabase; PharmacyDatabase().test_connection()\"")
    print("4. Run sample data: python sample_data_ingestion.py")
    print("5. Start extracting data from your PDF reports")
    print("\n📚 Documentation:")
    print("- README.md - Complete documentation")
    print("- database_connection.py - Python API reference")
    print("- database_setup.sql - Database schema")


def main():
    """Main setup function."""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_postgresql():
        print("\n💡 PostgreSQL Installation:")
        system = platform.system().lower()
        if system == "darwin":  # macOS
            print("   brew install postgresql")
            print("   brew services start postgresql")
        elif system == "linux":
            print("   sudo apt-get install postgresql postgresql-contrib")
            print("   sudo systemctl start postgresql")
        elif system == "windows":
            print("   Download from: https://www.postgresql.org/download/windows/")
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create environment file
    if not create_env_file():
        return False
    
    # Provide database setup instructions
    setup_database()
    
    # Test connection (optional)
    response = input("\nWould you like to test the database connection? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        test_connection()
    
    # Run sample data
    run_sample_data()
    
    # Print next steps
    print_next_steps()
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1) 