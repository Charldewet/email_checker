#!/usr/bin/env python3
"""
Test Email Processing - Check what emails are being found and processed
"""

import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_email_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_email_search():
    """Test the email search functionality"""
    logger.info("🧪 TESTING EMAIL SEARCH")
    logger.info("="*50)
    
    try:
        from improved_classify_and_organize import ImprovedPDFClassifier
        
        # Create classifier instance
        classifier = ImprovedPDFClassifier()
        
        # Connect to IMAP
        mail = classifier.connect_imap()
        if not mail:
            logger.error("❌ Failed to connect to IMAP")
            return
        
        logger.info("✅ Connected to Gmail IMAP")
        
        # Test different day ranges
        for days in [1, 2, 3]:
            logger.info(f"\n📧 Testing email search for last {days} days:")
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            date_str = cutoff_date.strftime('%d-%b-%Y')
            logger.info(f"  Cutoff date: {date_str}")
            
            # Get emails
            emails = classifier.get_recent_emails(mail, days)
            logger.info(f"  Found {len(emails)} emails with PDF attachments")
            
            # Show email details
            for i, email in enumerate(emails[:5]):  # Show first 5
                subject = email.get('subject', 'No Subject')
                date = email.get('date', 'No Date')
                logger.info(f"    Email {i+1}: {subject} - {date}")
        
        # Close connection
        mail.logout()
        logger.info("✅ Email search test completed")
        
    except Exception as e:
        logger.error(f"❌ Email search test failed: {e}")

def test_today_emails():
    """Test specifically for today's emails"""
    logger.info("\n🧪 TESTING TODAY'S EMAILS")
    logger.info("="*50)
    
    try:
        from improved_classify_and_organize import ImprovedPDFClassifier
        
        # Create classifier instance
        classifier = ImprovedPDFClassifier()
        
        # Connect to IMAP
        mail = classifier.connect_imap()
        if not mail:
            logger.error("❌ Failed to connect to IMAP")
            return
        
        logger.info("✅ Connected to Gmail IMAP")
        
        # Get emails from last 1 day (today)
        emails = classifier.get_recent_emails(mail, 1)
        logger.info(f"📧 Found {len(emails)} emails with PDF attachments from today")
        
        # Look for emails around 16:18 time
        for email in emails:
            subject = email.get('subject', 'No Subject')
            date = email.get('date', 'No Date')
            
            # Check if this might be the 16:18 email
            if '16' in str(date) or '18' in str(date) or '45' in str(subject):
                logger.info(f"🔍 Potential match: {subject} - {date}")
        
        # Close connection
        mail.logout()
        logger.info("✅ Today's email test completed")
        
    except Exception as e:
        logger.error(f"❌ Today's email test failed: {e}")

def main():
    """Main test function"""
    logger.info("🚀 STARTING EMAIL PROCESSING TESTS")
    logger.info("="*50)
    
    test_email_search()
    test_today_emails()
    
    logger.info("\n✅ ALL EMAIL TESTS COMPLETED")

if __name__ == "__main__":
    main() 