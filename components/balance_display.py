"""
Composant de'affichage du solde (Balance Display)
[UNIFIED] 2026-04-08 - Affichage unifié du solde dans tout le programme

Usage:
    from components.balance_display import BalanceDisplay
    
    # Pour client
    balance = BalanceDisplay("client")
    balance.set_value(5000, "DA")
    balance.set_customer_id(customer_id)
    
    # Pour compte treasurie
    balance = BalanceDisplay("account")  
    balance.set_value(10000, "EUR")
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class BalanceDisplay(QWidget):
    """
    Composant unifié pour afficher le solde.
    - Affiche le solde à côté d'un ComboBox
    - Se met à jour automatiquement lors du changement de sélection
    - Couleur: vert pour positif, rouge pour négatif
    """
    
    balanceChanged = pyqtSignal(float, str)  # amount, currency
    
    def __init__(self, display_type="client", parent=None):
        super().__init__(parent)
        self.display_type = display_type  # "client", "account", "supplier"
        self.current_value = 0.0
        self.currency = "DA"
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self.icon_label = QLabel("💰")
        self.icon_label.setStyleSheet("font-size: 14px;")
        
        self.value_label = QLabel("Solde: 0")
        self.value_label.setObjectName("balanceValue")
        self._update_style()
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def _update_style(self):
        """Met à jour le style selon le type de solde"""
        if self.current_value > 0:
            color = "#238636"  # Vert - positif
            symbol = "+"
        elif self.current_value < 0:
            color = "#f85149"  # Rouge - négatif
            symbol = ""
        else:
            color = "#7d8590"  # Gris - neutre
            symbol = ""
        
        formatted = f"{self.current_value:,.0f} {self.currency}".replace(",", " ")
        self.value_label.setText(f"Solde: {symbol}{formatted}")
        self.value_label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            font-weight: bold;
        """)
    
    def set_value(self, amount, currency="DA"):
        """Définit la valeur du solde"""
        self.current_value = float(amount) if amount else 0.0
        self.currency = currency
        self._update_style()
        self.balanceChanged.emit(self.current_value, self.currency)
    
    def set_customer_id(self, customer_id, service=None):
        """Définit l'ID du client pour mise à jour automatique"""
        self.target_id = customer_id
        self.service = service
        if service and customer_id:
            self._load_customer_balance(customer_id)
    
    def set_account_id(self, account_id, service=None):
        """Définit l'ID du compte pour mise à jour automatique"""
        self.target_id = account_id
        self.service = service
        if service and account_id:
            self._load_account_balance(account_id)
    
    def set_supplier_id(self, supplier_id, service=None):
        """Définit l'ID du fournisseur pour mise à jour automatique"""
        self.target_id = supplier_id
        self.service = service
        if service and supplier_id:
            self._load_supplier_balance(supplier_id)
    
    def _load_customer_balance(self, customer_id):
        """Charge le solde du client"""
        if self.service:
            try:
                customer = self.service.get_customer(customer_id)
                if customer:
                    self.set_value(customer.get('balance', 0), "DA")
            except:
                pass
    
    def _load_account_balance(self, account_id):
        """Charge le solde du compte"""
        if self.service:
            try:
                account = self.service.get_account(account_id)
                if account:
                    currency = account.get('currency', 'DA')
                    self.set_value(account.get('balance', 0), currency)
            except:
                pass
    
    def _load_supplier_balance(self, supplier_id):
        """Charge le solde du fournisseur"""
        if self.service:
            try:
                supplier = self.service.get_supplier(supplier_id)
                if supplier:
                    self.set_value(supplier.get('balance', 0), "DA")
            except:
                pass
    
    def update_from_combo(self, combo, service=None):
        """Met à jour le solde depuis un ComboBox (pour les dialogs existants)"""
        self.service = service
        current_id = combo.currentData()
        if current_id:
            if self.display_type == "client":
                self._load_customer_balance(current_id)
            elif self.display_type == "account":
                self._load_account_balance(current_id)
            elif self.display_type == "supplier":
                self._load_supplier_balance(current_id)
    
    def clear(self):
        """Efface le solde"""
        self.set_value(0, "DA")