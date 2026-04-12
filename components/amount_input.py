"""
Widget de saisie de montants avec formatage automatique
"""
from PyQt6.QtWidgets import QLineEdit, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import pyqtSignal, Qt, QLocale
from PyQt6.QtGui import QDoubleValidator

from utils.formatters import format_amount, parse_amount


class AmountInput(QWidget):
    """
    Widget de saisie de montants avec formatage automatique.
    Format: 15 000.00 DA
    """
    
    valueChanged = pyqtSignal(float)
    
    def __init__(self, currency_symbol: str = "DA", parent=None):
        super().__init__(parent)
        self.currency_symbol = currency_symbol
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Champ de saisie
        self.input = QLineEdit()
        self.input.setPlaceholderText("0.00")
        self.input.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Validateur pour n'accepter que des nombres
        # Utiliser QLocale.c() pour forcer le point comme séparateur décimal dans le validateur
        validator = QDoubleValidator(0.0, 999999999.99, 2)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        validator.setLocale(QLocale.c())
        self.input.setValidator(validator)
        
        # Label pour le symbole de devise
        self.symbol_label = QLabel(self.currency_symbol)
        self.symbol_label.setStyleSheet("font-weight: bold;")
        
        layout.addWidget(self.input)
        layout.addWidget(self.symbol_label)
        
        # Connecter les signaux
        self.input.textChanged.connect(self._on_text_changed)
        self.input.editingFinished.connect(self._format_display)
    
    def _on_text_changed(self, text: str):
        """Appelé quand le texte change"""
        try:
            # Remplacer la virgule par un point pour le float() et retirer les espaces
            clean_text = text.replace(" ", "").replace(",", ".")
            if clean_text:
                try:
                    value = float(clean_text)
                    self.valueChanged.emit(value)
                except ValueError:
                    pass
        except ValueError:
            pass
    
    def _format_display(self):
        """Formate l'affichage du montant"""
        try:
            value = self.value()
            if value > 0:
                # Formater avec espaces pour les milliers
                formatted = f"{value:,.2f}".replace(",", " ")
                self.input.setText(formatted)
        except ValueError:
            pass
    
    def get_amount(self) -> float:
        """Alias pour value() pour compatibilité"""
        return self.value()

    def value(self) -> float:
        """
        Retourne la valeur actuelle.
        
        Returns:
            Valeur en float
        """
        # Remplacer la virgule par un point et retirer les espaces
        text = self.input.text().replace(" ", "").replace(",", ".")
        try:
            return float(text) if text else 0.0
        except ValueError:
            return 0.0
    
    def setValue(self, value: float):
        """
        Définit la valeur.
        
        Args:
            value: Valeur à définir
        """
        if value > 0:
            formatted = f"{value:,.2f}".replace(",", " ")
            self.input.setText(formatted)
        else:
            self.input.clear()
    
    def setCurrencySymbol(self, symbol: str):
        """
        Change le symbole de devise.
        
        Args:
            symbol: Nouveau symbole
        """
        self.currency_symbol = symbol
        self.symbol_label.setText(symbol)

    def set_currency_symbol(self, symbol: str):
        """Alias pour setCurrencySymbol"""
        self.setCurrencySymbol(symbol)
    
    def clear(self):
        """Efface le champ"""
        self.input.clear()
    
    def setReadOnly(self, readonly: bool):
        """
        Définit le mode lecture seule.
        
        Args:
            readonly: True pour lecture seule
        """
        self.input.setReadOnly(readonly)
    
    def setPlaceholderText(self, text: str):
        """
        Définit le texte d'espace réservé.
        
        Args:
            text: Texte à afficher
        """
        self.input.setPlaceholderText(text)
