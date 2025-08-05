#!/usr/bin/env python3
"""
Pharmacy Email Monitor Web Service
==================================

This Flask web service runs on Render and automatically checks for new pharmacy reports
every 10 minutes, processes them, and stores the data in the Render PostgreSQL database.
"""

import os
import time
import threading
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import schedule

# Import our pharmacy monitoring modules
from email_monitor import PharmacyEmailMonitor
from render_database_connection import RenderPharmacyDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables
monitor = None
is_running = False
last_check_time = None
last_check_result = None
stats = {
    'total_emails_processed': 0,
    'total_reports_processed': 0,
    'last_successful_check': None,
    'errors': []
}

def initialize_monitor():
    """Initialize the email monitor"""
    global monitor
    try:
        monitor = PharmacyEmailMonitor()
        logger.info("✅ Email monitor initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize email monitor: {e}")
        stats['errors'].append(f"Monitor initialization failed: {e}")
        return False

def check_for_new_reports():
    """Check for new pharmacy reports and process them"""
    global last_check_time, last_check_result, stats
    
    logger.info("🔄 Starting scheduled email check...")
    last_check_time = datetime.now()
    
    try:
        if not monitor:
            if not initialize_monitor():
                last_check_result = "Failed to initialize monitor"
                return
        
        # Process one email cycle
        success = monitor.process_single_email_cycle()
        
        if success:
            last_check_result = "Success"
            stats['last_successful_check'] = datetime.now().isoformat()
            logger.info("✅ Email check completed successfully")
        else:
            last_check_result = "Failed"
            logger.warning("⚠️ Email check failed")
            
    except Exception as e:
        error_msg = f"Email check error: {e}"
        logger.error(f"❌ {error_msg}")
        stats['errors'].append(error_msg)
        last_check_result = f"Error: {e}"

def start_scheduler():
    """Start the scheduler to run email checks every 10 minutes"""
    global is_running
    
    if is_running:
        logger.info("Scheduler already running")
        return
    
    logger.info("🚀 Starting email monitoring scheduler...")
    
    # Schedule email checks every 10 minutes
    schedule.every(10).minutes.do(check_for_new_reports)
    
    # Run initial check after 30 seconds
    schedule.every(30).seconds.do(check_for_new_reports)
    
    is_running = True
    
    def run_scheduler():
        while is_running:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("✅ Scheduler started successfully")

def stop_scheduler():
    """Stop the scheduler"""
    global is_running
    is_running = False
    logger.info("🛑 Scheduler stopped")

# Flask Routes

@app.route('/')
def home():
    """Home page with service status"""
    return jsonify({
        'service': 'Pharmacy Email Monitor',
        'status': 'running' if is_running else 'stopped',
        'last_check': last_check_time.isoformat() if last_check_time else None,
        'last_result': last_check_result,
        'uptime': 'Active' if is_running else 'Inactive'
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        db = RenderPharmacyDatabase()
        db_stats = db.get_database_stats()
        db.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'scheduler': 'running' if is_running else 'stopped',
            'last_check': last_check_time.isoformat() if last_check_time else None,
            'database_stats': db_stats
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/stats')
def get_stats():
    """Get monitoring statistics"""
    return jsonify({
        'stats': stats,
        'scheduler_status': {
            'running': is_running,
            'last_check_time': last_check_time.isoformat() if last_check_time else None,
            'last_check_result': last_check_result
        }
    })

@app.route('/check-now', methods=['POST'])
def manual_check():
    """Manually trigger an email check"""
    try:
        logger.info("📧 Manual email check triggered")
        check_for_new_reports()
        
        return jsonify({
            'status': 'success',
            'message': 'Email check completed',
            'result': last_check_result,
            'check_time': last_check_time.isoformat() if last_check_time else None
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Email check failed: {e}'
        }), 500

@app.route('/start', methods=['POST'])
def start_monitoring():
    """Start the monitoring service"""
    try:
        start_scheduler()
        return jsonify({
            'status': 'success',
            'message': 'Monitoring service started'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start monitoring: {e}'
        }), 500

@app.route('/stop', methods=['POST'])
def stop_monitoring():
    """Stop the monitoring service"""
    try:
        stop_scheduler()
        return jsonify({
            'status': 'success',
            'message': 'Monitoring service stopped'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to stop monitoring: {e}'
        }), 500

@app.route('/database/stats')
def database_stats():
    """Get database statistics"""
    try:
        db = RenderPharmacyDatabase()
        stats = db.get_database_stats()
        db.close()
        
        return jsonify({
            'status': 'success',
            'database_stats': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get database stats: {e}'
        }), 500

@app.route('/database/pharmacies')
def get_pharmacies():
    """Get all pharmacies"""
    try:
        db = RenderPharmacyDatabase()
        pharmacies = db.get_all_pharmacies()
        db.close()
        
        return jsonify({
            'status': 'success',
            'pharmacies': pharmacies
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get pharmacies: {e}'
        }), 500

@app.route('/database/dates')
def get_dates():
    """Get available report dates"""
    try:
        pharmacy = request.args.get('pharmacy')
        db = RenderPharmacyDatabase()
        dates = db.get_available_dates(pharmacy)
        db.close()
        
        return jsonify({
            'status': 'success',
            'dates': dates
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get dates: {e}'
        }), 500

@app.route('/database/performance/<pharmacy_code>')
def get_performance(pharmacy_code):
    """Get pharmacy performance data"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({
                'status': 'error',
                'message': 'start_date and end_date parameters required'
            }), 400
        
        db = RenderPharmacyDatabase()
        performance = db.get_pharmacy_performance(pharmacy_code, start_date, end_date)
        db.close()
        
        return jsonify({
            'status': 'success',
            'pharmacy_code': pharmacy_code,
            'performance': performance
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get performance data: {e}'
        }), 500

@app.route('/database/top-products/<pharmacy_code>')
def get_top_products(pharmacy_code):
    """Get top selling products for a pharmacy"""
    try:
        date = request.args.get('date')
        limit = int(request.args.get('limit', 10))
        
        if not date:
            return jsonify({
                'status': 'error',
                'message': 'date parameter required'
            }), 400
        
        db = RenderPharmacyDatabase()
        products = db.get_top_selling_products(pharmacy_code, date, limit)
        db.close()
        
        return jsonify({
            'status': 'success',
            'pharmacy_code': pharmacy_code,
            'date': date,
            'top_products': products
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get top products: {e}'
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Initialize the monitor
    if initialize_monitor():
        # Start the scheduler
        start_scheduler()
        
        # Get port from environment (Render sets PORT)
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"🚀 Starting Pharmacy Email Monitor Web Service on port {port}")
        logger.info("📧 Email monitoring will run every 10 minutes")
        logger.info("🌐 Web service endpoints available:")
        logger.info("   GET  / - Service status")
        logger.info("   GET  /health - Health check")
        logger.info("   GET  /stats - Monitoring statistics")
        logger.info("   POST /check-now - Manual email check")
        logger.info("   POST /start - Start monitoring")
        logger.info("   POST /stop - Stop monitoring")
        logger.info("   GET  /database/stats - Database statistics")
        logger.info("   GET  /database/pharmacies - List pharmacies")
        logger.info("   GET  /database/dates - Available dates")
        logger.info("   GET  /database/performance/<pharmacy> - Performance data")
        logger.info("   GET  /database/top-products/<pharmacy> - Top products")
        
        # Start Flask app
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.error("❌ Failed to initialize monitor. Exiting.")
        exit(1) 