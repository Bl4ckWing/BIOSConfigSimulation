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

# Globale Variable
all_views_html = ""

def generate_items_html(items, parent_id, current_path_string):
    """
    Erstellt HTML für Items und ruft rekursiv generate_view auf,
    wobei der Pfad (Breadcrumb) erweitert wird.
    """
    global all_views_html
    rows_html = ""
    
    for item in items:
        label = item.get("label", "N/A")
        value = item.get("value", "")
        item_type = item.get("type", "item")
        
        data_attrs = f'data-type="{item_type}"'
        
        if item_type == "submenu":
            submenu_id = f"view-{uuid.uuid4().hex[:8]}"
            data_attrs += f' data-target="{submenu_id}"'
            
            # REKURSION: Pfad erweitern (z.B. "Advanced" -> "Advanced > CPU Config")
            new_path = f"{current_path_string} > {label}"
            generate_view(submenu_id, item.get("items", []), path_label=new_path)
        
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

def generate_view(view_id, items, path_label=""):
    """
    Erstellt einen Screen mit sichtbarer Überschrift (Breadcrumb).
    """
    global all_views_html
    
    # Hier übergeben wir den aktuellen Pfad an die Items-Funktion
    content_rows = generate_items_html(items, view_id, path_label)
    
    # HTML Aufbau: Jetzt mit sichtbarem Header
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
    print("--- BIOS HTML Generator (Breadcrumbs) ---")
    
    config = json.loads(load_file(CONFIG_PATH))
    
    theme_name = config.get('theme', 'award_blue')
    theme_css = load_file(os.path.join(THEMES_DIR, f"{theme_name}.css"))
    template = load_file(TEMPLATE_PATH)

    nav_tabs_html = ""
    
    for index, tab in enumerate(config['tabs']):
        nav_tabs_html += f'<div class="nav-item" data-target="tab-view-{index}">{tab["name"]}</div>\n'
        
        # Startpunkt der Rekursion: Pfad ist nur der Tab-Name
        generate_view(f"tab-view-{index}", tab['items'], path_label=tab['name'])

    final_html = template.replace("{TITLE}", config['title'])
    final_html = final_html.replace("{NAV_TABS}", nav_tabs_html)
    final_html = final_html.replace("{TAB_CONTENT}", all_views_html) 
    final_html = final_html.replace("{FOOTER}", config.get('footer_text', ''))
    final_html = final_html.replace("{THEME_CSS}", theme_css)
    final_html = final_html.replace("{JSON_DATA}", json.dumps({"title": config["title"]}))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"ERFOLG: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()