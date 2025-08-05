#!/usr/bin/env python3
"""
Email Monitor Setup Script
==========================

This script helps set up and configure the pharmacy email monitor service.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_dependencies():
    """Check if required Python packages are installed"""
    print("🔍 Checking Python dependencies...")
    
    required_packages = [
        'imaplib',  # Built-in
        'email',    # Built-in
        'psycopg2',
        'fitz',     # PyMuPDF
        'pathlib',  # Built-in
        'json',     # Built-in
        'logging'   # Built-in
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package in ['imaplib', 'email', 'pathlib', 'json', 'logging']:
                # These are built-in modules
                continue
            elif package == 'fitz':
                import fitz
            elif package == 'psycopg2':
                import psycopg2
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        
        for package in missing_packages:
            if package == 'fitz':
                package = 'PyMuPDF'
            elif package == 'psycopg2':
                package = 'psycopg2-binary'
            
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    else:
        print("✅ All required packages are installed")
    
    return True

def setup_environment_variables():
    """Set up environment variables"""
    print("\n🔧 Setting up environment variables...")
    
    # Check if .env file exists
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Create .env file
    env_content = """# Pharmacy Email Monitor Environment Variables

# Gmail Credentials
REITZ_GMAIL_USERNAME=dmr.tlc.reitz@gmail.com
REITZ_GMAIL_APP_PASSWORD=dkcj ixgf vhkf jupx

# Database Configuration (Update with your Render database URL)
DATABASE_URL=postgresql://your_username:your_password@your_host:5432/your_database

# Optional: Logging level
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("⚠️  Please update DATABASE_URL with your Render database connection string")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating necessary directories...")
    
    directories = [
        'temp_email_pdfs',
        'logs',
        '../temp_classified_pdfs'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory already exists: {directory}")
    
    return True

def setup_systemd_service():
    """Set up systemd service for automatic startup"""
    print("\n🔧 Setting up systemd service...")
    
    # Check if running on macOS (no systemd)
    if sys.platform == 'darwin':
        print("⚠️  macOS detected - systemd not available")
        print("💡 To run the email monitor on macOS, use:")
        print("   python3 email_monitor.py")
        print("   or")
        print("   nohup python3 email_monitor.py > email_monitor.log 2>&1 &")
        return True
    
    # Check if systemd is available
    try:
        subprocess.run(['systemctl', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  systemd not available on this system")
        return True
    
    # Copy service file to systemd directory
    service_file = Path('pharmacy-email-monitor.service')
    systemd_dir = Path('/etc/systemd/system')
    
    if not systemd_dir.exists():
        print("❌ systemd directory not found")
        return False
    
    try:
        # Update service file with correct paths
        current_dir = Path.cwd()
        user = os.getenv('USER', 'charldewet')
        
        with open(service_file, 'r') as f:
            service_content = f.read()
        
        # Replace placeholders
        service_content = service_content.replace(
            '/Users/charldewet/Python/pharmacyDatabase/Scripts',
            str(current_dir)
        )
        service_content = service_content.replace(
            'User=charldewet',
            f'User={user}'
        )
        service_content = service_content.replace(
            'your_render_database_url_here',
            os.getenv('DATABASE_URL', 'postgresql://localhost/pharmacy_reports')
        )
        
        # Write updated service file
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Copy to systemd directory (requires sudo)
        print("📋 Service file updated")
        print("💡 To install the service, run:")
        print(f"   sudo cp {service_file} {systemd_dir}/")
        print("   sudo systemctl daemon-reload")
        print("   sudo systemctl enable pharmacy-email-monitor")
        print("   sudo systemctl start pharmacy-email-monitor")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to set up systemd service: {e}")
        return False

def test_setup():
    """Test the setup"""
    print("\n🧪 Testing setup...")
    
    try:
        # Test environment variables
        if not os.getenv('REITZ_GMAIL_USERNAME'):
            print("❌ REITZ_GMAIL_USERNAME not set")
            return False
        
        if not os.getenv('REITZ_GMAIL_APP_PASSWORD'):
            print("❌ REITZ_GMAIL_APP_PASSWORD not set")
            return False
        
        print("✅ Environment variables are set")
        
        # Test if email monitor can be imported
        from email_monitor import PharmacyEmailMonitor
        print("✅ Email monitor module can be imported")
        
        # Test if test script can be imported
        from test_email_monitor import test_email_connection
        print("✅ Test module can be imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Pharmacy Email Monitor Setup")
    print("=" * 40)
    
    # Run setup steps
    steps = [
        ("Checking Python dependencies", check_python_dependencies),
        ("Setting up environment variables", setup_environment_variables),
        ("Creating directories", create_directories),
        ("Setting up systemd service", setup_systemd_service),
        ("Testing setup", test_setup)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔧 {step_name}...")
        if not step_func():
            print(f"❌ {step_name} failed")
            return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update the DATABASE_URL in .env file with your Render database connection")
    print("2. Test the email monitor: python3 test_email_monitor.py")
    print("3. Run the email monitor: python3 email_monitor.py")
    
    if sys.platform != 'darwin':
        print("4. Install systemd service (if desired):")
        print("   sudo cp pharmacy-email-monitor.service /etc/systemd/system/")
        print("   sudo systemctl daemon-reload")
        print("   sudo systemctl enable pharmacy-email-monitor")
        print("   sudo systemctl start pharmacy-email-monitor")
    
    return True

if __name__ == "__main__":
    main() 