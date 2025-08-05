import fitz  # PyMuPDF
from pathlib import Path

def examine_trading_summary():
    """
    Examine the content of a trading summary report to understand its structure
    """
    # Path to a trading summary PDF
    pdf_path = Path("../temp_classified_pdfs/2025-08-04/REITZ/trading_summary_20250805-09h51m22s-Complete.pdf")
    
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return
    
    # Open and extract text
    doc = fitz.open(str(pdf_path))
    
    print("=== TRADING SUMMARY CONTENT ===")
    print(f"Number of pages: {len(doc)}")
    print("\n" + "="*60)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n--- PAGE {page_num + 1} ---")
        print(text)
        print("-" * 40)
    
    doc.close()

if __name__ == "__main__":
    examine_trading_summary() 