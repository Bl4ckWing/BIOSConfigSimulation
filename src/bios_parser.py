import re
import json
import os
import html

# --- PFAD KONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

INPUT_FILE = os.path.join(PROJECT_ROOT, 'data', '03_ifr_dumps', 'bios_dump.txt')
TEMPLATE_FILE = os.path.join(PROJECT_ROOT, 'templates', 'bios_template.html')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'bios_ui.html')
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config', 'bios_data.json')

class IfrDumpParser:
    """
    Ein zustandsbehafteter Parser für IFR Text Dumps.
    Reduziert Komplexität durch Aufteilung in Handler-Methoden.
    """
    def __init__(self):
        self.forms = {}
        self.current_form_id = None
        self.referenced_forms = set()
        self._compile_regex()

    def _compile_regex(self):
        # Optimierte Regex (Keine Reluctant Quantifiers mehr wo möglich)
        
        # Form: "0x1234 Form: Title (0x1)"
        # [^\(]+  -> Nimm alles bis zur ersten Klammer (Greedy, aber sicher)
        self.re_form = re.compile(r"^\s*(0x[\da-fA-F]+)\s+Form:\s+([^\(\r\n]+)\s+\((0x[\da-fA-F]+)\)")
        
        # Ref: "Ref: Label ... FormId: 0x12"
        # Hier müssen wir etwas flexibel bleiben, aber wir ankern an "FormId:"
        self.re_ref = re.compile(r"Ref:\s+(.+?)\s+.*FormId:\s+(0x[\da-fA-F]+)")
        
        # OneOf: "OneOf: Label , Variable: 0x12"
        # [^,]+ -> Nimm alles bis zum ersten Komma
        self.re_oneof = re.compile(r"OneOf:\s+([^,]+)\s*,.*Variable:\s+(0x[\da-fA-F]+)")
        
        # Option: "Option: Label , Value: 0x12"
        self.re_option = re.compile(r"Option:\s+([^,]+)\s*,.*Value:\s+(0x[\da-fA-F]+)")
        
        # CheckBox: "CheckBox: Label , Variable: 0x12"
        self.re_checkbox = re.compile(r"CheckBox:\s+([^,]+)\s*,.*Variable:\s+(0x[\da-fA-F]+)")
        
        # Text
        self.re_text = re.compile(r"(?:Subtitle:\s+Statement.Prompt:|Text:)\s+([^,\r\n]+)(?:,|$)")

    def parse(self, filename):
        if not os.path.exists(filename):
            print(f"KRITISCHER FEHLER: Datei nicht gefunden: {filename}")
            return {}, []

        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                self._process_line(line.strip())

        return self._build_hierarchy()

    def _process_line(self, line):
        """Entscheidet, welcher Handler für die Zeile zuständig ist."""
        if not line:
            return

        # Reihenfolge wichtig: Erst Form Check, dann Items
        if self._handle_form(line): return
        
        # Nur weitermachen, wenn wir in einer Form sind
        if not self.current_form_id: return

        if self._handle_ref(line): return
        if self._handle_oneof(line): return
        if self._handle_checkbox(line): return
        if self._handle_option(line): return
        if self._handle_text(line): return

    def _handle_form(self, line):
        m = self.re_form.search(line)
        if m:
            _, title, form_id = m.groups()
            self.current_form_id = form_id
            self.forms[form_id] = {
                "id": form_id,
                "title": title.strip(),
                "items": []
            }
            return True
        return False

    def _handle_ref(self, line):
        m = self.re_ref.search(line)
        if m:
            label, target_id = m.groups()
            self.referenced_forms.add(target_id)
            self._add_item({
                "type": "submenu",
                "label": label.strip(),
                "target": target_id
            })
            return True
        return False

    def _handle_oneof(self, line):
        m = self.re_oneof.search(line)
        if m:
            label, var_id = m.groups()
            self._add_item({
                "type": "select",
                "label": label.strip(),
                "id": var_id,
                "value": "Select...", 
                "options": []
            })
            return True
        return False

    def _handle_checkbox(self, line):
        m = self.re_checkbox.search(line)
        if m:
            label, var_id = m.groups()
            self._add_item({
                "type": "select",
                "label": label.strip(),
                "id": var_id,
                "value": "Disabled",
                "options": ["Disabled", "Enabled"]
            })
            return True
        return False

    def _handle_option(self, line):
        # Optionen gehören zum letzten Item, wenn es ein Select ist
        items = self.forms[self.current_form_id]["items"]
        if not items: return False
        
        m = self.re_option.search(line)
        if m:
            last = items[-1]
            if last["type"] == "select":
                opt_lbl, _ = m.groups()
                clean_lbl = opt_lbl.strip()
                last["options"].append(clean_lbl)
                # Default Value setzen
                if last["value"] == "Select...":
                    last["value"] = clean_lbl
            return True
        return False

    def _handle_text(self, line):
        m = self.re_text.search(line)
        if m:
            txt = m.group(1).strip()
            if txt:
                self._add_item({"type": "text", "label": txt})
            return True
        return False

    def _add_item(self, item):
        self.forms[self.current_form_id]["items"].append(item)

    def _build_hierarchy(self):
        """Bestimmt Root-Tabs basierend auf Referenzen."""
        # Alles was NICHT referenziert wurde, ist ein Root-Element
        root_ids = [fid for fid in self.forms if fid not in self.referenced_forms]
        root_ids.sort(key=lambda x: int(x, 16))

        real_tabs = []
        # Fallunterscheidung: Wrapper Setup Form?
        if len(root_ids) == 1:
            setup_id = root_ids[0]
            # Wenn nur 1 Root da ist, nehmen wir dessen Kinder als Tabs
            for item in self.forms[setup_id]["items"]:
                if item["type"] == "submenu" and item["target"] in self.forms:
                    real_tabs.append(self.forms[item["target"]])
        else:
            for rid in root_ids:
                real_tabs.append(self.forms[rid])
        
        return self.forms, real_tabs


def generate_html(all_forms, root_tabs):
    nav_html = ""
    for idx, tab in enumerate(root_tabs):
        active = " active" if idx == 0 else ""
        nav_html += f'<div class="nav-item{active}" data-target="view_{tab["id"]}">{html.escape(tab["title"])}</div>'

    views_html = ""
    for form_id, form in all_forms.items():
        rows_html = ""
        for item in form["items"]:
            lbl = html.escape(item["label"])
            
            if item["type"] == "submenu":
                target = item["target"]
                rows_html += f'''
                <div class="menu-row" data-type="submenu" data-target="view_{target}" data-help="Enter Submenu">
                    <span class="item-label">{lbl}</span>
                    <span class="item-value">►</span>
                </div>'''
            
            elif item["type"] == "select":
                val = html.escape(item["value"])
                opts = json.dumps(item["options"]).replace('"', '&quot;')
                item_id = item["id"]
                rows_html += f'''
                <div class="menu-row" data-type="select" data-id="{item_id}" data-options="{opts}" data-help="Change Option">
                    <span class="item-label">{lbl}</span>
                    <span class="item-value" style="color:var(--text-color);">{val}</span>
                </div>'''
                
            elif item["type"] == "text":
                rows_html += f'''
                <div class="menu-row" style="color: yellow; pointer-events:none;">
                    <span class="item-label">{lbl}</span>
                    <span class="item-value"></span>
                </div>'''

        views_html += f'''
        <div id="view_{form_id}" class="view-section">
            <div class="col-items">{rows_html}</div>
            <div class="col-help">
                <div style="font-weight:bold; border-bottom:1px solid #fff; margin-bottom:5px;">{html.escape(form["title"])}</div>
                <div>Select an item to configure.</div>
            </div>
        </div>
        '''
        
    return nav_html, views_html

def ensure_directories():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

def main():
    print("--- BIOS PARSER V2 (Clean) ---")
    ensure_directories()
    
    print(f"Lese Input: {INPUT_FILE}")
    parser = IfrDumpParser()
    all_forms, root_tabs = parser.parse(INPUT_FILE)
    
    if not root_tabs:
        print("ABBRUCH: Keine Tabs gefunden.")
        return

    print(f"Hierarchie: {len(root_tabs)} Tabs, {len(all_forms)} Forms.")
    
    nav_html, views_html = generate_html(all_forms, root_tabs)
    
    # JSON Config speichern
    js_data = {"tabs": list(all_forms.values())}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(js_data, indent=2))
    print(f"Config OK: {CONFIG_FILE}")

    # HTML generieren
    if not os.path.exists(TEMPLATE_FILE):
        print("FEHLER: Template fehlt.")
        return

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    final_html = template.replace("{TITLE}", "BIOS SETUP UTILITY") \
                         .replace("{NAV_TABS}", nav_html) \
                         .replace("{TAB_CONTENT}", views_html) \
                         .replace("{FOOTER}", "v02.61 American Megatrends - F10: Save  ESC: Back") \
                         .replace("{THEME_CSS}", "") \
                         .replace("{JSON_DATA}", json.dumps(js_data))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"HTML OK: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()