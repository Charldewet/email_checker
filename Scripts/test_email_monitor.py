#!/usr/bin/env python3
"""
Test Email Monitor
=================

This script tests the email monitor functionality without running the continuous loop.
Useful for debugging and testing the email connection and PDF processing.
"""

import os
import sys
from email_monitor import PharmacyEmailMonitor

def test_email_connection():
    """Test Gmail connection"""
    print("🧪 Testing Gmail Connection")
    print("=" * 40)
    
    monitor = PharmacyEmailMonitor()
    
    # Test IMAP connection
    mail = monitor.connect_imap()
    if mail:
        print("✅ Gmail IMAP connection successful")
        
        # Test getting unread emails
        unread_emails = monitor.get_unread_emails(mail)
        print(f"📧 Found {len(unread_emails)} unread emails with PDFs")
        
        for email_data in unread_emails:
            print(f"   • {email_data['subject']} (from: {email_data['from']})")
        
        mail.logout()
        return True
    else:
        print("❌ Gmail IMAP connection failed")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🧪 Testing Database Connection")
    print("=" * 40)
    
    monitor = PharmacyEmailMonitor()
    
    if monitor.db:
        print("✅ Database connection successful")
        
        # Test database stats
        stats = monitor.db.get_database_stats()
        print(f"📊 Database Statistics:")
        print(f"   • Pharmacies: {stats.get('pharmacies', 0)}")
        print(f"   • Daily Summaries: {stats.get('daily_summaries', 0)}")
        print(f"   • Sales Details: {stats.get('sales_details', 0)}")
        
        return True
    else:
        print("❌ Database connection failed")
        return False

def test_single_email_processing():
    """Test processing a single email cycle"""
    print("\n🧪 Testing Single Email Processing Cycle")
    print("=" * 50)
    
    monitor = PharmacyEmailMonitor()
    
    # Run one processing cycle
    success = monitor.process_single_email_cycle()
    
    if success:
        print("✅ Email processing cycle completed successfully")
    else:
        print("❌ Email processing cycle failed")
    
    return success

def main():
    """Run all tests"""
    print("🧪 Pharmacy Email Monitor Test Suite")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('REITZ_GMAIL_USERNAME') or not os.getenv('REITZ_GMAIL_APP_PASSWORD'):
        print("❌ Please set REITZ_GMAIL_USERNAME and REITZ_GMAIL_APP_PASSWORD environment variables")
        return
    
    # Run tests
    tests = [
        ("Gmail Connection", test_email_connection),
        ("Database Connection", test_database_connection),
        ("Email Processing", test_single_email_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Email monitor is ready to run.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main() 