# Improved Pharmacy Data Pipeline

## Overview

This improved pipeline implements a robust "keep the largest value" strategy to ensure data quality and prevent data loss. The system processes emails from the last 2 days, classifies PDF reports, and intelligently updates the database by always keeping the highest values for each metric.

## Key Improvements

### 1. **Removed Timestamp Dependencies**
- No more timestamp-based file naming
- Simplified classification process
- More reliable file organization

### 2. **Email Processing from Last 2 Days**
- Automatically processes emails from the last 2 days
- Extracts PDF attachments directly from Gmail
- Organizes files by date and pharmacy

### 3. **"Keep Largest Value" Strategy**
- Compares new data with existing database values
- Always keeps the higher value for each metric
- Prevents data degradation from partial reports

## Pipeline Components

### 1. Improved Classification (`improved_classify_and_organize.py`)
- Processes emails from Gmail
- Extracts PDF attachments
- Classifies reports by type and pharmacy
- Organizes files in `temp_classified_test/date/pharmacy/` structure

### 2. Improved Data Pipeline (`improved_data_pipeline.py`)
- Extracts data from all report types
- Calculates derived metrics
- Implements largest value comparison logic
- Updates database with best data

### 3. Orchestrator (`run_improved_pipeline.py`)
- Coordinates the entire process
- Provides comprehensive logging
- Handles errors gracefully
- Cleans up temporary files

## How the "Keep Largest Value" Strategy Works

### Example Scenario:
**Existing Database Data:**
- Turnover: R1,000
- Transactions: 50
- Scripts: 20

**New Report Data:**
- Turnover: R30,000
- Transactions: 150
- Scripts: 45

**Result:**
- Turnover: R30,000 (keeps new - larger)
- Transactions: 150 (keeps new - larger)
- Scripts: 45 (keeps new - larger)

### Logic:
1. **No existing data**: Use new data
2. **New > Existing**: Keep new data
3. **Existing ≥ New**: Keep existing data
4. **Equal values**: Keep existing data

## File Structure

```
temp_classified_test/
├── 2025-08-07/
│   ├── REITZ/
│   │   ├── turnover_summary_report.pdf
│   │   ├── trading_summary_report.pdf
│   │   └── dispensary_summary_report.pdf
│   └── TLC WINTERTON/
│       ├── turnover_summary_report.pdf
│       └── transaction_summary_report.pdf
└── 2025-08-08/
    └── REITZ/
        └── gross_profit_report.pdf
```

## Usage

### Quick Start
```bash
cd Scripts
python run_improved_pipeline.py
```

### Individual Components
```bash
# Run classification only
python improved_classify_and_organize.py

# Run data pipeline only
python improved_data_pipeline.py

# Test the pipeline
python test_improved_pipeline.py
```

## Configuration

### Environment Variables
```bash
export REITZ_GMAIL_USERNAME="dmr.tlc.reitz@gmail.com"
export REITZ_GMAIL_APP_PASSWORD="your_app_password"
export DATABASE_URL="your_database_url"
```

### Logging
Logs are stored in `Scripts/logs/`:
- `classification.log` - Classification process logs
- `improved_pipeline.log` - Data pipeline logs
- `orchestrator.log` - Main orchestrator logs
- `test_pipeline.log` - Test execution logs

## Metrics Handled

### Financial Metrics (Keep Largest)
- Turnover
- Gross Profit Value
- Cost of Sales
- Purchases
- Dispensary Turnover
- Cash Sales
- Account Sales
- COD Sales

### Transaction Metrics (Keep Largest)
- Total Transactions
- Total Scripts

### Stock Metrics (Keep Largest)
- Opening Stock
- Closing Stock

### Derived Metrics (Based on Highest Turnover Record)
- Gross Profit Percentage
- Average Basket Value
- Average Basket Size
- Average Script Value
- Stock Adjustments

## Error Handling

### Classification Errors
- Invalid PDF files are logged and skipped
- Email connection issues are handled gracefully
- Missing dates default to "UNKNOWN_DATE"

### Database Errors
- Connection failures are logged
- Query errors are handled with rollback
- Missing pharmacy codes are logged

### Pipeline Errors
- Individual extraction failures don't stop the pipeline
- Partial data is still processed
- Comprehensive error logging

## Testing

### Test Script
```bash
python test_improved_pipeline.py
```

### Test Coverage
- Largest value strategy logic
- Database connection
- Test data creation
- Error scenarios

## Monitoring

### Log Files
Monitor the log files for:
- Processing status
- Error messages
- Data comparison results
- Database updates

### Database Verification
Check the database after processing:
```sql
SELECT pharmacy_code, report_date, turnover, transactions_total 
FROM daily_summary 
WHERE report_date >= CURRENT_DATE - INTERVAL '2 days'
ORDER BY report_date DESC, pharmacy_code;
```

## Troubleshooting

### Common Issues

1. **Gmail Connection Failed**
   - Check app password
   - Verify 2FA is enabled
   - Check network connection

2. **Database Connection Failed**
   - Verify DATABASE_URL environment variable
   - Check database server status
   - Verify network connectivity

3. **PDF Classification Issues**
   - Check PDF file integrity
   - Verify report format
   - Review classification keywords

4. **Data Extraction Errors**
   - Check PDF text extraction
   - Verify report structure
   - Review extraction patterns

### Debug Mode
Enable debug logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

### Processing Time
- Classification: ~2-5 minutes for 2 days of emails
- Data extraction: ~1-3 minutes per pharmacy/date
- Database updates: ~30 seconds per record

### Resource Usage
- Memory: ~100-200MB during processing
- Disk: Temporary files cleaned up automatically
- Network: Gmail and database connections

## Future Enhancements

### Planned Improvements
1. **Parallel Processing**: Process multiple pharmacies simultaneously
2. **Incremental Updates**: Only process new/changed files
3. **Data Validation**: Additional data quality checks
4. **Backup Strategy**: Automatic database backups before updates
5. **Web Interface**: Dashboard for monitoring and manual overrides

### Configuration Options
1. **Processing Window**: Configurable email processing period
2. **Threshold Values**: Customizable comparison thresholds
3. **Notification System**: Email/SMS alerts for processing status
4. **Retry Logic**: Automatic retry for failed operations

## Support

For issues or questions:
1. Check the log files for detailed error messages
2. Review the troubleshooting section
3. Test with the test script
4. Verify environment configuration

## Version History

### v2.0 (Current)
- Implemented "keep largest value" strategy
- Removed timestamp dependencies
- Added comprehensive logging
- Improved error handling
- Added test suite

### v1.0 (Previous)
- Basic classification and extraction
- Timestamp-based file naming
- Simple database updates 