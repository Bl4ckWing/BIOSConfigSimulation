import re
import json
import sys
import os

def clean_label(text):
    """Entfernt ANSI Farbcodes, Hex-Endungen und Whitespace."""
    # Entferne ANSI Codes wie \x1b[;44;m
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    # Entferne geschweifte Klammern am Ende {02 87...}
    text = re.sub(r'\s*\{.*\}$', '', text)
    # Entferne "Statement" Präfix falls vorhanden
    text = text.replace("Statement {", "").replace("}", "")
    return text.strip()

def parse_ifr_dump(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Wir bauen eine einfache Struktur.
    # Da IFR sehr komplex verschachtelt ist, vereinfachen wir es für die Simulation:
    # Alles was "Form" auf Level 0 ist, wird ein TAB.
    # Alles darunter sind Items.
    
    tabs = []
    current_tab = None
    current_item = None # Das Item, zu dem wir gerade Optionen hinzufügen (bei OneOf/Setting)
    
    # Stack für Verschachtelung (wird hier vereinfacht genutzt)
    # Wir nutzen Einrückung (Tabs) um zu wissen, wo wir sind? 
    # Nein, IFR ist oft flach oder nutzt "End" Tags. Wir nutzen eine einfache State-Machine.

    # Regex Pattern
    re_form = re.compile(r'^\s*0x[\dA-F]+\s+Form:\s+(.+?),')
    re_subtitle = re.compile(r'^\s*0x[\dA-F]+\s+Subtitle:\s+(.+)')
    re_text = re.compile(r'^\s*0x[\dA-F]+\s+Text:\s+(.+)')
    
    # "Setting" oder "OneOf" sind Auswahlmenüs
    re_setting = re.compile(r'^\s*0x[\dA-F]+\s+(?:Setting|OneOf):\s+(.+?),') 
    
    # Optionen
    re_option = re.compile(r'^\s*0x[\dA-F]+\s+(?:OneOfOption|Option):\s+(.+?),')
    
    # End Tags
    re_end_options = re.compile(r'^\s*0x[\dA-F]+\s+End of Options')

    print(f"Lese {len(lines)} Zeilen...")

    for line in lines:
        line = line.strip()
        if not line.startswith("0x"): continue # Überspringe leere Zeilen/Header

        # 1. FORM (Neuer Tab)
        match_form = re_form.match(line)
        if match_form:
            label = clean_label(match_form.group(1))
            # Erstelle neuen Tab
            current_tab = {
                "name": label,
                "items": []
            }
            tabs.append(current_tab)
            current_item = None # Reset
            continue

        # Wenn wir noch keinen Tab haben, überspringen wir den Rest (Header-Kram)
        if not current_tab:
            continue

        # 2. SUBTITLE (Als Text-Item oder Separator)
        match_sub = re_subtitel = re_subtitle.match(line)
        if match_sub:
            label = clean_label(match_sub.group(1))
            if not label: continue # Leere Subtitles überspringen
            item = {
                "type": "text",
                "label": f"--- {label} ---",
                "value": ""
            }
            current_tab["items"].append(item)
            current_item = None
            continue

        # 3. TEXT (Reine Info)
        match_text = re_text.match(line)
        if match_text:
            label = clean_label(match_text.group(1))
            # Oft steht Text: Label { ... }, wir tun so als wäre es ein Item
            item = {
                "type": "item", # "item" statt "text" damit es anwählbar aussieht (oder "text" für read-only)
                "label": label,
                "value": "[Info]"
            }
            current_tab["items"].append(item)
            current_item = None
            continue

        # 4. SETTING / ONE_OF (Das Dropdown)
        match_set = re_setting.match(line)
        if match_set:
            label = clean_label(match_set.group(1))
            new_item = {
                "type": "item",
                "label": label,
                "value": "Select...", # Platzhalter, wird oft durch erste Option ersetzt
                "options": []
            }
            current_tab["items"].append(new_item)
            current_item = new_item # Wir merken uns dieses Item, um Optionen hinzuzufügen
            continue

        # 5. OPTION (Gehört zum aktuellen Setting)
        if current_item is not None:
            match_opt = re_option.match(line)
            if match_opt:
                opt_label = clean_label(match_opt.group(1))
                current_item["options"].append(opt_label)
                # Setze den ersten Wert als Default, falls noch keiner da ist
                if current_item["value"] == "Select...":
                    current_item["value"] = opt_label
                continue
            
            # Ende der Optionen
            if re_end_options.match(line):
                current_item = None
                continue

    return tabs

def main():
    if len(sys.argv) < 2:
        print("Benutzung: python src/import_ifr.py <pfad_zu_ifr_txt>")
        print("Beispiel:  python src/import_ifr.py bios_dump.txt")
        return

    input_file = sys.argv[1]
    output_file = os.path.join("config", "imported_bios.json")

    print(f"Starte Import von: {input_file}")
    
    parsed_tabs = parse_ifr_dump(input_file)
    
    if not parsed_tabs:
        print("WARNUNG: Keine Forms gefunden! Ist das Format korrekt?")
        # Fallback: Erstelle einen Dummy-Tab, falls nur Items gefunden wurden
        return

    # Baue das finale JSON Config Objekt
    bios_config = {
        "title": "IMPORTED BIOS SETUP",
        "theme": "ami_grey", # AMI passt meistens besser zu IFR Dumps
        "tabs": parsed_tabs,
        "footer_text": "v02.61 (C)Copyright 1985-202x, American Megatrends, Inc."
    }

    # Speichern
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bios_config, f, indent=2)

    print(f"\nERFOLG! Config erstellt: {output_file}")
    print(f"Jetzt ausführen: python src/main.py imported_bios.json")

if __name__ == "__main__":
    main()