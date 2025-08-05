# 📧 Pharmacy Email Monitor System

## Overview

The Pharmacy Email Monitor is an automated system that continuously monitors a Gmail account for new pharmacy report emails, extracts PDF attachments, processes them through the complete data pipeline, and stores the results in a Render PostgreSQL database.

## 🚀 Features

- **🔄 Continuous Monitoring**: Checks Gmail every 10 minutes for new emails
- **📎 PDF Extraction**: Automatically extracts PDF attachments from emails
- **🔍 Smart Classification**: Classifies reports into 6 types (trading, turnover, transaction, gross profit, dispensary, department)
- **📊 Data Extraction**: Extracts all relevant data from each report type
- **🗄️ Database Storage**: Stores processed data in Render PostgreSQL database
- **🧹 Automatic Cleanup**: Removes PDFs after processing (no file storage)
- **📝 Comprehensive Logging**: Detailed logs for monitoring and debugging
- **🛡️ Error Handling**: Robust error handling with retry mechanisms
- **⚡ Background Service**: Can run as a systemd service on Linux

## 📋 Prerequisites

1. **Gmail Account**: With app password enabled
2. **Render PostgreSQL Database**: Set up and configured
3. **Python 3.8+**: With required dependencies
4. **Network Access**: For Gmail IMAP and database connections

## 🛠️ Installation & Setup

### 1. Quick Setup

```bash
# Run the setup script
python3 setup_email_monitor.py
```

### 2. Manual Setup

#### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 2: Set Environment Variables
Create a `.env` file:
```bash
# Gmail Credentials
REITZ_GMAIL_USERNAME=dmr.tlc.reitz@gmail.com
REITZ_GMAIL_APP_PASSWORD=dkcj ixgf vhkf jupx

# Database Configuration
DATABASE_URL=postgresql://your_username:your_password@your_host:5432/your_database

# Optional: Logging level
LOG_LEVEL=INFO
```

#### Step 3: Create Directories
```bash
mkdir -p temp_email_pdfs logs ../temp_classified_pdfs
```

## 🧪 Testing

### Test Email Connection
```bash
python3 test_email_monitor.py
```

This will test:
- ✅ Gmail IMAP connection
- ✅ Database connection
- ✅ Email processing cycle

### Test Individual Components
```bash
# Test Gmail connection only
python3 -c "from email_monitor import PharmacyEmailMonitor; m = PharmacyEmailMonitor(); print('Gmail connection:', m.connect_imap() is not None)"

# Test database connection only
python3 -c "from render_database_connection import RenderPharmacyDatabase; db = RenderPharmacyDatabase(); print('Database connection:', db.test_connection())"
```

## 🚀 Running the Monitor

### Option 1: Direct Execution
```bash
python3 email_monitor.py
```

### Option 2: Background Process (macOS/Linux)
```bash
nohup python3 email_monitor.py > email_monitor.log 2>&1 &
```

### Option 3: Systemd Service (Linux)
```bash
# Copy service file
sudo cp pharmacy-email-monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable pharmacy-email-monitor
sudo systemctl start pharmacy-email-monitor

# Check status
sudo systemctl status pharmacy-email-monitor

# View logs
sudo journalctl -u pharmacy-email-monitor -f
```

## 📊 How It Works

### 1. Email Monitoring Cycle
```
🔄 Every 10 minutes:
├── Connect to Gmail IMAP
├── Search for unread emails with PDFs
├── Extract PDF attachments
├── Process through data pipeline
├── Store in database
├── Clean up files
└── Mark emails as processed
```

### 2. Data Processing Pipeline
```
📧 Email with PDFs
    ↓
📁 Extract PDFs to temp directory
    ↓
🔍 Classify reports by type
    ↓
📊 Extract data from each report
    ↓
🔄 Combine all data
    ↓
🗄️ Insert into database
    ↓
🧹 Clean up temporary files
```

### 3. Report Types Supported
- **Trading Summary**: Financial metrics, stock levels
- **Turnover Summary**: Sales data, payment methods
- **Transaction Summary**: Transaction counts, basket analysis
- **Gross Profit Report**: Product-level sales data
- **Dispensary Summary**: Script counts, dispensary revenue
- **Department Listing**: Department codes and categories

## 📝 Logging

### Log Files
- `email_monitor.log`: Main application log
- `processed_emails.json`: Track processed email IDs

### Log Levels
- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures
- **DEBUG**: Detailed debugging info

### Sample Log Output
```
2024-01-15 10:30:00 - INFO - 🔄 Starting email processing cycle
2024-01-15 10:30:05 - INFO - Found 2 new emails with PDFs
2024-01-15 10:30:10 - INFO - Extracted PDF: report_2024-01-15.pdf
2024-01-15 10:30:15 - INFO - Step 1: Classifying and organizing PDFs
2024-01-15 10:30:20 - INFO - ✅ Trading summary extraction completed
2024-01-15 10:30:25 - INFO - ✅ Successfully inserted data for REITZ_2024-01-15
2024-01-15 10:30:30 - INFO - ✅ Cleanup completed
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `REITZ_GMAIL_USERNAME` | Gmail account email | Yes |
| `REITZ_GMAIL_APP_PASSWORD` | Gmail app password | Yes |
| `DATABASE_URL` | Render PostgreSQL connection string | Yes |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | No |

### Monitoring Interval
Change the monitoring interval in `email_monitor.py`:
```python
monitor.run_continuous_monitoring(interval_minutes=10)  # Change 10 to desired minutes
```

### Email Processing Settings
- **Temp Directory**: `temp_email_pdfs/`
- **Processed Tracking**: `processed_emails.json`
- **Log File**: `email_monitor.log`

## 🛡️ Security

### Gmail Security
- Uses app passwords (not regular passwords)
- IMAP over SSL
- No email content stored permanently

### Database Security
- SSL connections to Render
- Environment variable credentials
- No hardcoded passwords

### File Security
- Temporary files only
- Automatic cleanup after processing
- No PDF storage on disk

## 🔍 Troubleshooting

### Common Issues

#### 1. Gmail Connection Failed
```
❌ Failed to connect to Gmail IMAP: [AUTHENTICATIONFAILED]
```
**Solution**: 
- Check app password is correct
- Enable 2-factor authentication
- Generate new app password

#### 2. Database Connection Failed
```
❌ Database connection failed: connection to server failed
```
**Solution**:
- Verify DATABASE_URL is correct
- Check network connectivity
- Ensure Render database is running

#### 3. PDF Processing Failed
```
❌ PDF processing pipeline failed: No module named 'fitz'
```
**Solution**:
```bash
pip install PyMuPDF
```

#### 4. Permission Denied
```
❌ Permission denied: temp_email_pdfs/
```
**Solution**:
```bash
chmod 755 temp_email_pdfs/
```

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python3 email_monitor.py
```

### Manual Email Processing
Process a single email cycle:
```python
from email_monitor import PharmacyEmailMonitor
monitor = PharmacyEmailMonitor()
monitor.process_single_email_cycle()
```

## 📈 Monitoring & Maintenance

### Health Checks
```bash
# Check if service is running
ps aux | grep email_monitor

# Check log file size
ls -lh email_monitor.log

# Check processed emails count
wc -l processed_emails.json
```

### Database Monitoring
```python
from render_database_connection import RenderPharmacyDatabase
db = RenderPharmacyDatabase()
stats = db.get_database_stats()
print(f"Records: {stats}")
```

### Performance Metrics
- **Processing Time**: ~30-60 seconds per email
- **Memory Usage**: ~50-100MB
- **Storage**: Minimal (temporary files only)
- **Network**: IMAP + database connections

## 🔄 Updates & Maintenance

### Updating the Monitor
```bash
# Stop the service
sudo systemctl stop pharmacy-email-monitor  # Linux
# or
pkill -f email_monitor.py  # macOS

# Update code
git pull

# Restart the service
sudo systemctl start pharmacy-email-monitor  # Linux
# or
nohup python3 email_monitor.py > email_monitor.log 2>&1 &  # macOS
```

### Backup Considerations
- **Database**: Render handles automatic backups
- **Configuration**: Backup `.env` file
- **Logs**: Rotate log files periodically

## 📞 Support

### Log Analysis
```bash
# View recent errors
grep ERROR email_monitor.log | tail -10

# View processing statistics
grep "Successfully processed" email_monitor.log | wc -l
```

### Common Commands
```bash
# Start monitoring
python3 email_monitor.py

# Test setup
python3 test_email_monitor.py

# View logs
tail -f email_monitor.log

# Check service status (Linux)
sudo systemctl status pharmacy-email-monitor
```

## 🎯 Success Metrics

- **✅ Emails Processed**: Track in `processed_emails.json`
- **✅ Database Records**: Monitor record counts
- **✅ Processing Time**: Average time per email
- **✅ Error Rate**: Failed vs successful processing
- **✅ Uptime**: Service availability

---

**🎉 Your pharmacy email monitoring system is now fully automated!** 