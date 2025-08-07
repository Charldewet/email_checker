#!/usr/bin/env python3
"""
Improved PDF Classification and Organization
===========================================

This script processes PDFs from emails received in the last 2 days,
classifies them by report type and pharmacy, and organizes them into
appropriate folders without timestamp-based naming.
"""

import os
import shutil
from pathlib import Path
import fitz  # PyMuPDF
import re
from datetime import datetime, timedelta
import email
import imaplib
import tempfile
import logging

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/classification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define keywords for each report type
REPORT_KEYWORDS = {
    "turnover_summary": ["TOTAL TURNOVER", "GP %", "BASKET VALUE", "TRANSACTIONS"],
    "gross_profit_report": ["GROSS PROFIT", "STOCK CODE", "SALES QTY", "DEPT"],
    "trading_summary": ["OPENING STOCK", "CLOSING STOCK", "PURCHASES", "ADJUSTMENTS"],
    "dispensary_summary": ["SCRIPT STATISTICS", "CLAIMABLE SCRIPTS", "PRIVATE SCRIPTS", "DOCTOR SCRIPT"],
    "transaction_summary": ["INVOICING AUDIT TRAIL"]
}

# Define known pharmacy names
KNOWN_PHARMACIES = ["REITZ", "TLC WINTERTON"]

class ImprovedPDFClassifier:
    def __init__(self):
        """Initialize the classifier"""
        self.gmail_user = os.getenv('REITZ_GMAIL_USERNAME', 'dmr.tlc.reitz@gmail.com')
        self.gmail_password = os.getenv('REITZ_GMAIL_APP_PASSWORD', 'dkcj ixgf vhkf jupx')
        self.imap_server = 'imap.gmail.com'
        self.temp_dir = Path("temp_classified_test")
        self.temp_dir.mkdir(exist_ok=True)
        
    def connect_imap(self):
        """Connect to Gmail IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.gmail_user, self.gmail_password)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to Gmail IMAP: {e}")
            return None
    
    def get_recent_emails(self, mail, days: int = 2):
        """Get emails from the last N days with PDF attachments"""
        recent_emails = []
        
        try:
            # Select inbox
            mail.select('INBOX')
            
            # Calculate date range (last N days) - Account for GMT+2 timezone
            # Add 2 hours to ensure we capture emails from today in GMT+2
            cutoff_date = datetime.now() - timedelta(days=days) + timedelta(hours=2)
            date_str = cutoff_date.strftime('%d-%b-%Y')
            
            logger.info(f"Searching for emails since {date_str} (accounting for GMT+2 timezone)")
            
            # Search for emails since cutoff date
            status, messages = mail.search(None, f'SINCE {date_str}')
            
            if status != 'OK':
                logger.error("Failed to search emails")
                return recent_emails
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
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
                            'id': email_id,
                            'message': email_message,
                            'subject': email_message.get('subject', 'No Subject'),
                            'date': email_message.get('date', 'No Date')
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            logger.info(f"Found {len(recent_emails)} emails with PDF attachments from last {days} days")
            return recent_emails
            
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            return recent_emails
    
    def extract_pdf_attachments(self, email_message, email_id: str):
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
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                        temp_file.write(part.get_payload(decode=True))
                        temp_path = Path(temp_file.name)
                        pdf_files.append(temp_path)
                        logger.info(f"Extracted PDF: {filename} -> {temp_path}")
            
            return pdf_files
            
        except Exception as e:
            logger.error(f"Error extracting PDF attachments: {e}")
            return pdf_files
    
    def extract_pharmacy_name(self, text):
        """Extract pharmacy name from the text"""
        text_upper = text.upper()
        
        # Look for known pharmacy names
        for pharmacy in KNOWN_PHARMACIES:
            if pharmacy in text_upper:
                return pharmacy
        
        # Special handling for TLC WINTERTON variations
        if "TLC" in text_upper and "WINTERTON" in text_upper:
            return "TLC WINTERTON"
        elif "WINTERTON" in text_upper or "WINTERTO" in text_upper:
            return "TLC WINTERTON"
        
        # Look for patterns like "PHARMACY: [NAME]" or similar
        pharmacy_patterns = [
            r'PHARMACY[:\s]+([A-Z\s]+)',
            r'STORE[:\s]+([A-Z\s]+)',
            r'BRANCH[:\s]+([A-Z\s]+)',
            r'LOCATION[:\s]+([A-Z\s]+)'
        ]
        
        for pattern in pharmacy_patterns:
            match = re.search(pattern, text_upper)
            if match:
                pharmacy_name = match.group(1).strip()
                if len(pharmacy_name) > 2:
                    return pharmacy_name
        
        return "UNKNOWN_PHARMACY"
    
    def extract_date(self, text):
        """Extract date from the text"""
        # Look for date ranges in the format shown in the images
        date_range_patterns = [
            r'from:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+to:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})\s*-\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'range.*from:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+to:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'period.*from:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+to:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
            r'date from\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})\s+date to\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})'
        ]
        
        for pattern in date_range_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the last match - use the end date (last 3 values)
                match = matches[-1]
                try:
                    if len(match) == 6:  # Full range pattern
                        # Use the end date (last 3 values)
                        year, month, day = match[3], match[4], match[5]
                    else:
                        # Fallback to first 3 values
                        year, month, day = match[0], match[1], match[2]
                    
                    # Format as YYYY-MM-DD
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    continue
        
        # If no date range found, look for single dates in YYYY/MM/DD format
        single_date_patterns = [
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',    # YYYY-MM-DD
            r'(\d{1,2})\s+(\w{3})\s+(\d{4})',        # DD MMM YYYY
            r'(\w{3})\s+(\d{1,2})\s+(\d{4})'         # MMM DD YYYY
        ]
        
        for pattern in single_date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Take the last match (most recent/relevant)
                match = matches[-1]
                try:
                    if len(match[0]) == 4:  # YYYY format
                        year, month, day = match
                    elif len(match[2]) == 4:  # YYYY at end
                        day, month, year = match
                    else:
                        # Assume DD/MM/YY format
                        day, month, year = match
                        if len(year) == 2:
                            year = '20' + year
                    
                    # Convert month name to number if needed
                    if month.isalpha():
                        month_names = {
                            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
                        }
                        month = month_names.get(month.upper(), '01')
                    
                    # Format as YYYY-MM-DD
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    continue
        
        return None
    
    def classify_pdf(self, file_path):
        """Classify PDF by report type"""
        doc = fitz.open(file_path)
        text = ""
        
        # Extract text from the first 2 pages
        for i in range(min(2, len(doc))):
            text += doc[i].get_text().upper()
        doc.close()

        # Determine report type by keyword matches
        scores = {}
        for report_type, keywords in REPORT_KEYWORDS.items():
            scores[report_type] = sum(1 for kw in keywords if kw in text)

        # Get report type with highest score
        best_match = max(scores, key=scores.get)
        if scores[best_match] == 0:
            return "unknown"
        
        return best_match
    
    def process_emails_and_classify(self, days: int = 2):
        """Main function to process emails and classify PDFs"""
        logger.info(f"Starting email processing for last {days} days...")
        
        # Connect to Gmail
        mail = self.connect_imap()
        if not mail:
            logger.error("Failed to connect to Gmail")
            return False
        
        try:
            # Get recent emails
            recent_emails = self.get_recent_emails(mail, days)
            
            if not recent_emails:
                logger.info("No emails with PDF attachments found")
                return True
            
            # Process each email
            for email_data in recent_emails:
                logger.info(f"Processing email: {email_data['subject']}")
                
                # Extract PDF attachments
                pdf_files = self.extract_pdf_attachments(email_data['message'], email_data['id'])
                
                # Process each PDF
                for pdf_file in pdf_files:
                    try:
                        logger.info(f"Processing PDF: {pdf_file.name}")
                        
                        # Open PDF and extract text
                        doc = fitz.open(str(pdf_file))
                        text = ""
                        for i in range(min(2, len(doc))):
                            text += doc[i].get_text()
                        doc.close()
                        
                        # Classify the PDF
                        report_type = self.classify_pdf(str(pdf_file))
                        logger.info(f"  Detected report type: {report_type}")
                        
                        # Extract pharmacy name
                        pharmacy_name = self.extract_pharmacy_name(text)
                        logger.info(f"  Detected pharmacy: {pharmacy_name}")
                        
                        # Extract date
                        date_str = self.extract_date(text)
                        if date_str:
                            logger.info(f"  Detected date: {date_str}")
                        else:
                            # Try to extract date from filename
                            filename_date = re.search(r'(\d{8})', pdf_file.name)
                            if filename_date:
                                date_str = filename_date.group(1)
                                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                                logger.info(f"  Extracted date from filename: {date_str}")
                            else:
                                date_str = "UNKNOWN_DATE"
                                logger.info(f"  No date found, using: {date_str}")
                        
                        # Create folder structure: temp_dir/date/pharmacy/
                        date_folder = self.temp_dir / date_str
                        pharmacy_folder = date_folder / pharmacy_name
                        pharmacy_folder.mkdir(parents=True, exist_ok=True)
                        
                        # Create new filename based on classification (NO TIMESTAMP)
                        original_name = Path(pdf_file.name).name
                        new_filename = f"{report_type}_{original_name}"
                        new_filepath = pharmacy_folder / new_filename
                        
                        # Copy the file to the appropriate folder
                        shutil.copy2(pdf_file, new_filepath)
                        logger.info(f"  Saved as: {new_filepath}")
                        
                        # Clean up temporary file
                        pdf_file.unlink()
                        
                    except Exception as e:
                        logger.error(f"  Error processing {pdf_file.name}: {str(e)}")
                        # Clean up temporary file even if processing failed
                        try:
                            pdf_file.unlink()
                        except:
                            pass
            
            logger.info("Email processing and classification complete!")
            return True
            
        except Exception as e:
            logger.error(f"Error in email processing: {e}")
            return False
        finally:
            try:
                mail.logout()
            except:
                pass
    
    def display_summary(self):
        """Display summary of organized files"""
        logger.info("\n" + "="*80)
        logger.info("📊 CLASSIFICATION SUMMARY")
        logger.info("="*80)
        
        # List all files in organized structure
        for date_folder in self.temp_dir.iterdir():
            if date_folder.is_dir() and date_folder.name != "__pycache__":
                logger.info(f"\n📅 Date: {date_folder.name}")
                for pharmacy_folder in date_folder.iterdir():
                    if pharmacy_folder.is_dir():
                        logger.info(f"  🏪 Pharmacy: {pharmacy_folder.name}")
                        for file in pharmacy_folder.glob("*.pdf"):
                            logger.info(f"    📄 {file.name}")

def main():
    """Main function"""
    classifier = ImprovedPDFClassifier()
    
    # Process emails from last 2 days
    success = classifier.process_emails_and_classify(days=2)
    
    if success:
        classifier.display_summary()
        logger.info("✅ Classification process completed successfully!")
    else:
        logger.error("❌ Classification process failed!")

if __name__ == "__main__":
    main() 