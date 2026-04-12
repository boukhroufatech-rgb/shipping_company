"""
Composant SummaryCard pour afficher des indicateurs clés (KPI)
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False


class MiniChart(QWidget):
    """Mini chart widget for displaying sparkline trends"""
    
    def __init__(self, data: list = None, color: str = "#27ae60", parent=None):
        super().__init__(parent)
        self.data = data or [0, 0, 0, 0, 0]
        self.color = color
        self.setMinimumSize(100, 30)
        self.setMaximumSize(150, 40)
    
    def set_data(self, data: list):
        self.data = data
        self.update()
    
    def paintEvent(self, event):
        if not self.data or len(self.data) < 2:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Calculate points
        min_val = min(self.data)
        max_val = max(self.data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        points = []
        for i, val in enumerate(self.data):
            x = (i / (len(self.data) - 1)) * w
            y = h - ((val - min_val) / range_val) * (h - 4) - 2
            points.append((x, y))
        
        # Draw line
        pen = QPen(QColor(self.color))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPolyline([p for p in points])
        
        # Draw area fill
        painter.setBrush(QBrush(QColor(self.color + "30")))
        poly = points + [(w, h), (0, h)]
        painter.drawPolygon(poly)


class SummaryCard(QFrame):
    """
    Card widget for displaying key metrics with high-end aesthetics.
    Features: Icon support, dynamic colors, shadows, and clean typography.
    """
    
    def __init__(self, title: str, value: str = "0.00", color: str = "#3498db", icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        self.icon_char = icon
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure the look and feel of the card"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(200, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Get theme colors dynamically
        try:
            from modules.settings.service import SettingsService
            settings = SettingsService()
            theme_id = settings.get_setting("active_theme", "emerald")
            from core.themes import THEMES
            theme = THEMES.get(theme_id, THEMES["emerald"])
            bg_color = theme["colors"].get("bg_secondary", "#112e2a")
            text_main = theme["colors"].get("text_main", "#e6edf3")
            text_secondary = theme["colors"].get("text_secondary", "#7d8590")
            border_color = theme["colors"].get("border", "#214d47")
        except:
            # Fallback to default theme
            bg_color = "#112e2a"
            text_main = "#e6edf3"
            text_secondary = "#7d8590"
            border_color = "#214d47"
        
        # Modern CSS Styling - Theme-aware
        style = f"""
            SummaryCard {{
                background-color: {bg_color};
                border-left: 6px solid {self.color};
                border-radius: 10px;
                border: 1px solid {border_color};
            }}
            QLabel#Title {{
                color: {text_secondary};
                font-size: 13px;
                font-weight: 500;
                text-transform: uppercase;
            }}
            QLabel#Value {{
                color: {text_main};
                font-size: 22px;
                font-weight: bold;
            }}
            QLabel#Icon {{
                font-size: 28px;
                background-color: transparent;
            }}
        """
        self.setStyleSheet(style)
        
        # Drop Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Content Layout
        content_layout = QVBoxLayout()
        
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("Title")
        
        self.value_label = QLabel(self.value)
        self.value_label.setObjectName("Value")
        
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.value_label)
        content_layout.addStretch()
        
        # Icon
        self.icon_label = QLabel(self.icon_char)
        self.icon_label.setObjectName("Icon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        layout.addWidget(self.icon_label)

    def set_value(self, value: str):
        """Update the displayed value"""
        self.value_label.setText(value)
        
    def set_title(self, title: str):
        """Update the displayed title"""
        self.title_label.setText(title)

    def set_color(self, color: str):
        """Update the accent color and border style"""
        self.color = color
        self._setup_ui()
    
    def set_chart_data(self, data: list):
        """Add mini chart to the card"""
        if not hasattr(self, '_chart'):
            self._chart = MiniChart(data, self.color)
            # Insert chart before the icon
            self.layout().insertWidget(2, self._chart, 1)
        else:
            self._chart.set_data(data)


class AnimatedLabel(QLabel):
    """Animated label that counts up/down to a value"""
    
    def __init__(self, end_value: float = 0, prefix: str = "", suffix: str = "", 
                 duration: int = 1000, parent=None):
        super().__init__(parent)
        self.end_value = end_value
        self.prefix = prefix
        self.suffix = suffix
        self.duration = duration
        self.current_value = 0
        self._start_ani()
    
    def _start_ani(self):
        from PyQt6.QtCore import QTimer
        steps = 30
        interval = self.duration / steps
        self.step_value = (self.end_value - self.current_value) / steps
        self.step_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_value)
        self.timer.start(int(interval))
    
    def _update_value(self):
        self.step_count += 1
        self.current_value += self.step_value
        if self.step_count >= 30:
            self.current_value = self.end_value
            self.timer.stop()
        self.setText(f"{self.prefix}{self.current_value:,.2f}{self.suffix}")
    
    def set_value(self, value: float):
        """Set new target value for animation"""
        self.end_value = value
        self.current_value = 0
        self._start_ani()


class TrendLabel(QLabel):
    """Label showing trend indicator with color"""
    
    def __init__(self, value: float = 0, parent=None):
        super().__init__(parent)
        self.set_value(value)
    
    def set_value(self, value: float):
        if value > 0:
            self.setText(f"⬆ {value:+.1f}%")
            self.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif value < 0:
            self.setText(f"⬇ {value:.1f}%")
            self.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            self.setText("➖ 0%")
            self.setStyleSheet("color: #7f8c8d;")
