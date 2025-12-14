import json
import os
import uuid

# Pfade
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'bios_config.json')
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates', 'bios_template.html')
THEMES_DIR = os.path.join(BASE_DIR, 'src', 'themes')
OUTPUT_PATH = os.path.join(BASE_DIR, 'output', 'index.html')

def load_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"FEHLER: Datei nicht gefunden: {path}")
        exit(1)

# Globale Liste für alle generierten Screens (Views)
all_views_html = ""

def generate_items_html(items, parent_id):
    """
    Erstellt HTML für eine Liste von Items.
    Wenn ein Item ein Submenü ist, wird rekursiv ein neuer View erstellt.
    """
    global all_views_html
    rows_html = ""
    
    for item in items:
        label = item.get("label", "N/A")
        value = item.get("value", "")
        item_type = item.get("type", "item")
        
        # Attribute für JS
        data_attrs = f'data-type="{item_type}"'
        
        # Wenn es ein Submenü ist, erstellen wir einen neuen View dafür
        if item_type == "submenu":
            submenu_id = f"view-{uuid.uuid4().hex[:8]}"
            data_attrs += f' data-target="{submenu_id}"'
            
            # REKURSION: Erstelle den HTML-Content für das Submenü
            generate_view(submenu_id, item.get("items", []), parent_title=label)
        
        # Options speichern wir direkt im DOM als JSON-String (einfacher für JS)
        if "options" in item:
            opts_json = json.dumps(item["options"]).replace('"', '&quot;')
            data_attrs += f' data-options="{opts_json}"'

        rows_html += f'''
        <div class="menu-row" {data_attrs}>
            <span class="item-label">{label}</span>
            <span class="item-value">{value}</span>
        </div>
        '''
    return rows_html

def generate_view(view_id, items, parent_title=""):
    """
    Erstellt einen kompletten 'Screen' (View) und fügt ihn der globalen Variable hinzu.
    """
    global all_views_html
    
    content_rows = generate_items_html(items, view_id)
    
    # Ein View ist standardmäßig versteckt (hidden)
    all_views_html += f'''
    <div id="{view_id}" class="view-container hidden">
        <div class="view-header-internal">Settings: {parent_title}</div>
        <div class="view-content-wrapper" style="display:flex; width:100%;">
            <div class="column-left">{content_rows}</div>
            <div class="column-right">
                <p><strong>Help</strong></p>
                <p><small>Specific help for {parent_title}...</small></p>
            </div>
        </div>
    </div>
    '''

def main():
    global all_views_html
    print("--- BIOS HTML Generator (Recursive) ---")
    
    config = json.loads(load_file(CONFIG_PATH))
    
    # Theme laden
    theme_name = config.get('theme', 'award_blue')
    theme_css = load_file(os.path.join(THEMES_DIR, f"{theme_name}.css"))
    template = load_file(TEMPLATE_PATH)

    # 1. Navigation Tabs generieren
    nav_tabs_html = ""
    
    # 2. Views generieren (für jeden Tab ein Haupt-View)
    for index, tab in enumerate(config['tabs']):
        # Tab Navigation
        nav_tabs_html += f'<div class="nav-item" data-target="tab-view-{index}">{tab["name"]}</div>\n'
        
        # Tab Inhalt (Rekursiver Startpunkt)
        generate_view(f"tab-view-{index}", tab['items'], parent_title=tab['name'])

    # 3. Zusammenbauen
    final_html = template.replace("{TITLE}", config['title'])
    final_html = final_html.replace("{NAV_TABS}", nav_tabs_html)
    # {TAB_CONTENT} wird jetzt durch ALLE Views (Tabs + Submenüs) ersetzt
    final_html = final_html.replace("{TAB_CONTENT}", all_views_html) 
    final_html = final_html.replace("{FOOTER}", config.get('footer_text', ''))
    final_html = final_html.replace("{THEME_CSS}", theme_css)
    
    # Config brauchen wir im JS kaum noch, da alles im DOM steht, aber title etc. ist nützlich
    final_html = final_html.replace("{JSON_DATA}", json.dumps({"title": config["title"]}))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"ERFOLG: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()