#!/usr/bin/env python3
"""
Debug Email Processing
======================

This script helps debug why Winterton data isn't being extracted from today's emails.
"""

import os
import sys
import imaplib
import email
from datetime import datetime, timedelta
from pathlib import Path

def connect_gmail():
    """Connect to Gmail IMAP"""
    gmail_user = 'dmr.tlc.reitz@gmail.com'
    gmail_password = 'dkcj ixgf vhkf jupx'
    imap_server = 'imap.gmail.com'
    
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(gmail_user, gmail_password)
        return mail
    except Exception as e:
        print(f"❌ Failed to connect to Gmail: {e}")
        return None

def get_recent_emails(mail, days=2):
    """Get recent emails with PDFs"""
    try:
        mail.select('INBOX')
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Search for emails in date range
        date_criteria = f'(SINCE "{start_date.strftime("%d-%b-%Y")}")'
        status, email_ids = mail.search(None, date_criteria)
        
        if status != 'OK':
            print("❌ Failed to search emails")
            return []
        
        recent_emails = []
        email_id_list = email_ids[0].split()
        
        print(f"📧 Found {len(email_id_list)} emails in the last {days} days")
        
        for email_id in email_id_list:
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                subject = email_message.get('Subject', 'No Subject')
                from_addr = email_message.get('From', 'Unknown')
                date = email_message.get('Date', 'Unknown')
                
                # Check if email has PDF attachments
                has_pdf = False
                pdf_names = []
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    
                    filename = part.get_filename()
                    if filename and filename.lower().endswith('.pdf'):
                        has_pdf = True
                        pdf_names.append(filename)
                
                if has_pdf:
                    recent_emails.append({
                        'id': email_id.decode(),
                        'subject': subject,
                        'from': from_addr,
                        'date': date,
                        'pdfs': pdf_names
                    })
                    print(f"📎 Email: {subject[:50]}... | PDFs: {pdf_names}")
                
            except Exception as e:
                print(f"❌ Error processing email {email_id}: {e}")
                continue
        
        return recent_emails
        
    except Exception as e:
        print(f"❌ Error getting recent emails: {e}")
        return []

def extract_and_check_pdfs(mail, emails):
    """Extract PDFs and check their content for dates"""
    temp_dir = Path('temp_debug_pdfs')
    temp_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Extracting PDFs to {temp_dir}...")
    
    for email_data in emails:
        email_id = email_data['id']
        subject = email_data['subject']
        
        print(f"\n📧 Processing email: {subject[:50]}...")
        
        try:
            status, msg_data = mail.fetch(email_id.encode(), '(RFC822)')
            if status != 'OK':
                continue
            
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                
                filename = part.get_filename()
                if filename and filename.lower().endswith('.pdf'):
                    # Save PDF
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_filename = f"{timestamp}_{email_id}_{filename}"
                    filepath = temp_dir / safe_filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    print(f"   📄 Saved: {filename} -> {filepath}")
                    
                    # Try to extract date from PDF content
                    try:
                        import fitz  # PyMuPDF
                        doc = fitz.open(filepath)
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        doc.close()
                        
                        # Look for date patterns
                        import re
                        date_patterns = [
                            r'DATE FROM\s*:\s*(\d{4})/(\d{1,2})/(\d{1,2})',
                            r'(\d{4})/(\d{1,2})/(\d{1,2})',
                            r'(\d{1,2})/(\d{1,2})/(\d{4})',
                            r'Report Date\s*:\s*(\d{4})-(\d{1,2})-(\d{1,2})'
                        ]
                        
                        found_dates = []
                        for pattern in date_patterns:
                            matches = re.findall(pattern, text)
                            for match in matches:
                                if len(match) == 3:
                                    if len(match[0]) == 4:  # YYYY/MM/DD
                                        found_dates.append(f"{match[0]}-{match[1].zfill(2)}-{match[2].zfill(2)}")
                                    else:  # DD/MM/YYYY
                                        found_dates.append(f"{match[2]}-{match[1].zfill(2)}-{match[0].zfill(2)}")
                        
                        if found_dates:
                            print(f"   📅 Found dates: {found_dates}")
                            
                            # Check if any dates are today
                            today = datetime.now().strftime('%Y-%m-%d')
                            if today in found_dates:
                                print(f"   ✅ CONTAINS TODAY'S DATA ({today})!")
                            else:
                                print(f"   ❌ No today's data found (today: {today})")
                        else:
                            print(f"   ❓ No dates found in PDF")
                        
                        # Look for pharmacy names
                        if 'WINTERTON' in text.upper() or 'TLC' in text.upper():
                            print(f"   🏪 Contains Winterton/TLC references")
                        elif 'REITZ' in text.upper():
                            print(f"   🏪 Contains Reitz references")
                        else:
                            print(f"   ❓ No clear pharmacy references found")
                            
                    except Exception as e:
                        print(f"   ❌ Error reading PDF: {e}")
        
        except Exception as e:
            print(f"   ❌ Error processing email: {e}")

def main():
    """Main debug function"""
    print("🔍 Debug Email Processing")
    print("=" * 50)
    
    # Connect to Gmail
    mail = connect_gmail()
    if not mail:
        return
    
    try:
        # Get recent emails
        emails = get_recent_emails(mail, days=2)
        
        if not emails:
            print("❌ No emails with PDFs found")
            return
        
        print(f"\n📊 Found {len(emails)} emails with PDFs")
        
        # Extract and check PDFs
        extract_and_check_pdfs(mail, emails)
        
        print(f"\n✅ Debug completed!")
        print(f"📁 Check the 'temp_debug_pdfs' directory for extracted files")
        
    finally:
        mail.logout()

if __name__ == "__main__":
    main() 