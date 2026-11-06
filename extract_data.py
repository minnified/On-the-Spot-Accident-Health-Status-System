import os
import zipfile
from pypdf import PdfReader

def extract_pdf(pdf_path, out_txt):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Successfully extracted PDF to {out_txt}")
    except Exception as e:
        print(f"Error extracting PDF: {e}")

def unzip_file(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Successfully extracted {zip_path} to {extract_to}")
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")

if __name__ == "__main__":
    pdf_path = r"C:\Users\Achal Mahale KIBBCOM\Downloads\Phone Link\8th sem phase 0.pdf"
    out_txt = r"c:\Users\Achal Mahale KIBBCOM\.gemini\antigravity\playground\metallic-gemini\medical_ecg\project_presentation.txt"
    extract_pdf(pdf_path, out_txt)

    aug_zip = r"C:\Users\Achal Mahale KIBBCOM\Downloads\Phone Link\augmented.zip"
    test_zip = r"C:\Users\Achal Mahale KIBBCOM\Downloads\Phone Link\test.zip"
    
    aug_out = r"c:\Users\Achal Mahale KIBBCOM\.gemini\antigravity\playground\metallic-gemini\medical_ecg\datasets\augmented"
    test_out = r"c:\Users\Achal Mahale KIBBCOM\.gemini\antigravity\playground\metallic-gemini\medical_ecg\datasets\test"
    
    unzip_file(aug_zip, aug_out)
    unzip_file(test_zip, test_out)
