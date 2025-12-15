import re
import json
import sys
import os
import uuid

# --- PFADE KONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, 'data', '03_ifr_dumps')
OUTPUT_DIR = os.path.join(BASE_DIR, 'config', 'input')

def clean_label(text):
    text = re.sub(r'\x1b\[[0-9;]*m', '', text) # ANSI Farben weg
    text = re.sub(r'\s*\{.*\}$', '', text)     # {Hex} weg
    text = text.replace("Statement {", "").replace("}", "")
    return text.strip()

def parse_ifr_dump(file_path):
    print(f"Lese Datei: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"FEHLER: Datei nicht gefunden: {file_path}")
        return []

    tabs = []
    current_tab = None
    current_item = None
    
    re_form = re.compile(r'^\s*0x[\dA-F]+\s+Form:\s+(.+?),')
    re_subtitle = re.compile(r'^\s*0x[\dA-F]+\s+Subtitle:\s+(.+)')
    re_text = re.compile(r'^\s*0x[\dA-F]+\s+Text:\s+(.+)')
    re_setting = re.compile(r'^\s*0x[\dA-F]+\s+(?:Setting|OneOf):\s+(.+?),') 
    re_option = re.compile(r'^\s*0x[\dA-F]+\s+(?:OneOfOption|Option):\s+(.+?),')
    re_end_options = re.compile(r'^\s*0x[\dA-F]+\s+End of Options')

    for line in lines:
        line = line.strip()
        if not line.startswith("0x"): continue

        # 1. FORM (Tab)
        match_form = re_form.match(line)
        if match_form:
            label = clean_label(match_form.group(1))
            current_tab = { "name": label, "items": [] }
            tabs.append(current_tab)
            current_item = None
            continue

        if not current_tab: continue

        # 2. SUBTITLE
        match_sub = re_subtitle.match(line)
        if match_sub:
            label = clean_label(match_sub.group(1))
            if label:
                item = { "type": "text", "label": f"--- {label} ---", "value": "" }
                current_tab["items"].append(item)
            current_item = None
            continue

        # 3. TEXT
        match_text = re_text.match(line)
        if match_text:
            label = clean_label(match_text.group(1))
            item = { "type": "item", "label": label, "value": "[Info]" }
            current_tab["items"].append(item)
            current_item = None
            continue

        # 4. SETTING
        match_set = re_setting.match(line)
        if match_set:
            label = clean_label(match_set.group(1))
            new_item = {
                "id": f"item-{uuid.uuid4().hex[:8]}", # Generiere ID direkt hier!
                "type": "item",
                "label": label,
                "value": "Select...",
                "options": []
            }
            current_tab["items"].append(new_item)
            current_item = new_item
            continue

        # 5. OPTIONS
        if current_item is not None:
            match_opt = re_option.match(line)
            if match_opt:
                opt_label = clean_label(match_opt.group(1))
                current_item["options"].append(opt_label)
                if current_item["value"] == "Select...":
                    current_item["value"] = opt_label
                continue
            
            if re_end_options.match(line):
                current_item = None
                continue

    return tabs

def main():
    if len(sys.argv) < 2:
        print("Benutzung: python src/import_ifr.py <dateiname.txt>")
        print(f"Hinweis: Die Datei muss in '{INPUT_DIR}' liegen.")
        return

    filename = sys.argv[1]
    input_path = os.path.join(INPUT_DIR, filename)
    
    # Check ob der User den vollen Pfad oder nur den Namen angegeben hat
    if not os.path.exists(input_path) and os.path.exists(filename):
        input_path = filename # Fallback für absoluten Pfad
    
    output_filename = os.path.splitext(os.path.basename(filename))[0] + ".json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    parsed_tabs = parse_ifr_dump(input_path)
    
    if not parsed_tabs:
        print("Keine Daten extrahiert.")
        return

    bios_config = {
        "title": "IMPORTED BIOS SETUP",
        "theme": "ami_grey",
        "tabs": parsed_tabs,
        "footer_text": "Auto-Imported from IFR Dump"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bios_config, f, indent=2)

    print(f"ERFOLG! JSON gespeichert in: {output_path}")

if __name__ == "__main__":
    main()