import json
import os

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

def main():
    print("--- BIOS HTML Generator (Modular) ---")
    
    # 1. Config laden
    json_str = load_file(CONFIG_PATH)
    config = json.loads(json_str)
    
    # 2. Theme laden
    theme_name = config.get('theme', 'award_blue') # Fallback auf award_blue
    theme_file = os.path.join(THEMES_DIR, f"{theme_name}.css")
    print(f"Lade Theme: {theme_name}...")
    theme_css = load_file(theme_file)

    # 3. Template laden
    template = load_file(TEMPLATE_PATH)

    # 4. HTML Fragmente bauen
    nav_tabs_html = ""
    tab_content_html = ""

    for index, tab in enumerate(config['tabs']):
        nav_tabs_html += f'<div class="nav-item">{tab["name"]}</div>\n'
        
        rows_html = ""
        for item in tab['items']:
            rows_html += f'''
            <div class="menu-row">
                <span class="item-label">{item["label"]}</span>
                <span class="item-value">{item["value"]}</span>
            </div>
            '''
        
        tab_content_html += f'''
        <div class="tab-pane-wrapper hidden" style="width:100%; display:flex;">
            <div class="column-left">{rows_html}</div>
            <div class="column-right">
                <p><strong>Item Specific Help</strong></p>
                <p><small>Press Enter to select or change value.</small></p>
            </div>
        </div>
        '''

    # 5. Ersetzen
    final_html = template.replace("{TITLE}", config['title'])
    final_html = final_html.replace("{NAV_TABS}", nav_tabs_html)
    final_html = final_html.replace("{TAB_CONTENT}", tab_content_html)
    final_html = final_html.replace("{FOOTER}", config.get('footer_text', ''))
    final_html = final_html.replace("{JSON_DATA}", json.dumps(config))
    final_html = final_html.replace("{THEME_CSS}", theme_css) # HIER passiert die Magie

    # 6. Speichern
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"ERFOLG: One-Pager erstellt unter: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()