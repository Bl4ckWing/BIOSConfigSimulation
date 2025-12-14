# BIOSConfigSimulation

> Turn JSON configurations into interactive, nostalgia-fueled BIOS setup screens.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.x-yellow.svg)

## 📖 About
This tool allows you to simulate classic "Blue Screen" BIOS interfaces (reminiscent of Award/Phoenix BIOS from the 90s/00s). It parses a configuration file and builds a lightweight, self-contained HTML file. The output supports keyboard navigation (Arrow keys, Enter, Esc) just like the real thing, without requiring any external dependencies or backend server.

## ✨ Features
* **JSON-driven:** Define tabs, menu items, and values in a simple, human-readable format.
* **Standalone Output:** Generates a single `.html` file with embedded CSS and JS (easy to share or embed).
* **Interactive:** Simulates keyboard navigation (Tabs, Arrows, Selection).
* **Customizable:** Uses CSS variables for easy theming (change colors to simulate AMI/Grey or custom styles).
* **No Dependencies:** The generated HTML runs in any modern browser.

## 🚀 Quick Start

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/your-username/bios-html-generator.git](https://github.com/your-username/bios-html-generator.git)
    cd bios-html-generator
    ```

2.  **Edit the Configuration:**
    Modify `config/bios_data.json` to define your menu structure.

3.  **Build the BIOS:**
    Run the generator script:
    ```bash
    python src/main.py
    ```

4.  **View the Result:**
    Open the generated `output/index.html` in your browser.

## 🛠 Configuration Example
```json
{
  "title": "PHOENIX - AWARD BIOS CMOS SETUP UTILITY",
  "tabs": [
    {
      "name": "Advanced",
      "items": [
        { "label": "CPU Frequency", "value": "4.00 GHz" }
      ]
    }
  ]
}
