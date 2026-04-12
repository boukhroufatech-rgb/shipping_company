"""
Vue pour le module Dashboard - Tableau de Bord Premium
[UPDATED] - Responsive Design avec QSplitter et SizePolicy
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

from datetime import datetime
from .service import DashboardService
from core.themes import THEMES
from modules.settings.service import SettingsService
from components.summary_card import SummaryCard


class DashboardView(QWidget):
    """Vue principale de la Dashboard - Design Responsive"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = DashboardService()
        self._load_theme_colors()
        self._setup_ui()
        self.refresh()
    
    def _load_theme_colors(self):
        try:
            settings = SettingsService()
            theme_id = settings.get_setting("active_theme", "emerald")
            self.theme = THEMES.get(theme_id, THEMES["emerald"])
        except:
            self.theme = THEMES["emerald"]
        self.colors = self.theme["colors"]
    
    def _get_color(self, key, default=""):
        return self.colors.get(key, default)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        bg_main = self._get_color("bg_main", "#0a1f1c")
        text_main = self._get_color("text_main", "#e6edf3")
        text_secondary = self._get_color("text_secondary", "#7d8590")
        border = self._get_color("border", "#214d47")
        accent = self._get_color("accent", "#2ea043")
        
        self.setStyleSheet(f"background-color: {bg_main};")
        
        # -- HEADER --
        header = QHBoxLayout()
        title = QLabel("Tableau de Bord")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {text_main}; border: none;")
        header.addWidget(title)
        header.addStretch()
        date_lbl = QLabel(datetime.now().strftime("%d %B %Y"))
        date_lbl.setStyleSheet(f"color: {text_secondary}; font-size: 12px;")
        header.addWidget(date_lbl)
        layout.addLayout(header)
        
        # -- CARTES KPI (Responsive - Equal width) --
        cards_container = QHBoxLayout()
        cards_container.setSpacing(10)
        
        self.card_dzd = SummaryCard("Liquidite (DA)", "0.00 DA", "#2ecc71", "")
        self.card_foreign = SummaryCard("Devises Etrangeres", "0.00", "#f39c12", "")
        self.card_logistics = SummaryCard("Containers Actifs", "0", "#3498db", "")
        self.card_debts = SummaryCard("Creances", "0.00 DA", "#e74c3c", "")
        
        for card in [self.card_dzd, self.card_foreign, self.card_logistics, self.card_debts]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            cards_container.addWidget(card)
        
        # Equal stretch for all cards
        for _ in range(4):
            cards_container.addStretch(1)
        
        layout.addLayout(cards_container)
        
        # -- GRAPHIQUES (QSplitter for resizing) --
        if PYQTGRAPH_AVAILABLE:
            splitter = QSplitter(Qt.Orientation.Horizontal)
            splitter.setHandleWidth(3)
            splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {border}; }}")
            
            self.chart1_frame = self._create_chart_frame("Repartition par Devise")
            self.chart2_frame = self._create_chart_frame("Historique Transactions")
            
            splitter.addWidget(self.chart1_frame)
            splitter.addWidget(self.chart2_frame)
            splitter.setSizes([400, 600])
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 2)
            
            layout.addWidget(splitter, 1)
        
        # -- TABLEAU ACTIVITÉS --
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._get_color("bg_secondary", "#112e2a")};
                border-radius: 8px; border: 1px solid {border};
            }}
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        table_title = QLabel("Activites Financieres Recentes")
        table_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {text_main}; border: none;")
        table_layout.addWidget(table_title)
        
        self.activity_table = QTableWidget(5, 4)
        self.activity_table.setHorizontalHeaderLabels(["Date", "Type", "Montant", "Description"])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.activity_table.setStyleSheet(f"""
            QTableWidget {{
                border: none; background-color: transparent; color: {text_main};
            }}
            QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {border}; }}
            QHeaderView::section {{
                background-color: {self._get_color("bg_tertiary", "#1a3d38")};
                color: {text_secondary}; padding: 6px; border: none; font-weight: bold;
            }}
        """)
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_table.verticalHeader().setVisible(False)
        table_layout.addWidget(self.activity_table)
        
        # Add stretch to make table flexible
        table_layout.addStretch()
        
        layout.addWidget(table_frame, 1)
        
        # -- BOTTOM STATS --
        stats_container = QHBoxLayout()
        stats_container.setSpacing(10)
        
        for title, color in [
            ("Comptes Actifs", accent),
            ("Transactions Today", "#3498db"),
            ("En Attente", "#f39c12")
        ]:
            box = self._create_stat_box(title, "0", color)
            box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            stats_container.addWidget(box)
        
        # Equal stretch for stats boxes
        for _ in range(3):
            stats_container.addStretch(1)
        
        layout.addLayout(stats_container)
    
    def _create_chart_frame(self, title: str) -> QFrame:
        """Create responsive chart frame"""
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._get_color("bg_secondary", "#112e2a")};
                border-radius: 8px; border: 1px solid {self._get_color("border", "#214d47")};
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            font-size: 13px; font-weight: bold; 
            color: {self._get_color('text_main', '#e6edf3')}; border: none;
        """)
        layout.addWidget(title_lbl)
        
        widget = pg.PlotWidget()
        widget.setBackground(self._get_color("bg_secondary", "#112e2a"))
        widget.setMinimumHeight(150)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(widget)
        
        # Store widget reference for later
        if "Repartition" in title:
            self.bar_widget = widget
        else:
            self.line_widget = widget
        
        return frame
    
    def _create_stat_box(self, title: str, value: str, color: str) -> QFrame:
        """Create responsive stat box"""
        box = QFrame()
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        box.setStyleSheet(f"""
            QFrame {{
                background-color: {self._get_color("bg_secondary", "#112e2a")};
                border-radius: 8px; border: 1px solid {self._get_color("border", "#214d47")};
            }}
        """)
        
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 8, 12, 8)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            font-size: 11px; color: {self._get_color('text_secondary', '#7d8590')}; border: none;
        """)
        
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color}; border: none;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addStretch()
        
        return box
    
    def _update_bar_chart(self, data: dict):
        if not PYQTGRAPH_AVAILABLE or not hasattr(self, 'bar_widget'):
            return
        self.bar_widget.clear()
        values, labels = [], []
        dzd = data.get('dzd', 0)
        if dzd > 0:
            values.append(dzd)
            labels.append("DA")
        for curr in data.get('foreign', []):
            values.append(curr.get('in_dzd', 0))
            labels.append(curr.get('code', ''))
        if values:
            x = list(range(len(values)))
            bar = pg.BarGraphItem(x=x, height=values, width=0.6, brush='#2ea043')
            self.bar_widget.addItem(bar)
            self.bar_widget.getAxis('bottom').setTicks([list(zip(x, labels))])
    
    def _update_line_chart(self, history: list):
        if not PYQTGRAPH_AVAILABLE or not hasattr(self, 'line_widget') or not history:
            return
        self.line_widget.clear()
        x = list(range(len(history)))
        y = history
        colors = ["#27ae60" if v >= 0 else "#e74c3c" for v in y]
        bar = pg.BarGraphItem(x=x, height=y, width=0.5, brushes=colors)
        self.line_widget.addItem(bar)

    def refresh(self):
        data = self.service.get_summary_data()
        
        # Update cards
        dzd_val = data['real']['total_dzd']
        self.card_dzd.set_value(f"{dzd_val:,.2f} DA")
        
        foreign_dzd = data['real']['total_foreign_dzd']
        foreign_str = " | ".join([f"{f['symbol']} {f['amount']:,.0f}" for f in data['real']['foreign_details']])
        self.card_foreign.set_value(f"Eq: {foreign_dzd:,.0f} DA\n{foreign_str or 'Aucune'}")
        
        log = data['real_logistics']
        self.card_logistics.set_value(f"{log['active_containers']} | {log['pending_arrival']} en attente")
        
        debts = data['real_debts']
        self.card_debts.set_value(f"Creances: {debts['customer_receivables']:,.0f} DA\nDettes: {debts['supplier_payables']:,.0f} DA")
        
        # Update charts
        if PYQTGRAPH_AVAILABLE:
            pie_data = {'dzd': dzd_val, 'foreign': data['real']['foreign_details']}
            self._update_bar_chart(pie_data)
            trans_history = data['real'].get('trans_history', [])
            self._update_line_chart(trans_history)
        
        # Update table
        recent = data['real']['recent_transactions']
        self.activity_table.setRowCount(len(recent))
        for i, t in enumerate(recent):
            self.activity_table.setItem(i, 0, QTableWidgetItem(t['date']))
            self.activity_table.setItem(i, 1, QTableWidgetItem(t['type']))
            self.activity_table.setItem(i, 2, QTableWidgetItem(t['amount']))
            self.activity_table.setItem(i, 3, QTableWidgetItem(t['desc']))
            if self.activity_table.item(i, 1):
                color = QColor("#27ae60") if t['type'] == "CREDIT" else QColor("#e74c3c")
                self.activity_table.item(i, 1).setForeground(color)