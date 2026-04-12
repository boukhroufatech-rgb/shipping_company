"""
Vue centrale pour la gestion des catalogues (Master Data).
Regroupe les listes de références (Frais, Marchandises, etc.) au même endroit.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import pyqtSignal

from components.enhanced_table import EnhancedTableView
from components.smart_form import SmartFormDialog
from components.dialogs import show_error, show_success, confirm_action
from components.catalog_dialog import GenericCatalogDialog
from utils.formatters import format_date

from modules.logistics.expense_service import ExpenseService
from modules.logistics.port_service import PortService
from modules.logistics.transitaire_service import TransitaireService
from modules.currency.service import CurrencyService
from utils.constants import SUPPLIER_TYPE_CURRENCY

# ============================================================================
# BASE CATALOG TAB (Réutilisable)
# ============================================================================

class BaseCatalogTab(QWidget):
    """Tab générique pour afficher et gérer un catalogue simple."""
    dataChanged = pyqtSignal()

    def __init__(self, title, get_data_func, create_func, update_func, delete_func, restore_func,
                 headers, schema, parent=None):
        super().__init__(parent)
        self.get_data_func = get_data_func
        self.create_func = create_func
        self.update_func = update_func
        self.delete_func = delete_func
        self.restore_func = restore_func
        self.schema = schema
        self.title = title
        self.headers = headers

        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = EnhancedTableView(table_id=f"catalog_{self.title}")
        self.table.set_headers(self.headers)
        
        # Actions
        self.table.addClicked.connect(self.add_item)
        self.table.editClicked.connect(self.edit_item)
        self.table.deleteClicked.connect(self.delete_item)
        self.table.restoreClicked.connect(self.restore_item)
        self.table.refreshClicked.connect(self.load_data)
        
        layout.addWidget(self.table)

    def load_data(self):
        data = self.get_data_func()
        self.table.clear_rows()
        for i, item in enumerate(data):
            # نتأكد أن البيانات ليست فارغة قبل الإضافة
            if isinstance(item, dict):
                row_values = list(item.values())
            elif isinstance(item, list):
                row_values = item
            else:
                row_values = [str(item)]
            
            if len(row_values) > 0:
                is_active = True
                if isinstance(item, dict):
                    is_active = item.get('is_active', True)
                self.table.add_row([str(i + 1)] + row_values, is_active=is_active)

    def add_item(self):
        dialog = SmartFormDialog(f"Ajouter à {self.title}", self.schema, parent=self)
        if dialog.exec():
            res = dialog.get_results()
            success, msg, _ = self.create_func(**res)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def edit_item(self, row_idx):
        row_data = self.table.get_row_data(row_idx)
        try:
            item_id = int(row_data[1])
        except (ValueError, IndexError):
            return show_error(self, "Erreur", "Impossible de récupérer l'ID.")

        # Find the current data
        current_data = None
        for item in self.get_data_func():
            if item[0] == str(item_id):
                current_data = {
                    'name': item[1], 'country': item[2], 
                    'port_type': item[3] if len(item) > 3 else 'AUTRE',
                    'description': item[4] if len(item) > 4 else ''
                }
                break
        
        dialog = SmartFormDialog(f"Modifier {self.title}", self.schema, current_data, parent=self)
        if dialog.exec():
            res = dialog.get_results()
            success, msg = self.update_func(item_id, **res)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def delete_item(self):
        selected_rows = self.table.get_selected_rows()
        if not selected_rows:
            return show_error(self, "Erreur", "Veuillez sélectionner un élément.")
        row_idx = selected_rows[0]
        row_data = self.table.get_row_data(row_idx)
        try:
            item_id = int(row_data[1]) # Assume ID is at index 1
        except (ValueError, IndexError):
            return show_error(self, "Erreur", "Impossible de récupérer l'ID.")
            
        if confirm_action(self, "Archiver", "Confirmer l'archivage ?"):
            success, msg = self.delete_func(item_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def restore_item(self):
        selected_rows = self.table.get_selected_rows()
        if not selected_rows:
            return show_error(self, "Erreur", "Veuillez sélectionner un élément.")
        row_idx = selected_rows[0]
        row_data = self.table.get_row_data(row_idx)
        try:
            item_id = int(row_data[1])
        except (ValueError, IndexError):
            return show_error(self, "Erreur", "Impossible de récupérer l'ID.")

        if confirm_action(self, "Restaurer", "Confirmer la restauration ?"):
            success, msg = self.restore_func(item_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)


# ============================================================================
# CHANGEURS CATALOG TAB (Spécialisé pour Fournisseurs de Devises)
# ============================================================================

class ChangeursCatalogTab(QWidget):
    """Gestion indépendante des Changeurs (Fournisseurs de Devises)."""
    dataChanged = pyqtSignal()

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = EnhancedTableView(table_id="catalog_changeurs")
        self.table.set_headers([
            "N°", "ID", "Nom", "Contact", "Téléphone", "Email", "Statut"
        ])

        # Actions
        self.table.addClicked.connect(self.add_changeur)
        self.table.editClicked.connect(self.edit_changeur)
        self.table.deleteClicked.connect(self.delete_changeur)
        self.table.restoreClicked.connect(self.restore_changeur)
        self.table.refreshClicked.connect(self.load_data)

        layout.addWidget(self.table)

    def load_data(self):
        # Filter specifically for CURRENCY type
        suppliers = self.service.get_all_suppliers(filter_status="all", supplier_type=SUPPLIER_TYPE_CURRENCY)
        self.table.clear_rows()
        
        for i, s in enumerate(suppliers):
            status = "Actif" if s.get('is_active') else "Archivé"
            self.table.add_row([
                str(i + 1),
                str(s['id']),
                s['name'],
                s.get('contact', ''),
                s.get('phone', ''),
                s.get('email', ''),
                status
            ], is_active=s.get('is_active'))

    def add_changeur(self):
        schema = [
            {'name': 'name', 'label': 'Nom du Changeur', 'type': 'text', 'required': True},
            {'name': 'contact', 'label': 'Contact', 'type': 'text'},
            {'name': 'phone', 'label': 'Téléphone', 'type': 'text'},
            {'name': 'email', 'label': 'Email', 'type': 'text'},
        ]
        
        dialog = SmartFormDialog("Nouveau Changeur", schema, parent=self)
        if dialog.exec():
            res = dialog.get_results()
            res['supplier_type'] = SUPPLIER_TYPE_CURRENCY
            success, msg, _ = self.service.create_supplier(**res)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def edit_changeur(self, row_idx):
        row_data = self.table.get_row_data(row_idx)
        item_id = int(row_data[1])
        name = row_data[2]
        
        # Get current data
        suppliers = self.service.get_all_suppliers(filter_status="all", supplier_type=SUPPLIER_TYPE_CURRENCY)
        current = next((s for s in suppliers if s['id'] == item_id), {})

        schema = [
            {'name': 'name', 'label': 'Nom du Changeur', 'type': 'text', 'required': True},
            {'name': 'contact', 'label': 'Contact', 'type': 'text'},
            {'name': 'phone', 'label': 'Téléphone', 'type': 'text'},
            {'name': 'email', 'label': 'Email', 'type': 'text'},
        ]
        
        dialog = SmartFormDialog("Modifier Changeur", schema, current, parent=self)
        if dialog.exec():
            res = dialog.get_results()
            success, msg = self.service.update_supplier(item_id, **res)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def delete_changeur(self, row_idx):
        row_data = self.table.get_row_data(row_idx)
        item_id = int(row_data[1])
        name = row_data[2]
        
        if confirm_action(self, "Archiver", f"Confirmer l'archivage de '{name}' ?\n\nAttention: Impossible d'archiver s'il y a des opérations liées."):
            success, msg = self.service.delete_supplier(item_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)

    def restore_changeur(self, row_idx):
        row_data = self.table.get_row_data(row_idx)
        item_id = int(row_data[1])
        name = row_data[2]
        
        if confirm_action(self, "Restaurer", f"Confirmer la restauration de '{name}' ?"):
            success, msg = self.service.restore_supplier(item_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)


# ============================================================================
# MAIN VIEW
# ============================================================================

class CatalogManagementView(QWidget):
    """Vue principale de gestion des catalogues."""
    dataChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.expense_service = ExpenseService()
        self.port_service = PortService()
        self.transitaire_service = TransitaireService()
        self.currency_service = CurrencyService()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 1. Catalogue: Types de Frais
        # Schema simplifié pour le test
        expense_schema = [
            {'name': 'name', 'label': 'Nom du type', 'type': 'text', 'required': True},
            {'name': 'description', 'label': 'Description', 'type': 'text'},
        ]
        self.expenses_tab = BaseCatalogTab(
            title="Types de Frais",
            get_data_func=lambda: [
                [str(t['id']), t['name'], t.get('description', ''), 'Actif' if t.get('is_active') else 'Archivé'] 
                for t in self.expense_service.get_all_expense_types()
            ],
            create_func=lambda name, description: self.expense_service.create_expense_type(name, description),
            update_func=lambda id, name, description: self.expense_service.update_expense_type(id, name),
            delete_func=lambda id: self.expense_service.delete_expense_type(id),
            restore_func=lambda id: self.expense_service.restore_expense_type(id),
            headers=["N°", "ID", "Nom", "Description", "État"],
            schema=expense_schema,
            parent=self
        )
        self.expenses_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.expenses_tab, "Types de Frais")

        # 2. Catalogue: Marchandises (Licence Goods)
        goods_schema = [
            {'name': 'name', 'label': 'Nom de la marchandise', 'type': 'text', 'required': True},
            {'name': 'description', 'label': 'Description', 'type': 'text'},
        ]
        self.goods_tab = BaseCatalogTab(
            title="Marchandises",
            get_data_func=lambda: [
                [str(g['id']), g['name'], g.get('description', ''), 'Actif' if g.get('is_active') else 'Archivé']
                for g in self.currency_service.get_all_license_goods()
            ],
            create_func=lambda name, description: self.currency_service.create_license_goods(name, description),
            update_func=lambda id, name, description: self.currency_service.update_license_goods(id, name, description),
            delete_func=lambda id: self.currency_service.delete_license_goods(id),
            restore_func=lambda id: self.currency_service.restore_license_goods(id),
            headers=["N°", "ID", "Nom", "Description", "État"],
            schema=goods_schema,
            parent=self
        )
        self.goods_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.goods_tab, "Marchandises")

        # 3. Catalogue: Ports / Destinations
        port_schema = [
            {'name': 'name', 'label': 'Nom du Port', 'type': 'text', 'required': True},
            {'name': 'country', 'label': 'Pays', 'type': 'text'},
            {'name': 'port_type', 'label': 'Type', 'type': 'dropdown', 'options': ['IMPORT', 'EXPORT', 'TRANSIT', 'AUTRE']},
            {'name': 'description', 'label': 'Description', 'type': 'text'},
        ]
        self.ports_tab = BaseCatalogTab(
            title="Ports / Destinations",
            get_data_func=lambda: [
                [str(p['id']), p['name'], p.get('country', ''), p.get('port_type', ''), p.get('description', ''), 'Actif' if p.get('is_active') else 'Archivé']
                for p in self.port_service.get_all_ports()
            ],
            create_func=lambda **kwargs: self.port_service.create_port(**kwargs),
            update_func=lambda id, **kwargs: self.port_service.update_port(id, **kwargs),
            delete_func=lambda id: self.port_service.delete_port(id),
            restore_func=lambda id: self.port_service.restore_port(id),
            headers=["N°", "ID", "Nom", "Pays", "Type", "Description", "État"],
            schema=port_schema,
            parent=self
        )
        self.ports_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.ports_tab, "Ports / Destinations")

        # 5. Catalogue: Transitaires
        transitaire_schema = [
            {'name': 'name', 'label': 'Nom du Transitaire', 'type': 'text', 'required': True},
            {'name': 'contact', 'label': 'Contact', 'type': 'text'},
            {'name': 'phone', 'label': 'Téléphone', 'type': 'text'},
            {'name': 'email', 'label': 'Email', 'type': 'text'},
            {'name': 'nif_rc', 'label': 'NIF / RC', 'type': 'text'},
            {'name': 'description', 'label': 'Notes', 'type': 'text'},
        ]
        self.transitaires_tab = BaseCatalogTab(
            title="Transitaires",
            get_data_func=lambda: [
                [str(t['id']), t['name'], t.get('contact', ''), t.get('phone', ''), t.get('email', ''), t.get('nif_rc', ''), 'Actif' if t.get('is_active') else 'Archivé']
                for t in self.transitaire_service.get_all_transitaires()
            ],
            create_func=lambda **kwargs: self.transitaire_service.create_transitaire(**kwargs),
            update_func=lambda id, **kwargs: self.transitaire_service.update_transitaire(id, **kwargs),
            delete_func=lambda id: self.transitaire_service.delete_transitaire(id),
            restore_func=lambda id: self.transitaire_service.restore_transitaire(id),
            headers=["N°", "ID", "Nom", "Contact", "Tél", "Email", "NIF/RC", "État"],
            schema=transitaire_schema,
            parent=self
        )
        self.transitaires_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.transitaires_tab, "Transitaires")
