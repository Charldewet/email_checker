# 🚀 Pharmacy Email Monitor Web Service - Render Deployment Guide

## Overview

This guide will help you deploy your pharmacy email monitoring system as a web service on Render. The service will automatically check for new pharmacy reports every 10 minutes and store the data in your Render PostgreSQL database.

## 🎯 What We're Building

### Web Service Features
- **🔄 Automated Monitoring**: Checks Gmail every 10 minutes
- **📧 Email Processing**: Extracts and processes pharmacy reports
- **🗄️ Database Storage**: Stores data in Render PostgreSQL
- **🌐 Web API**: RESTful endpoints for monitoring and data access
- **📊 Health Monitoring**: Built-in health checks and statistics

### API Endpoints
- `GET /` - Service status
- `GET /health` - Health check
- `GET /stats` - Monitoring statistics
- `POST /check-now` - Manual email check
- `POST /start` - Start monitoring
- `POST /stop` - Stop monitoring
- `GET /database/stats` - Database statistics
- `GET /database/pharmacies` - List pharmacies
- `GET /database/dates` - Available dates
- `GET /database/performance/<pharmacy>` - Performance data
- `GET /database/top-products/<pharmacy>` - Top products

## 📋 Prerequisites

1. **Render Account**: Already created
2. **PostgreSQL Database**: Already set up (`pharmacy-reports`)
3. **Gmail Credentials**: Already configured
4. **Git Repository**: Your code in a Git repository

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository

Ensure your repository has these files in the `Scripts/` directory:
- `app.py` - Main web service
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `email_monitor.py` - Email monitoring logic
- `render_database_connection.py` - Database connection
- All other pharmacy processing scripts

### Step 2: Deploy to Render

#### Option A: Using render.yaml (Recommended)

1. **Connect Repository**:
   - Go to your Render dashboard
   - Click "New +" → "Blueprint"
   - Connect your Git repository
   - Render will automatically detect `render.yaml`

2. **Deploy**:
   - Render will create both the database and web service
   - The web service will automatically connect to your database
   - Environment variables will be set automatically

#### Option B: Manual Deployment

1. **Create Web Service**:
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your Git repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python app.py`

2. **Configure Environment Variables**:
   ```
   DATABASE_URL=postgresql://pharmacy_user:PzL1HpYNaYOrmcfImjeZm8LitHTd4d7F@dpg-d28vb1muk2gs73frrns0-a.oregon-postgres.render.com/pharmacy_reports
   REITZ_GMAIL_USERNAME=dmr.tlc.reitz@gmail.com
   REITZ_GMAIL_APP_PASSWORD=dkcj ixgf vhkf jupx
   ```

3. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete

### Step 3: Verify Deployment

1. **Check Service Status**:
   ```bash
   curl https://your-service-name.onrender.com/
   ```

2. **Check Health**:
   ```bash
   curl https://your-service-name.onrender.com/health
   ```

3. **Check Database Connection**:
   ```bash
   curl https://your-service-name.onrender.com/database/stats
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Value |
|----------|-------------|-------|
| `DATABASE_URL` | Render PostgreSQL connection | Auto-set from database |
| `REITZ_GMAIL_USERNAME` | Gmail account | dmr.tlc.reitz@gmail.com |
| `REITZ_GMAIL_APP_PASSWORD` | Gmail app password | dkcj ixgf vhkf jupx |
| `PORT` | Web service port | Auto-set by Render |

### Service Settings

- **Plan**: Free (for testing) or Starter ($7/month for production)
- **Region**: Same as your database (Oregon)
- **Auto-deploy**: Enabled (deploys on Git push)
- **Health Check**: `/health` endpoint

## 📊 Monitoring Your Service

### Render Dashboard
- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, and network usage
- **Deployments**: Deployment history and status
- **Environment**: Environment variables and settings

### Service Endpoints

#### Check Service Status
```bash
curl https://your-service-name.onrender.com/
```

#### Get Health Status
```bash
curl https://your-service-name.onrender.com/health
```

#### Get Monitoring Statistics
```bash
curl https://your-service-name.onrender.com/stats
```

#### Manual Email Check
```bash
curl -X POST https://your-service-name.onrender.com/check-now
```

#### Get Database Statistics
```bash
curl https://your-service-name.onrender.com/database/stats
```

#### Get Pharmacy Performance
```bash
curl "https://your-service-name.onrender.com/database/performance/REITZ?start_date=2025-08-04&end_date=2025-08-04"
```

#### Get Top Products
```bash
curl "https://your-service-name.onrender.com/database/top-products/REITZ?date=2025-08-04&limit=10"
```

## 🔄 How It Works

### Automated Process
1. **Service Starts**: Web service initializes and starts scheduler
2. **Every 10 Minutes**: Scheduler triggers email check
3. **Email Processing**: 
   - Connects to Gmail
   - Finds unread emails with PDFs
   - Extracts PDF attachments
   - Processes through pipeline
   - Stores in database
   - Cleans up temporary files
4. **Health Monitoring**: Service reports status via API

### Manual Control
- **Start Monitoring**: `POST /start`
- **Stop Monitoring**: `POST /stop`
- **Manual Check**: `POST /check-now`
- **View Stats**: `GET /stats`

## 🛡️ Security Features

### Database Security
- ✅ SSL connections to PostgreSQL
- ✅ Environment variable credentials
- ✅ No hardcoded passwords

### Email Security
- ✅ App password authentication
- ✅ IMAP over SSL
- ✅ No email content storage

### Web Service Security
- ✅ HTTPS by default
- ✅ CORS enabled for API access
- ✅ Error handling and logging

## 📈 Performance & Scaling

### Free Tier Limits
- **CPU**: 0.1 cores
- **Memory**: 512MB RAM
- **Bandwidth**: 100GB/month
- **Sleep**: Service sleeps after 15 minutes of inactivity

### Production Scaling
- **Starter Plan**: $7/month (0.5 cores, 1GB RAM)
- **Standard Plan**: $25/month (1 core, 2GB RAM)
- **Pro Plan**: $100/month (2 cores, 4GB RAM)

### Performance Optimization
- **Connection Pooling**: Efficient database connections
- **Background Processing**: Email checks run in background threads
- **Error Recovery**: Automatic retry on failures
- **Resource Management**: Proper cleanup of temporary files

## 🔍 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs in Render dashboard
# Verify environment variables are set
# Check Python dependencies in requirements.txt
```

#### Database Connection Failed
```bash
# Verify DATABASE_URL is correct
# Check database is running
# Test connection manually
```

#### Email Processing Failed
```bash
# Check Gmail credentials
# Verify app password is correct
# Check Gmail IMAP settings
```

#### Service Sleeping (Free Tier)
- Free tier services sleep after 15 minutes
- First request after sleep takes 30-60 seconds
- Consider upgrading to paid plan for 24/7 operation

### Debug Commands

#### Check Service Logs
```bash
# View in Render dashboard
# Or use curl to check status
curl https://your-service-name.onrender.com/health
```

#### Test Database Connection
```bash
curl https://your-service-name.onrender.com/database/stats
```

#### Test Email Processing
```bash
curl -X POST https://your-service-name.onrender.com/check-now
```

## 🎯 Next Steps

### Immediate Actions
1. **Deploy the service** using the guide above
2. **Test the endpoints** to ensure everything works
3. **Monitor the logs** for the first few email checks
4. **Verify data** is being stored in the database

### Future Enhancements
1. **Web Dashboard**: Create a web interface for monitoring
2. **Email Alerts**: Add email notifications for processing issues
3. **Data Analytics**: Add more advanced reporting endpoints
4. **Mobile App**: Create a mobile app for monitoring

### Production Considerations
1. **Upgrade Plan**: Move to paid plan for 24/7 operation
2. **Backup Strategy**: Set up additional data backups
3. **Monitoring**: Add external monitoring services
4. **Security**: Implement API authentication if needed

## 🎉 Success Metrics

### Service Health
- ✅ **Service Running**: 24/7 availability
- ✅ **Email Processing**: Automatic every 10 minutes
- ✅ **Database Storage**: Data being stored correctly
- ✅ **API Endpoints**: All endpoints responding

### Data Processing
- ✅ **PDF Extraction**: Working correctly
- ✅ **Data Classification**: All report types processed
- ✅ **Database Insertion**: Data stored without errors
- ✅ **Cleanup**: Temporary files removed

---

## 🚀 Ready to Deploy!

Your pharmacy email monitoring system is ready to run as a web service on Render. This will provide:

- **🔄 24/7 Monitoring**: Automatic email checking
- **🌐 Web API**: Access to your data from anywhere
- **📊 Real-time Stats**: Monitor processing status
- **🛡️ Reliability**: Professional hosting and monitoring
- **📈 Scalability**: Easy to upgrade as you grow

**Deploy now and your pharmacy data will be automatically collected and stored! 🎉** 