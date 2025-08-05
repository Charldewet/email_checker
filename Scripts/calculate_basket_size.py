import json
from pathlib import Path
from typing import Dict, Any

def load_json_data(filename: str) -> list:
    """Load data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  File not found: {filename}")
        return []

def calculate_basket_size():
    """
    Calculate average basket size by combining transaction data and gross profit data
    """
    print("=== AVERAGE BASKET SIZE CALCULATION ===")
    print()
    
    # Load transaction summary data
    transaction_data = load_json_data("transaction_summary_extracted_data.json")
    if not transaction_data:
        print("❌ No transaction summary data found. Please run extract_transaction_summary.py first.")
        return
    
    # Load gross profit data
    gross_profit_data = load_json_data("gross_profit_extracted_data.json")
    if not gross_profit_data:
        print("❌ No gross profit data found. Please run extract_gross_profit.py first.")
        return
    
    print(f"📊 Found {len(transaction_data)} transaction reports and {len(gross_profit_data)} gross profit reports")
    print()
    
    # Create lookup dictionaries for easy matching
    transaction_lookup = {}
    for report in transaction_data:
        key = (report['pharmacy'], report['date'])
        transaction_lookup[key] = report
    
    gross_profit_lookup = {}
    for report in gross_profit_data:
        key = (report['pharmacy'], report['date'])
        gross_profit_lookup[key] = report
    
    # Calculate basket size for each pharmacy/date combination
    basket_size_results = []
    
    for (pharmacy, date), transaction_report in transaction_lookup.items():
        print(f"🏪 {pharmacy} - {date}")
        
        # Get transaction data
        transactions_total = transaction_report.get('transactions_total', 0)
        
        # Get gross profit data
        if (pharmacy, date) in gross_profit_lookup:
            gross_profit_report = gross_profit_lookup[(pharmacy, date)]
            total_products_sold = gross_profit_report['summary_stats']['total_sales_qty']
            
            # Calculate average basket size
            if transactions_total > 0:
                avg_basket_size = total_products_sold / transactions_total
            else:
                avg_basket_size = 0
            
            # Get other relevant data
            turnover = transaction_report.get('turnover', 0)
            avg_basket_value = transaction_report.get('avg_basket_value', 0)
            
            result = {
                'pharmacy': pharmacy,
                'date': date,
                'transactions_total': transactions_total,
                'total_products_sold': total_products_sold,
                'avg_basket_size': round(avg_basket_size, 2),
                'turnover': turnover,
                'avg_basket_value': avg_basket_value
            }
            
            basket_size_results.append(result)
            
            print(f"   📈 Transaction Data:")
            print(f"      • Total Transactions: {transactions_total:,}")
            print(f"      • Turnover: R{turnover:,.2f}")
            print(f"      • Average Basket Value: R{avg_basket_value:,.2f}")
            
            print(f"   📦 Product Data:")
            print(f"      • Total Products Sold: {total_products_sold:,.0f}")
            print(f"      • Average Basket Size: {avg_basket_size:.2f} items")
            
            # Calculate some additional insights
            if avg_basket_size > 0:
                items_per_rand = total_products_sold / turnover if turnover > 0 else 0
                print(f"   💡 Insights:")
                print(f"      • Items per R1 spent: {items_per_rand:.3f}")
                print(f"      • Average item value: R{turnover/total_products_sold:.2f}" if total_products_sold > 0 else "      • Average item value: R0.00")
            
            print(f"   " + "="*60)
            print()
        else:
            print(f"   ⚠️  No matching gross profit data found for {pharmacy} - {date}")
            print()
    
    # Save results to JSON
    output_file = "basket_size_calculations.json"
    with open(output_file, 'w') as f:
        json.dump(basket_size_results, f, indent=2, default=str)
    
    print(f"📊 Basket size calculations saved to: {output_file}")
    
    # Display summary
    print("\n=== SUMMARY ===")
    for result in basket_size_results:
        print(f"🏪 {result['pharmacy']} ({result['date']}):")
        print(f"   • {result['transactions_total']:,} transactions")
        print(f"   • {result['total_products_sold']:,.0f} products sold")
        print(f"   • Average basket size: {result['avg_basket_size']} items")
        print(f"   • Average basket value: R{result['avg_basket_value']:,.2f}")
        print()
    
    # Create database-ready format
    print("=== DATABASE INSERT FORMAT ===")
    for result in basket_size_results:
        print(f"-- {result['pharmacy']} - {result['date']}")
        print(f"UPDATE daily_summary SET")
        print(f"    avg_basket_size = {result['avg_basket_size']},")
        print(f"    transactions_total = {result['transactions_total']},")
        print(f"    turnover = {result['turnover']},")
        print(f"    avg_basket_value = {result['avg_basket_value']}")
        print(f"WHERE pharmacy_id = (SELECT id FROM pharmacies WHERE pharmacy_code = '{result['pharmacy']}')")
        print(f"  AND report_date = '{result['date']}';")
        print()
    
    return basket_size_results

if __name__ == "__main__":
    calculate_basket_size() 