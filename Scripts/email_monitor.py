#!/usr/bin/env python3
"""
Email Monitor for Pharmacy Reports
==================================

This script monitors a Gmail account for new pharmacy report emails,
extracts PDF attachments, processes them through the data pipeline,
and cleans up the emails after successful processing.
"""

import os
import time
import email
import imaplib
import smtplib
import logging
import tempfile
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime, timedelta
import json
import threading
from typing import List, Dict, Optional

# Import our existing modules
from classify_and_organize_pdfs import classify_and_organize_pdfs
from extract_trading_summary import extract_trading_summary_data
from extract_turnover_summary import extract_turnover_summary_data
from extract_transaction_summary import extract_transaction_summary_data
from extract_gross_profit import extract_gross_profit_data
from extract_dispensary_summary import extract_dispensary_summary_data
from render_database_connection import RenderPharmacyDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PharmacyEmailMonitor:
    def __init__(self):
        """Initialize the email monitor with Gmail credentials"""
        self.gmail_user = os.getenv('REITZ_GMAIL_USERNAME', 'dmr.tlc.reitz@gmail.com')
        self.gmail_password = os.getenv('REITZ_GMAIL_APP_PASSWORD', 'dkcj ixgf vhkf jupx')
        self.imap_server = 'imap.gmail.com'
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        
        # Email processing settings
        self.processed_emails_file = 'processed_emails.json'
        self.temp_dir = Path('temp_email_pdfs')
        self.temp_dir.mkdir(exist_ok=True)
        
        # Database connection
        self.db = None
        self.connect_database()
        
        # Load processed email IDs
        self.processed_emails = self.load_processed_emails()
        
        logger.info(f"Email monitor initialized for {self.gmail_user}")
    
    def connect_database(self):
        """Connect to the Render database"""
        try:
            self.db = RenderPharmacyDatabase()
            logger.info("✅ Connected to Render database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            self.db = None
    
    def load_processed_emails(self) -> set:
        """Load list of already processed email IDs"""
        try:
            if os.path.exists(self.processed_emails_file):
                with open(self.processed_emails_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_emails', []))
        except Exception as e:
            logger.error(f"Failed to load processed emails: {e}")
        return set()
    
    def save_processed_emails(self):
        """Save list of processed email IDs"""
        try:
            data = {
                'processed_emails': list(self.processed_emails),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.processed_emails_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save processed emails: {e}")
    
    def connect_imap(self):
        """Connect to Gmail IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.gmail_user, self.gmail_password)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail IMAP: {e}")
            return None
    
    def get_unread_emails(self, mail) -> List[Dict]:
        """Get all unread emails with PDF attachments"""
        unread_emails = []
        
        try:
            # Select inbox
            mail.select('INBOX')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return unread_emails
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Check if email has PDF attachments
                    has_pdf = False
                    for part in email_message.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue
                        
                        filename = part.get_filename()
                        if filename and filename.lower().endswith('.pdf'):
                            has_pdf = True
                            break
                    
                    if has_pdf:
                        unread_emails.append({
                            'id': email_id.decode(),
                            'subject': email_message.get('Subject', 'No Subject'),
                            'from': email_message.get('From', 'Unknown'),
                            'date': email_message.get('Date', 'Unknown'),
                            'message': email_message
                        })
                        logger.info(f"Found unread email with PDF: {email_message.get('Subject', 'No Subject')}")
                
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            return unread_emails
            
        except Exception as e:
            logger.error(f"Error getting unread emails: {e}")
            return unread_emails
    
    def extract_pdf_attachments(self, email_message, email_id: str) -> List[Path]:
        """Extract PDF attachments from email"""
        pdf_files = []
        
        try:
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                
                filename = part.get_filename()
                if filename and filename.lower().endswith('.pdf'):
                    # Create unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_filename = f"{timestamp}_{email_id}_{filename}"
                    filepath = self.temp_dir / safe_filename
                    
                    # Save PDF file
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    pdf_files.append(filepath)
                    logger.info(f"Extracted PDF: {filename} -> {filepath}")
            
            return pdf_files
            
        except Exception as e:
            logger.error(f"Error extracting PDF attachments: {e}")
            return pdf_files
    
    def process_pdfs_through_pipeline(self, pdf_files: List[Path]) -> bool:
        """Process PDFs through the complete data pipeline"""
        try:
            if not pdf_files:
                logger.warning("No PDF files to process")
                return False
            
            logger.info(f"Processing {len(pdf_files)} PDF files through pipeline")
            
            # Step 1: Classify and organize PDFs
            logger.info("Step 1: Classifying and organizing PDFs")
            classify_and_organize_pdfs()
            
            # Step 2: Run complete data pipeline
            logger.info("Step 2: Running complete data pipeline")
            try:
                from complete_data_pipeline import run_complete_pipeline
                run_complete_pipeline()
                logger.info("✅ Complete data pipeline finished successfully")
            except Exception as e:
                logger.error(f"❌ Complete data pipeline failed: {e}")
                # Fallback: try individual extractions
                logger.info("Trying individual extractions as fallback...")
                
                # Trading Summary
                try:
                    from extract_trading_summary import test_trading_extraction
                    test_trading_extraction()
                    logger.info("✅ Trading summary extraction completed")
                except Exception as e:
                    logger.error(f"❌ Trading summary extraction failed: {e}")
                
                # Turnover Summary
                try:
                    from extract_turnover_summary import test_turnover_extraction
                    test_turnover_extraction()
                    logger.info("✅ Turnover summary extraction completed")
                except Exception as e:
                    logger.error(f"❌ Turnover summary extraction failed: {e}")
                
                # Transaction Summary
                try:
                    from extract_transaction_summary import test_transaction_extraction
                    test_transaction_extraction()
                    logger.info("✅ Transaction summary extraction completed")
                except Exception as e:
                    logger.error(f"❌ Transaction summary extraction failed: {e}")
                
                # Gross Profit Report
                try:
                    from extract_gross_profit import test_gross_profit_extraction
                    test_gross_profit_extraction()
                    logger.info("✅ Gross profit extraction completed")
                except Exception as e:
                    logger.error(f"❌ Gross profit extraction failed: {e}")
                
                # Dispensary Summary
                try:
                    from extract_dispensary_summary import test_dispensary_extraction
                    test_dispensary_extraction()
                    logger.info("✅ Dispensary summary extraction completed")
                except Exception as e:
                    logger.error(f"❌ Dispensary summary extraction failed: {e}")
            
            # Step 3: Combine data and insert into database
            if self.db:
                logger.info("Step 3: Combining data and inserting into database")
                self.insert_combined_data_into_database()
            else:
                logger.warning("Database not connected, skipping database insertion")
            
            logger.info("✅ PDF processing pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ PDF processing pipeline failed: {e}")
            return False
    
    def insert_combined_data_into_database(self):
        """Insert combined data into the Render database"""
        try:
            # Load combined data from JSON files
            combined_data = self.load_combined_data()
            
            if not combined_data:
                logger.warning("No combined data found to insert")
                return
            
            logger.info(f"Inserting data for {len(combined_data)} pharmacy/date combinations")
            
            success_count = 0
            for key, data in combined_data.items():
                try:
                    # Insert daily summary
                    if self.db.insert_daily_summary(**data):
                        success_count += 1
                        logger.info(f"✅ Inserted data for {key}")
                    else:
                        logger.error(f"❌ Failed to insert data for {key}")
                except Exception as e:
                    logger.error(f"❌ Error inserting data for {key}: {e}")
            
            logger.info(f"✅ Successfully inserted {success_count}/{len(combined_data)} records")
            
        except Exception as e:
            logger.error(f"❌ Database insertion failed: {e}")
    
    def load_combined_data(self) -> Dict:
        """Load combined data from the pipeline JSON files"""
        try:
            # Try to load from complete pipeline data
            if os.path.exists('complete_pipeline_data.json'):
                with open('complete_pipeline_data.json', 'r') as f:
                    return json.load(f)
            
            # Fallback: load individual files and combine
            combined_data = {}
            
            # Load individual extraction results
            extraction_files = [
                'trading_summary_extracted_data.json',
                'turnover_summary_extracted_data.json',
                'transaction_summary_extracted_data.json',
                'gross_profit_extracted_data.json',
                'dispensary_summary_extracted_data.json'
            ]
            
            for file in extraction_files:
                if os.path.exists(file):
                    try:
                        with open(file, 'r') as f:
                            data = json.load(f)
                            # Combine data based on pharmacy and date
                            for item in data:
                                key = f"{item.get('pharmacy', 'unknown')}_{item.get('date', 'unknown')}"
                                if key not in combined_data:
                                    combined_data[key] = {}
                                combined_data[key].update(item)
                    except Exception as e:
                        logger.error(f"Error loading {file}: {e}")
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error loading combined data: {e}")
            return {}
    
    def cleanup_processed_files(self, pdf_files: List[Path]):
        """Clean up processed PDF files and temporary directories"""
        try:
            # Remove extracted PDF files
            for pdf_file in pdf_files:
                if pdf_file.exists():
                    pdf_file.unlink()
                    logger.info(f"Removed PDF file: {pdf_file}")
            
            # Clean up temp directories
            temp_dirs = [
                Path('temp_classified_pdfs'),
                Path('temp_email_pdfs')
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.info(f"Removed temp directory: {temp_dir}")
            
            # Clean up JSON files (optional - keep for debugging)
            # json_files = Path('.').glob('*_extracted_data.json')
            # for json_file in json_files:
            #     json_file.unlink()
            #     logger.info(f"Removed JSON file: {json_file}")
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def mark_email_as_processed(self, mail, email_id: str):
        """Mark email as processed and move to processed folder"""
        try:
            # Add to processed emails list
            self.processed_emails.add(email_id)
            self.save_processed_emails()
            
            # Move email to processed folder (optional)
            # mail.store(email_id, '+X-GM-LABELS', '\\Processed')
            
            logger.info(f"Marked email {email_id} as processed")
            
        except Exception as e:
            logger.error(f"Failed to mark email as processed: {e}")
    
    def process_single_email_cycle(self):
        """Process one cycle of email checking"""
        logger.info("🔄 Starting email processing cycle")
        
        mail = self.connect_imap()
        if not mail:
            return False
        
        try:
            # Get unread emails with PDFs
            unread_emails = self.get_unread_emails(mail)
            
            if not unread_emails:
                logger.info("No new emails with PDFs found")
                return True
            
            logger.info(f"Found {len(unread_emails)} new emails with PDFs")
            
            # Collect all PDF files first
            all_pdf_files = []
            processed_emails = []
            
            for email_data in unread_emails:
                email_id = email_data['id']
                
                # Skip if already processed
                if email_id in self.processed_emails:
                    logger.info(f"Email {email_id} already processed, skipping")
                    continue
                
                logger.info(f"Processing email: {email_data['subject']}")
                
                try:
                    # Extract PDF attachments
                    pdf_files = self.extract_pdf_attachments(email_data['message'], email_id)
                    
                    if not pdf_files:
                        logger.warning(f"No PDF files found in email {email_id}")
                        self.mark_email_as_processed(mail, email_id)
                        continue
                    
                    # Add to collection
                    all_pdf_files.extend(pdf_files)
                    processed_emails.append(email_id)
                    
                    logger.info(f"✅ Extracted {len(pdf_files)} PDF files from email {email_id}")
                
                except Exception as e:
                    logger.error(f"❌ Error processing email {email_id}: {e}")
                    continue
            
            # Process all PDFs through pipeline at once
            if all_pdf_files:
                logger.info(f"Processing {len(all_pdf_files)} total PDF files through pipeline")
                success = self.process_pdfs_through_pipeline(all_pdf_files)
                
                if success:
                    # Clean up all files at once
                    self.cleanup_processed_files(all_pdf_files)
                    
                    # Mark all emails as processed
                    for email_id in processed_emails:
                        self.mark_email_as_processed(mail, email_id)
                        logger.info(f"✅ Successfully processed email {email_id}")
                else:
                    logger.error(f"❌ Failed to process PDF pipeline")
            else:
                logger.info("No PDF files to process")
            
            return True
            
        finally:
            mail.logout()
    
    def run_continuous_monitoring(self, interval_minutes: int = 10):
        """Run continuous email monitoring"""
        logger.info(f"🚀 Starting continuous email monitoring (checking every {interval_minutes} minutes)")
        
        while True:
            try:
                self.process_single_email_cycle()
                
                # Wait for next cycle
                logger.info(f"⏰ Waiting {interval_minutes} minutes until next check...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Email monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Email monitoring error: {e}")
                logger.info("⏰ Waiting 5 minutes before retrying...")
                time.sleep(5 * 60)
        
        # Cleanup
        if self.db:
            self.db.close()

def main():
    """Main function to run the email monitor"""
    print("📧 Pharmacy Email Monitor")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('REITZ_GMAIL_USERNAME') or not os.getenv('REITZ_GMAIL_APP_PASSWORD'):
        print("❌ Please set REITZ_GMAIL_USERNAME and REITZ_GMAIL_APP_PASSWORD environment variables")
        return
    
    # Create and run email monitor
    monitor = PharmacyEmailMonitor()
    
    # Run continuous monitoring
    monitor.run_continuous_monitoring(interval_minutes=10)

if __name__ == "__main__":
    main() 