import fitz  # PyMuPDF

# Define keywords for each report type
REPORT_KEYWORDS = {
    "turnover_summary": ["TOTAL TURNOVER", "GP %", "BASKET VALUE", "TRANSACTIONS"],
    "gross_profit_report": ["GROSS PROFIT", "STOCK CODE", "SALES QTY", "DEPT"],
    "department_listing": ["DEPT CODE LISTING", "PROM DISC", "ALLOC TAX ID"],
    "trading_summary": ["OPENING STOCK", "CLOSING STOCK", "PURCHASES", "ADJUSTMENTS"]
}

def classify_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    
    # Extract text from the first 2 pages
    for i in range(min(2, len(doc))):
        text += doc[i].get_text().upper()

    # Determine report type by keyword matches
    scores = {}
    for report_type, keywords in REPORT_KEYWORDS.items():
        scores[report_type] = sum(1 for kw in keywords if kw in text)

    # Get report type with highest score
    best_match = max(scores, key=scores.get)
    if scores[best_match] == 0:
        return "unknown"
    
    return best_match

# Example usage:
if __name__ == "__main__":
    path = "example.pdf"  # Replace with dynamic path
    report_type = classify_pdf(path)
    print(f"Detected report type: {report_type}")
