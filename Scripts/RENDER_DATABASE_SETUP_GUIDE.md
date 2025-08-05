# 🗄️ Render PostgreSQL Database Setup - Step by Step Guide

## Overview
This guide will walk you through setting up a PostgreSQL database on Render for your pharmacy reporting system.

## Prerequisites
- Render account (free tier available)
- Basic understanding of databases (not required - this guide covers everything)

## Step 1: Create Render Account

### 1.1 Sign Up for Render
1. Go to [render.com](https://render.com)
2. Click **"Get Started"** or **"Sign Up"**
3. Choose **"Sign up with email"**
4. Enter your email and create a password
5. Verify your email address

### 1.2 Complete Account Setup
- No credit card required for free tier
- Choose your preferred region (closest to you)

## Step 2: Create PostgreSQL Database

### 2.1 Access Dashboard
1. Log into your Render dashboard
2. You'll see an empty dashboard with a **"New +"** button

### 2.2 Create Database Service
1. Click the **"New +"** button
2. Select **"PostgreSQL"** from the service options
3. You'll see the database configuration form

### 2.3 Configure Database Settings

Fill in the form with these exact values:

```
Name: pharmacy_reports
Database: pharmacy_reports
User: pharmacy_user
Region: [Choose closest to your location]
PostgreSQL Version: 15 (latest stable)
Plan: Free (for testing)
```

**Region Options:**
- **Frankfurt** (Europe)
- **London** (Europe)
- **Virginia** (US East)
- **Oregon** (US West)

**Plan Options:**
- **Free**: 1GB storage, 5 connections (perfect for testing)
- **Starter**: $7/month, 1GB storage, 10 connections
- **Standard**: $25/month, 10GB storage, 25 connections

### 2.4 Create Database
1. Click **"Create Database"**
2. Wait 2-3 minutes for the database to be created
3. You'll see a success message

## Step 3: Get Connection Details

### 3.1 Access Database Dashboard
1. Click on your new `pharmacy_reports` database
2. You'll see the database dashboard with connection details

### 3.2 Copy External Database URL
1. Look for **"External Database URL"**
2. It will look like this:
   ```
   postgresql://pharmacy_user:password123@dpg-abc123-a.frankfurt-postgres.render.com:5432/pharmacy_reports
   ```
3. Click the **"Copy"** button next to it
4. **Save this URL** - you'll need it for the next step

## Step 4: Set Up Environment Variables

### 4.1 Update .env File
1. Open your `.env` file in the Scripts directory
2. Replace the DATABASE_URL line with your actual Render URL:

```bash
# Gmail Credentials
REITZ_GMAIL_USERNAME=dmr.tlc.reitz@gmail.com
REITZ_GMAIL_APP_PASSWORD=dkcj ixgf vhkf jupx

# Database Configuration (Replace with your actual Render URL)
DATABASE_URL=postgresql://pharmacy_user:your_actual_password@your_actual_host:5432/pharmacy_reports

# Optional: Logging level
LOG_LEVEL=INFO
```

### 4.2 Set Environment Variable
Run this command in your terminal:

```bash
export DATABASE_URL="postgresql://pharmacy_user:your_actual_password@your_actual_host:5432/pharmacy_reports"
```

**Replace the URL with your actual Render database URL**

## Step 5: Set Up Database Schema

### 5.1 Run Database Setup Script
```bash
cd /Users/charldewet/Python/pharmacyDatabase/Scripts
python3 setup_render_database.py
```

This script will:
- ✅ Connect to your Render database
- ✅ Create all necessary tables
- ✅ Insert sample department codes
- ✅ Create database views and functions
- ✅ Test the connection

### 5.2 Verify Setup
You should see output like:
```
🗄️ Render PostgreSQL Database Setup
==================================================
✅ Connected to Render PostgreSQL database

🔧 Creating database schema...
✅ Database schema created successfully

📋 Inserting sample department codes...
✅ Inserted 12 department codes

🧪 Testing database queries...
✅ Found 2 pharmacies:
   • Reitz Pharmacy (REITZ)
   • TLC Winterton Pharmacy (TLC WINTERTON)

📊 Database Statistics:
   • pharmacies: 2 records
   • daily_summary: 0 records
   • department_codes: 12 records
   • sales_details: 0 records

🎉 Database setup completed successfully!
```

## Step 6: Test Complete System

### 6.1 Test Email Monitor with Database
```bash
python3 test_email_monitor.py
```

You should see:
```
🧪 Pharmacy Email Monitor Test Suite
==================================================
✅ PASS - Gmail Connection
✅ PASS - Database Connection
✅ PASS - Email Processing

🎯 Overall: 3/3 tests passed
🎉 All tests passed! Email monitor is ready to run.
```

### 6.2 Run Email Monitor
```bash
python3 email_monitor.py
```

This will start processing your 10 unread pharmacy report emails!

## Step 7: Monitor Your Database

### 7.1 Check Database in Render Dashboard
1. Go back to your Render dashboard
2. Click on your `pharmacy_reports` database
3. You can see:
   - **Connections**: Active database connections
   - **Storage**: Database size and usage
   - **Logs**: Database activity logs

### 7.2 Database Statistics
After processing emails, you can check:
- **Daily Summary Records**: One per pharmacy per date
- **Sales Details Records**: Product-level data
- **Database Size**: Should grow as data is added

## Troubleshooting

### Common Issues

#### 1. Connection Failed
```
❌ Failed to connect to database: connection to server failed
```
**Solutions:**
- Check your DATABASE_URL is correct
- Ensure you copied the External Database URL (not Internal)
- Verify the database is running in Render dashboard

#### 2. Authentication Failed
```
❌ Failed to connect to database: authentication failed
```
**Solutions:**
- Check username and password in the URL
- Ensure you're using the External Database URL
- Try regenerating the database password in Render

#### 3. Database Not Found
```
❌ Failed to connect to database: database "pharmacy_reports" does not exist
```
**Solutions:**
- Check the database name in the URL
- Ensure the database was created successfully
- Wait a few minutes for the database to fully initialize

### Getting Help

#### Render Support
- **Documentation**: [render.com/docs](https://render.com/docs)
- **Community**: [render.com/community](https://render.com/community)
- **Email Support**: Available for all plans

#### Database Monitoring
- **Logs**: Check database logs in Render dashboard
- **Metrics**: Monitor connections and storage usage
- **Backups**: Automatic backups are included

## Cost Management

### Free Tier Limits
- **Storage**: 1GB (plenty for testing)
- **Connections**: 5 concurrent
- **Backups**: 7-day retention
- **Cost**: $0/month

### When to Upgrade
- **Storage**: When approaching 1GB limit
- **Connections**: When you need more than 5 concurrent
- **Performance**: When you need faster queries

### Upgrade Path
1. **Free → Starter**: $7/month (10 connections)
2. **Starter → Standard**: $25/month (25 connections, 10GB storage)
3. **Standard → Pro**: $100/month (100 connections, 100GB storage)

## Security Best Practices

### Database Security
- ✅ SSL connections (enabled by default)
- ✅ Environment variables for credentials
- ✅ No hardcoded passwords
- ✅ Automatic backups

### Access Control
- ✅ Only your application can access the database
- ✅ No direct database access from internet
- ✅ Connection pooling for efficiency

## Next Steps

After successful setup:

1. **✅ Database Created**: Your Render PostgreSQL database is ready
2. **✅ Schema Created**: All tables, views, and functions are set up
3. **✅ Email Monitor Ready**: Can process pharmacy reports automatically
4. **🚀 Start Processing**: Run the email monitor to process your 10 emails

### Run the Complete System
```bash
# Start the email monitor (processes emails every 10 minutes)
python3 email_monitor.py

# Or run in background
nohup python3 email_monitor.py > email_monitor.log 2>&1 &
```

---

**🎉 Congratulations! Your pharmacy database system is now fully set up and ready to process reports automatically!** 