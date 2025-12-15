import json
import os
import uuid
import argparse
import sys

# --- GLOBALE VARIABLE ---
all_views_html = ""

# --- HELPER FUNKTIONEN ---

def load_file(path):
    """Liest eine Textdatei ein."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ FEHLER: Datei nicht gefunden: {path}")
        sys.exit(1)

def write_file(path, content):
    """Schreibt Inhalt in eine Datei."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def load_config(path):
    """Lädt die JSON Konfiguration."""
    content = load_file(path)
    return json.loads(content)

# --- GENERATOR LOGIK ---

def generate_items_html(items, parent_id, current_path_string):
    """Rekursive Funktion für Items und Untermenüs."""
    global all_views_html
    rows_html = ""
    
    for item in items:
        # ID-Logik: Behalte existierende IDs (Import) oder erstelle neue
        if "id" not in item:
            item["id"] = f"item-{uuid.uuid4().hex[:8]}"

        label = item.get("label", "N/A")
        value = item.get("value", "")
        item_type = item.get("type", "item")
        item_id = item["id"] 
        
        data_attrs = f'data-type="{item_type}" data-id="{item_id}"'
        
        if item_type == "submenu":
            submenu_id = f"view-{uuid.uuid4().hex[:8]}"
            data_attrs += f' data-target="{submenu_id}"'
            new_path = f"{current_path_string} > {label}"
            # Rekursion für das Untermenü
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
    """Erstellt einen View-Container (Seite)."""
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

def generate_html(config, project_root):
    """Baut das finale HTML zusammen."""
    global all_views_html
    all_views_html = "" # Reset
    
    # 1. Theme laden
    theme_name = config.get('theme', 'award_blue')
    theme_path = os.path.join(project_root, 'src', 'themes', f"{theme_name}.css")
    if os.path.exists(theme_path):
        theme_css = load_file(theme_path)
    else:
        print(f"⚠️ WARNUNG: Theme '{theme_name}' nicht gefunden. Nutze Standard.")
        theme_css = ""

    # 2. Template laden
    template_path = os.path.join(project_root, 'templates', 'bios_template.html')
    template = load_file(template_path)

    # 3. Tabs generieren
    nav_tabs_html = ""
    for index, tab in enumerate(config['tabs']):
        nav_tabs_html += f'<div class="nav-item" data-target="tab-view-{index}">{tab["name"]}</div>\n'
        generate_view(f"tab-view-{index}", tab['items'], path_label=tab['name'])

    # 4. Platzhalter ersetzen
    final_html = template.replace("{TITLE}", config.get('title', 'BIOS SETUP'))
    final_html = final_html.replace("{NAV_TABS}", nav_tabs_html)
    final_html = final_html.replace("{TAB_CONTENT}", all_views_html)
    final_html = final_html.replace("{FOOTER}", config.get('footer_text', ''))
    final_html = final_html.replace("{THEME_CSS}", theme_css)
    final_html = final_html.replace("{JSON_DATA}", json.dumps(config))
    
    return final_html

# --- MAIN ENTRY POINT ---

def main():
    # 1. Pfad-Bestimmung
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Eins hoch zu /my_bios_project
    
    default_config_dir = os.path.join(project_root, 'config', 'input')
    default_output_dir = os.path.join(project_root, 'output')

    # 2. Argumente verarbeiten
    parser = argparse.ArgumentParser(description="BIOS HTML Generator")
    parser.add_argument("config_file", nargs="?", default="bios_config.json", 
                        help="Name der Datei im config-Ordner (z.B. my_bios.json)")
    args = parser.parse_args()

    input_arg = args.config_file

    # 3. Logik: Wo liegt die Config-Datei?
    if os.path.isabs(input_arg) or os.path.dirname(input_arg):
        config_path = input_arg
    else:
        config_path = os.path.join(default_config_dir, input_arg)

    # 4. Logik: Wo speichern wir das HTML?
    filename_no_ext = os.path.splitext(os.path.basename(config_path))[0]
    output_path = os.path.join(default_output_dir, filename_no_ext + ".html")

    print(f"--- 🚀 BIOS Generator ---")
    print(f"Lese Config:   {config_path}")

    # 5. Check ob Datei existiert
    if not os.path.exists(config_path):
        print(f"❌ FEHLER: Datei nicht gefunden!")
        print(f"   Gesucht wurde hier: {config_path}")
        return

    # 6. Ausführen
    try:
        config_data = load_config(config_path)
        
        # Wichtig: Wir übergeben project_root, damit er Themes/Templates findet
        html_content = generate_html(config_data, project_root)
        
        write_file(output_path, html_content)

        print(f"Schreibe HTML: {output_path}")
        print(f"✅ FERTIG! Datei erfolgreich erstellt.")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON ERROR: Deine Konfigurationsdatei ist kaputt.")
        print(f"   Zeile {e.lineno}: {e.msg}")
    except Exception as e:
        print(f"❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()