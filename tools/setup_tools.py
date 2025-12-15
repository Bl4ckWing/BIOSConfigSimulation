import os
import urllib.request
import zipfile
import shutil
import sys

# --- KONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOOLS = {
    "UEFITool": {
        "url": "https://github.com/LongSoft/UEFITool/releases/download/0.28.0/UEFITool_0.28.0_win32.zip",
        "zip_name": "UEFITool.zip",
        "exe_name": "UEFITool.exe"
    },
    "IFRExtractor": {
        "url": "https://github.com/donovan6000/Universal-IFR-Extractor/releases/download/v0.3.6/Universal_IFR_Extractor_v0.3.6_Windows.zip",
        "zip_name": "IFRExtractor.zip",
        "exe_name": "Universal IFR Extractor.exe"
    }
}

def download_file(url, filepath):
    print(f"⬇️ Lade herunter: {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        print("   ✅ Download fertig.")
    except Exception as download_error:
        # Variable 'e' -> 'download_error' umbenannt
        print(f"   ❌ Fehler beim Download: {download_error}")
        sys.exit(1)

def extract_exe(zip_path, exe_name, target_folder):
    print(f"📦 Entpacke {exe_name}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            found = False
            for file_in_zip in zip_ref.namelist():
                if file_in_zip.endswith(exe_name):
                    source = zip_ref.open(file_in_zip)
                    target_path = os.path.join(target_folder, exe_name)
                    with open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                    found = True
                    break
            
            if not found:
                print(f"   ⚠️ Konnte {exe_name} nicht im Zip finden!")
                print(f"   Inhalt des Zips: {zip_ref.namelist()}")
            else:
                print(f"   ✅ Entpackt nach: {target_path}")
                
    except zipfile.BadZipFile:
        print("   ❌ Fehler: Die Datei ist kein gültiges ZIP.")
    except Exception as zip_error:
        # Auch hier: sprechender Name statt 'e'
        print(f"   ❌ Entpacken fehlgeschlagen: {zip_error}")

def main():
    print("--- 🛠️ SETUP EXTERNAL TOOLS ---")
    
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    for tool_name, config in TOOLS.items():
        zip_path = os.path.join(BASE_DIR, config["zip_name"])
        exe_path = os.path.join(BASE_DIR, config["exe_name"])
        
        if os.path.exists(exe_path):
            print(f"👍 {tool_name} ist bereits installiert.")
            continue
            
        download_file(config["url"], zip_path)
        extract_exe(zip_path, config["exe_name"], BASE_DIR)
        
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    print("\n✅ Alle Tools bereit im 'tools/' Ordner!")

if __name__ == "__main__":
    main()