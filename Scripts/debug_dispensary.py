import fitz  # PyMuPDF
from pathlib import Path

def debug_dispensary_pdf(pdf_path: str):
    """Debug function to examine PDF content"""
    print(f"=== DEBUGGING: {pdf_path} ===")
    
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    
    print("=== FULL TEXT CONTENT ===")
    print(text)
    print("=== END OF TEXT ===")
    
    doc.close()

if __name__ == "__main__":
    # Debug the REITZ dispensary summary
    pdf_path = "../temp_classified_pdfs/2025-08-04/REITZ/dispensary_summary_20250805-10h07m09s-Complete.pdf"
    debug_dispensary_pdf(pdf_path) 