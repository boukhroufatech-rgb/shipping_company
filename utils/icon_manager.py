"""
🖌️ IconManager - SVG Dynamic Tinting Engine
------------------------------------------
Charge et colorise les icônes SVG pour correspondre au Design System.
"""
import os
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, Qt

class IconManager:
    _cache = {}
    _icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")
    _emoji_map = {
        "💸": "hand-coins",
        "💵": "briefcase",
        "🔁": "refresh-cw",
        "➕": "plus",
        "👁️": "search",
        "❌": "trash-2",
        "🔄": "refresh-cw",
        "📜": "scroll",
        "💰": "hand-coins",
        "📈": "layout-dashboard",
    }
    
    _fallback_map = {
        "money-dollar": "hand-coins",
        "banknote": "briefcase",
        "eye": "search",
        "x": "trash-2",
    }

    @classmethod
    def get_icon(cls, name: str, color: str = "#2ea043", size: int = 24) -> QIcon:
        """
        Génère une icône SVG teintée dynamiquement.
        Args:
            name: Nom du fichier SVG (sans extension) ou emoji
            color: Code hexadécimal de la couleur (Accent)
            size: Taille de rendu
        """
        # Map emoji to icon name if needed
        if name in cls._emoji_map:
            name = cls._emoji_map[name]
        
        # Fallback for unknown icon names
        if name in cls._fallback_map:
            name = cls._fallback_map[name]
        
        cache_key = f"{name}_{color}_{size}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        svg_full_path = os.path.join(cls._icon_path, f"{name}.svg")
        
        # If not found, try fallback
        if not os.path.exists(svg_full_path) and name in cls._fallback_map:
            name = cls._fallback_map[name]
            svg_full_path = os.path.join(cls._icon_path, f"{name}.svg")
        
        if not os.path.exists(svg_full_path):
            print(f"⚠️ IconManager: {name}.svg non trouvé.")
            return QIcon()

        try:
            # Lire le SVG original
            with open(svg_full_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()

            # Remplacement dynamique de la couleur (Baseline: currentColor ou #FFFFFF)
            # On assume que le SVG utilise stroke="currentColor" ou un placeholder
            tinted_svg = svg_data.replace('currentColor', color).replace('#FFFFFF', color)

            # Rendu via QSvgRenderer
            renderer = QSvgRenderer(tinted_svg.encode('utf-8'))
            
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

            icon = QIcon(pixmap)
            cls._cache[cache_key] = icon
            return icon

        except Exception as e:
            print(f"❌ Erreur IconManager ({name}): {e}")
            return QIcon()

    @classmethod
    def get_main_icon(cls, theme_id: str, icon_name: str) -> QIcon:
        """Helper pour récupérer une icône de tab basée sur le thème actif"""
        from core.themes import THEMES
        accent_color = THEMES.get(theme_id, THEMES["emerald"])["colors"]["accent"]
        return cls.get_icon(icon_name, color=accent_color)
