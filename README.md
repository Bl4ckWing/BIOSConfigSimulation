# BIOS HTML Generator

> **Turn JSON configurations into fully interactive, retro-styled BIOS setup screens.**

This tool generates standalone, single-file HTML "One-Pagers" that simulate classic BIOS/UEFI environments. Perfect for documentation, mockups, educational tools, or retro-design projects.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Status](https://img.shields.io/badge/status-active-success.svg)

## ✨ Features

* **🎨 Retro Themes:** Switch between classic **Award Blue** (90s style) and **AMI Grey** (early 2000s/Office style) just by changing a config line.
* **📂 Deep Navigation:** Supports infinite nesting of submenus with automatic breadcrumb navigation (e.g., `Main > Advanced > CPU Config`).
* **⌨️ Full Keyboard Control:** Navigate using Arrow keys, Enter, and ESC – just like the real thing.
* **💾 Interactive & Persistent:** Change settings in the browser, press **F10** to save, and export a modified JSON file containing your changes.
* **🔄 Round-Trip Workflow:** Re-import exported JSON files to generate a new HTML file with your saved settings pre-loaded (thanks to unique ID tracking).
* **🚀 Zero Dependencies:** The generated HTML file requires no external CSS/JS files and runs offline. The generator uses only the Python Standard Library.

## 🛠️ Project Structure

```text
/src
  /themes          # CSS definitions (award_blue.css, ami_grey.css)
  main.py          # The generator script
/config
  bios_config.json # Default configuration input
  my_setup.json    # Custom configuration
/templates
  bios_template.html
/output
  bios_config.html # The generated result
```
### 🚀 Usage

### 1. Basic Generation
Run the script without arguments to use the default `config/bios_config.json`:

```bash
python src/main.py
### 2. Custom Configuration
You can pass any JSON file located in the `config/` folder as an argument:
```
```bash
python src/main.py my_custom_setup.json
# Creates: output/my_custom_setup.html

### 3. Help
Show available commands:
```bash
python src/main.py --help
```
## 🎮 How to use the BIOS Simulator

Once you open the generated HTML file in your browser:

* **Arrows:** Navigate tabs and items.
* **Enter:** Change a value (opens popup) or enter a Submenu.
* **Esc:** Go back / Exit submenu.
* **F10:** Open the **"Save & Exit"** dialog.
    * Select **[ Y ]** to download your current configuration as a JSON file.
    * This simulates a system reboot.

## ⚙️ Configuration (JSON)

Define your menu structure in `config/bios_config.json`.

### Example Structure
```json
{
  "title": "PHOENIX - AWARD BIOS CMOS SETUP UTILITY",
  "theme": "award_blue", 
  "tabs": [
    {
      "name": "Main",
      "items": [
        { 
            "label": "System Time", 
            "value": "12:00:00", 
            "options": ["12:00:00", "13:37:00"] 
        }
      ]
    },
    {
      "name": "Advanced",
      "items": [
        {
          "label": "CPU Configuration",
          "type": "submenu",
          "value": "> Press Enter",
          "items": [
             { "label": "Hyper-Threading", "value": "[Enabled]" }
          ]
        }
      ]
    }
  ]
}
```
### Key Properties
* **`theme`**: Choose between `"award_blue"` or `"ami_grey"`.
* **`type`**: Set to `"submenu"` to create a nested menu. Add an `items` array inside it.
* **`options`**: An array of strings. If present, pressing Enter will show a selection popup.
* **`id`**: *Automatically generated.* You don't need to write this manually. The generator adds unique IDs to track value changes during export.

## 🎨 Themes

| Theme Name | Description |
| :--- | :--- |
| **`award_blue`** | High-contrast blue background, yellow text, red highlights. The classic 90s gamer BIOS. |
| **`ami_grey`** | Grey background, navy blue text, windowed look. Typical for OEM/Office PCs. |

## 🤝 Contributing

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

