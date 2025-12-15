import os
import subprocess
import sys

# --- PFADE ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, 'tools')

IFR_EXE = os.path.join(TOOLS_DIR, "Universal IFR Extractor.exe")

EXTRACTED_DIR = os.path.join(BASE_DIR, 'data', '02_extracted')
TXT_DIR = os.path.join(BASE_DIR, 'data', '03_ifr_dumps')
PY_SRC = os.path.join(BASE_DIR, 'src')

def run_step(command_list, step_name):
    """Führt einen Befehl in der Konsole aus."""
    print(f"\n--- Schritt: {step_name} ---")
    try:
        subprocess.run(command_list, check=True, text=True)
        print("✅ OK")
    except subprocess.CalledProcessError as process_error:
        # Variable 'e' -> 'process_error' umbenannt
        print(f"❌ FEHLER in {step_name}:")
        print(f"   Return Code: {process_error.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ TOOL NICHT GEFUNDEN: {command_list[0]}")
        print("   Bitte führe zuerst 'python tools/setup_tools.py' aus!")
        sys.exit(1)

def main():
    # 1. Check Setup.bin
    setup_bin = os.path.join(EXTRACTED_DIR, 'setup.bin')
    if not os.path.exists(setup_bin):
        print(f"⚠️ FEHLER: Keine Datei gefunden unter: {setup_bin}")
        print("   Bitte extrahiere erst die 'Setup' Sektion mit UEFITool manuell!")
        return

    ifr_txt = os.path.join(TXT_DIR, 'bios_dump.txt')
    os.makedirs(TXT_DIR, exist_ok=True)

    # 2. IFR Extractor
    print("Start IFR Extractor...")
    run_step([IFR_EXE, setup_bin, ifr_txt], "IFR Extraction")

    # 3. Import (Text -> JSON)
    run_step([sys.executable, os.path.join(PY_SRC, 'import_ifr.py'), 'bios_dump.txt'], "Text Import")

    # 4. Generator (JSON -> HTML)
    run_step([sys.executable, os.path.join(PY_SRC, 'main.py'), 'bios_dump.json'], "HTML Generation")

    print("\n🎉 PIPELINE ERFOLGREICH! 🎉")
    print("Datei erstellt: output/bios_dump.html")

if __name__ == "__main__":
    main()