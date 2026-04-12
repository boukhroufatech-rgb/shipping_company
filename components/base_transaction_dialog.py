"""
Base Transaction Dialog Component - Professional Pattern
Réutilisable pour tous les dialogues de transactions financières
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QTextEdit, QDateEdit, QDialogButtonBox,
    QWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor

from components.amount_input import AmountInput
from components.dialogs import show_error, show_success


class BaseTransactionDialog(QDialog):
    """
    Classe de base pour les dialogues de transactions financières.
    Gère automatiquement l'affichage du solde lors de la sélection d'entité.
    
    Usage:
        class MyDialog(BaseTransactionDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.entity_service = my_service  # Service pour récupérer le solde
                self._setup_ui()
                
                # Configurer les paramètres de l'entité
                self.set_entity_config(
                    label="Client:",
                    get_entities_func=lambda: [(c['name'], c['id']) for c in service.get_all_customers()],
                    get_balance_func=lambda cid: service.get_customer_balance(cid)
                )
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entity_config = None
        self._amount_input = None
        self._sim_label = None
        
    def set_entity_config(self, label: str, get_entities_func, get_balance_func, 
                         entity_name: str = "Entité", currency: str = "DA"):
        """Configurer les paramètres de l'entité (client/fournisseur/partenaire)"""
        self._entity_config = {
            "label": label,
            "get_entities": get_entities_func,
            "get_balance": get_balance_func,
            "entity_name": entity_name,
            "currency": currency
        }
    
    def _create_entity_field(self, layout: QFormLayout, extra_widgets: list = None):
        """Créer le champ d'entité avec affichage du solde"""
        if not self._entity_config:
            return None
            
        # Entity combo
        self._entity_combo = QComboBox()
        self._entity_combo.setEditable(True)
        self._entity_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._entity_combo.lineEdit().setPlaceholderText(f"Rechercher {self._entity_config['entity_name']}...")
        
        # Load entities
        for name, id in self._entity_config["get_entities"]():
            self._entity_combo.addItem(name, id)
        
        # Balance label
        self._balance_label = QLabel()
        self._balance_label.setStyleSheet("""
            QLabel {
                color: #7d8590;
                font-size: 12px;
                padding: 4px;
            }
        """)
        
        # Connect signal
        self._entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        
        # Add to layout
        layout.addRow(self._entity_config["label"], self._entity_combo)
        layout.addRow("", self._balance_label)
        
        # Initial balance
        self._on_entity_changed()
        
        return self._entity_combo
    
    def _create_amount_field(self, layout: QFormLayout, label: str = "Montant:"):
        """Créer le champ de montant avec simulation"""
        self._amount_input = AmountInput(currency_symbol=self._entity_config["currency"] if self._entity_config else "DA")
        self._amount_input.valueChanged.connect(self._update_simulation)
        
        layout.addRow(label, self._amount_input)
        
        # Simulation label
        self._sim_label = QLabel()
        self._sim_label.setStyleSheet("""
            QLabel {
                background-color: #0d1117;
                color: #e6edf3;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addRow("", self._sim_label)
        
        return self._amount_input
    
    def _create_date_field(self, layout: QFormLayout, label: str = "Date:", default_date: QDate = None):
        """Créer le champ de date"""
        date_edit = QDateEdit()
        date_edit.setDate(default_date or QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setFixedWidth(140)
        layout.addRow(label, date_edit)
        return date_edit
    
    def _create_text_field(self, layout: QFormLayout, label: str, placeholder: str = "", height: int = 0):
        """Créer un champ de texte ou textarea"""
        if height > 0:
            widget = QTextEdit()
            widget.setMaximumHeight(height)
            widget.setPlaceholderText(placeholder)
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(placeholder)
        layout.addRow(label, widget)
        return widget
    
    def _create_combo_field(self, layout: QFormLayout, label: str, options: list):
        """Créer un champ dropdown"""
        combo = QComboBox()
        for name, value in options:
            combo.addItem(name, value)
        layout.addRow(label, combo)
        return combo
    
    def _create_buttons(self, layout: QVBoxLayout, accept_text: str = "Enregistrer", reject_text: str = "Annuler"):
        """Créer les boutons standard"""
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        
        # Customize button text
        btn_ok = btns.button(QDialogButtonBox.StandardButton.Ok)
        btn_ok.setText(accept_text)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        
        btn_cancel = btns.button(QDialogButtonBox.StandardButton.Cancel)
        btn_cancel.setText(reject_text)
        
        layout.addWidget(btns)
        return btns
    
    def _on_entity_changed(self):
        """Callback when entity selection changes"""
        if not self._entity_config or not hasattr(self, '_balance_label'):
            return
            
        entity_id = self._entity_combo.currentData()
        if entity_id and self._entity_config["get_balance"]:
            balance = self._entity_config["get_balance"](entity_id)
            currency = self._entity_config.get("currency", "DA")
            self._balance_label.setText(f"💰 Solde actuel: {balance:,.2f} {currency}")
        else:
            self._balance_label.setText("")
        
        # Update simulation if amount exists
        if hasattr(self, '_amount_input'):
            self._update_simulation()
    
    def _update_simulation(self):
        """Mettre à jour la simulation du nouveau solde"""
        if not self._entity_config or not hasattr(self, '_sim_label') or not hasattr(self, '_amount_input'):
            return
            
        entity_id = self._entity_combo.currentData()
        if not entity_id:
            self._sim_label.setText("")
            return
        
        current_balance = self._entity_config["get_balance"](entity_id)
        amount = self._amount_input.get_amount()
        new_balance = current_balance - amount
        currency = self._entity_config.get("currency", "DA")
        
        if new_balance > 0:
            color = "#f0883e"  # Orange
            status = f"➖ Remaining: {new_balance:,.2f} {currency}"
        elif new_balance == 0:
            color = "#2ecc71"  # Green
            status = "✅ Soldé!"
        else:
            color = "#2ecc71"  # Green (credit)
            status = f"✓ Credit: {abs(new_balance):,.2f} {currency}"
        
        self._sim_label.setText(f"💡 Après opération: <span style='color: {color}'>{status}</span>")
    
    def _validate_and_accept(self):
        """Validation par défaut - peut être surchargée"""
        if hasattr(self, '_entity_combo') and not self._entity_combo.currentData():
            show_error(self, "Erreur", f"Veuillez sélectionner {self._entity_config['entity_name']}")
            return
        if hasattr(self, '_amount_input') and self._amount_input.get_amount() <= 0:
            show_error(self, "Erreur", "Le montant doit être supérieur à 0")
            return
        self.accept()
    
    def get_entity_id(self):
        """Récupérer l'ID de l'entité sélectionnée"""
        return self._entity_combo.currentData() if hasattr(self, '_entity_combo') else None
    
    def get_amount(self):
        """Récupérer le montant"""
        return self._amount_input.get_amount() if hasattr(self, '_amount_input') else 0