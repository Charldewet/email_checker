# New API Endpoints Implementation

## Overview
Two new endpoints have been added to support monthly summary reports with aggregated sales data across date ranges.

## Endpoints Created

### 1. Best Sellers by Quantity for Date Range

**Endpoint:** `GET /pharmacies/{pharmacyId}/stock-activity/by-quantity/range`

**Query Parameters:**
- `from` (required): Start date in YYYY-MM-DD format
- `to` (required): End date in YYYY-MM-DD format
- `limit` (optional): Number of top items to return (default: 20)

**Description:**
Returns the top-selling products by quantity sold within the specified date range, aggregated across all days in that range.

**Response Example:**
```json
[
  {
    "product_name": "PANADO TABS 500MG 24'S",
    "nappi_code": "123456",
    "quantity_sold": 245,
    "total_sales": 12450.50,
    "gp_percent": 35.2
  },
  ...
]
```

**Usage Example:**
```
GET /pharmacies/123/stock-activity/by-quantity/range?from=2025-10-01&to=2025-10-15&limit=20
```

**Sorting:** By `quantity_sold` descending

---

### 2. Low GP Products for Date Range

**Endpoint:** `GET /pharmacies/{pharmacyId}/stock-activity/low-gp/range`

**Query Parameters:**
- `from` (required): Start date in YYYY-MM-DD format
- `to` (required): End date in YYYY-MM-DD format
- `threshold` (required): Maximum GP% to include (e.g., 20 for products with GP% ≤ 20%)
- `limit` (optional): Number of items to return (default: 100)
- `exclude_pdst` (optional): Boolean to exclude PDST/KSAA products (default: false)

**Description:**
Returns products with GP% at or below the specified threshold within the date range, aggregated across all days. Excludes products with zero or negative turnover.

**Response Example:**
```json
[
  {
    "product_name": "DISPRIN TABS 300MG 24'S", 
    "nappi_code": "789012",
    "quantity_sold": 12,
    "total_sales": 450.00,
    "total_cost": 410.00,
    "gp_value": 40.00,
    "gp_percent": 8.9
  },
  ...
]
```

**Usage Example:**
```
GET /pharmacies/123/stock-activity/low-gp/range?from=2025-10-01&to=2025-10-15&threshold=20&limit=100&exclude_pdst=true
```

**Sorting:** By `gp_percent` ascending (worst GP first)

---

## Business Rules Implemented

### Both Endpoints:
- ✅ Aggregate all sales for each product across the entire date range
- ✅ Only include products that had actual sales in the date range
- ✅ Group by stock_code and description to aggregate multiple days

### Low GP Endpoint Specifically:
- ✅ Filter out products with zero or negative turnover (`sales_value > 0`)
- ✅ Filter out PDST/KSAA products when `exclude_pdst=true`
- ✅ Filter by products with `gp_percent <= threshold`
- ✅ Sort worst GP first for immediate visibility

---

## Use Cases

### Monthly Summary Tab
When a user selects October 15, 2025 on the Monthly Summary tab:

1. **Call for Best Sellers:**
   ```
   GET /pharmacies/123/stock-activity/by-quantity/range?from=2025-10-01&to=2025-10-15&limit=20
   ```
   This shows the 20 best-selling products by quantity for the entire month-to-date period.

2. **Call for Low GP Products:**
   ```
   GET /pharmacies/123/stock-activity/low-gp/range?from=2025-10-01&to=2025-10-15&threshold=20&limit=100
   ```
   This shows products with GP% ≤ 20% for the entire month-to-date period.

These endpoints aggregate data across ALL days in the date range, not just a single day.

---

## Technical Implementation

### Database Queries
Both endpoints use SQL aggregation functions (`SUM`, `AVG`) to aggregate data across the date range:

```sql
-- Best Sellers
SELECT 
    description as product_name,
    stock_code as nappi_code,
    SUM(sales_qty)::INTEGER as quantity_sold,
    SUM(sales_value) as total_sales,
    AVG(gross_profit_percent) as gp_percent
FROM sales_details
WHERE pharmacy_id = %s 
AND report_date BETWEEN %s AND %s
AND sales_qty > 0
GROUP BY stock_code, description
ORDER BY SUM(sales_qty) DESC
LIMIT %s
```

```sql
-- Low GP Products
SELECT 
    description as product_name,
    stock_code as nappi_code,
    SUM(sales_qty)::INTEGER as quantity_sold,
    SUM(sales_value) as total_sales,
    SUM(sales_cost) as total_cost,
    SUM(gross_profit) as gp_value,
    AVG(gross_profit_percent) as gp_percent
FROM sales_details
WHERE pharmacy_id = %s 
AND report_date BETWEEN %s AND %s
AND sales_value > 0
AND gross_profit_percent IS NOT NULL
AND gross_profit_percent <= %s
GROUP BY stock_code, description
ORDER BY AVG(gross_profit_percent) ASC
LIMIT %s
```

### Error Handling
- Returns `400 Bad Request` if required parameters are missing
- Returns `400 Bad Request` if threshold is not numeric (for low GP endpoint)
- Returns empty array `[]` if no results found
- Validates date formats using existing `format_date()` function

---

## Integration

### Files Modified
- **Scripts/api_endpoints.py**: Added new function `register_stock_activity_endpoints()` and registered it in `register_all_endpoints()`

### Files Using These Endpoints
- **Scripts/app.py**: Uses the endpoints via `register_all_endpoints()`
- **Scripts/app_improved.py**: Uses the endpoints via `register_all_endpoints()`

---

## Testing Recommendations

### Best Sellers Endpoint:
1. Test with valid date range and verify aggregation works correctly
2. Test with different pharmacy IDs
3. Test with various limit values
4. Verify sorting by quantity_sold descending

### Low GP Products Endpoint:
1. Test with various threshold values (e.g., 5, 10, 15, 20)
2. Test `exclude_pdst=true` to verify PDST/KSAA filtering
3. Verify only products with actual sales are returned
4. Verify sorting by gp_percent ascending
5. Test with edge cases (no products found, all products filtered out)

---

## Backwards Compatibility
✅ All existing endpoints remain unchanged
✅ New endpoints are added to the existing registration system
✅ No breaking changes to existing functionality

---

## Next Steps
1. Deploy the updated application
2. Test the endpoints with real data
3. Update frontend to consume these new endpoints for Monthly Summary tab
4. Monitor performance for large date ranges
