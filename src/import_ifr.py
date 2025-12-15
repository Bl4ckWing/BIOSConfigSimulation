import re
import json
import sys
import os
import uuid

# --- PFADE KONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, 'data', '03_ifr_dumps')
OUTPUT_DIR = os.path.join(BASE_DIR, 'config', 'input')

class IfrParser:
    """
    Ein Parser für IFR Text Dumps.
    Nutzt eine Dispatcher-Liste, um Cyclomatic Complexity zu minimieren.
    """
    def __init__(self):
        self.tabs = []
        self.current_tab = None
        self.current_item = None
        
        # Regex Patterns
        self.re_form = re.compile(r'^\s*0x[\dA-F]+\s+Form:\s+(.+?),')
        self.re_subtitle = re.compile(r'^\s*0x[\dA-F]+\s+Subtitle:\s+(.+)')
        self.re_text = re.compile(r'^\s*0x[\dA-F]+\s+Text:\s+(.+)')
        self.re_setting = re.compile(r'^\s*0x[\dA-F]+\s+(?:Setting|OneOf):\s+(.+?),') 
        self.re_option = re.compile(r'^\s*0x[\dA-F]+\s+(?:OneOfOption|Option):\s+(.+?),')
        self.re_end_options = re.compile(r'^\s*0x[\dA-F]+\s+End of Options')

    def clean_label(self, text):
        """Bereinigt Strings von ANSI-Codes und Metadaten."""
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        text = re.sub(r'\s*\{.*\}$', '', text)
        text = text.replace("Statement {", "").replace("}", "")
        return text.strip()

    def parse_file(self, file_path):
        """Hauptmethode: Liest Datei und delegiert Zeilenverarbeitung."""
        print(f"Lese Datei: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"❌ FEHLER: Datei nicht gefunden: {file_path}")
            return []

        for line in lines:
            self._process_line(line.strip())

        return self.tabs

    def _process_line(self, line):
        """Entscheidet, welcher Handler für die Zeile zuständig ist."""
        if not line.startswith("0x"): 
            return

        # 1. Level: Neue Tabs (Forms) haben Vorrang
        if self._handle_form(line): 
            return
        
        # 2. Level: Inhalt (nur wenn wir in einem Tab sind)
        if not self.current_tab: 
            return

        # Dispatcher-Liste: Wir probieren alle Handler der Reihe nach
        # Das eliminiert die vielen if-Statements für SonarQube
        item_handlers = [
            self._handle_subtitle,
            self._handle_text,
            self._handle_setting,
            self._handle_options
        ]

        for handler in item_handlers:
            if handler(line):
                return

    # --- HANDLER METHODEN ---

    def _handle_form(self, line):
        match = self.re_form.match(line)
        if match:
            label = self.clean_label(match.group(1))
            self.current_tab = { "name": label, "items": [] }
            self.tabs.append(self.current_tab)
            self.current_item = None
            return True
        return False

    def _handle_subtitle(self, line):
        match = self.re_subtitle.match(line)
        if match:
            label = self.clean_label(match.group(1))
            if label:
                self._add_item("text", f"--- {label} ---", "")
            self.current_item = None
            return True
        return False

    def _handle_text(self, line):
        match = self.re_text.match(line)
        if match:
            label = self.clean_label(match.group(1))
            self._add_item("item", label, "[Info]")
            self.current_item = None
            return True
        return False

    def _handle_setting(self, line):
        match = self.re_setting.match(line)
        if match:
            label = self.clean_label(match.group(1))
            new_item = self._add_item("item", label, "Select...")
            new_item["options"] = []
            new_item["id"] = f"item-{uuid.uuid4().hex[:8]}"
            self.current_item = new_item
            return True
        return False

    def _handle_options(self, line):
        if self.current_item is None:
            return False

        match_opt = self.re_option.match(line)
        if match_opt:
            opt_label = self.clean_label(match_opt.group(1))
            self.current_item["options"].append(opt_label)
            # Default setzen
            if self.current_item["value"] == "Select...":
                self.current_item["value"] = opt_label
            return True
        
        if self.re_end_options.match(line):
            self.current_item = None
            return True

        return False

    def _add_item(self, type_name, label, value):
        """Hilfsmethode um Redundanz beim Hinzufügen zu vermeiden."""
        item = {"type": type_name, "label": label, "value": value}
        self.current_tab["items"].append(item)
        return item

def main():
    if len(sys.argv) < 2:
        print("Benutzung: python src/import_ifr.py <dateiname.txt>")
        print(f"Hinweis: Die Datei muss in '{INPUT_DIR}' liegen.")
        return

    filename = sys.argv[1]
    input_path = os.path.join(INPUT_DIR, filename)
    
    if not os.path.exists(input_path) and os.path.exists(filename):
        input_path = filename 
    
    output_filename = os.path.splitext(os.path.basename(filename))[0] + ".json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    parser = IfrParser()
    parsed_tabs = parser.parse_file(input_path)
    
    if not parsed_tabs:
        print("⚠️ Keine Daten extrahiert.")
        return

    bios_config = {
        "title": "IMPORTED BIOS SETUP",
        "theme": "ami_grey",
        "tabs": parsed_tabs,
        "footer_text": "Auto-Imported from IFR Dump"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bios_config, f, indent=2)

    print(f"✅ ERFOLG! JSON gespeichert in: {output_path}")

if __name__ == "__main__":
    main()