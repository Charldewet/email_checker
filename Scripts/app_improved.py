#!/usr/bin/env python3
"""
Improved Pharmacy Email Monitor Web Service
===========================================

This Flask web service runs on Render and automatically checks for new pharmacy reports
every 5 minutes using the improved pipeline with "keep the largest value" logic.
"""

import os
import time
import threading
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import schedule

# Import our improved pipeline modules
from improved_classify_and_organize import ImprovedPDFClassifier
from improved_data_pipeline import ImprovedDataPipeline
from render_database_connection import RenderPharmacyDatabase
from api_endpoints import register_all_endpoints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database connection for API endpoints
try:
    api_db = RenderPharmacyDatabase()
    # Register all Phase 1 API endpoints
    register_all_endpoints(app, api_db)
    logger.info("✅ All Phase 1 API endpoints registered successfully")
except Exception as e:
    logger.error(f"❌ Failed to register API endpoints: {e}")

# Global variables
classifier = None
pipeline = None
is_running = False
last_check_time = None
last_check_result = None
stats = {
    'total_emails_processed': 0,
    'total_reports_processed': 0,
    'last_successful_check': None,
    'errors': [],
    'improved_pipeline_runs': 0
}

def initialize_improved_pipeline():
    """Initialize the improved pipeline components"""
    global classifier, pipeline
    try:
        classifier = ImprovedPDFClassifier()
        pipeline = ImprovedDataPipeline()
        logger.info("✅ Improved pipeline components initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize improved pipeline: {e}")
        stats['errors'].append(f"Pipeline initialization failed: {e}")
        return False

def run_improved_pipeline():
    """Run the complete improved pipeline with keep largest value logic"""
    global last_check_time, last_check_result, stats
    
    logger.info("🔄 Starting improved pipeline with 'keep largest value' logic...")
    last_check_time = datetime.now()
    
    try:
        if not classifier or not pipeline:
            if not initialize_improved_pipeline():
                last_check_result = "Failed to initialize pipeline"
                return False
        
        # Step 1: Run improved classification (process emails from last 2 days)
        logger.info("📧 Step 1: Running improved classification...")
        classification_success = classifier.process_emails_and_classify(days=2)
        
        if not classification_success:
            logger.error("❌ Classification failed")
            last_check_result = "Classification failed"
            return False
        
        # Step 2: Run improved data pipeline with largest value strategy
        logger.info("📊 Step 2: Running improved data pipeline...")
        pipeline.run_complete_pipeline()
        
        # Update stats
        stats['improved_pipeline_runs'] += 1
        stats['last_successful_check'] = datetime.now().isoformat()
        last_check_result = "Success - Improved pipeline completed"
        
        logger.info("✅ Improved pipeline completed successfully!")
        return True
        
    except Exception as e:
        error_msg = f"Pipeline execution failed: {e}"
        logger.error(f"❌ {error_msg}")
        stats['errors'].append(error_msg)
        last_check_result = f"Error: {e}"
        return False

def start_scheduler():
    """Start the scheduler to run the improved pipeline every 5 minutes"""
    global is_running
    
    if is_running:
        logger.warning("⚠️ Scheduler is already running")
        return
    
    logger.info("🚀 Starting improved pipeline scheduler (every 5 minutes)...")
    is_running = True
    
    # Schedule the improved pipeline to run every 5 minutes
    schedule.every(5).minutes.do(run_improved_pipeline)
    
    def run_scheduler():
        while is_running:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Don't run initial check immediately - let the scheduler handle it
    logger.info("✅ Scheduler started - pipeline will run in 5 minutes")

def stop_scheduler():
    """Stop the scheduler"""
    global is_running
    is_running = False
    schedule.clear()
    logger.info("⏹️ Scheduler stopped")

# API Endpoints

@app.route('/')
def home():
    """Home page with service status"""
    status = "Running" if is_running else "Stopped"
    return jsonify({
        "service": "Improved Pharmacy Email Monitor",
        "status": status,
        "description": "Automatically processes pharmacy reports every 5 minutes using 'keep largest value' logic",
        "last_check": last_check_time.isoformat() if last_check_time else None,
        "last_result": last_check_result,
        "endpoints": {
            "/health": "Health check",
            "/stats": "Service statistics",
            "/check-now": "Manual pipeline run (POST)",
            "/start": "Start monitoring (POST)",
            "/stop": "Stop monitoring (POST)",
            "/database/stats": "Database statistics",
            "/database/pharmacies": "List pharmacies",
            "/database/dates": "Available dates",
            "/api/*": "Financial data API endpoints"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = RenderPharmacyDatabase()
        db_stats = db.get_database_stats()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Improved Pharmacy Email Monitor",
            "scheduler_running": is_running,
            "database": {
                "connected": True,
                "pharmacies": db_stats.get('pharmacies', 0),
                "daily_summaries": db_stats.get('daily_summaries', 0)
            },
            "last_check": last_check_time.isoformat() if last_check_time else None,
            "last_result": last_check_result
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/stats')
def get_stats():
    """Get service statistics"""
    return jsonify({
        "improved_pipeline_runs": stats['improved_pipeline_runs'],
        "total_emails_processed": stats['total_emails_processed'],
        "total_reports_processed": stats['total_reports_processed'],
        "last_successful_check": stats['last_successful_check'],
        "scheduler_running": is_running,
        "last_check_time": last_check_time.isoformat() if last_check_time else None,
        "last_check_result": last_check_result,
        "recent_errors": stats['errors'][-5:] if stats['errors'] else []
    })

@app.route('/check-now', methods=['POST'])
def manual_check():
    """Manually trigger the improved pipeline"""
    try:
        logger.info("🔄 Manual pipeline trigger requested")
        success = run_improved_pipeline()
        
        return jsonify({
            "success": success,
            "message": "Improved pipeline executed manually",
            "result": last_check_result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/start', methods=['POST'])
def start_monitoring():
    """Start the monitoring service"""
    try:
        start_scheduler()
        return jsonify({
            "success": True,
            "message": "Improved pipeline monitoring started",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/stop', methods=['POST'])
def stop_monitoring():
    """Stop the monitoring service"""
    try:
        stop_scheduler()
        return jsonify({
            "success": True,
            "message": "Monitoring stopped",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/database/stats')
def database_stats():
    """Get database statistics"""
    try:
        db = RenderPharmacyDatabase()
        stats = db.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/database/pharmacies')
def get_pharmacies():
    """Get list of pharmacies"""
    try:
        db = RenderPharmacyDatabase()
        pharmacies = db.get_all_pharmacies()
        return jsonify(pharmacies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/database/dates')
def get_dates():
    """Get available dates"""
    try:
        db = RenderPharmacyDatabase()
        pharmacy = request.args.get('pharmacy')
        dates = db.get_available_dates(pharmacy)
        return jsonify(dates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/database/performance/<pharmacy_code>')
def get_performance(pharmacy_code):
    """Get pharmacy performance data"""
    try:
        db = RenderPharmacyDatabase()
        start_date = request.args.get('start_date', '2025-01-01')
        end_date = request.args.get('end_date', '2025-12-31')
        
        performance = db.get_pharmacy_performance(pharmacy_code, start_date, end_date)
        return jsonify(performance)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/database/top-products/<pharmacy_code>')
def get_top_products(pharmacy_code):
    """Get top selling products for a pharmacy"""
    try:
        db = RenderPharmacyDatabase()
        date = request.args.get('date', '2025-08-07')
        limit = int(request.args.get('limit', 10))
        
        products = db.get_top_selling_products(pharmacy_code, date, limit)
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Improved Pharmacy Email Monitor Service")
    logger.info("📊 Using 'keep largest value' logic for data quality")
    logger.info("⏰ Pipeline will run every 5 minutes")
    
    # Start the scheduler automatically
    start_scheduler()
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 