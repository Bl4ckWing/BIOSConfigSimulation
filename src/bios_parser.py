import re
import json
import os
import html

# --- DATEI KONFIGURATION ---
INPUT_FILE = "bios_dump.txt"
TEMPLATE_FILE = "bios_template.html"
OUTPUT_FILE = "bios_ui.html"

def parse_dump(filename):
    """Liest den Dump und erstellt eine hierarchische Struktur."""
    if not os.path.exists(filename):
        print(f"Fehler: {filename} nicht gefunden.")
        return {}, []

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    forms = {}
    current_form_id = None
    
    # IDs von Forms, die von anderen referenziert werden (also Untermenüs sind)
    referenced_forms = set() 

    # --- REGEX ---
    # Form Start: "0x1234 Form: Main (0x1)"
    re_form = re.compile(r"^\s*(0x[0-9A-F]+)\s+Form:\s+(.+?)\s+\((0x[0-9A-F]+)\)")
    # Referenz/Untermenü: "Ref: ... FormId: 0x12"
    re_ref = re.compile(r"Ref:\s+(.+?)\s+.*FormId:\s+(0x[0-9A-F]+)")
    # Auswahl: "OneOf: ... Variable: 0x12"
    re_oneof = re.compile(r"OneOf:\s+(.+?)\s+.*Variable:\s+(0x[0-9A-F]+)")
    re_option = re.compile(r"Option:\s+(.+?)\s+,\s+Value:\s+(0x[0-9A-F]+)")
    # Checkbox
    re_checkbox = re.compile(r"CheckBox:\s+(.+?)\s+.*Variable:\s+(0x[0-9A-F]+)")
    # Text/Subtitle (einfache Erkennung)
    re_text = re.compile(r"Subtitle:\s+Statement.Prompt:\s+(.+?)(?:,|$)|Text:\s+(.+?)(?:,|$)")

    # 1. DURCHLAUF: Rohdaten einlesen
    for line in lines:
        line = line.strip()
        
        # A) Neue Form
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

        if not current_form_id:
            continue

        items = forms[current_form_id]["items"]

        # B) Submenü Link (Ref)
        m_ref = re_ref.search(line)
        if m_ref:
            label, target_id = m_ref.groups()
            referenced_forms.add(target_id) # Aha, target_id ist ein Kind!
            items.append({
                "type": "submenu",
                "label": label.strip(),
                "target": target_id
            })
            continue

        # C) Select / OneOf
        m_oneof = re_oneof.search(line)
        if m_oneof:
            label, var_id = m_oneof.groups()
            items.append({
                "type": "select",
                "label": label.strip(),
                "id": var_id,
                "value": "Select...", # Platzhalter
                "options": []
            })
            continue

        # D) Optionen für Select
        m_opt = re_option.search(line)
        if m_opt and items:
            last = items[-1]
            if last["type"] == "select":
                opt_lbl, _ = m_opt.groups()
                last["options"].append(opt_lbl.strip())
                if last["value"] == "Select...": last["value"] = opt_lbl.strip() # Default setzen
            continue

        # E) Checkbox (als Select behandeln)
        m_chk = re_checkbox.search(line)
        if m_chk:
            label, var_id = m_chk.groups()
            items.append({
                "type": "select",
                "label": label.strip(),
                "id": var_id,
                "value": "Disabled",
                "options": ["Disabled", "Enabled"]
            })
            continue
            
        # F) Text/Subtitle (Optional, für Optik)
        m_txt = re_text.search(line)
        if m_txt:
            # Nimm die erste Gruppe die nicht None ist
            txt = next((g for g in m_txt.groups() if g is not None), "")
            if txt.strip():
                items.append({"type": "text", "label": txt.strip()})

    # 2. HIERARCHIE BESTIMMEN
    # Root Tabs sind alle Forms, die NICHT referenziert wurden.
    # (Ausnahme: Oft gibt es eine "Setup"-Form, die alles umschließt. Die filtern wir ggf. raus)
    root_ids = [fid for fid in forms if fid not in referenced_forms]
    root_ids.sort(key=lambda x: int(x, 16))

    # Spezialfall: Wenn es nur EINE Root gibt (z.B. "Setup"), sind deren Kinder die wahren Tabs
    real_tabs = []
    if len(root_ids) == 1:
        setup_id = root_ids[0]
        # Wir schauen in die Items der Setup Form
        for item in forms[setup_id]["items"]:
            if item["type"] == "submenu" and item["target"] in forms:
                real_tabs.append(forms[item["target"]])
    else:
        # Sonst sind die Roots die Tabs
        for rid in root_ids:
            real_tabs.append(forms[rid])

    return forms, real_tabs

def build_html_parts(all_forms, root_tabs):
    """Erzeugt die HTML-Fragmente für das Template."""
    
    # 1. NAV TABS (Nur die Hauptkategorien)
    nav_html = ""
    for idx, tab in enumerate(root_tabs):
        active = " active" if idx == 0 else ""
        nav_html += f'<div class="nav-item{active}" data-target="view_{tab["id"]}">{html.escape(tab["title"])}</div>'

    # 2. VIEW CONTENT (Alle Menüs, auch Untermenüs)
    views_html = ""
    for form_id, form in all_forms.items():
        rows_html = ""
        
        for item in form["items"]:
            lbl = html.escape(item["label"])
            
            if item["type"] == "submenu":
                target = item["target"]
                rows_html += f'''
                <div class="menu-row" data-type="submenu" data-target="view_{target}" data-help="Go to Submenu">
                    <span class="item-label">{lbl}</span>
                    <span class="item-value">►</span>
                </div>'''
            
            elif item["type"] == "select":
                val = html.escape(item["value"])
                # Optionen als JSON Attribut
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

        # View Wrapper
        views_html += f'''
        <div id="view_{form_id}" class="view-section">
            <div class="col-items">{rows_html}</div>
            <div class="col-help">
                <div style="font-weight:bold; border-bottom:1px solid #fff; margin-bottom:5px;">{html.escape(form["title"])}</div>
                <div>Help text for specific item configuration.</div>
            </div>
        </div>
        '''
        
    return nav_html, views_html

def main():
    print(f"Lese {INPUT_FILE}...")
    all_forms, root_tabs = parse_dump(INPUT_FILE)
    
    if not root_tabs:
        print("Keine Tabs gefunden! Format prüfen.")
        return

    print(f"Hierarchie erkannt: {len(root_tabs)} Haupt-Tabs, {len(all_forms)} Menüs gesamt.")
    
    nav_html, views_html = build_html_parts(all_forms, root_tabs)
    
    # JSON Daten für das JavaScript State Management
    # Wir übergeben einfach alle Forms in einer flachen Liste an 'tabs',
    # damit BIOS.idMap alle IDs findet. Die Navigation regelt das HTML.
    js_data = {"tabs": list(all_forms.values())}
    json_str = json.dumps(js_data)

    print(f"Lese Template {TEMPLATE_FILE}...")
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
        
    print(f"Fertig! Datei erstellt: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()