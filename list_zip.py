import zipfile
import sys

def list_zip(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            names = zip_ref.namelist()
            print(f"Total files in zip: {len(names)}")
            print("First 20 files:")
            for n in names[:20]:
                print(n)
            print("Last 20 files:")
            for n in names[-20:]:
                print(n)
    except Exception as e:
        print(f"Error reading zip: {e}")

if __name__ == "__main__":
    list_zip(sys.argv[1])
