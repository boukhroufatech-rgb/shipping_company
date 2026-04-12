"""
Composant de simulation (Simulation Display)
[UNIFIED] 2026-04-08 - Affichage unifié de la simulation dans tout le programme

Usage:
    from components.simulation_display import SimulationDisplay
    
    # Simulation simple (montant + currency)
    sim = SimulationDisplay()
    sim.set_amount(1000, "DA")
    
    # Simulation avec taux de change
    sim = SimulationDisplay(simulation_type="currency")
    sim.set_amount(100, "EUR")
    sim.set_currency_rate(145)
    # Affiche: 100 EUR = 14,500 DA
    
    # Simulation multi-devises
    sim = SimulationDisplay(simulation_type="multi")
    sim.add_conversion(100, "EUR", 145)
    sim.add_conversion(50, "USD", 135)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont


class SimulationDisplay(QWidget):
    """
    Composant unifié pour afficher la simulation.
    - Affiche le montant calculé avec le taux de change
    - Style cohérent dans tout le programme
    - Supporte plusieurs types de simulation
    """
    
    def __init__(self, simulation_type="simple", parent=None):
        super().__init__(parent)
        self.simulation_type = simulation_type  # "simple", "currency", "multi"
        self.amount = 0.0
        self.currency = "DA"
        self.conversions = []  # Pour type "multi"
        self._setup_ui()
    
    def _setup_ui(self):
        self.main_frame = QFrame()
        self.main_frame.setObjectName("simulationFrame")
        self.main_frame.setStyleSheet("""
            QFrame#simulationFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_frame)
        
        inner_layout = QVBoxLayout(self.main_frame)
        inner_layout.setContentsMargins(8, 8, 8, 8)
        inner_layout.setSpacing(4)
        
        # Label principal
        self.main_label = QLabel()
        self.main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_label.setStyleSheet("""
            color: #58a6ff;
            font-size: 14px;
            font-weight: bold;
        """)
        inner_layout.addWidget(self.main_label)
        
        # Label secondaire (pour les détails)
        self.detail_label = QLabel()
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setStyleSheet("""
            color: #8b949e;
            font-size: 11px;
        """)
        inner_layout.addWidget(self.detail_label)
        
        self._update_display()
    
    def _update_display(self):
        """Met à jour l'affichage selon le type de simulation"""
        if self.simulation_type == "simple":
            self._update_simple()
        elif self.simulation_type == "currency":
            self._update_currency()
        elif self.simulation_type == "multi":
            self._update_multi()
    
    def _update_simple(self):
        """Simulation simple: juste le montant"""
        formatted = self._format_amount(self.amount)
        self.main_label.setText(f"💰 {formatted} {self.currency}")
        self.detail_label.setText("")
    
    def _update_currency(self):
        """Simulation avec taux de change"""
        if hasattr(self, 'rate') and self.rate:
            converted = self.amount * self.rate
            converted_formatted = self._format_amount(converted)
            main_formatted = self._format_amount(self.amount)
            
            self.main_label.setText(f"💱 {main_formatted} {self.currency} = {converted_formatted} DA")
            self.detail_label.setText(f"Taux: {self.rate:.2f}")
        else:
            self.main_label.setText(f"💰 {self._format_amount(self.amount)} {self.currency}")
            self.detail_label.setText("Taux: --")
    
    def _update_multi(self):
        """Simulation multi-devises"""
        if not self.conversions:
            self.main_label.setText("Aucune conversion")
            self.detail_label.setText("")
            return
        
        total_dzd = 0
        lines = []
        for amount, currency, rate in self.conversions:
            converted = amount * rate
            total_dzd += converted
            lines.append(f"{self._format_amount(amount)} {currency} = {self._format_amount(converted)} DA")
        
        self.main_label.setText(f"💰 Total: {self._format_amount(total_dzd)} DA")
        self.detail_label.setText("\n".join(lines))
    
    def _format_amount(self, value):
        """Formate le montant avec des espaces comme séparateur de milliers"""
        return f"{value:,.0f}".replace(",", " ")
    
    def set_amount(self, amount, currency="DA"):
        """Définit le montant de base"""
        self.amount = float(amount) if amount else 0.0
        self.currency = currency
        self._update_display()
    
    def set_currency_rate(self, rate):
        """Définit le taux de change (pour type 'currency')"""
        self.rate = float(rate) if rate else 0.0
        self._update_display()
    
    def add_conversion(self, amount, currency, rate):
        """Ajoute une conversion (pour type 'multi')"""
        self.conversions.append((amount, currency, rate))
        self._update_display()
    
    def clear_conversions(self):
        """Efface toutes les conversions"""
        self.conversions = []
        self._update_display()
    
    def set_total(self, total, currency="DA"):
        """Définit un total (pour affichage simple)"""
        self.amount = float(total) if total else 0.0
        self.currency = currency
        self._update_display()
    
    def hide(self):
        """Cache le composant"""
        super().hide()
    
    def show(self):
        """Affiche le composant"""
        super().show()
    
    def set_visible(self, visible):
        """Affiche ou cache selon la valeur"""
        if visible:
            self.show()
        else:
            self.hide()


class AmountSimulationLabel(QLabel):
    """
    Version simplifiée - juste un QLabel avec style unifié
    Usage: label = AmountSimulationLabel(); label.set_amount(1000, "DA")
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.amount = 0.0
        self.currency = "DA"
        self._set_style()
    
    def _set_style(self):
        self.setStyleSheet("""
            QLabel {
                background-color: #0d1117;
                color: #58a6ff;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
        """)
    
    def set_amount(self, amount, currency="DA"):
        self.amount = float(amount) if amount else 0.0
        self.currency = currency
        formatted = f"{self.amount:,.0f}".replace(",", " ")
        self.setText(f"💰 {formatted} {currency}")
    
    def set_converted(self, from_amount, from_currency, to_amount, to_currency, rate):
        """Affiche le montant converti"""
        from_formatted = f"{from_amount:,.0f}".replace(",", " ")
        to_formatted = f"{to_amount:,.0f}".replace(",", " ")
        self.setText(f"💱 {from_formatted} {from_currency} → {to_formatted} {to_currency}\nTaux: {rate:.2f}")
    
    def clear(self):
        self.setText("")