"""
Wizard 3 Etapes pour creer ou modifier une Facture avec Conteneurs et Marchandises
Step 1: Facture (BILL)
Step 2: Conteneurs
Step 3: Marchandises par Conteneur
"""
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFormLayout, QComboBox,
    QDateEdit, QTextEdit, QGroupBox, QStackedWidget,
    QSpinBox, QDoubleSpinBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor
from datetime import datetime

from components.amount_input import AmountInput
from components.dialogs import show_error, show_success, confirm_action, create_quick_add_layout
from components.enhanced_table import EnhancedTableView
from components.catalog_dialog import GenericCatalogDialog
from utils.formatters import format_amount
from utils.logger import log_error


class ShipmentWizard(QDialog):
    """Assistant de creation/modification de Facture: 3 etapes"""
    dataSaved = pyqtSignal()

    def __init__(self, logistics_service, currency_service, treasury_service,
                 customer_service, edit_container_id=None, parent=None):
        super().__init__(parent)
        self.logistics_service = logistics_service
        self.currency_service = currency_service
        self.treasury_service = treasury_service
        self.customer_service = customer_service

        from modules.logistics.expense_service import ExpenseService
        self.expense_service = ExpenseService()

        self.edit_container_id = edit_container_id
        self.is_edit = edit_container_id is not None
        self.current_step = 0
        self.containers_data = []  # [{"number": "MSKU123", "goods": [...]}]

        if self.is_edit:
            self.setWindowTitle("Modifier Facture")
        else:
            self.setWindowTitle("Nouvelle Facture")

        self.setMinimumSize(700, 550)
        self._setup_ui()
        self._load_data()
        if self.is_edit:
            self._load_edit_data()
        self._update_step()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # === Indicateur d'etapes ===
        steps_bar = QHBoxLayout()
        self.step_indicators = []
        step_names = ["1. Facture (BILL)", "2. Conteneurs", "3. Marchandises"]
        for i, name in enumerate(step_names):
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_layout.addWidget(lbl)
            frame.setFixedHeight(40)
            steps_bar.addWidget(frame)
            self.step_indicators.append(frame)
        layout.addLayout(steps_bar)

        # === Separateur ===
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #30363d;")
        layout.addWidget(sep)

        # === Pages ===
        self.stack = QStackedWidget()

        self.page1 = self._build_step1()
        self.stack.addWidget(self.page1)

        self.page2 = self._build_step2()
        self.stack.addWidget(self.page2)

        self.page3 = self._build_step3()
        self.stack.addWidget(self.page3)

        layout.addWidget(self.stack)

        # === Navigation ===
        nav = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setStyleSheet("padding: 10px 20px;")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_prev = QPushButton("< precedent")
        self.btn_prev.setStyleSheet("padding: 10px 20px;")
        self.btn_prev.clicked.connect(self._prev_step)

        self.btn_add_expense = QPushButton("+ Ajouter Coût")
        self.btn_add_expense.setStyleSheet("padding: 10px 20px; background-color: #388bfd; color: white;")
        self.btn_add_expense.clicked.connect(self._add_expense)

        self.page_label = QLabel("Etape 1/3")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("font-weight: bold; color: #58a6ff;")

        self.btn_confirm = QPushButton("Confirmer")
        self.btn_confirm.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #238636; color: white;")
        self.btn_confirm.clicked.connect(self._confirm)

        self.btn_next = QPushButton("Suivant >")
        self.btn_next.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #1f6feb; color: white;")
        self.btn_next.clicked.connect(self._next_step)

        nav.addWidget(self.btn_cancel)
        nav.addWidget(self.btn_prev)
        nav.addWidget(self.btn_add_expense)
        nav.addStretch()
        nav.addWidget(self.page_label)
        nav.addStretch()
        nav.addWidget(self.btn_confirm)
        nav.addWidget(self.btn_next)
        layout.addLayout(nav)

    # ========================================================================
    # PAGE 1: Facture BILL
    # ========================================================================

    def _build_step1(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Information Facture BILL")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff; padding: 4px;")
        layout.addWidget(title)

        form = QFormLayout()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setFixedWidth(140)
        form.addRow("Date:", self.date_input)

        self.bill_input = QLineEdit()
        self.bill_input.setPlaceholderText("N° de BILL...")
        form.addRow("N° BILL:", self.bill_input)

        self.agent_combo = QComboBox()
        self.agent_widget = create_quick_add_layout(self.agent_combo, self._quick_add_agent)
        form.addRow("Agent Maritime:", self.agent_widget)

        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("N° de facture...")
        form.addRow("N° Facture:", self.invoice_input)

        self.license_combo = QComboBox()
        if self.is_edit:
            licenses = self.logistics_service.get_all_licenses(filter_status="all")
        else:
            licenses = self.logistics_service.get_all_licenses(filter_status="active")
        for lic in licenses:
            remaining = lic['remaining_usd']
            self.license_combo.addItem(
                f"{lic['supplier_name']} ({remaining:.2f} $ restant)", lic['id']
            )
        self.license_widget = create_quick_add_layout(self.license_combo, self._quick_add_license)
        form.addRow("Licence:", self.license_widget)

        self.shipment_type_combo = QComboBox()
        self.shipment_type_combo.addItem("🚢 Maritime", "MARITIME")
        self.shipment_type_combo.addItem("🚚 Terrestre", "TERRESTRIAL")
        self.shipment_type_combo.addItem("✈️ Aérien", "AERIAL")
        form.addRow("Type de Shp:", self.shipment_type_combo)

        self.transfer_amount = AmountInput()
        self.transfer_amount.input.textChanged.connect(self._calculate_equivalent)
        form.addRow("Montant Transfert Bancaire (USD):", self.transfer_amount)

        self.exchange_rate = AmountInput()
        self.exchange_rate.input.textChanged.connect(self._calculate_equivalent)
        form.addRow("Taux de Change:", self.exchange_rate)

        self.equivalent_label = QLabel("= 0.00 DA")
        self.equivalent_label.setStyleSheet("font-weight: bold; color: #238636; font-size: 16px; padding: 4px;")
        form.addRow("Equivalent DA:", self.equivalent_label)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Ex: Alger, Oran...")
        form.addRow("Port:", self.port_input)

        self.transitaire_input = QLineEdit()
        self.transitaire_input.setPlaceholderText("Nom du transitaire...")
        form.addRow("Transitaire:", self.transitaire_input)

        self.shipment_rate = AmountInput()
        self.shipment_rate.input.textChanged.connect(self._calculate_expedition)
        form.addRow("Taux de change expedition:", self.shipment_rate)

        self.expedition_label = QLabel("= 0.00 DA")
        self.expedition_label.setStyleSheet("font-weight: bold; color: #238636; font-size: 16px; padding: 4px;")
        form.addRow("Equivalent expedition:", self.expedition_label)

        layout.addLayout(form)
        layout.addStretch()
        return page

    def _calculate_equivalent(self):
        try:
            amount = self.transfer_amount.get_amount()
            rate = self.exchange_rate.get_amount()
            equivalent = amount * rate
            self.equivalent_label.setText(f"= {equivalent:,.2f} DA")
        except:
            self.equivalent_label.setText("= 0.00 DA")

    def _calculate_expedition(self):
        try:
            amount = self.transfer_amount.get_amount()
            rate = self.shipment_rate.get_amount()
            result = amount * rate
            self.expedition_label.setText(f"= {result:,.2f} DA")
        except:
            self.expedition_label.setText("= 0.00 DA")

    def _quick_add_agent(self, combo):
        from modules.currency.views import run_supplier_dialog
        from utils.constants import SUPPLIER_TYPE_SHIPPING
        success, msg, new_id = run_supplier_dialog(self.currency_service, SUPPLIER_TYPE_SHIPPING, parent=self)
        if success:
            self.agent_combo.clear()
            agents = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_SHIPPING)
            for a in agents:
                self.agent_combo.addItem(a['name'], a['id'])
            idx = self.agent_combo.findData(new_id)
            if idx >= 0:
                self.agent_combo.setCurrentIndex(idx)

    def _quick_add_license(self, combo):
        from components.smart_form import SmartFormDialog
        from utils.constants import SUPPLIER_TYPE_LICENSE

        # Charger les titulaires pour le choix
        suppliers = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_LICENSE)
        supp_options = [(s['name'], s['id']) for s in suppliers]

        # Callback pour ajouter un titulaire rapidement
        def on_add_owner(cbo):
            from modules.currency.views import run_supplier_dialog
            success, msg, new_id = run_supplier_dialog(self.currency_service, SUPPLIER_TYPE_LICENSE, parent=self)
            if success:
                cbo.clear()
                for s in self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_LICENSE):
                    cbo.addItem(s['name'], s['id'])
                idx = cbo.findData(new_id)
                if idx >= 0:
                    cbo.setCurrentIndex(idx)

        LICENSE_SCHEMA = [
            {'name': 'date', 'label': "Date d'achat", 'type': 'date', 'required': True},
            {'name': 'supplier_id', 'label': "Titulaire", 'type': 'dropdown', 'options': supp_options, 'required': True, 'quick_add_callback': on_add_owner},
            {'name': 'license_type', 'label': "Type de marchandise", 'type': 'text'},
            {'name': 'total_usd', 'label': 'Montant Total (USD)', 'type': 'number', 'required': True},
            {'name': 'total_dzd', 'label': 'Prix Total Facture (DA)', 'type': 'number', 'required': True},
            {'name': 'commission_rate', 'label': '% Commission Dédouanement (0-100)', 'type': 'number', 'default': 30.0, 'placeholder': 'Ex: 30 (سيُحسب كـ 30%)'},
            {'name': 'notes', 'label': 'Notes', 'type': 'text'},
        ]

        dialog = SmartFormDialog("Nouvelle Licence", LICENSE_SCHEMA, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            success, msg, lic_id = self.logistics_service.create_license(**results)
            if success:
                # Actualiser la liste des licences
                self.license_combo.clear()
                licenses = self.logistics_service.get_all_licenses(filter_status="all")
                for lic in licenses:
                    remaining = lic['remaining_usd']
                    self.license_combo.addItem(
                        f"{lic['supplier_name']} ({remaining:.2f} $ restant)", lic['id']
                    )
                idx = self.license_combo.findData(lic_id)
                if idx >= 0:
                    self.license_combo.setCurrentIndex(idx)
            else:
                show_error(self, "Erreur", msg)

    # ========================================================================
    # PAGE 2: Conteneurs
    # ========================================================================

    def _build_step2(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Conteneurs de la Facture")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff; padding: 4px;")
        layout.addWidget(title)

        add_layout = QHBoxLayout()
        self.cont_input = QLineEdit()
        self.cont_input.setPlaceholderText("N° Conteneur (ex: MSKU1234567)")
        self.btn_add_cont = QPushButton("+ Ajouter")
        self.btn_add_cont.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #238636; color: white;")
        self.btn_add_cont.clicked.connect(self._add_or_edit_container)
        self.cont_input.returnPressed.connect(self._add_or_edit_container)
        add_layout.addWidget(self.cont_input, 3)
        add_layout.addWidget(self.btn_add_cont, 1)
        layout.addLayout(add_layout)

        # Bouton Annuler (caché par défaut)
        self.btn_cancel_cont_edit = QPushButton("Annuler")
        self.btn_cancel_cont_edit.setStyleSheet("padding: 10px 20px; background-color: #6e7681; color: white;")
        self.btn_cancel_cont_edit.setVisible(False)
        self.btn_cancel_cont_edit.clicked.connect(self._cancel_container_edit)
        layout.addWidget(self.btn_cancel_cont_edit)

        self._editing_container_index = None  # Suivi du mode édition conteneur

        # [CUSTOM] 2026-04-04 - EnhancedTableView pour conteneurs (unification du design)
        # [WHY]: Remplacer QTableWidget par EnhancedTableView pour un design unifie avec le reste du programme.
        #        Toolbar et status filter caches car non necessaires dans un wizard.
        self.containers_table = EnhancedTableView(table_id="wizard_containers")
        self.containers_table.set_headers(["N°", "N° Conteneur", "Marchandises", ""])
        self.containers_table.hide_column(3)  # Cacher colonne action
        self.containers_table.toolbar.setVisible(False)
        self.containers_table.status_filter.setVisible(False)
        self.containers_table.footer.setVisible(False)
        self.containers_table.table.doubleClicked.connect(self._on_container_double_clicked)
        layout.addWidget(self.containers_table)

        self.cont_info = QLabel("0 conteneur(s) ajoute(s)")
        self.cont_info.setStyleSheet("color: #8b949e; padding: 4px;")
        layout.addWidget(self.cont_info)

        return page

    def _add_or_edit_container(self):
        """Ajouter un nouveau conteneur ou modifier un existant"""
        num = self.cont_input.text().strip()
        if not num:
            return show_error(self, "Erreur", "Entrez le numéro du conteneur.")

        if self._editing_container_index is not None:
            # Mode modification
            old_num = self.containers_data[self._editing_container_index]["number"]
            if num != old_num:
                for c in self.containers_data:
                    if c["number"] == num:
                        return show_error(self, "Erreur", f"Le conteneur {num} existe deja.")
            self.containers_data[self._editing_container_index]["number"] = num
            self._cancel_container_edit()
        else:
            # Mode ajout
            for c in self.containers_data:
                if c["number"] == num:
                    return show_error(self, "Erreur", f"Le conteneur {num} existe deja.")
            self.containers_data.append({"number": num, "goods": []})

        self.cont_input.clear()
        self._refresh_containers_table()

    def _cancel_container_edit(self):
        """Annuler le mode édition conteneur"""
        self._editing_container_index = None
        self.btn_add_cont.setText("+ Ajouter")
        self.btn_add_cont.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #238636; color: white;")
        self.btn_cancel_cont_edit.setVisible(False)
        self.cont_input.clear()

    def _remove_container(self, row):
        if 0 <= row < len(self.containers_data):
            self.containers_data.pop(row)
            self._refresh_containers_table()

    def _refresh_containers_table(self):
        self.containers_table.clear_rows()
        for i, cont in enumerate(self.containers_data):
            self.containers_table.add_row([
                None,  # N° auto
                cont["number"],
                f"{len(cont['goods'])} marchandise(s)",
                ""  # Colonne action cachee
            ])
        self.containers_table.resize_columns_to_contents()
        self.cont_info.setText(f"{len(self.containers_data)} conteneur(s) ajoute(s)")

    def _on_container_double_clicked(self, index):
        row = index.row()
        if row >= 0 and row < len(self.containers_data):
            self._remove_container(row)

    # ========================================================================
    # PAGE 3: Marchandises par Conteneur
    # ========================================================================

    def _build_step3(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Marchandises dans les Conteneurs")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff; padding: 4px;")
        layout.addWidget(title)

        sel_layout = QHBoxLayout()
        sel_layout.addWidget(QLabel("Conteneur:"))
        self.cont_selector = QComboBox()
        self.cont_selector.currentIndexChanged.connect(self._on_container_selected)
        sel_layout.addWidget(self.cont_selector, 3)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        form_group = QGroupBox("Ajouter une marchandise")
        form = QFormLayout(form_group)

        # [CUSTOM] 2026-04-04 - Quick Add pour Client (regle 10: Smoothness)
        # [WHY]: Permettre l'ajout rapide d'un client sans quitter le wizard.
        self.customer_combo = QComboBox()
        self.customer_widget = create_quick_add_layout(self.customer_combo, self._quick_add_customer)
        form.addRow("Client:", self.customer_widget)

        # [CUSTOM] 2026-04-04 - Quick Add pour Type de Marchandise via Catalog (regle 11)
        # [WHY]: Gestion centralisee des types de marchandises via GenericCatalogDialog.
        self.goods_type_combo = QComboBox()
        self.goods_type_combo.setEditable(True)
        self.goods_type_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.goods_type_combo.lineEdit().setPlaceholderText("Rechercher ou ajouter un type...")

        # [UNIFIED] 2026-04-08 - Add completer for search like SmartForm
        from PyQt6.QtWidgets import QCompleter
        from PyQt6.QtCore import Qt
        completer = QCompleter(self.goods_type_combo.model())
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.goods_type_combo.setCompleter(completer)
        popup = completer.popup()
        popup.setStyleSheet("""
            QListView {
                background-color: #112e2a;
                color: #e6edf3;
                border: 1px solid #214d47;
            }
            QListView::item {
                padding: 8px;
            }
            QListView::item:selected {
                background-color: #2ea043;
                color: white;
            }
            QListView::item:hover {
                background-color: #1a3d38;
            }
        """)

        self.goods_type_widget = create_quick_add_layout(self.goods_type_combo, self._open_goods_catalog)
        form.addRow("Type de Marchandise:", self.goods_type_widget)

        self.goods_qty = QSpinBox()
        self.goods_qty.setRange(0, 99999)
        form.addRow("Quantite (Cartons):", self.goods_qty)

        self.goods_cbm = QDoubleSpinBox()
        self.goods_cbm.setRange(0, 9999)
        self.goods_cbm.setDecimals(4)
        self.goods_cbm.valueChanged.connect(self._calc_goods_total)
        form.addRow("CBM:", self.goods_cbm)

        self.goods_price = QLineEdit()
        self.goods_price.setPlaceholderText("Prix CBM en DA")
        self.goods_price.textChanged.connect(self._calc_goods_total)
        form.addRow("Prix CBM (DA):", self.goods_price)

        self.goods_discount = QLineEdit()
        self.goods_discount.setPlaceholderText("Remise en DA (0 si aucune)")
        self.goods_discount.textChanged.connect(self._calc_goods_total)
        form.addRow("Remise (DA):", self.goods_discount)

        self.goods_total_label = QLabel("= 0.00 DA")
        self.goods_total_label.setStyleSheet("font-weight: bold; color: #238636; font-size: 16px;")
        form.addRow("Total:", self.goods_total_label)

        # Bouton Ajouter / Modifier
        self.btn_add_good = QPushButton("+ Ajouter au conteneur")
        self.btn_add_good.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #238636; color: white;")
        self.btn_add_good.clicked.connect(self._add_or_edit_good)
        form.addRow("", self.btn_add_good)

        # Bouton Annuler (caché par défaut)
        self.btn_cancel_edit = QPushButton("Annuler")
        self.btn_cancel_edit.setStyleSheet("padding: 10px 20px; background-color: #6e7681; color: white;")
        self.btn_cancel_edit.setVisible(False)
        self.btn_cancel_edit.clicked.connect(self._cancel_edit)
        form.addRow("", self.btn_cancel_edit)

        self._editing_row_index = None  # Suivi du mode édition

        layout.addWidget(form_group)

        # [CUSTOM] 2026-04-04 - EnhancedTableView pour marchandises (unification du design)
        # [WHY]: Remplacer QTableWidget par EnhancedTableView pour un design unifie avec le reste du programme.
        #        Toolbar et status filter caches car non necessaires dans un wizard.
        self.goods_table = EnhancedTableView(table_id="wizard_goods")
        self.goods_table.set_headers(["N°", "Client", "Marchandise", "Qte", "CBM", "Prix (DA)", "Remise (DA)", "Total (DA)", ""])
        self.goods_table.hide_column(8)  # Cacher colonne action
        self.goods_table.toolbar.setVisible(False)
        self.goods_table.status_filter.setVisible(False)
        self.goods_table.footer.setVisible(False)
        self.goods_table.table.doubleClicked.connect(self._on_good_double_clicked)
        layout.addWidget(self.goods_table)

        self.goods_info = QLabel("")
        self.goods_info.setStyleSheet("font-weight: bold; color: #58a6ff; padding: 4px;")
        layout.addWidget(self.goods_info)

        return page

    def _calc_goods_total(self):
        cbm = self.goods_cbm.value()
        try:
            price = float(self.goods_price.text().replace(",", ".").replace(" ", "")) if self.goods_price.text().strip() else 0
        except ValueError:
            price = 0
        try:
            discount = float(self.goods_discount.text().replace(",", ".").replace(" ", "")) if self.goods_discount.text().strip() else 0
        except ValueError:
            discount = 0
        total = (cbm * price) - discount
        self.goods_total_label.setText(f"= {total:,.2f} DA")

    def _quick_add_customer(self, combo):
        """Ajout rapide d'un client depuis le wizard (regle 10) - appelle le schema original"""
        from modules.customers.views import CUSTOMER_SCHEMA
        from components.smart_form import SmartFormDialog
        dialog = SmartFormDialog("Nouveau Client", CUSTOMER_SCHEMA, parent=self)
        if dialog.exec():
            try:
                customer = self.customer_service.create_customer(**dialog.get_results())
                if customer:
                    combo.addItem(dialog.get_results()['name'], customer.id)
                    combo.setCurrentIndex(combo.count() - 1)
            except Exception as e:
                show_error(self, "Erreur", f"Erreur lors de la creation du client: {str(e)}")

    def _open_goods_catalog(self, combo):
        """Ouvrir le catalogue des types de marchandises (regle 11)"""
        from core.database import get_session
        from core.models import LicenseGoodsCatalog

        def get_data(include_inactive=False):
            with get_session() as session:
                query = session.query(LicenseGoodsCatalog)
                if not include_inactive:
                    query = query.filter(LicenseGoodsCatalog.is_active == True)
                items = query.order_by(LicenseGoodsCatalog.id).all()
                return [{'id': i.id, 'name': i.name, 'description': i.description or '', 'is_active': i.is_active} for i in items]

        def create_data(name, desc):
            with get_session() as session:
                exists = session.query(LicenseGoodsCatalog).filter_by(name=name).first()
                if exists:
                    return False, "Ce type existe deja", None
                new_item = LicenseGoodsCatalog(name=name, description=desc or '')
                session.add(new_item)
                session.flush()
                return True, "Type cree avec succes", new_item.id

        def delete_data(item_id):
            with get_session() as session:
                item = session.query(LicenseGoodsCatalog).get(item_id)
                if item:
                    item.is_active = False
                    return True, "Type supprime", None
                return False, "Element introuvable", None

        def restore_data(item_id):
            with get_session() as session:
                item = session.query(LicenseGoodsCatalog).get(item_id)
                if item:
                    item.is_active = True
                    return True, "Type restaure", None
                return False, "Element introuvable", None

        catalog = GenericCatalogDialog(
            title="Catalogue des Types de Marchandises",
            get_data_func=get_data,
            create_data_func=create_data,
            delete_data_func=delete_data,
            restore_data_func=restore_data,
            primary_placeholder="Nom du type",
            secondary_placeholder="Description (optionnel)",
            headers=["N", "ID", "Nom", "Description"],
            parent=self
        )
        if catalog.exec():
            # Recharger les types
            self._load_goods_types()

    def _load_goods_types(self):
        """Charger les types de marchandises depuis le catalogue"""
        from core.database import get_session
        from core.models import LicenseGoodsCatalog
        current = self.goods_type_combo.currentText()
        self.goods_type_combo.clear()
        with get_session() as session:
            types = session.query(LicenseGoodsCatalog).filter_by(is_active=True).order_by(LicenseGoodsCatalog.name).all()
            for t in types:
                self.goods_type_combo.addItem(t.name, t.id)
        if current:
            idx = self.goods_type_combo.findText(current)
            if idx >= 0:
                self.goods_type_combo.setCurrentIndex(idx)

    def _on_container_selected(self, index):
        self._cancel_edit()
        self._refresh_goods_table()

    def _add_or_edit_good(self):
        """Ajouter une nouvelle marchandise ou modifier une existante"""
        cont_index = self.cont_selector.currentIndex()
        if cont_index < 0 or cont_index >= len(self.containers_data):
            return show_error(self, "Erreur", "Selectionnez un conteneur.")

        customer = self.customer_combo.currentText()
        goods_type = self.goods_type_combo.currentText()
        qty = self.goods_qty.value()
        cbm = self.goods_cbm.value()
        try:
            price = float(self.goods_price.text().replace(",", ".").replace(" ", "")) if self.goods_price.text().strip() else 0
        except ValueError:
            price = 0
        try:
            discount = float(self.goods_discount.text().replace(",", ".").replace(" ", "")) if self.goods_discount.text().strip() else 0
        except ValueError:
            discount = 0
        total = (cbm * price) - discount

        if not customer or customer == "Aucun":
            return show_error(self, "Erreur", "Selectionnez un client.")
        if cbm <= 0:
            return show_error(self, "Erreur", "Le CBM doit etre superieur a zero.")

        good = {
            "customer": customer,
            "customer_id": self.customer_combo.currentData(),
            "goods_type": goods_type,
            "qty": qty,
            "cbm": cbm,
            "price": price,
            "discount": discount,
            "total": total
        }

        if self._editing_row_index is not None:
            # Mode modification
            self.containers_data[cont_index]["goods"][self._editing_row_index] = good
            self._cancel_edit()
        else:
            # Mode ajout
            self.containers_data[cont_index]["goods"].append(good)

        self._clear_goods_form()
        self._refresh_goods_table()

    def _remove_good(self, row):
        cont_index = self.cont_selector.currentIndex()
        if 0 <= cont_index < len(self.containers_data):
            goods = self.containers_data[cont_index]["goods"]
            if 0 <= row < len(goods):
                goods.pop(row)
                self._refresh_goods_table()

    def _refresh_goods_table(self):
        cont_index = self.cont_selector.currentIndex()
        if cont_index < 0:
            self.goods_table.clear_rows()
            return

        goods = self.containers_data[cont_index]["goods"]
        self.goods_table.clear_rows()

        total_cbm = 0
        total_amount = 0

        for i, g in enumerate(goods):
            self.goods_table.add_row([
                None,  # N° auto
                g["customer"],
                g["goods_type"],
                str(g["qty"]),
                f"{g['cbm']:.4f}",
                f"{g['price']:,.2f} DA",
                f"{g['discount']:,.2f} DA",
                f"{g['total']:,.2f} DA",
                ""  # Colonne action cachee
            ])
            total_cbm += g["cbm"]
            total_amount += g["total"]

        self.goods_table.resize_columns_to_contents()
        self.goods_info.setText(
            f"Total: {len(goods)} marchandise(s) | {total_cbm:.4f} CBM | {total_amount:,.2f} DA"
        )

    def _on_good_double_clicked(self, index):
        """Double-clic sur une ligne → chargement pour modification"""
        source_row = self.goods_table.proxy_model.mapToSource(index).row()
        cont_index = self.cont_selector.currentIndex()
        if 0 <= cont_index < len(self.containers_data):
            goods = self.containers_data[cont_index]["goods"]
            if 0 <= source_row < len(goods):
                g = goods[source_row]
                # Remplir le formulaire avec les données
                idx = self.customer_combo.findData(g.get("customer_id"))
                if idx >= 0:
                    self.customer_combo.setCurrentIndex(idx)
                else:
                    idx = self.customer_combo.findText(g["customer"])
                    if idx >= 0:
                        self.customer_combo.setCurrentIndex(idx)

                idx = self.goods_type_combo.findText(g["goods_type"])
                if idx >= 0:
                    self.goods_type_combo.setCurrentIndex(idx)

                self.goods_qty.setValue(g["qty"])
                self.goods_cbm.setValue(g["cbm"])
                self.goods_price.setText(f"{g['price']:,.2f}")
                self.goods_discount.setText(f"{g['discount']:,.2f}")
                self._calc_goods_total()

                # Passer en mode édition
                self._editing_row_index = source_row
                self.btn_add_good.setText("✓ Modifier la marchandise")
                self.btn_add_good.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #d29922; color: white;")
                self.btn_cancel_edit.setVisible(True)

    def _cancel_edit(self):
        """Annuler le mode édition"""
        self._editing_row_index = None
        self.btn_add_good.setText("+ Ajouter au conteneur")
        self.btn_add_good.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #238636; color: white;")
        self.btn_cancel_edit.setVisible(False)
        self._clear_goods_form()

    def _clear_goods_form(self):
        """Vider le formulaire de marchandise"""
        self.goods_qty.setValue(0)
        self.goods_cbm.setValue(0)
        self.goods_price.clear()
        self.goods_discount.clear()
        self.goods_total_label.setText("= 0.00 DA")

    def _on_container_double_clicked(self, index):
        """Double-clic sur une ligne → chargement pour modification"""
        source_row = self.containers_table.proxy_model.mapToSource(index).row()
        if 0 <= source_row < len(self.containers_data):
            cont = self.containers_data[source_row]
            self.cont_input.setText(cont["number"])
            self._editing_container_index = source_row
            self.btn_add_cont.setText("✓ Modifier le conteneur")
            self.btn_add_cont.setStyleSheet("padding: 10px 20px; font-weight: bold; background-color: #d29922; color: white;")
            self.btn_cancel_cont_edit.setVisible(True)

    # ========================================================================
    # NAVIGATION
    # ========================================================================

    def _update_step(self):
        self.stack.setCurrentIndex(self.current_step)

        for i, indicator in enumerate(self.step_indicators):
            if i == self.current_step:
                indicator.setStyleSheet(
                    "background-color: #1f6feb; border-radius: 4px; "
                    "QLabel { color: white; font-weight: bold; }"
                )
            else:
                indicator.setStyleSheet(
                    "background-color: #161b22; border-radius: 4px; "
                    "QLabel { color: #8b949e; }"
                )

        self.btn_prev.setEnabled(self.current_step > 0)
        btn_text = "Mettre a jour" if (self.current_step == 2 and self.is_edit) else ("Enregistrer" if self.current_step == 2 else "Suivant >")
        self.btn_next.setText(btn_text)
        self.page_label.setText(f"Etape {self.current_step + 1}/3")

        if self.current_step == 2:
            self._refresh_container_selector()

    def _next_step(self):
        if self.current_step == 0:
            if not self.bill_input.text().strip():
                return show_error(self, "Erreur", "Entrez le numero de BILL.")
            if self.license_combo.currentIndex() < 0:
                return show_error(self, "Erreur", "Selectionnez une licence.")
            if not self.is_edit and self.transfer_amount.get_amount() <= 0:
                return show_error(self, "Erreur", "Le montant de transfert doit etre > 0.")
            self.current_step = 1
            self._update_step()
        elif self.current_step == 1:
            if not self.containers_data:
                return show_error(self, "Erreur", "Ajoutez au moins un conteneur.")
            self.current_step = 2
            self._update_step()
        elif self.current_step == 2:
            self._save()

    def _prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step()

    def _confirm(self):
        """Confirmer et sauvegarder depuis n'importe quelle etape"""
        if not self.bill_input.text().strip():
            return show_error(self, "Erreur", "Entrez le numero de BILL.")
        if self.license_combo.currentIndex() < 0:
            return show_error(self, "Erreur", "Selectionnez une licence.")
        if not self.containers_data:
            return show_error(self, "Erreur", "Ajoutez au moins un conteneur.")
        self._save()

    def _refresh_container_selector(self):
        self.cont_selector.clear()
        for cont in self.containers_data:
            self.cont_selector.addItem(cont["number"])

    # ========================================================================
    # CHARGEMENT DES DONNEES
    # ========================================================================

    def _load_data(self):
        # Licences (deja chargees dans _build_step1)

        # Agents maritimes
        from utils.constants import SUPPLIER_TYPE_SHIPPING
        agents = self.currency_service.get_all_suppliers(supplier_type=SUPPLIER_TYPE_SHIPPING)
        for a in agents:
            self.agent_combo.addItem(a['name'], a['id'])

        # Clients
        customers = self.customer_service.get_all_customers()
        for c in customers:
            self.customer_combo.addItem(c['name'] if isinstance(c, dict) else c.name,
                                        c['id'] if isinstance(c, dict) else c.id)

        # Types de marchandises
        self._load_goods_types()

    def _load_edit_data(self):
        """Charge les donnees existantes pour la modification"""
        containers = self.logistics_service.get_all_containers(filter_status="all")
        cont = next((c for c in containers if c['id'] == self.edit_container_id), None)
        if not cont:
            return

        # Page 1: Informations facture
        if cont.get('shipping_date'):
            d = cont['shipping_date']
            self.date_input.setDate(QDate(d.year, d.month, d.day))
        elif cont.get('date_opened'):
            d = cont['date_opened']
            self.date_input.setDate(QDate(d.year, d.month, d.day))
        self.bill_input.setText(cont.get('bill_number', ''))
        self.invoice_input.setText(cont.get('invoice_number', ''))
        self.port_input.setText(cont.get('discharge_port', ''))
        self.transitaire_input.setText(cont.get('transitaire', ''))
        self.transfer_amount.setValue(cont.get('used_usd_amount') or 0)
        self.exchange_rate.setValue(cont.get('taux') or 0)
        self.shipment_rate.setValue(cont.get('taux_expedition') or 0)

        # Selectionner l'agent
        if cont.get('shipping_supplier_id'):
            idx = self.agent_combo.findData(cont['shipping_supplier_id'])
            if idx >= 0:
                self.agent_combo.setCurrentIndex(idx)

        # Selectionner la licence
        if cont.get('license_id'):
            idx = self.license_combo.findData(cont['license_id'])
            if idx >= 0:
                self.license_combo.setCurrentIndex(idx)

        # Selectionner le type de shp
        shipment_type = cont.get('shipment_type', 'MARITIME')
        idx = self.shipment_type_combo.findData(shipment_type)
        if idx >= 0:
            self.shipment_type_combo.setCurrentIndex(idx)

        # Page 2: Conteneur existant (un seul en mode edition)
        self.containers_data = [{
            "number": cont.get('container_number', ''),
            "container_id": cont['id'],
            "goods": []
        }]
        self._refresh_containers_table()

        # Page 3: Charger les marchandises existantes
        try:
            from core.database import get_session
            from core.models import CustomerGoods
            with get_session() as session:
                goods = session.query(CustomerGoods).filter_by(
                    container_id=self.edit_container_id, is_active=True
                ).all()
                customer_names = {c['id'] if isinstance(c, dict) else c.id: c['name'] if isinstance(c, dict) else c.name
                                  for c in self.customer_service.get_all_customers()}
                for g in goods:
                    self.containers_data[0]["goods"].append({
                        "customer": customer_names.get(g.customer_id, "Inconnu"),
                        "customer_id": g.customer_id,
                        "goods_type": g.goods_type,
                        "cartons": g.cartons,
                        "qty": g.cartons,
                        "cbm": g.cbm,
                        "price": g.cbm_price_usd or 0,
                        "discount": g.discount_usd or 0,
                        "total": (g.cbm * (g.cbm_price_usd or 0)) - (g.discount_usd or 0)
                    })
        except Exception as e:
            log_error(e, context="ShipmentWizard._load_goods")

    # ========================================================================
    # SAUVEGARDE
    # ========================================================================

    def _save(self):
        total_goods = sum(len(c["goods"]) for c in self.containers_data)
        if total_goods == 0:
            return show_error(self, "Erreur", "Ajoutez au moins une marchandise dans un conteneur.")

        data = {
            "shipment": {
                "date": datetime.combine(self.date_input.date().toPyDate(), datetime.now().time()),
                "bill_number": self.bill_input.text().strip(),
                "agent_id": self.agent_combo.currentData(),
                "invoice_number": self.invoice_input.text().strip(),
                "license_id": self.license_combo.currentData(),
                "shipment_type": self.shipment_type_combo.currentData(),
                "transfer_amount_usd": self.transfer_amount.get_amount(),
                "exchange_rate": self.exchange_rate.get_amount(),
                "equivalent_dzd": self.transfer_amount.get_amount() * self.exchange_rate.get_amount(),
                "port": self.port_input.text().strip(),
                "transitaire": self.transitaire_input.text().strip(),
                "shipment_rate": self.shipment_rate.get_amount(),
                "equivalent_expedition": self.transfer_amount.get_amount() * self.shipment_rate.get_amount(),
            },
            "containers": self.containers_data
        }

        if self.is_edit:
            success, msg = self.logistics_service.update_shipment_with_goods(
                self.edit_container_id, data
            )
        else:
            success, msg = self.logistics_service.create_shipment_with_goods(data)

        if success:
            show_success(self, "Succes", msg)
            self.dataSaved.emit()
            self.accept()
        else:
            show_error(self, "Erreur", msg)

    def _add_expense(self):
        """Ouvrir le dialogue pour ajouter une dépense liée à cette facture"""
        # Vérifier que la licence est sélectionnée
        license_id = self.license_combo.currentData()
        if not license_id:
            show_error(self, "Erreur", "Sélectionnez d'abord une licence")
            return

        from modules.expenses.views import ExpenseDialog
        dialog = ExpenseDialog(
            self.expense_service, self.logistics_service,
            self.currency_service, self.treasury_service,
            self.customer_service, parent=self
        )

        # Pré-remplir la licence (si le dialogue le permet)
        # Note: le dialogue s'ouvrira en mode normal, l'utilisateur peut lier à la licence ou conteneur
        if dialog.exec():
            show_success(self, "Succès", "Coût ajouté avec succès")
            # Pas besoin de recharger les données du wizard
