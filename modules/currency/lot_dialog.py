"""
Dialogue de sélection des LOTs pour la consommation de devises.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from components.amount_input import AmountInput
from components.dialogs import show_error, show_success
from utils.formatters import format_amount, format_date


class LotSelectionDialog(QDialog):
    """
    Dialogue pour sélectionner un ou plusieurs LOTs pour consommation.
    Supporte deux modes:
    - FIFO: Consommation automatique du plus ancien au plus récent
    - Manuel: L'utilisateur choisit quel LOT consommer
    """

    def __init__(self, service, currency_id, currency_code, amount_to_consume=0.0, parent=None):
        super().__init__(parent)
        self.service = service
        self.currency_id = currency_id
        self.currency_code = currency_code
        self.amount_to_consume = amount_to_consume
        self.selected_lots = {}  # {lot_id: amount_to_consume}

        self.setWindowTitle(f"Consommer {currency_code} - Sélection des LOTs")
        self.setMinimumSize(800, 500)
        self._setup_ui()
        self._load_lots()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Info section
        info_group = QGroupBox("Informations")
        info_layout = QFormLayout()
        self.lbl_currency = QLabel(f"{self.currency_code}")
        self.lbl_currency.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addRow("Devise:", self.lbl_currency)

        self.lbl_amount = QLabel(format_amount(self.amount_to_consume))
        self.lbl_amount.setStyleSheet("font-weight: bold; font-size: 14px; color: #e6edf3;")
        info_layout.addRow("Montant à consommer:", self.lbl_amount)

        self.lbl_total_available = QLabel("0.00")
        info_layout.addRow("Total disponible:", self.lbl_total_available)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # LOTs table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "N°", "Date", "Fournisseur", "Quantité", "Rest", "À consommer"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_fifo = QPushButton("⚡ FIFO (Automatique)")
        self.btn_fifo.clicked.connect(self._apply_fifo)
        self.btn_fifo.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #388bfd; }
        """)
        btn_layout.addWidget(self.btn_fifo)

        self.btn_manual = QPushButton("✓ Confirmer (Manuel)")
        self.btn_manual.clicked.connect(self._confirm_manual)
        self.btn_manual.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        btn_layout.addWidget(self.btn_manual)

        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #30363d; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #484f58; }
        """)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _load_lots(self):
        """Charge les LOTs disponibles"""
        lots = self.service.get_available_lots(self.currency_id)

        self.table.setRowCount(len(lots))
        total_available = 0.0

        for i, lot in enumerate(lots):
            total_available += lot['remaining']

            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(format_date(lot['date'])))
            self.table.setItem(i, 2, QTableWidgetItem(lot['supplier_name']))
            self.table.setItem(i, 3, QTableWidgetItem(format_amount(lot['amount'])))
            self.table.setItem(i, 4, QTableWidgetItem(format_amount(lot['remaining'])))

            # Input pour la quantité à consommer
            input_widget = AmountInput()
            input_widget.setMaximum(lot['remaining'])
            input_widget.setValue(0.0)
            input_widget.valueChanged.connect(lambda val, row=i: self._on_lot_change(row, val))
            self.table.setCellWidget(i, 5, input_widget)

            # Colorer les lignes avec peu de reste
            if lot['remaining'] < lot['amount'] * 0.2:
                for col in range(6):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(QColor("#3d1f00"))

        self.lbl_total_available.setText(format_amount(total_available))

    def _on_lot_change(self, row, value):
        """Callback quand l'utilisateur modifie la quantité à consommer d'un LOT"""
        lot_id = int(self.table.item(row, 0).text())
        if value > 0:
            self.selected_lots[lot_id] = value
        elif lot_id in self.selected_lots:
            del self.selected_lots[lot_id]

    def _apply_fifo(self):
        """Applique la méthode FIFO automatiquement"""
        if self.amount_to_consume <= 0:
            show_error(self, "Erreur", "Veuillez spécifier un montant à consommer.")
            return

        success, message = self.service.consume_from_lots_fifo(self.currency_id, self.amount_to_consume)
        if success:
            show_success(self, "Succès", message)
            self.accept()
        else:
            show_error(self, "Erreur", message)

    def _confirm_manual(self):
        """Confirme la consommation manuelle des LOTs sélectionnés"""
        if not self.selected_lots:
            show_error(self, "Erreur", "Veuillez sélectionner au moins un LOT.")
            return

        total = sum(self.selected_lots.values())
        if self.amount_to_consume > 0 and abs(total - self.amount_to_consume) > 0.01:
            reply = QMessageBox.question(
                self, "Confirmation",
                f"Le total sélectionné ({total:.2f}) ne correspond pas au montant demandé ({self.amount_to_consume:.2f}).\n\n"
                f"Voulez-vous continuer quand même ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Consommer chaque LOT sélectionné
        errors = []
        for lot_id, amount in self.selected_lots.items():
            success, message = self.service.consume_from_lot(lot_id, amount)
            if not success:
                errors.append(f"LOT {lot_id}: {message}")

        if errors:
            show_error(self, "Erreurs", "\n".join(errors))
        else:
            show_success(self, "Succès", "Consommation enregistrée avec succès.")
            self.accept()

    def get_consumed_amount(self) -> float:
        """Retourne le montant total consommé"""
        return sum(self.selected_lots.values())
