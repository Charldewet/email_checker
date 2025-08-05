import fitz  # PyMuPDF
import re
import pandas as pd

# Step 1: Load the PDF
doc = fitz.open("/mnt/data/20250716-11h36m16s-Complete.pdf")

# Step 2: Clean raw lines by removing headers, footers, and subtotal blocks
cleaned_lines = []
header_keywords = [
    "REITZ APTEEK", "PAGE:", "CODE", "DESCRIPTION", "ON HAND", 
    "SALES", "COST", "GROSS", "TURNOVER", "GP%", "QTY", "VALUE"
]
exclusion_keywords = ["MAIN-DEPT", "SUB-DEPT", "TOTAL", "-------"]

for page in doc:
    lines = page.get_text().split("\n")
    for line in lines:
        if any(keyword in line for keyword in header_keywords):
            continue
        if any(keyword in line for keyword in exclusion_keywords):
            continue
        if set(line.strip()) <= {"-", " "}:
            continue
        cleaned_lines.append(line.strip())

# Step 3: Define regex pattern to extract structured sales data
pattern = re.compile(
    r"^([A-Z0-9]{6})\s+([A-Z0-9\-]{4,})\s+(.*?)\s+"
    r"(-?\d+\.\d{3})\s+(-?\d+\.\d{3})\s+(-?\d+\.\d{2})\s+"
    r"(-?\d+\.\d{2})\s+(-?\d+\.\d{2})\s+(-?\d+\.\d{3})\s+(-?\d+\.\d{3})$"
)

# Step 4: Extract matched values
records = []
for line in cleaned_lines:
    match = pattern.match(line)
    if match:
        dept, stock_code, desc, on_hand, sales_qty, sales_val, sales_cost, gp_val, turnover_pct, gp_pct = match.groups()
        records.append({
            "DepartmentCode": dept.strip(),
            "StockCode": stock_code.strip(),
            "Description": desc.strip(),
            "OnHand": float(on_hand),
            "SalesQty": float(sales_qty),
            "SalesValue": float(sales_val),
            "SalesCost": float(sales_cost),
            "GrossProfit": float(gp_val),
            "TurnoverPercent": float(turnover_pct),
            "GrossProfitPercent": float(gp_pct)
        })

# Step 5: Convert to DataFrame and export
df = pd.DataFrame(records)
df.to_csv("/mnt/data/full_sales_breakdown.csv", index=False)