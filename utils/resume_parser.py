"""
Module untuk parsing PDF resume
"""
import pdfplumber
import re

def extract_text_from_pdf(pdf_file) -> str:
    """
    Ekstrak teks dari file PDF
    
    Args:
        pdf_file: File object dari Streamlit file uploader
        
    Returns:
        String berisi seluruh teks dari PDF
    """
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise Exception(f"Gagal membaca PDF: {str(e)}")
    
    return text.strip()

def extract_email_from_text(text: str) -> str:
    """
    Ekstrak email dari teks menggunakan regex (fallback jika AI gagal)
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else ""

def extract_name_from_text(text: str) -> str:
    """
    Ekstrak nama dari teks (fallback sederhana)
    Biasanya nama ada di baris pertama atau kedua
    """
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        # Filter: nama biasanya 2-4 kata, tanpa angka
        if len(line.split()) in [2, 3, 4] and not re.search(r'\d', line):
            if len(line) < 50 and len(line) > 3:
                return line
    return "Tidak terdeteksi"