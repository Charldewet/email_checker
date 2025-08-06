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
        self.report_timestamps_file = 'report_timestamps.json'
        self.temp_dir = Path('temp_email_pdfs')
        self.temp_dir.mkdir(exist_ok=True)
        
        # Database connection
        self.db = None
        self.connect_database()
        
        # Load processed email IDs and report timestamps
        self.processed_emails = self.load_processed_emails()
        self.report_timestamps = self.load_report_timestamps()
        
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
    
    def load_report_timestamps(self) -> Dict:
        """Load timestamp tracking for report dates"""
        try:
            if Path(self.report_timestamps_file).exists():
                with open(self.report_timestamps_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading report timestamps: {e}")
            return {}
    
    def save_report_timestamps(self):
        """Save timestamp tracking for report dates"""
        try:
            with open(self.report_timestamps_file, 'w') as f:
                json.dump(self.report_timestamps, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving report timestamps: {e}")
    
    def should_process_report(self, report_date: str, email_timestamp: datetime) -> bool:
        """Check if we should process this report based on timestamp"""
        if report_date not in self.report_timestamps:
            return True  # New report date, always process
        
        last_timestamp_str = self.report_timestamps[report_date].get('last_email_timestamp')
        if not last_timestamp_str:
            return True
        
        try:
            last_timestamp = datetime.fromisoformat(last_timestamp_str)
            return email_timestamp > last_timestamp
        except:
            return True  # If we can't parse, play it safe and process
    
    def update_report_timestamp(self, report_date: str, email_timestamp: datetime):
        """Update the timestamp for a report date"""
        if report_date not in self.report_timestamps:
            self.report_timestamps[report_date] = {}
        
        self.report_timestamps[report_date]['last_email_timestamp'] = email_timestamp.isoformat()
        self.report_timestamps[report_date]['last_processed'] = datetime.now().isoformat()
    
    def connect_imap(self):
        """Connect to Gmail IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.gmail_user, self.gmail_password)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail IMAP: {e}")
            return None
    
    def get_recent_emails(self, mail, days: int = 2) -> List[Dict]:
        """Get emails from the last N days with PDF attachments"""
        recent_emails = []
        
        try:
            # Select inbox
            mail.select('INBOX')
            
            # Calculate date range (last N days)
            cutoff_date = datetime.now() - timedelta(days=days)
            date_str = cutoff_date.strftime('%d-%b-%Y')
            
            # Search for emails since cutoff date
            status, messages = mail.search(None, f'SINCE {date_str}')
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return recent_emails
            
            email_ids = messages[0].split()
            logger.info(f"Checking {len(email_ids)} emails from last {days} days")
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Determine a reliable timestamp for this email
                    try:
                        # Prefer the server-side INTERNALDATE (timezone-safe and monotonic)
                        status_int, int_data = mail.fetch(email_id, '(INTERNALDATE)')
                        if status_int == 'OK' and int_data:
                            raw = int_data[0][0] if isinstance(int_data[0], tuple) else int_data[0]
                            internal_ts = imaplib.Internaldate2tuple(raw)
                            email_timestamp = datetime.fromtimestamp(time.mktime(internal_ts))
                        else:
                            raise ValueError("INTERNALDATE not available")
                    except Exception as e:
                        # Fallback to parsing the Date: header or use current time
                        email_timestamp = datetime.now()
                        date_hdr = email_message.get('Date', '')
                        if date_hdr:
                            try:
                                date_str_clean = date_hdr.split(' (')[0].split(' +')[0]
                                email_timestamp = datetime.strptime(date_str_clean, '%a, %d %b %Y %H:%M:%S')
                            except Exception:
                                logger.warning(f"Could not parse email Date header '{date_hdr}'")
                    
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
                        recent_emails.append({
                            'id': email_id.decode(),
                            'subject': email_message.get('Subject', 'No Subject'),
                            'from': email_message.get('From', 'Unknown'),
                            'date': email_message.get('Date', 'Unknown'),
                            'timestamp': email_timestamp,
                            'message': email_message
                        })
                
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            logger.info(f"Found {len(recent_emails)} emails with PDFs from last {days} days")
            return recent_emails
            
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            return recent_emails
    
    def extract_report_date_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract report date from PDF content"""
        try:
            # First try to extract from filename (as fallback)
            filename = pdf_path.name
            filename_date = self.extract_date_from_filename(filename)
            
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Date patterns to match (more comprehensive)
            import re
            date_patterns = [
                # DATE FROM : 2025/08/05 DATE TO : 2025/08/05
                r'DATE FROM\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+DATE TO\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
                # 05/08/2025 - 05/08/2025
                r'(\d{1,2})/(\d{1,2})/(\d{4})\s*-\s*(\d{1,2})/(\d{1,2})/(\d{4})',
                # Report Date : 2025-08-05
                r'Report Date\s*:\s*(\d{4})-(\d{1,2})-(\d{1,2})',
                # Date : 05/08/2025
                r'Date\s*:\s*(\d{1,2})/(\d{1,2})/(\d{4})',
                # Any 2025/08/05 pattern
                r'(\d{4})/(\d{1,2})/(\d{1,2})',
                # Any 05/08/2025 pattern
                r'(\d{1,2})/(\d{1,2})/(\d{4})'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    # Use the last match found (likely the most recent/relevant)
                    match = matches[-1]
                    
                    if 'DATE TO' in pattern:
                        # Use the "TO" date (end date)
                        year, month, day = match[3], match[4], match[5]
                    elif len(match) == 6:
                        # Date range, use end date
                        day, month, year = match[3], match[4], match[5]
                    elif len(match) == 3:
                        if len(match[0]) == 4:
                            # YYYY/MM/DD format
                            year, month, day = match[0], match[1], match[2]
                        else:
                            # DD/MM/YYYY format
                            day, month, year = match[0], match[1], match[2]
                    
                    # Format as YYYY-MM-DD
                    extracted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    logger.info(f"Extracted date {extracted_date} from PDF content")
                    return extracted_date
            
            # If no date found in PDF content, use filename date
            if filename_date:
                logger.info(f"Using filename date {filename_date} as fallback")
                return filename_date
            
            return None
        except Exception as e:
            logger.error(f"Error extracting date from {pdf_path}: {e}")
            # Try filename as last resort
            filename = pdf_path.name
            return self.extract_date_from_filename(filename)
    
    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from filename as fallback"""
        try:
            import re
            # Look for date patterns in filename like 20250805-09h51m22s-Complete.pdf
            patterns = [
                r'(\d{4})(\d{2})(\d{2})-\d{2}h\d{2}m\d{2}s',  # 20250805-09h51m22s
                r'(\d{4})-(\d{2})-(\d{2})',  # 2025-08-05
                r'(\d{2})(\d{2})(\d{4})',    # 05082025
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filename)
                if match:
                    if len(match.group(1)) == 4:
                        # YYYYMMDD or YYYY-MM-DD
                        year, month, day = match.group(1), match.group(2), match.group(3)
                    else:
                        # DDMMYYYY
                        day, month, year = match.group(1), match.group(2), match.group(3)
                    
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return None
        except Exception as e:
            logger.error(f"Error extracting date from filename {filename}: {e}")
            return None
    
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
                    # Ensure temp directory exists
                    self.temp_dir.mkdir(exist_ok=True)
                    
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
            from classify_and_organize_pdfs import classify_and_organize_pdfs
            classify_and_organize_pdfs("temp_email_pdfs")
            
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
            # Try to use the insert_data_to_database script directly
            logger.info("Using direct database insertion script...")
            try:
                from insert_data_to_database import main as insert_main
                insert_main()
                logger.info("✅ Data inserted using direct insertion script")
                return
            except Exception as e:
                logger.error(f"Direct insertion failed: {e}")
            
            # Fallback: Load combined data from JSON files
            combined_data = self.load_combined_data()
            
            if not combined_data:
                logger.warning("No combined data found to insert")
                # Try to list available JSON files for debugging
                json_files = list(Path('.').glob('*.json'))
                logger.info(f"Available JSON files: {[f.name for f in json_files]}")
                return
            
            logger.info(f"Inserting data for {len(combined_data)} pharmacy/date combinations")
            
            success_count = 0
            for key, data in combined_data.items():
                try:
                    # Extract the data properly for insertion
                    insert_data = self.prepare_data_for_insertion(data)
                    
                    # Insert daily summary
                    if self.db.insert_daily_summary(**insert_data):
                        success_count += 1
                        logger.info(f"✅ Inserted data for {key}")
                    else:
                        logger.error(f"❌ Failed to insert data for {key}")
                except Exception as e:
                    logger.error(f"❌ Error inserting data for {key}: {e}")
            
            logger.info(f"✅ Successfully inserted {success_count}/{len(combined_data)} records")
            
        except Exception as e:
            logger.error(f"❌ Database insertion failed: {e}")
    
    def prepare_data_for_insertion(self, data):
        """Prepare combined data for database insertion"""
        try:
            # If data is nested (from complete_pipeline_data.json), extract the fields
            if isinstance(data, dict):
                insert_data = {}
                
                # Extract basic info
                insert_data['pharmacy_code'] = data.get('pharmacy', 'UNKNOWN')
                insert_data['report_date'] = data.get('date', '2025-08-04')
                
                # Extract from trading summary
                trading = data.get('trading_summary', {})
                insert_data['stock_opening'] = trading.get('stock_opening')
                insert_data['stock_closing'] = trading.get('stock_closing')
                insert_data['purchases'] = trading.get('purchases')
                insert_data['adjustments'] = trading.get('adjustments')
                insert_data['cost_of_sales'] = trading.get('cost_of_sales')
                insert_data['gp_value'] = trading.get('gp_value')
                insert_data['gp_percent'] = trading.get('gp_percent')
                
                # Extract from turnover summary (override turnover)
                turnover = data.get('turnover_summary', {})
                insert_data['turnover'] = turnover.get('turnover')
                insert_data['sales_cash'] = turnover.get('sales_cash')
                insert_data['sales_account'] = turnover.get('sales_account')
                insert_data['sales_cod'] = turnover.get('sales_cod')
                
                # Extract from transaction summary
                transaction = data.get('transaction_summary', {})
                insert_data['transactions_total'] = transaction.get('transactions_total')
                insert_data['avg_basket_value'] = transaction.get('avg_basket_value')
                
                # Extract from gross profit
                gross_profit = data.get('gross_profit', {})
                if gross_profit and transaction.get('transactions_total'):
                    total_qty = gross_profit.get('total_sales_qty', 0)
                    transactions = transaction.get('transactions_total', 1)
                    insert_data['avg_basket_size'] = total_qty / transactions if transactions > 0 else 0
                
                # Extract from dispensary summary
                dispensary = data.get('dispensary_summary', {})
                insert_data['script_total'] = dispensary.get('script_total')
                insert_data['disp_turnover'] = dispensary.get('disp_turnover')
                insert_data['avg_script_value'] = dispensary.get('avg_script_value')
                
                return insert_data
            else:
                return data
                
        except Exception as e:
            logger.error(f"Error preparing data for insertion: {e}")
            return data
    
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
        """Process one cycle of email checking with date-based logic"""
        logger.info("🔄 Starting email processing cycle")
        
        mail = self.connect_imap()
        if not mail:
            return False
        
        try:
            # Get recent emails with PDFs (last 2 days)
            recent_emails = self.get_recent_emails(mail, days=2)
            
            if not recent_emails:
                logger.info("No emails with PDFs found")
                return True
            
            # Group emails by report date and find latest for each date
            reports_by_date = {}
            examined_emails = []  # Track all emails examined in this cycle
            
            for email_data in recent_emails:
                email_id = email_data['id']
                email_timestamp = email_data['timestamp']
                
                # Skip if this email was already processed
                if email_id in self.processed_emails:
                    logger.info(f"Skipping already processed email {email_id}")
                    continue
                
                # Track that we examined this email (even if it doesn't contain useful data)
                examined_emails.append(email_id)
                logger.info(f"Processing email: {email_data['subject']}")
                
                try:
                    # Extract PDF attachments
                    pdf_files = self.extract_pdf_attachments(email_data['message'], email_id)
                    
                    if not pdf_files:
                        logger.warning(f"No PDF files found in email {email_id}")
                        continue
                    
                    # Extract report dates from PDFs
                    for pdf_file in pdf_files:
                        report_date = self.extract_report_date_from_pdf(pdf_file)
                        if report_date:
                            logger.info(f"Found report for date: {report_date}")
                            
                            # Check if we should process this report
                            if self.should_process_report(report_date, email_timestamp):
                                if report_date not in reports_by_date:
                                    reports_by_date[report_date] = {
                                        'pdf_files': [],
                                        'email_timestamp': email_timestamp,
                                        'email_id': email_id
                                    }
                                elif email_timestamp > reports_by_date[report_date]['email_timestamp']:
                                    # This email is newer, replace the data
                                    reports_by_date[report_date] = {
                                        'pdf_files': [],
                                        'email_timestamp': email_timestamp,
                                        'email_id': email_id
                                    }
                                
                                # Add PDF if this is the latest email for this date
                                if reports_by_date[report_date]['email_timestamp'] == email_timestamp:
                                    reports_by_date[report_date]['pdf_files'].append(pdf_file)
                            else:
                                logger.info(f"Skipping report for {report_date} - we have newer data")
                        else:
                            logger.warning(f"Could not extract date from {pdf_file}")
                    
                    logger.info(f"✅ Extracted {len(pdf_files)} PDF files from email {email_id}")
                
                except Exception as e:
                    logger.error(f"❌ Error processing email {email_id}: {e}")
                    continue
            
            # Collect all PDF files for batch processing
            all_pdf_files = []
            processed_dates = []
            
            if reports_by_date:
                logger.info(f"Processing reports for {len(reports_by_date)} dates")
                
                for report_date, report_data in reports_by_date.items():
                    pdf_files = report_data['pdf_files']
                    email_timestamp = report_data['email_timestamp']
                    
                    if pdf_files:
                        logger.info(f"Found {len(pdf_files)} PDFs for date: {report_date}")
                        all_pdf_files.extend(pdf_files)
                        processed_dates.append((report_date, email_timestamp))
                
                if all_pdf_files:
                    logger.info(f"Processing {len(all_pdf_files)} total PDFs through pipeline")
                    
                    # Process all PDFs together
                    success = self.process_pdfs_through_pipeline(all_pdf_files)
                    
                    if success:
                        # Update timestamp tracking for all dates
                        for report_date, email_timestamp in processed_dates:
                            self.update_report_timestamp(report_date, email_timestamp)
                        
                        self.save_report_timestamps()
                        
                        # Mark all processed emails as processed
                        for report_date, report_data in reports_by_date.items():
                            email_id = report_data['email_id']
                            self.processed_emails.add(email_id)
                            logger.info(f"Marked email {email_id} as processed")
                        
                        self.save_processed_emails()
                        
                        # Clean up all files at once
                        self.cleanup_processed_files(all_pdf_files)
                        
                        logger.info(f"✅ Successfully processed all reports")
                    else:
                        logger.error(f"❌ Failed to process reports")
                else:
                    logger.info("No PDF files found to process")
            
            # Always mark all examined emails as processed to prevent re-examination
            # (Removed in favour of only marking successfully processed emails)
            
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