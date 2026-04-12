"""
🎨 Design System & UI Themes Manager (Extended Pro Version)
---------------------------------------------------------
Ce fichier centralise 13 thèmes professionnels pour une expérience personnalisée.
"""

# 1. 🌈 DÉFINITION DES PALETTES (13 THÈMES)
# ----------------------------------------
THEMES = {
    # --- THÈMES ORIGINAUX ---
    "emerald": {
        "name": "💎 Premium Emerald (Forest)",
        "colors": {
            "bg_main": "#0a1f1c", "bg_secondary": "#112e2a", "bg_tertiary": "#1a3d38",
            "text_main": "#e6edf3", "text_secondary": "#7d8590", "accent": "#2ea043",
            "accent_hover": "#3fb950", "border": "#214d47", "border_focus": "#2ea043",
            "success": "#2ea043", "error": "#ff7b72", "warning": "#d29922", "selection": "#1a7f37",
            "filter_bg": "#0a1f1c", "filter_border_top": "#1a3d38", "filter_text": "#7d8590",
            "filter_combo_bg": "#112e2a", "filter_combo_text": "#e6edf3", "filter_combo_border": "#214d47",
            "filter_combo_popup_bg": "#1a3d38", "filter_combo_selection": "#2ea043"
        }
    },
    "midnight": {
        "name": "🌌 Premium Midnight (Dark)",
        "colors": {
            "bg_main": "#0d1117", "bg_secondary": "#161b22", "bg_tertiary": "#21262d",
            "text_main": "#c9d1d9", "text_secondary": "#8b949e", "accent": "#58a6ff",
            "accent_hover": "#1f6feb", "border": "#30363d", "border_focus": "#58a6ff",
            "success": "#238636", "error": "#da3633", "warning": "#d29922", "selection": "#1f6feb",
            "filter_bg": "#0d1117", "filter_border_top": "#21262d", "filter_text": "#8b949e",
            "filter_combo_bg": "#21262d", "filter_combo_text": "#c9d1d9", "filter_combo_border": "#30363d",
            "filter_combo_popup_bg": "#161b22", "filter_combo_selection": "#1f6feb"
        }
    },
    "light": {
        "name": "☁️ Light Professional",
        "colors": {
            "bg_main": "#ffffff", "bg_secondary": "#f6f8fa", "bg_tertiary": "#ebf0f4",
            "text_main": "#24292f", "text_secondary": "#57606a", "accent": "#0969da",
            "accent_hover": "#0550ae", "border": "#d0d7de", "border_focus": "#0969da",
            "success": "#1a7f37", "error": "#cf222e", "warning": "#9a6700", "selection": "#0969da",
            "filter_bg": "#ffffff", "filter_border_top": "#ebf0f4", "filter_text": "#57606a",
            "filter_combo_bg": "#f6f8fa", "filter_combo_text": "#24292f", "filter_combo_border": "#d0d7de",
            "filter_combo_popup_bg": "#ebf0f4", "filter_combo_selection": "#0969da"
        }
    },

    # --- NOUVEAUX THÈMES (PROPOSÉS) ---
    "burgundy": {
        "name": "🍷 Imperial Burgundy",
        "colors": {
            "bg_main": "#2b0505", "bg_secondary": "#410a0a", "bg_tertiary": "#5a0f0f",
            "text_main": "#f4ecd8", "text_secondary": "#a28b8b", "accent": "#d4af37",
            "accent_hover": "#e5c158", "border": "#4e1b1b", "border_focus": "#d4af37",
            "success": "#2ea043", "error": "#ff7b72", "warning": "#d29922", "selection": "#5a0f0f",
            "filter_bg": "#2b0505", "filter_border_top": "#5a0f0f", "filter_text": "#a28b8b",
            "filter_combo_bg": "#410a0a", "filter_combo_text": "#f4ecd8", "filter_combo_border": "#4e1b1b",
            "filter_combo_popup_bg": "#5a0f0f", "filter_combo_selection": "#d4af37"
        }
    },
    "navy": {
        "name": "⚓ Royal Navy Captain",
        "colors": {
            "bg_main": "#001529", "bg_secondary": "#002140", "bg_tertiary": "#003366",
            "text_main": "#ffffff", "text_secondary": "#8c9fb1", "accent": "#d4af37",
            "accent_hover": "#ffd700", "border": "#003a70", "border_focus": "#d4af37",
            "success": "#52c41a", "error": "#f5222d", "warning": "#faad14", "selection": "#003366",
            "filter_bg": "#001529", "filter_border_top": "#003366", "filter_text": "#8c9fb1",
            "filter_combo_bg": "#002140", "filter_combo_text": "#ffffff", "filter_combo_border": "#003a70",
            "filter_combo_popup_bg": "#003366", "filter_combo_selection": "#d4af37"
        }
    },
    "slate": {
        "name": "🏙️ Modern Slate Eng.",
        "colors": {
            "bg_main": "#1c232b", "bg_secondary": "#242c36", "bg_tertiary": "#2d3846",
            "text_main": "#ebf1f5", "text_secondary": "#9badbc", "accent": "#00bcd4",
            "accent_hover": "#26c6da", "border": "#37474f", "border_focus": "#00bcd4",
            "success": "#4caf50", "error": "#f44336", "warning": "#ff9800", "selection": "#2d3846",
            "filter_bg": "#1c232b", "filter_border_top": "#2d3846", "filter_text": "#9badbc",
            "filter_combo_bg": "#242c36", "filter_combo_text": "#ebf1f5", "filter_combo_border": "#37474f",
            "filter_combo_popup_bg": "#2d3846", "filter_combo_selection": "#00bcd4"
        }
    },
    "frost": {
        "name": "❄️ Nordic Frost (Light)",
        "colors": {
            "bg_main": "#f0f4f8", "bg_secondary": "#d9e2ec", "bg_tertiary": "#bcccdc",
            "text_main": "#102a43", "text_secondary": "#486581", "accent": "#2b6cb0",
            "accent_hover": "#2c5282", "border": "#9fb3c8", "border_focus": "#2b6cb0",
            "success": "#2f855a", "error": "#c53030", "warning": "#b7791f", "selection": "#bcccdc",
            "filter_bg": "#f0f4f8", "filter_border_top": "#bcccdc", "filter_text": "#486581",
            "filter_combo_bg": "#d9e2ec", "filter_combo_text": "#102a43", "filter_combo_border": "#9fb3c8",
            "filter_combo_popup_bg": "#bcccdc", "filter_combo_selection": "#2b6cb0"
        }
    },
    "sepia": {
        "name": "📜 Vintage Sepia Archive",
        "colors": {
            "bg_main": "#f4ecd8", "bg_secondary": "#eaddc0", "bg_tertiary": "#dac8a4",
            "text_main": "#433422", "text_secondary": "#7c6a53", "accent": "#8b4513",
            "accent_hover": "#a0522d", "border": "#c1ae8c", "border_focus": "#8b4513",
            "success": "#228b22", "error": "#b22222", "warning": "#cd853f", "selection": "#dac8a4",
            "filter_bg": "#f4ecd8", "filter_border_top": "#dac8a4", "filter_text": "#7c6a53",
            "filter_combo_bg": "#eaddc0", "filter_combo_text": "#433422", "filter_combo_border": "#c1ae8c",
            "filter_combo_popup_bg": "#dac8a4", "filter_combo_selection": "#8b4513"
        }
    },
    "dracula": {
        "name": "🧬 Dracula Night Pro",
        "colors": {
            "bg_main": "#282a36", "bg_secondary": "#44475a", "bg_tertiary": "#6272a4",
            "text_main": "#f8f8f2", "text_secondary": "#bd93f9", "accent": "#ff79c6",
            "accent_hover": "#ff92df", "border": "#44475a", "border_focus": "#bd93f9",
            "success": "#50fa7b", "error": "#ff5555", "warning": "#f1fa8c", "selection": "#6272a4",
            "filter_bg": "#282a36", "filter_border_top": "#6272a4", "filter_text": "#bd93f9",
            "filter_combo_bg": "#44475a", "filter_combo_text": "#f8f8f2", "filter_combo_border": "#44475a",
            "filter_combo_popup_bg": "#6272a4", "filter_combo_selection": "#ff79c6"
        }
    },
    "sahara": {
        "name": "🏜️ Sahara Desert Gold",
        "colors": {
            "bg_main": "#e1d1b5", "bg_secondary": "#cfb68d", "bg_tertiary": "#bc9e6c",
            "text_main": "#3e2723", "text_secondary": "#5d4037", "accent": "#af5f00",
            "accent_hover": "#d46a00", "border": "#a88a5e", "border_focus": "#af5f00",
            "success": "#558b2f", "error": "#c62828", "warning": "#ef6c00", "selection": "#bc9e6c",
            "filter_bg": "#e1d1b5", "filter_border_top": "#bc9e6c", "filter_text": "#5d4037",
            "filter_combo_bg": "#cfb68d", "filter_combo_text": "#3e2723", "filter_combo_border": "#a88a5e",
            "filter_combo_popup_bg": "#bc9e6c", "filter_combo_selection": "#af5f00"
        }
    },
    "cyber": {
        "name": "⚡ Cyberpunk 2077 Neon",
        "colors": {
            "bg_main": "#0b0e14", "bg_secondary": "#1a1f29", "bg_tertiary": "#252d3d",
            "text_main": "#fdfd00", "text_secondary": "#ff00ff", "accent": "#00ffff",
            "accent_hover": "#fdfd00", "border": "#252d3d", "border_focus": "#00ffff",
            "success": "#00ff00", "error": "#ff0000", "warning": "#ff8800", "selection": "#252d3d",
            "filter_bg": "#0b0e14", "filter_border_top": "#252d3d", "filter_text": "#ff00ff",
            "filter_combo_bg": "#1a1f29", "filter_combo_text": "#fdfd00", "filter_combo_border": "#252d3d",
            "filter_combo_popup_bg": "#252d3d", "filter_combo_selection": "#00ffff"
        }
    },
    "obsidian": {
        "name": "♟️ Obsidian Executive",
        "colors": {
            "bg_main": "#0a0a0a", "bg_secondary": "#151515", "bg_tertiary": "#222222",
            "text_main": "#e0e0e0", "text_secondary": "#a0a0a0", "accent": "#bf9b30",
            "accent_hover": "#dfbb50", "border": "#333333", "border_focus": "#bf9b30",
            "success": "#2e7d32", "error": "#c62828", "warning": "#f57f17", "selection": "#222222",
            "filter_bg": "#0a0a0a", "filter_border_top": "#222222", "filter_text": "#a0a0a0",
            "filter_combo_bg": "#151515", "filter_combo_text": "#e0e0e0", "filter_combo_border": "#333333",
            "filter_combo_popup_bg": "#222222", "filter_combo_selection": "#bf9b30"
        }
    },
    "olive": {
        "name": "🍃 Tuscany Olive Garden",
        "colors": {
            "bg_main": "#3b4a20", "bg_secondary": "#4a5a2a", "bg_tertiary": "#5a6a3a",
            "text_main": "#f5f5dc", "text_secondary": "#dce0cd", "accent": "#98bf64",
            "accent_hover": "#a8cf74", "border": "#4a5a2a", "border_focus": "#98bf64",
            "success": "#a8cf74", "error": "#cd5c5c", "warning": "#ffd700", "selection": "#5a6a3a",
            "filter_bg": "#3b4a20", "filter_border_top": "#5a6a3a", "filter_text": "#dce0cd",
            "filter_combo_bg": "#4a5a2a", "filter_combo_text": "#f5f5dc", "filter_combo_border": "#4a5a2a",
            "filter_combo_popup_bg": "#5a6a3a", "filter_combo_selection": "#98bf64"
        }
    }
}

# 2. 📝 TEMPLATE QSS GLOBAL (Multi-Thème)
# -------------------------------------
QSS_TEMPLATE = """
QMainWindow {{ background-color: {bg_main}; }}

/* Onglets Custom */
QTabWidget::pane {{ border: 1px solid {border}; background-color: {bg_main}; top: -1px; }}
QTabBar::tab {{
    background-color: {bg_main}; color: {text_secondary};
    border: 1px solid {border}; border-bottom-color: transparent;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    padding: 8px 16px; margin-right: 2px;
}}
QTabBar::tab:selected {{ background-color: {bg_secondary}; color: {accent}; border-bottom: 2px solid {accent}; }}
QTabBar::tab:hover:!selected {{ background-color: {bg_tertiary}; color: {text_main}; }}

/* Status & Menus */
QStatusBar {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {bg_main}, stop:1 {bg_secondary}); border-top: 1px solid {border}; color: {text_secondary}; }}
QMenuBar {{ background-color: {bg_main}; color: {text_main}; border-bottom: 1px solid {border}; }}
QMenuBar::item:selected {{ background-color: {bg_tertiary}; }}
QMenu {{ background-color: {bg_secondary}; color: {text_main}; border: 1px solid {border}; }}
QMenu::item:selected {{ background-color: {selection}; color: #ffffff; }}

/* Widgets Forms */
QGroupBox {{ color: {accent}; font-weight: bold; border: 1px solid {border}; border-radius: 8px; margin-top: 1.5ex; padding: 10px; }}
QLabel {{ color: {text_main}; }}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {{
    background-color: {bg_main}; color: {text_main};
    border: 1px solid {border}; border-radius: 6px; padding: 5px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {border_focus}; }}

/* Boutons */
QPushButton {{ background-color: {bg_tertiary}; color: {text_main}; border: 1px solid {border}; border-radius: 6px; padding: 6px 16px; }}
QPushButton:hover {{ background-color: {accent}; color: #ffffff; }}
QPushButton:pressed {{ background-color: {accent_hover}; }}
QPushButton:disabled {{ background-color: {bg_secondary}; color: {text_secondary}; }}

/* Tables */
QTableView#mainTable {{
    background-color: {bg_main}; alternate-background-color: {bg_secondary};
    color: {text_main}; gridline-color: {bg_tertiary}; border: none;
    selection-background-color: {selection}; selection-color: #ffffff;
}}
QHeaderView::section {{
    background-color: {bg_tertiary}; color: {text_secondary}; border: none;
    border-right: 1px solid {border}; border-bottom: 2px solid {accent};
    padding: 5px; font-weight: bold;
}}
QTableView#footerTable {{ background-color: {bg_secondary}; color: {warning}; font-weight: bold; border-top: 2px solid {bg_tertiary}; }}

/* QTableWidget - Default alignment for amount/numeric cells */
QTableWidget::item {{ padding: 4px; }}
QTableWidget::item:selected {{ background-color: {selection}; color: #ffffff; }}

/* Scrollbars */
QScrollBar:vertical {{ background: {bg_secondary}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {border}; border-radius: 5px; min-height: 20px; }}
QScrollBar:horizontal {{ background: {bg_secondary}; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {border}; border-radius: 5px; min-width: 20px; }}

/* StatusFilter Component */
QWidget#statusFilterContainer {{ background: {filter_bg}; border-top: 1px solid {filter_border_top}; }}
QWidget#statusFilterContainer QLabel {{ color: {filter_text}; font-size: 11px; font-weight: bold; border: none; }}
QWidget#statusFilterContainer QComboBox {{
    background-color: {filter_combo_bg}; color: {filter_combo_text};
    border: 1px solid {filter_combo_border}; border-radius: 4px; padding: 2px 8px; min-width: 150px;
}}
QWidget#statusFilterContainer QComboBox::drop-down {{ border: none; }}
QWidget#statusFilterContainer QComboBox QAbstractItemView {{
    background-color: {filter_combo_popup_bg}; color: {filter_combo_text};
    selection-background-color: {filter_combo_selection}; border: 1px solid {filter_combo_border};
}}
"""

def get_theme_qss(theme_id="emerald"):
    theme = THEMES.get(theme_id, THEMES["emerald"])
    return QSS_TEMPLATE.format(**theme["colors"])
