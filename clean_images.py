import os
from PIL import Image

def clean_directory(dir_path):
    removed = 0
    scanned = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(root, file)
                scanned += 1
                try:
                    with Image.open(path) as img:
                        img.verify()
                except Exception as e:
                    print(f"Removing corrupted image: {path} ({e})")
                    os.remove(path)
                    removed += 1
    print(f"Directory: {dir_path} | Scanned: {scanned} | Removed: {removed}")

if __name__ == "__main__":
    clean_directory(r"c:\Users\Achal Mahale KIBBCOM\.gemini\antigravity\playground\metallic-gemini\medical_ecg\datasets\augmented")
    clean_directory(r"c:\Users\Achal Mahale KIBBCOM\.gemini\antigravity\playground\metallic-gemini\medical_ecg\datasets\test")
