import zipfile
import os
import re

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def safe_extract_zip(zip_path, extract_to):
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for info in zf.infolist():
            # Splitting by generic slash
            parts = info.filename.replace('\\', '/').split('/')
            
            # Clean parts: remove leading/trailing spaces, replace invalid chars
            clean_parts = []
            for p in parts:
                cp = sanitize_filename(p).strip()
                if cp:
                    clean_parts.append(cp)
                    
            if not clean_parts:
                continue
                
            out_path = os.path.join(extract_to, *clean_parts)
            
            if info.is_dir() or info.filename.endswith('/'):
                os.makedirs(out_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                try:
                    with zf.open(info) as f_in:
                        with open(out_path, 'wb') as f_out:
                            f_out.write(f_in.read())
                except Exception as e:
                    print(f"Skipped {info.filename}: {e}")

safe_extract_zip(r"C:\Users\Achal Mahale KIBBCOM\Downloads\Phone Link\augmented.zip", r"c:\Users\Achal Mahale KIBBCOM\.gemini\antigravity\playground\metallic-gemini\medical_ecg\datasets\augmented")
