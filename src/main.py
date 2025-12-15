import json
import os
import uuid
import argparse
import sys

# --- HELPER KLASSE ---

class BiosHtmlGenerator:
    """
    Klasse zur Generierung des BIOS HTMLs.
    Kapselt den State (gesammelte Views) und trennt Logik von HTML-Strings.
    """
    def __init__(self, project_root):
        self.project_root = project_root
        self.all_views_html = [] # Liste statt String für bessere Performance
        self.template_path = os.path.join(project_root, 'templates', 'bios_template.html')

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ FEHLER: Datei nicht gefunden: {path}")
            sys.exit(1)

    def generate(self, config):
        """Hauptmethode zum Erstellen des HTMLs."""
        # 1. Theme laden
        theme_name = config.get('theme', 'award_blue')
        theme_css = self._load_theme(theme_name)

        # 2. Template laden
        template = self.load_file(self.template_path)

        # 3. Tabs und Views generieren
        nav_tabs_html = self._generate_tabs(config.get('tabs', []))

        # 4. Zusammenbauen
        # Wir nutzen .replace() statt f-strings für das große Template, 
        # um SonarQube nicht mit riesigen Strings zu verwirren.
        final_html = template.replace("{TITLE}", config.get('title', 'BIOS SETUP'))
        final_html = final_html.replace("{NAV_TABS}", nav_tabs_html)
        final_html = final_html.replace("{TAB_CONTENT}", "".join(self.all_views_html))
        final_html = final_html.replace("{FOOTER}", config.get('footer_text', ''))
        final_html = final_html.replace("{THEME_CSS}", theme_css)
        final_html = final_html.replace("{JSON_DATA}", json.dumps(config))
        
        return final_html

    def _load_theme(self, theme_name):
        path = os.path.join(self.project_root, 'src', 'themes', f"{theme_name}.css")
        if os.path.exists(path):
            return self.load_file(path)
        print(f"⚠️ WARNUNG: Theme '{theme_name}' nicht gefunden. Nutze Standard.")
        return ""

    def _generate_tabs(self, tabs):
        html_parts = []
        for index, tab in enumerate(tabs):
            tab_id = f"tab-view-{index}"
            # Einfacher f-string ohne Logik
            html_parts.append(f'<div class="nav-item" data-target="{tab_id}">{tab["name"]}</div>\n')
            self._generate_view(tab_id, tab.get('items', []), tab['name'])
        return "".join(html_parts)

    def _generate_view(self, view_id, items, path_label):
        """Erstellt eine View (Seite) und speichert sie im globalen State."""
        # parent_id wurde entfernt, da ungenutzt
        content_rows = self._generate_items_html(items, path_label)
        
        # HTML Block als Variable definieren um f-string Komplexität zu senken
        view_html = (
            f'<div id="{view_id}" class="view-container hidden">\n'
            f'    <div class="view-header-internal">{path_label}</div>\n'
            f'    <div class="view-content-wrapper" style="display:flex; width:100%;">\n'
            f'        <div class="column-left">{content_rows}</div>\n'
            f'        <div class="column-right">\n'
            f'            <p><strong>Item Help</strong></p>\n'
            f'            <p><small>Menu Level: {path_label}</small></p>\n'
            f'        </div>\n'
            f'    </div>\n'
            f'</div>\n'
        )
        self.all_views_html.append(view_html)

    def _generate_items_html(self, items, current_path_string):
        """Iteriert über Items und delegiert das HTML-Rendering."""
        rows = []
        for item in items:
            # ID Sicherstellung
            if "id" not in item:
                item["id"] = f"item-{uuid.uuid4().hex[:8]}"
            
            # Rekursion für Submenüs
            self._handle_submenu_recursion(item, current_path_string)
            
            # HTML für diese Zeile bauen
            rows.append(self._render_row(item))
            
        return "".join(rows)

    def _handle_submenu_recursion(self, item, current_path):
        """Prüft auf Submenü und generiert ggf. rekursiv die neue View."""
        if item.get("type") == "submenu":
            submenu_id = f"view-{uuid.uuid4().hex[:8]}"
            item["_target_id"] = submenu_id # Temporär speichern für Renderer
            new_path = f"{current_path} > {item.get('label', '')}"
            self._generate_view(submenu_id, item.get("items", []), new_path)

    def _render_row(self, item):
        """Erzeugt das HTML für eine einzelne Zeile (ohne komplexe Logik im String)."""
        label = item.get("label", "N/A")
        value = item.get("value", "")
        item_type = item.get("type", "item")
        item_id = item["id"]
        
        # Attribute bauen
        attrs = [f'data-type="{item_type}"', f'data-id="{item_id}"']
        
        if "_target_id" in item:
            attrs.append(f'data-target="{item["_target_id"]}"')
        
        if "options" in item:
            # JSON Escaping separat machen, nicht im f-string
            opts = json.dumps(item["options"]).replace('"', '&quot;')
            attrs.append(f'data-options="{opts}"')

        attr_string = " ".join(attrs)

        # Sauberer, einfacher HTML String
        return (
            f'<div class="menu-row" {attr_string}>\n'
            f'    <span class="item-label">{label}</span>\n'
            f'    <span class="item-value">{value}</span>\n'
            f'</div>\n'
        )

# --- MAIN ENTRY POINT ---

def get_paths(args_file):
    """Ermittelt Ein- und Ausgabepfade."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    default_config_dir = os.path.join(project_root, 'config', 'input')
    default_output_dir = os.path.join(project_root, 'output')

    # Input Pfad
    if os.path.isabs(args_file) or os.path.dirname(args_file):
        config_path = args_file
    else:
        config_path = os.path.join(default_config_dir, args_file)

    # Output Pfad
    filename_no_ext = os.path.splitext(os.path.basename(config_path))[0]
    output_path = os.path.join(default_output_dir, filename_no_ext + ".html")
    
    return project_root, config_path, output_path

def main():
    parser = argparse.ArgumentParser(description="BIOS HTML Generator")
    parser.add_argument("config_file", nargs="?", default="bios_config.json", 
                        help="Datei im config/input Ordner")
    args = parser.parse_args()

    project_root, config_path, output_path = get_paths(args.config_file)

    print("--- 🚀 BIOS Generator ---")
    print(f"Lese Config:   {config_path}")

    if not os.path.exists(config_path):
        print(f"❌ FEHLER: Datei nicht gefunden: {config_path}")
        return

    try:
        # 1. Config lesen
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 2. Generator starten
        generator = BiosHtmlGenerator(project_root)
        html_content = generator.generate(config_data)
        
        # 3. Schreiben
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Schreibe HTML: {output_path}")
        print("✅ FERTIG!")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON ERROR: {e.msg} (Zeile {e.lineno})")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()