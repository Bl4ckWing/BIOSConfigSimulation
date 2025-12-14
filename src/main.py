import json
import os
import uuid

# --- PFADE ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'bios_config.json')
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates', 'bios_template.html')
THEMES_DIR = os.path.join(BASE_DIR, 'src', 'themes')
OUTPUT_PATH = os.path.join(BASE_DIR, 'output', 'index.html')

# Globale Variable für den gesammelten HTML-Code aller Views
all_views_html = ""

def load_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"FEHLER: Datei nicht gefunden: {path}")
        exit(1)

def generate_items_html(items, parent_id, current_path_string):
    """
    Erstellt HTML für Items. 
    WICHTIG: Erzeugt Unique IDs und schreibt sie in das Config-Objekt zurück.
    """
    global all_views_html
    rows_html = ""
    
    for item in items:
        # 1. GENERIERE UNIQUE ID (falls noch nicht vorhanden)
        # Wir schreiben das direkt in das item-Dict, damit es später im JSON dump landet.
        if "id" not in item:
            item["id"] = f"item-{uuid.uuid4().hex[:8]}"

        label = item.get("label", "N/A")
        value = item.get("value", "")
        item_type = item.get("type", "item")
        item_id = item["id"] 
        
        # HTML Attribute für JS (Data Binding)
        data_attrs = f'data-type="{item_type}" data-id="{item_id}"'
        
        # Fall: Submenü
        if item_type == "submenu":
            submenu_id = f"view-{uuid.uuid4().hex[:8]}"
            data_attrs += f' data-target="{submenu_id}"'
            
            # Pfad erweitern (Breadcrumb)
            new_path = f"{current_path_string} > {label}"
            
            # Rekursion: Submenü generieren
            generate_view(submenu_id, item.get("items", []), path_label=new_path)
        
        # Fall: Item mit Optionen
        if "options" in item:
            # Optionen als JSON-String im HTML speichern
            opts_json = json.dumps(item["options"]).replace('"', '&quot;')
            data_attrs += f' data-options="{opts_json}"'

        rows_html += f'''
        <div class="menu-row" {data_attrs}>
            <span class="item-label">{label}</span>
            <span class="item-value">{value}</span>
        </div>
        '''
    return rows_html

def generate_view(view_id, items, path_label=""):
    """
    Erstellt einen kompletten Screen (View Container)
    """
    global all_views_html
    
    content_rows = generate_items_html(items, view_id, path_label)
    
    all_views_html += f'''
    <div id="{view_id}" class="view-container hidden">
        <div class="view-header-internal">{path_label}</div>
        <div class="view-content-wrapper" style="display:flex; width:100%;">
            <div class="column-left">{content_rows}</div>
            <div class="column-right">
                <p><strong>Item Help</strong></p>
                <p><small>Menu Level: {path_label}</small></p>
            </div>
        </div>
    </div>
    '''

def main():
    global all_views_html
    print("--- BIOS HTML Generator (Final Version) ---")
    
    # 1. Config laden
    config_str = load_file(CONFIG_PATH)
    config = json.loads(config_str)
    
    # 2. Theme laden
    theme_name = config.get('theme', 'award_blue')
    theme_path = os.path.join(THEMES_DIR, f"{theme_name}.css")
    if os.path.exists(theme_path):
        theme_css = load_file(theme_path)
    else:
        print(f"WARNUNG: Theme '{theme_name}' nicht gefunden. Nutze Fallback.")
        theme_css = "" # Oder Standard CSS hier einfügen

    # 3. Template laden
    template = load_file(TEMPLATE_PATH)

    # 4. HTML generieren
    nav_tabs_html = ""
    
    for index, tab in enumerate(config['tabs']):
        # Navigation Tabs
        nav_tabs_html += f'<div class="nav-item" data-target="tab-view-{index}">{tab["name"]}</div>\n'
        
        # Startpunkt der Rekursion pro Tab
        generate_view(f"tab-view-{index}", tab['items'], path_label=tab['name'])

    # 5. Ersetzen
    final_html = template.replace("{TITLE}", config['title'])
    final_html = final_html.replace("{NAV_TABS}", nav_tabs_html)
    final_html = final_html.replace("{TAB_CONTENT}", all_views_html) 
    final_html = final_html.replace("{FOOTER}", config.get('footer_text', ''))
    final_html = final_html.replace("{THEME_CSS}", theme_css)
    
    # WICHTIG: Das Config-Objekt wird JETZT erst in JS injiziert, 
    # nachdem generate_items_html die IDs hinzugefügt hat!
    final_html = final_html.replace("{JSON_DATA}", json.dumps(config))

    # 6. Speichern
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"ERFOLG: One-Pager erstellt unter: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()