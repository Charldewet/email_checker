#!/usr/bin/env python3
"""
Pharmacy Dashboard API Endpoints
===============================

Phase 1 implementation of all financial and basic analytics endpoints
to maintain compatibility with existing frontend dashboard.
"""

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from render_database_connection import RenderPharmacyDatabase

logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_cache_store = {}
_cache_ttl_seconds = 60

def _cache_get_or_set(key: str, compute_fn):
    now = datetime.utcnow()
    entry = _cache_store.get(key)
    if entry and (now - entry['ts']).total_seconds() < _cache_ttl_seconds:
        return entry['value']
    value = compute_fn()
    _cache_store[key] = {'value': value, 'ts': now}
    return value

def get_pharmacy_header():
    """Get pharmacy code from X-Pharmacy header"""
    return request.headers.get('X-Pharmacy', 'REITZ')  # Default to REITZ if not provided

def format_date(date_str: str) -> str:
    """Ensure date is in YYYY-MM-DD format"""
    try:
        # Handle various date formats
        if '/' in date_str:
            date_obj = datetime.strptime(date_str, '%Y/%m/%d')
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str

def register_financial_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register all financial data endpoints"""
    
    @app.route('/api/turnover', methods=['GET'])
    def get_latest_turnover():
        """Get latest turnover data"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        query = """
        SELECT turnover, report_date 
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        ORDER BY report_date DESC 
        LIMIT 1
        """
        
        result = db.execute_query(query, (pharmacy_id,))
        if not result:
            return jsonify({'turnover': 0, 'date': None})
        
        return jsonify({
            'turnover': float(result[0]['turnover']) if result[0]['turnover'] else 0,
            'date': result[0]['report_date'].strftime('%Y-%m-%d')
        })
    
    @app.route('/api/turnover_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_turnover_for_range(start_date, end_date):
        """Get turnover for date range"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT SUM(turnover) as total_turnover
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        total_turnover = float(result[0]['total_turnover']) if result[0]['total_turnover'] else 0
        
        return jsonify({'total_turnover': total_turnover})
    
    @app.route('/api/daily_turnover_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_turnover_for_range(start_date, end_date):
        """Get daily turnover for range"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, turnover
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'turnover': float(row['turnover']) if row['turnover'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/gp_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_gp_for_range(start_date, end_date):
        """Get gross profit for range"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT 
            SUM(gp_value) as total_gp_value,
            AVG(gp_percent) as avg_gp_percent
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        return jsonify({
            'total_gp_value': float(result[0]['total_gp_value']) if result[0]['total_gp_value'] else 0,
            'avg_gp_percent': float(result[0]['avg_gp_percent']) if result[0]['avg_gp_percent'] else 0
        })
    
    @app.route('/api/costs_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_costs_for_range(start_date, end_date):
        """Get cost of sales for range"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT SUM(cost_of_sales) as total_cost_of_sales
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        return jsonify({
            'total_cost_of_sales': float(result[0]['total_cost_of_sales']) if result[0]['total_cost_of_sales'] else 0
        })

    @app.route('/api/kpis/summary', methods=['GET'])
    def get_kpis_summary():
        """Return Daily, MTD, YTD summaries in one call."""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404

        as_of = request.args.get('as_of')
        if not as_of:
            # Default to latest available date for this pharmacy
            latest = db.execute_query(
                "SELECT MAX(report_date) AS d FROM daily_summary WHERE pharmacy_id = %s",
                (pharmacy_id,)
            )
            if not latest or not latest[0]['d']:
                return jsonify({'daily': {}, 'mtd': {}, 'ytd': {}, 'insights': []})
            as_of = latest[0]['d'].strftime('%Y-%m-%d')
        else:
            as_of = format_date(as_of)

        cache_key = f"kpis_summary:{pharmacy_id}:{as_of}"

        def compute():
            # Daily
            daily_q = """
                SELECT turnover, gp_value, purchases, cost_of_sales, gp_percent, transactions_total,
                       avg_basket_value, disp_turnover, script_total, avg_script_value,
                       sales_cash, sales_account, sales_cod
                FROM daily_summary WHERE pharmacy_id = %s AND report_date = %s
            """
            daily_r = db.execute_query(daily_q, (pharmacy_id, as_of))
            daily = daily_r[0] if daily_r else {}

            # MTD (sum up to as_of inclusive)
            mtd_q = """
                SELECT COALESCE(SUM(turnover),0) AS turnover,
                       COALESCE(SUM(gp_value),0) AS gp_value,
                       COALESCE(SUM(purchases),0) AS purchases,
                       COALESCE(SUM(cost_of_sales),0) AS cost_of_sales,
                       COALESCE(SUM(transactions_total),0) AS transactions_total,
                       COALESCE(SUM(disp_turnover),0) AS disp_turnover,
                       COALESCE(SUM(script_total),0) AS script_total
                FROM daily_summary
                WHERE pharmacy_id = %s
                  AND report_date >= date_trunc('month', %s::date)::date
                  AND report_date <= %s::date
            """
            mtd = db.execute_query(mtd_q, (pharmacy_id, as_of, as_of))[0]
            # Compute MTD avg_basket_value = turnover / transactions_total
            mtd_abv = float(mtd['turnover']) / mtd['transactions_total'] if mtd['transactions_total'] else 0.0
            # Compute MTD avg_script_value = disp_turnover / script_total
            mtd_asv = float(mtd['disp_turnover']) / mtd['script_total'] if mtd['script_total'] else 0.0

            # YTD (sum up to as_of inclusive)
            ytd_q = """
                SELECT COALESCE(SUM(turnover),0) AS turnover,
                       COALESCE(SUM(gp_value),0) AS gp_value,
                       COALESCE(SUM(purchases),0) AS purchases,
                       COALESCE(SUM(cost_of_sales),0) AS cost_of_sales,
                       COALESCE(SUM(transactions_total),0) AS transactions_total,
                       COALESCE(SUM(disp_turnover),0) AS disp_turnover,
                       COALESCE(SUM(script_total),0) AS script_total
                FROM daily_summary
                WHERE pharmacy_id = %s
                  AND report_date >= date_trunc('year', %s::date)::date
                  AND report_date <= %s::date
            """
            ytd = db.execute_query(ytd_q, (pharmacy_id, as_of, as_of))[0]
            ytd_abv = float(ytd['turnover']) / ytd['transactions_total'] if ytd['transactions_total'] else 0.0
            ytd_asv = float(ytd['disp_turnover']) / ytd['script_total'] if ytd['script_total'] else 0.0

            return {
                'daily': {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in daily.items()} if daily else {},
                'mtd': {**{k: float(v) for k, v in mtd.items()}, 'avg_basket_value': round(mtd_abv, 2), 'avg_script_value': round(mtd_asv, 2)},
                'ytd': {**{k: float(v) for k, v in ytd.items()}, 'avg_basket_value': round(ytd_abv, 2), 'avg_script_value': round(ytd_asv, 2)},
                'as_of': as_of
            }

        payload = _cache_get_or_set(cache_key, compute)
        return jsonify(payload)

def register_transaction_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register transaction and basket analytics endpoints"""
    
    @app.route('/api/transactions_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_transactions_for_range(start_date, end_date):
        """Get transaction counts for range"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT SUM(transactions_total) as total_transactions
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        return jsonify({
            'total_transactions': int(result[0]['total_transactions']) if result[0]['total_transactions'] else 0
        })
    
    @app.route('/api/daily_avg_basket_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_avg_basket_for_range(start_date, end_date):
        """Get daily average basket values"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, avg_basket_value, avg_basket_size
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'avg_basket_value': float(row['avg_basket_value']) if row['avg_basket_value'] else 0,
                'avg_basket_size': float(row['avg_basket_size']) if row['avg_basket_size'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/avg_basket_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_avg_basket_for_range(start_date, end_date):
        """Get average basket metrics for range"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT 
            AVG(avg_basket_value) as avg_basket_value,
            AVG(avg_basket_size) as avg_basket_size
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        return jsonify({
            'avg_basket_value': float(result[0]['avg_basket_value']) if result[0]['avg_basket_value'] else 0,
            'avg_basket_size': float(result[0]['avg_basket_size']) if result[0]['avg_basket_size'] else 0
        })

def register_dispensary_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register dispensary analytics endpoints"""
    
    @app.route('/api/dispensary_vs_total_turnover/<start_date>/<end_date>', methods=['GET'])
    def get_dispensary_vs_total_turnover(start_date, end_date):
        """Compare dispensary vs total turnover"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT 
            SUM(disp_turnover) as total_dispensary_turnover,
            SUM(turnover) as total_turnover
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        dispensary_turnover = float(result[0]['total_dispensary_turnover']) if result[0]['total_dispensary_turnover'] else 0
        total_turnover = float(result[0]['total_turnover']) if result[0]['total_turnover'] else 0
        
        dispensary_percentage = (dispensary_turnover / total_turnover * 100) if total_turnover > 0 else 0
        
        return jsonify({
            'dispensary_turnover': dispensary_turnover,
            'total_turnover': total_turnover,
            'dispensary_percentage': dispensary_percentage
        })
    
    @app.route('/api/daily_dispensary_turnover_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_dispensary_turnover_for_range(start_date, end_date):
        """Get daily dispensary turnover"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, disp_turnover
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'dispensary_turnover': float(row['disp_turnover']) if row['disp_turnover'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/daily_scripts_dispensed_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_scripts_dispensed_for_range(start_date, end_date):
        """Get daily scripts dispensed"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, script_total, avg_script_value
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'scripts_dispensed': int(row['script_total']) if row['script_total'] else 0,
                'avg_script_value': float(row['avg_script_value']) if row['avg_script_value'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/daily_dispensary_percent_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_dispensary_percent_for_range(start_date, end_date):
        """Get dispensary percentage of total"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT 
            report_date, 
            disp_turnover, 
            turnover,
            CASE 
                WHEN turnover > 0 THEN (disp_turnover / turnover * 100)
                ELSE 0
            END as dispensary_percentage
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'dispensary_percentage': float(row['dispensary_percentage']) if row['dispensary_percentage'] else 0
            })
        
        return jsonify(data)

def register_payment_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register payment methods analytics endpoints"""
    
    @app.route('/api/daily_cash_sales_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_cash_sales_for_range(start_date, end_date):
        """Get daily cash sales"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, sales_cash
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'cash_sales': float(row['sales_cash']) if row['sales_cash'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/daily_account_sales_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_account_sales_for_range(start_date, end_date):
        """Get daily account sales"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, sales_account
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'account_sales': float(row['sales_account']) if row['sales_account'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/daily_cod_sales_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_cod_sales_for_range(start_date, end_date):
        """Get daily COD sales"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, sales_cod
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'cod_sales': float(row['sales_cod']) if row['sales_cod'] else 0
            })
        
        return jsonify(data)
    
    # Note: Cash tenders and credit card tenders are not in our current database
    # These endpoints will return empty arrays for now
    @app.route('/api/daily_cash_tenders_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_cash_tenders_for_range(start_date, end_date):
        """Get daily cash tenders - Not implemented yet"""
        return jsonify([])
    
    @app.route('/api/daily_credit_card_tenders_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_credit_card_tenders_for_range(start_date, end_date):
        """Get daily credit card tenders - Not implemented yet"""
        return jsonify([])

def register_stock_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register stock and inventory analytics endpoints"""
    
    @app.route('/api/daily_purchases_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_purchases_for_range(start_date, end_date):
        """Get daily stock purchases"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, purchases
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'purchases': float(row['purchases']) if row['purchases'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/daily_cost_of_sales_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_cost_of_sales_for_range(start_date, end_date):
        """Get daily cost of sales"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, cost_of_sales
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'cost_of_sales': float(row['cost_of_sales']) if row['cost_of_sales'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/opening_stock_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_opening_stock_for_range(start_date, end_date):
        """Get opening stock values"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, stock_opening
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'opening_stock': float(row['stock_opening']) if row['stock_opening'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/closing_stock_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_closing_stock_for_range(start_date, end_date):
        """Get closing stock values"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, stock_closing
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'closing_stock': float(row['stock_closing']) if row['stock_closing'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/monthly_closing_stock_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_monthly_closing_stock_for_range(start_date, end_date):
        """Get monthly closing stock"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT 
            DATE_TRUNC('month', report_date) as month,
            MAX(stock_closing) as closing_stock
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        GROUP BY DATE_TRUNC('month', report_date)
        ORDER BY month
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'month': row['month'].strftime('%Y-%m'),
                'closing_stock': float(row['closing_stock']) if row['closing_stock'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/stock_adjustments_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_stock_adjustments_for_range(start_date, end_date):
        """Get stock adjustments"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, adjustments
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'adjustments': float(row['adjustments']) if row['adjustments'] else 0
            })
        
        return jsonify(data)

def register_performance_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register performance metrics endpoints"""
    
    @app.route('/api/daily_gp_percent_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_daily_gp_percent_for_range(start_date, end_date):
        """Get daily gross profit percentages"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT report_date, gp_percent
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'gp_percent': float(row['gp_percent']) if row['gp_percent'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/turnover_ratio_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_turnover_ratio_for_range(start_date, end_date):
        """Get turnover ratios"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT 
            report_date,
            turnover,
            stock_opening,
            CASE 
                WHEN stock_opening > 0 THEN (turnover / stock_opening)
                ELSE 0
            END as turnover_ratio
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'turnover_ratio': float(row['turnover_ratio']) if row['turnover_ratio'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/days_of_inventory_for_range/<start_date>/<end_date>', methods=['GET'])
    def get_days_of_inventory_for_range(start_date, end_date):
        """Get days of inventory"""
        pharmacy_code = get_pharmacy_header()
        pharmacy_id = db.get_pharmacy_id_by_code(pharmacy_code)
        
        if not pharmacy_id:
            return jsonify({'error': 'Pharmacy not found'}), 404
        
        start_date = format_date(start_date)
        end_date = format_date(end_date)
        
        query = """
        SELECT 
            report_date,
            stock_closing,
            cost_of_sales,
            CASE 
                WHEN cost_of_sales > 0 THEN (stock_closing / cost_of_sales)
                ELSE 0
            END as days_of_inventory
        FROM daily_summary 
        WHERE pharmacy_id = %s 
        AND report_date BETWEEN %s AND %s
        ORDER BY report_date
        """
        
        result = db.execute_query(query, (pharmacy_id, start_date, end_date))
        
        data = []
        for row in result:
            data.append({
                'date': row['report_date'].strftime('%Y-%m-%d'),
                'days_of_inventory': float(row['days_of_inventory']) if row['days_of_inventory'] else 0
            })
        
        return jsonify(data)

def register_basic_stock_analytics_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register basic stock analytics endpoints using sales_details data"""
    
    @app.route('/api/stock/daily_summary/<int:pharmacy_id>/<date>', methods=['GET'])
    def get_daily_summary(pharmacy_id, date):
        """Get daily stock summary for a pharmacy"""
        date = format_date(date)
        
        query = """
        SELECT 
            ds.*,
            p.pharmacy_code,
            p.name as pharmacy_name
        FROM daily_summary ds
        JOIN pharmacies p ON ds.pharmacy_id = p.id
        WHERE ds.pharmacy_id = %s AND ds.report_date = %s
        """
        
        result = db.execute_query(query, (pharmacy_id, date))
        
        if not result:
            return jsonify({'error': 'No data found'}), 404
        
        row = result[0]
        return jsonify({
            'pharmacy_id': pharmacy_id,
            'pharmacy_code': row['pharmacy_code'],
            'pharmacy_name': row['pharmacy_name'],
            'date': date,
            'turnover': float(row['turnover']) if row['turnover'] else 0,
            'gp_value': float(row['gp_value']) if row['gp_value'] else 0,
            'gp_percent': float(row['gp_percent']) if row['gp_percent'] else 0,
            'transactions_total': int(row['transactions_total']) if row['transactions_total'] else 0,
            'avg_basket_value': float(row['avg_basket_value']) if row['avg_basket_value'] else 0,
            'script_total': int(row['script_total']) if row['script_total'] else 0,
            'stock_opening': float(row['stock_opening']) if row['stock_opening'] else 0,
            'stock_closing': float(row['stock_closing']) if row['stock_closing'] else 0
        })
    
    @app.route('/api/stock/top_moving/<int:pharmacy_id>/<date>', methods=['GET'])
    def get_top_moving(pharmacy_id, date):
        """Get top moving products for a specific date"""
        date = format_date(date)
        limit = request.args.get('limit', 10, type=int)
        
        query = """
        SELECT 
            stock_code,
            description,
            sales_qty,
            sales_value,
            gross_profit,
            gross_profit_percent,
            department_code
        FROM sales_details sd
        WHERE sd.pharmacy_id = %s 
        AND sd.report_date = %s
        AND sd.sales_qty > 0
        ORDER BY sd.sales_qty DESC
        LIMIT %s
        """
        
        result = db.execute_query(query, (pharmacy_id, date, limit))
        
        data = []
        for row in result:
            data.append({
                'stock_code': row['stock_code'],
                'description': row['description'],
                'sales_qty': int(row['sales_qty']) if row['sales_qty'] else 0,
                'sales_value': float(row['sales_value']) if row['sales_value'] else 0,
                'gross_profit': float(row['gross_profit']) if row['gross_profit'] else 0,
                'gross_profit_percent': float(row['gross_profit_percent']) if row['gross_profit_percent'] else 0,
                'department_code': row['department_code']
            })
        
        return jsonify(data)
    
    @app.route('/api/stock/top_departments/<int:pharmacy_id>/<date>', methods=['GET'])
    def get_top_departments(pharmacy_id, date):
        """Get top performing departments"""
        date = format_date(date)
        limit = request.args.get('limit', 5, type=int)
        
        query = """
        SELECT 
            department_code,
            SUM(sales_qty) as total_qty,
            SUM(sales_value) as total_value,
            SUM(gross_profit) as total_gp,
            COUNT(*) as product_count
        FROM sales_details sd
        WHERE sd.pharmacy_id = %s 
        AND sd.report_date = %s
        GROUP BY department_code
        ORDER BY total_value DESC
        LIMIT %s
        """
        
        result = db.execute_query(query, (pharmacy_id, date, limit))
        
        data = []
        for row in result:
            data.append({
                'department_code': row['department_code'],
                'total_qty': int(row['total_qty']) if row['total_qty'] else 0,
                'total_value': float(row['total_value']) if row['total_value'] else 0,
                'total_gp': float(row['total_gp']) if row['total_gp'] else 0,
                'product_count': int(row['product_count']),
                'avg_gp_percent': float(row['total_gp'] / row['total_value'] * 100) if row['total_value'] and row['total_gp'] else 0
            })
        
        return jsonify(data)
    
    @app.route('/api/stock/low_gp_products/<int:pharmacy_id>/<date>', methods=['GET'])
    def get_low_gp_products(pharmacy_id, date):
        """Get products with low gross profit"""
        date = format_date(date)
        threshold = request.args.get('threshold', 20, type=float)
        
        query = """
        SELECT 
            stock_code,
            description,
            sales_qty,
            sales_value,
            gross_profit,
            gross_profit_percent,
            department_code
        FROM sales_details sd
        WHERE sd.pharmacy_id = %s 
        AND sd.report_date = %s
        AND sd.gross_profit_percent < %s
        AND sd.sales_qty > 0
        ORDER BY sd.sales_value DESC
        """
        
        result = db.execute_query(query, (pharmacy_id, date, threshold))
        
        data = []
        for row in result:
            data.append({
                'stock_code': row['stock_code'],
                'description': row['description'],
                'sales_qty': int(row['sales_qty']) if row['sales_qty'] else 0,
                'sales_value': float(row['sales_value']) if row['sales_value'] else 0,
                'gross_profit': float(row['gross_profit']) if row['gross_profit'] else 0,
                'gross_profit_percent': float(row['gross_profit_percent']) if row['gross_profit_percent'] else 0,
                'department_code': row['department_code']
            })
        
        return jsonify(data)
    
    @app.route('/api/stock/health', methods=['GET'])
    def stock_health():
        """Stock service health check"""
        return jsonify({'status': 'healthy', 'service': 'stock_analytics'})

def register_status_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register system status endpoints"""
    
    @app.route('/api/status', methods=['GET'])
    def get_system_status():
        """Get system status and stats"""
        try:
            # Get database stats
            stats_query = """
            SELECT 
                COUNT(DISTINCT pharmacy_id) as total_pharmacies,
                COUNT(*) as total_daily_summaries,
                MAX(report_date) as latest_date,
                MIN(report_date) as earliest_date
            FROM daily_summary
            """
            
            stats_result = db.execute_query(stats_query)
            
            # Get sales details stats
            sales_query = """
            SELECT COUNT(*) as total_sales_records
            FROM sales_details
            """
            
            sales_result = db.execute_query(sales_query)
            
            return jsonify({
                'status': 'healthy',
                'database': {
                    'total_pharmacies': int(stats_result[0]['total_pharmacies']) if stats_result[0]['total_pharmacies'] else 0,
                    'total_daily_summaries': int(stats_result[0]['total_daily_summaries']),
                    'total_sales_records': int(sales_result[0]['total_sales_records']),
                    'latest_date': stats_result[0]['latest_date'].strftime('%Y-%m-%d') if stats_result[0]['latest_date'] else None,
                    'earliest_date': stats_result[0]['earliest_date'].strftime('%Y-%m-%d') if stats_result[0]['earliest_date'] else None
                },
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 500
    
    @app.route('/api/health_check', methods=['GET'])
    def api_health_check():
        """API health check endpoint"""
        return jsonify({'status': 'healthy', 'service': 'api'})

def register_all_endpoints(app: Flask, db: RenderPharmacyDatabase):
    """Register all Phase 1 API endpoints"""
    register_financial_endpoints(app, db)
    register_transaction_endpoints(app, db)
    register_dispensary_endpoints(app, db)
    register_payment_endpoints(app, db)
    register_stock_endpoints(app, db)
    register_performance_endpoints(app, db)
    register_basic_stock_analytics_endpoints(app, db)
    register_status_endpoints(app, db)
    
    logger.info("✅ All Phase 1 API endpoints registered successfully") 