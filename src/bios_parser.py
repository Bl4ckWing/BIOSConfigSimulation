import re
import json
import os
import html

# --- PFAD KONFIGURATION (Automatisch) ---
# Bestimmt den Pfad, in dem dieses Skript liegt (/src)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Geht eine Ebene höher zum Projekt-Root
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Absolute Pfade zusammenbauen
INPUT_FILE = os.path.join(PROJECT_ROOT, 'input', 'bios_dump.txt')
TEMPLATE_FILE = os.path.join(PROJECT_ROOT, 'templates', 'bios_template.html')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'bios_ui.html')
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config', 'bios_data.json')

def ensure_directories():
    """Stellt sicher, dass Output- und Config-Ordner existieren."""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

def parse_dump(filename):
    """Liest den Dump und erstellt eine hierarchische Struktur."""
    if not os.path.exists(filename):
        print(f"KRITISCHER FEHLER: Input-Datei nicht gefunden:\n -> {filename}")
        return {}, []

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    forms = {}
    current_form_id = None
    referenced_forms = set() 

    # --- REGEX ---
    re_form = re.compile(r"^\s*(0x[0-9A-F]+)\s+Form:\s+(.+?)\s+\((0x[0-9A-F]+)\)")
    re_ref = re.compile(r"Ref:\s+(.+?)\s+.*FormId:\s+(0x[0-9A-F]+)")
    re_oneof = re.compile(r"OneOf:\s+(.+?)\s+.*Variable:\s+(0x[0-9A-F]+)")
    re_option = re.compile(r"Option:\s+(.+?)\s+,\s+Value:\s+(0x[0-9A-F]+)")
    re_checkbox = re.compile(r"CheckBox:\s+(.+?)\s+.*Variable:\s+(0x[0-9A-F]+)")
    re_text = re.compile(r"Subtitle:\s+Statement.Prompt:\s+(.+?)(?:,|$)|Text:\s+(.+?)(?:,|$)")

    # 1. Parsing Durchlauf
    for line in lines:
        line = line.strip()
        
        m_form = re_form.search(line)
        if m_form:
            _, title, form_id = m_form.groups()
            current_form_id = form_id
            forms[form_id] = {
                "id": form_id,
                "title": title.strip(),
                "items": []
            }
            continue

        if not current_form_id: continue

        items = forms[current_form_id]["items"]

        # Submenü Link
        m_ref = re_ref.search(line)
        if m_ref:
            label, target_id = m_ref.groups()
            referenced_forms.add(target_id)
            items.append({"type": "submenu", "label": label.strip(), "target": target_id})
            continue

        # Select / OneOf
        m_oneof = re_oneof.search(line)
        if m_oneof:
            label, var_id = m_oneof.groups()
            items.append({"type": "select", "label": label.strip(), "id": var_id, "value": "Select...", "options": []})
            continue

        # Optionen
        m_opt = re_option.search(line)
        if m_opt and items:
            last = items[-1]
            if last["type"] == "select":
                opt_lbl, _ = m_opt.groups()
                last["options"].append(opt_lbl.strip())
                if last["value"] == "Select...": last["value"] = opt_lbl.strip()
            continue

        # Checkbox
        m_chk = re_checkbox.search(line)
        if m_chk:
            label, var_id = m_chk.groups()
            items.append({"type": "select", "label": label.strip(), "id": var_id, "value": "Disabled", "options": ["Disabled", "Enabled"]})
            continue
            
        # Text Label
        m_txt = re_text.search(line)
        if m_txt:
            txt = next((g for g in m_txt.groups() if g is not None), "")
            if txt.strip():
                items.append({"type": "text", "label": txt.strip()})

    # 2. Hierarchie
    root_ids = [fid for fid in forms if fid not in referenced_forms]
    root_ids.sort(key=lambda x: int(x, 16))

    # Setup-Wrapper auflösen, falls vorhanden
    real_tabs = []
    if len(root_ids) == 1:
        setup_id = root_ids[0]
        for item in forms[setup_id]["items"]:
            if item["type"] == "submenu" and item["target"] in forms:
                real_tabs.append(forms[item["target"]])
    else:
        for rid in root_ids:
            real_tabs.append(forms[rid])

    return forms, real_tabs

def build_html_parts(all_forms, root_tabs):
    """Baut HTML Fragmente."""
    
    # Nav Bar
    nav_html = ""
    for idx, tab in enumerate(root_tabs):
        active = " active" if idx == 0 else ""
        nav_html += f'<div class="nav-item{active}" data-target="view_{tab["id"]}">{html.escape(tab["title"])}</div>'

    # Content Views
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
                opts_str = json.dumps(item["options"]).replace('"', '&quot;')
                item_id = item["id"]
                rows_html += f'''
                <div class="menu-row" data-type="select" data-id="{item_id}" data-options="{opts_str}" data-help="Change Option">
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
                <div>Config Info...</div>
            </div>
        </div>
        '''
        
    return nav_html, views_html

def main():
    print("--- BIOS PARSER START ---")
    ensure_directories()
    
    print(f"Lese Input: {INPUT_FILE}")
    all_forms, root_tabs = parse_dump(INPUT_FILE)
    
    if not root_tabs:
        print("ABBRUCH: Keine Tabs gefunden.")
        return

    print(f"Verarbeite: {len(root_tabs)} Tabs, {len(all_forms)} Menüs.")
    
    nav_html, views_html = build_html_parts(all_forms, root_tabs)
    
    # JSON Config erstellen
    js_data = {"tabs": list(all_forms.values())}
    json_str = json.dumps(js_data)

    # Config speichern (in /config)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(js_data, indent=2))
    print(f"Config gespeichert: {CONFIG_FILE}")

    # HTML generieren
    if not os.path.exists(TEMPLATE_FILE):
        print(f"FEHLER: Template nicht gefunden in {TEMPLATE_FILE}")
        return

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    final_html = template.replace("{TITLE}", "BIOS SETUP UTILITY") \
                         .replace("{NAV_TABS}", nav_html) \
                         .replace("{TAB_CONTENT}", views_html) \
                         .replace("{FOOTER}", "v02.61 American Megatrends - F10: Save & Exit  ESC: Back") \
                         .replace("{THEME_CSS}", "") \
                         .replace("{JSON_DATA}", json_str)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"ERFOLG: UI gespeichert in {OUTPUT_FILE}")
    print("-------------------------")

if __name__ == "__main__":
    main()