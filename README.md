# 🏥 Pharmacy Email Monitor Web Service

A comprehensive web service that automatically monitors Gmail for pharmacy reports, processes PDF data, and stores it in a PostgreSQL database on Render.

## 🚀 Features

- **📧 Automated Email Monitoring**: Checks Gmail every 10 minutes for new pharmacy reports
- **📄 PDF Processing**: Extracts and classifies pharmacy reports (trading, turnover, transaction, gross profit, dispensary summaries)
- **🗄️ Database Storage**: Stores processed data in Render PostgreSQL database
- **🌐 Web API**: RESTful API endpoints for monitoring and data access
- **📊 Real-time Statistics**: Health checks and monitoring statistics
- **🔄 24/7 Operation**: Runs continuously on Render cloud platform

## 📋 Supported Report Types

1. **Trading Summary**: Financial and stock data
2. **Turnover Summary**: Sales and revenue data
3. **Transaction Summary**: Transaction counts and basket analysis
4. **Gross Profit Report**: Product-level sales data with department mapping
5. **Dispensary Summary**: Script statistics and dispensary revenue

## 🏪 Supported Pharmacies

- **REITZ**: Main pharmacy location
- **TLC WINTERTON**: Secondary pharmacy location

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL (Render)
- **Email**: Gmail IMAP
- **PDF Processing**: PyMuPDF (fitz)
- **Scheduling**: Python schedule library
- **Hosting**: Render (Free/Paid tiers)

## 🚀 Quick Start

### Prerequisites

1. **Render Account**: For database and web service hosting
2. **Gmail Account**: With app password for email access
3. **Git Repository**: This repository cloned locally

### Deployment

1. **Fork/Clone** this repository
2. **Deploy to Render** using the [deployment guide](Scripts/RENDER_WEB_SERVICE_SETUP.md)
3. **Configure Environment Variables**:
   ```
   DATABASE_URL=your_render_postgresql_url
   REITZ_GMAIL_USERNAME=your_gmail_username
   REITZ_GMAIL_APP_PASSWORD=your_gmail_app_password
   ```
4. **Access the Web Service** at your Render URL

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service status |
| `GET` | `/health` | Health check |
| `GET` | `/stats` | Monitoring statistics |
| `POST` | `/check-now` | Manual email check |
| `POST` | `/start` | Start monitoring |
| `POST` | `/stop` | Stop monitoring |
| `GET` | `/database/stats` | Database statistics |
| `GET` | `/database/pharmacies` | List pharmacies |
| `GET` | `/database/dates` | Available dates |
| `GET` | `/database/performance/<pharmacy>` | Performance data |
| `GET` | `/database/top-products/<pharmacy>` | Top products |

## 📁 Project Structure

```
pharmacyDatabase/
├── Scripts/
│   ├── app.py                          # Main Flask web service
│   ├── requirements.txt                # Python dependencies
│   ├── render.yaml                     # Render deployment config
│   ├── email_monitor.py                # Email monitoring logic
│   ├── render_database_connection.py   # Database connection
│   ├── classify_and_organize_pdfs.py   # PDF classification
│   ├── extract_*.py                    # Data extraction scripts
│   ├── complete_data_pipeline.py       # Full data pipeline
│   ├── insert_data_to_database.py      # Database insertion
│   ├── load_department_codes.py        # Department codes loader
│   ├── setup_render_database.py        # Database setup
│   ├── test_email_monitor.py           # Testing utilities
│   ├── RENDER_WEB_SERVICE_SETUP.md     # Deployment guide
│   └── DEPLOYMENT_SUMMARY.md           # Deployment summary
├── Departments/
│   └── Departments.csv                 # Department codes reference
└── README.md                           # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Render PostgreSQL connection string | Yes |
| `REITZ_GMAIL_USERNAME` | Gmail account username | Yes |
| `REITZ_GMAIL_APP_PASSWORD` | Gmail app password | Yes |

### Gmail Setup

1. Enable 2-factor authentication on your Gmail account
2. Generate an app password for this service
3. Use the app password in the `REITZ_GMAIL_APP_PASSWORD` environment variable

## 📊 Data Processing Pipeline

1. **Email Check**: Every 10 minutes, check for unread emails with PDFs
2. **PDF Extraction**: Download and extract PDF attachments
3. **Classification**: Classify reports by type and pharmacy
4. **Data Extraction**: Extract relevant data from each report type
5. **Database Storage**: Store processed data in PostgreSQL
6. **Cleanup**: Remove temporary files

## 🗄️ Database Schema

### Tables

- **pharmacies**: Pharmacy information
- **daily_summary**: Daily pharmacy performance data
- **department_codes**: Department code mappings
- **sales_details**: Detailed product sales data

### Key Metrics Stored

- Turnover and revenue data
- Transaction counts and basket analysis
- Stock levels and adjustments
- Script statistics and dispensary data
- Product-level sales with department mapping

## 🛡️ Security Features

- **HTTPS**: All connections encrypted
- **Environment Variables**: No hardcoded credentials
- **SSL Database**: Secure database connections
- **App Passwords**: Secure Gmail authentication
- **Error Handling**: Comprehensive error logging

## 📈 Performance & Scaling

### Free Tier (Testing)
- **CPU**: 0.1 cores
- **Memory**: 512MB RAM
- **Cost**: $0/month
- **Limitation**: Sleeps after 15 minutes

### Paid Plans (Production)
- **Starter**: $7/month (24/7 operation)
- **Standard**: $25/month (1 core, 2GB RAM)
- **Pro**: $100/month (2 cores, 4GB RAM)

## 🔍 Monitoring & Troubleshooting

### Health Checks
- **Service Status**: `GET /health`
- **Database Connection**: Automatic health checks
- **Email Processing**: Real-time monitoring

### Logs
- **Application Logs**: Available in Render dashboard
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: CPU, memory, and network usage

### Common Issues
- **Service Sleeping**: Free tier limitation (upgrade to paid plan)
- **Database Connection**: Check `DATABASE_URL` environment variable
- **Email Processing**: Verify Gmail credentials and app password

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the [deployment guide](Scripts/RENDER_WEB_SERVICE_SETUP.md)
2. Review the [troubleshooting section](#monitoring--troubleshooting)
3. Open an issue on GitHub

## 🎉 Acknowledgments

- **Render**: For hosting and database services
- **Gmail**: For email integration
- **PyMuPDF**: For PDF processing capabilities
- **Flask**: For the web framework

---

**🚀 Deploy now and enjoy automated pharmacy data collection!** 