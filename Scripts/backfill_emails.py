#!/usr/bin/env python3
"""
Backfill Emails CLI
===================

One-off tool to ingest historical PDF reports from Gmail and populate the database.

Usage examples:
  - python Scripts/backfill_emails.py --since 2025-07-01 --until 2025-08-11 --folder AllMail --batch-days 2
  - python Scripts/backfill_emails.py --since 2025-08-01 --pharmacy REITZ --dry-run

Environment:
  - REITZ_GMAIL_USERNAME
  - REITZ_GMAIL_APP_PASSWORD
  - DATABASE_URL
"""

import os
import sys
import argparse
import imaplib
import email
from email.message import Message
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
import tempfile

# Local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from improved_classify_and_organize import ImprovedPDFClassifier
from improved_data_pipeline import ImprovedDataPipeline
from render_database_connection import RenderPharmacyDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GMAIL_IMAP = 'imap.gmail.com'


def ymd_to_gmail(d: date) -> str:
    return d.strftime('%d-%b-%Y')


def connect_imap(user: str, app_password: str):
    mail = imaplib.IMAP4_SSL(GMAIL_IMAP)
    mail.login(user, app_password)
    return mail


def resolve_mailbox(mail: imaplib.IMAP4_SSL, requested: str) -> str:
    """Return a mailbox name acceptable to Gmail IMAP for the requested folder.
    Supports 'INBOX' and 'AllMail' (maps to '[Gmail]/All Mail'). Falls back to INBOX.
    """
    if requested.upper() == 'INBOX':
        return 'INBOX'
    candidates = ['[Gmail]/All Mail', '[Google Mail]/All Mail', 'All Mail']
    for cand in candidates:
        try:
            typ, _ = mail.status(cand, '(MESSAGES)')
            if typ == 'OK':
                return cand
        except Exception:
            continue
    return 'INBOX'


def search_pdf_uids(mail: imaplib.IMAP4_SSL, folder: str, start: date, end_exclusive: date):
    """Search for PDF messages in [folder] between [start, end_exclusive). Returns list of ids."""
    # Prefer Gmail X-GM-RAW for precise range
    try:
        mbox = resolve_mailbox(mail, folder)
        mail.select(mbox)
        # Gmail after/before use YYYY/MM/DD format
        q = f"X-GM-RAW \"after:{start.strftime('%Y/%m/%d')} before:{end_exclusive.strftime('%Y/%m/%d')} filename:pdf\""
        status, data = mail.search(None, q)
        if status == 'OK' and data and data[0]:
            return data[0].split()
        raise RuntimeError('X-GM-RAW returned no results')
    except Exception:
        # Fallback to SINCE/BEFORE (day granularity)
        mbox = resolve_mailbox(mail, folder)
        mail.select(mbox)
        since = ymd_to_gmail(start)
        before = ymd_to_gmail(end_exclusive)
        status, data = mail.search(None, f'SINCE {since} BEFORE {before}')
        return data[0].split() if status == 'OK' and data else []


def extract_pdf_attachments(msg: Message) -> list[Path]:
    files: list[Path] = []
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        cd = part.get('Content-Disposition')
        is_pdf = (part.get_content_type() == 'application/pdf')
        fname = part.get_filename() or ''
        if not is_pdf and not (fname and fname.lower().endswith('.pdf')):
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(part.get_payload(decode=True) or b'')
            files.append(Path(tmp.name))
    return files


def classify_and_store(pdf_file: Path, classifier: ImprovedPDFClassifier, base_dir: Path) -> Path | None:
    import fitz
    import re
    try:
        doc = fitz.open(str(pdf_file))
        text = ''
        for i in range(min(2, len(doc))):
            text += doc[i].get_text()
        doc.close()
        report_type = classifier.classify_pdf(str(pdf_file))
        pharmacy_name = classifier.extract_pharmacy_name(text)
        date_str = classifier.extract_date(text)
        if not date_str:
            # fallback: try filename yyyymmdd
            m = re.search(r'(20\d{6})', pdf_file.name)
            if m:
                raw = m.group(1)
                date_str = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        if not date_str:
            logger.warning(f"No date detected for {pdf_file.name}; skipping")
            return None
        # Build destination: temp_classified_test/<date>/<pharmacy>/
        date_folder = base_dir / date_str
        pharm_folder = date_folder / pharmacy_name
        pharm_folder.mkdir(parents=True, exist_ok=True)
        dest = pharm_folder / f"{report_type}_{pdf_file.name}"
        dest.write_bytes(pdf_file.read_bytes())
        return dest
    except Exception as e:
        logger.error(f"Classify/store failed for {pdf_file}: {e}")
        return None


def chunk_dates(start: date, end_inclusive: date, step_days: int):
    cur = start
    while cur <= end_inclusive:
        nxt = min(cur + timedelta(days=step_days), end_inclusive + timedelta(days=1))
        yield cur, nxt  # [cur, nxt)
        cur = nxt


def run_backfill(args: argparse.Namespace) -> int:
    gmail_user = os.getenv('REITZ_GMAIL_USERNAME')
    gmail_app_password = os.getenv('REITZ_GMAIL_APP_PASSWORD')
    if not gmail_user or not gmail_app_password:
        logger.error('Missing Gmail credentials in environment')
        return 1
    if not os.getenv('DATABASE_URL'):
        logger.error('Missing DATABASE_URL in environment')
        return 1

    start = datetime.strptime(args.since, '%Y-%m-%d').date()
    end = datetime.strptime(args.until, '%Y-%m-%d').date()
    folder = 'INBOX' if args.folder.upper() == 'INBOX' else 'All Mail'

    mail = connect_imap(gmail_user, gmail_app_password)
    db = RenderPharmacyDatabase()
    classifier = ImprovedPDFClassifier()
    pipeline = ImprovedDataPipeline()

    base_dir = Path('temp_classified_test')
    base_dir.mkdir(exist_ok=True)

    total_downloaded = 0
    total_inserted = 0

    # Track processed UIDs to avoid reprocessing auto mode
    processed_uid_sql = "INSERT INTO processed_emails(uid, pharmacy_code, message_id) VALUES (%s,%s,%s) ON CONFLICT (uid) DO NOTHING"

    try:
        for s, e in chunk_dates(start, end, args.batch_days):
            logger.info(f"Batch {s} to {e - timedelta(days=1)} ({folder})")
            uids = search_pdf_uids(mail, folder, s, e)
            logger.info(f"Found {len(uids)} candidate messages")
            for uid in uids:
                # Fetch message
                status, data = mail.fetch(uid, '(RFC822)')
                if status != 'OK':
                    continue
                msg = email.message_from_bytes(data[0][1])
                # Optional filter by pharmacy name in subject
                if args.pharmacy and args.pharmacy.upper() not in (msg.get('subject','').upper()):
                    # still process; pharmacy detected from content during classify
                    pass
                pdfs = extract_pdf_attachments(msg)
                if not pdfs:
                    continue
                for p in pdfs:
                    dest = classify_and_store(p, classifier, base_dir)
                    try:
                        p.unlink()
                    except Exception:
                        pass
                    if dest:
                        total_downloaded += 1
                # Mark processed UID
                try:
                    db.execute_query(processed_uid_sql, (uid.decode() if isinstance(uid, bytes) else str(uid), None, msg.get('Message-Id')))
                except Exception:
                    pass
            if args.dry_run:
                logger.info("Dry run: skipping DB pipeline")
                continue
            # Run the improved pipeline (will upsert into DB)
            try:
                pipeline.run_complete_pipeline()
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
        logger.info(f"Backfill complete. PDFs saved: {total_downloaded}")
        return 0
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Backfill historical pharmacy emails into the database')
    p.add_argument('--since', required=True, help='Start date YYYY-MM-DD (inclusive)')
    p.add_argument('--until', required=False, default=date.today().strftime('%Y-%m-%d'), help='End date YYYY-MM-DD (inclusive)')
    p.add_argument('--folder', default='AllMail', help='IMAP folder: INBOX or AllMail (default)')
    p.add_argument('--pharmacy', default=None, help='Optional filter by pharmacy name in subject (best effort)')
    p.add_argument('--batch-days', type=int, default=3, help='Process in date batches of N days (default 3)')
    p.add_argument('--dry-run', action='store_true', help='Download and classify only; do not write to DB')
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    return run_backfill(args)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:])) 