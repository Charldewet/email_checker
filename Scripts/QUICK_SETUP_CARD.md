# 🚀 Quick Setup Card - Render PostgreSQL Database

## ⚡ 5-Minute Setup Checklist

### ✅ Step 1: Create Render Account (2 minutes)
- [ ] Go to [render.com](https://render.com)
- [ ] Sign up with email
- [ ] Verify email address

### ✅ Step 2: Create Database (2 minutes)
- [ ] Click "New +" → "PostgreSQL"
- [ ] Name: `pharmacy_reports`
- [ ] Database: `pharmacy_reports`
- [ ] User: `pharmacy_user`
- [ ] Plan: Free
- [ ] Click "Create Database"

### ✅ Step 3: Get Connection URL (30 seconds)
- [ ] Click on your database
- [ ] Copy "External Database URL"
- [ ] Save it somewhere safe

### ✅ Step 4: Set Environment Variable (30 seconds)
```bash
export DATABASE_URL="your_copied_url_here"
```

### ✅ Step 5: Run Setup Script (1 minute)
```bash
python3 setup_render_database.py
```

### ✅ Step 6: Test System (30 seconds)
```bash
python3 test_email_monitor.py
```

### ✅ Step 7: Start Email Monitor
```bash
python3 email_monitor.py
```

## 🔧 Quick Commands

### Set Database URL
```bash
export DATABASE_URL="postgresql://pharmacy_user:password@host:5432/pharmacy_reports"
```

### Setup Database
```bash
python3 setup_render_database.py
```

### Test Everything
```bash
python3 test_email_monitor.py
```

### Start Monitoring
```bash
python3 email_monitor.py
```

### Check Status
```bash
tail -f email_monitor.log
```

## 📞 Need Help?

### Common Issues
- **Connection failed**: Check DATABASE_URL is correct
- **Auth failed**: Use External URL, not Internal
- **Database not found**: Wait 2-3 minutes after creation

### Support
- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Community**: [render.com/community](https://render.com/community)

## 💰 Cost
- **Free Tier**: $0/month (1GB storage, 5 connections)
- **Starter**: $7/month (1GB storage, 10 connections)
- **Standard**: $25/month (10GB storage, 25 connections)

---

**🎯 Goal: Get your pharmacy email monitor running in under 10 minutes!** 