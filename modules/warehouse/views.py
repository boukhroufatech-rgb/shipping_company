"""
Vues pour le module Warehouse (Gestion des entrepôts)
Standardized & Purified
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialog, QFormLayout, QTabWidget,
    QLineEdit, QComboBox, QTextEdit, QDialogButtonBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal

from components.enhanced_table import EnhancedTableView
from components.smart_form import SmartFormDialog
from components.dialogs import show_error, show_success, confirm_delete
from utils.formatters import format_date
from .service import WarehouseService

WAREHOUSE_SCHEMA = [
    {"name": "name", "label": "Nom de l'entrepôt", "type": "text", "required": True},
    {"name": "address", "label": "Adresse", "type": "multiline"},
    {"name": "is_main", "label": "Entrepôt principal", "type": "checkbox"},
    {"name": "notes", "label": "Notes", "type": "text"}
]


class WarehouseView(QWidget):
    """Vue principale du module Warehouse"""
    dataChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.service = WarehouseService()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.warehouses_tab = WarehousesListTab(self.service)
        self.warehouses_tab.dataChanged.connect(self.dataChanged.emit)
        self.tabs.addTab(self.warehouses_tab, "Entrepôts")
        
        self.stocks_tab = StocksTab(self.service)
        self.tabs.addTab(self.stocks_tab, "Stocks")
        
        self.movements_tab = MovementsTab(self.service)
        self.tabs.addTab(self.movements_tab, "Mouvements")
    
    def refresh(self):
        self.warehouses_tab.load_data()
        self.stocks_tab.load_data()
        self.movements_tab.load_data()


class WarehousesListTab(QWidget):
    """Tab pour la liste des entrepôts"""
    dataChanged = pyqtSignal()
    
    def __init__(self, service: WarehouseService):
        super().__init__()
        self.service = service
        self._setup_ui()
        self.load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Table - EnhancedTableView has built-in action buttons
        self.table = EnhancedTableView(table_id="warehouses")
        self.table.set_headers(["N°", "ID", "Nom", "Adresse", "Principal", "Notes"])
        
        # Connect EnhancedTableView actions
        self.table.addClicked.connect(self.add_warehouse)
        self.table.editClicked.connect(lambda idx: self._set_selected_and_edit(idx))
        self.table.deleteClicked.connect(lambda idx: self._set_selected_and_delete(idx))
        
        layout.addWidget(self.table)
        
        self.selected_id = None
    
    def _set_selected_and_edit(self, row_idx):
        self.selected_id = int(self.table.get_row_data(row_idx)[1])
        self.edit_warehouse()
    
    def _set_selected_and_delete(self, row_idx):
        self.selected_id = int(self.table.get_row_data(row_idx)[1])
        self.delete_warehouse()
    
    def load_data(self):
        warehouses = self.service.get_all_warehouses()
        self.table.clear_rows()
        for i, w in enumerate(warehouses, 1):
            main_str = "Oui" if w['is_main'] else "Non"
            self.table.add_row([
                str(i), str(w['id']), w['name'], w['address'] or "", main_str, w['notes'] or ""
            ])
        self.table.resize_columns_to_contents()
    
    def add_warehouse(self):
        dialog = SmartFormDialog("Nouvel Entrepôt", WAREHOUSE_SCHEMA, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            success, msg, wid = self.service.create_warehouse(**results)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)
    
    def edit_warehouse(self):
        if not self.selected_id:
            return show_error(self, "Erreur", "Sélectionnez un entrepôt")
        
        warehouse = self.service.get_warehouse(self.selected_id)
        if not warehouse:
            return show_error(self, "Erreur", "Entrepôt non trouvé")
        
        dialog = SmartFormDialog("Modifier Entrepôt", WAREHOUSE_SCHEMA, data=warehouse, parent=self)
        if dialog.exec():
            results = dialog.get_results()
            success, msg = self.service.update_warehouse(self.selected_id, **results)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)
    
    def delete_warehouse(self):
        if not self.selected_id:
            return show_error(self, "Erreur", "Sélectionnez un entrepôt")
        
        if confirm_delete(self, "cet entrepôt"):
            success, msg = self.service.delete_warehouse(self.selected_id)
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
                self.selected_id = None
                self.dataChanged.emit()
            else:
                show_error(self, "Erreur", msg)


class StocksTab(QWidget):
    """Tab pour les stocks"""
    def __init__(self, service: WarehouseService):
        super().__init__()
        self.service = service
        self._setup_ui()
        self.load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Filter by warehouse + Buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Entrepôt:"))
        self.combo_warehouse = QComboBox()
        self.combo_warehouse.currentIndexChanged.connect(self.load_data)
        top_layout.addWidget(self.combo_warehouse)
        
        self.btn_receive = QPushButton("استلام بضاعة")
        self.btn_receive.clicked.connect(self.receive_stock)
        self.btn_deliver = QPushButton("تسليم بضاعة")
        self.btn_deliver.clicked.connect(self.deliver_stock)
        top_layout.addWidget(self.btn_receive)
        top_layout.addWidget(self.btn_deliver)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Table
        self.table = EnhancedTableView(table_id="warehouse_stocks")
        self.table.set_headers(["N°", "ID", "Client", "Conteneur", "Type Marchandise", "Quantité", "Poids (kg)", "Notes"])
        self.selected_stock_id = None
        self.table.editClicked.connect(lambda idx: self._set_selected(idx))
        layout.addWidget(self.table)
        
        self.refresh_warehouses()
    
    def _set_selected(self, row_idx):
        self.selected_stock_id = int(self.table.get_row_data(row_idx)[1])
    
    def refresh_warehouses(self):
        self.combo_warehouse.blockSignals(True)
        self.combo_warehouse.clear()
        for w in self.service.get_all_warehouses():
            self.combo_warehouse.addItem(w['name'], w['id'])
        self.combo_warehouse.blockSignals(False)
    
    def load_data(self):
        wid = self.combo_warehouse.currentData()
        if not wid:
            self.table.clear_rows()
            return
        
        stocks = self.service.get_warehouse_stocks(wid)
        self.table.clear_rows()
        for i, s in enumerate(stocks, 1):
            self.table.add_row([
                str(i), str(s['id']), s['customer_name'], 
                str(s['container_id'] or ""), s['goods_type'],
                str(s['quantity']), f"{s['weight']:.2f}", s['notes'] or ""
            ])
        self.table.resize_columns_to_contents()
        self.selected_stock_id = None
    
    def receive_stock(self):
        """استلام بضاعة جديدة في المخزن"""
        wid = self.combo_warehouse.currentData()
        if not wid:
            return show_error(self, "Erreur", "Sélectionnez un entrepôt")
        
        from modules.customers.service import CustomerService
        customer_service = CustomerService()
        customers = [(c['name'], c['id']) for c in customer_service.get_all_customers()]
        
        if not customers:
            return show_error(self, "Erreur", "Aucun client disponible")
        
        schema = [
            {"name": "customer_id", "label": "Client", "type": "dropdown", "options": customers, "required": True},
            {"name": "container_id", "label": "Conteneur ID", "type": "number"},
            {"name": "goods_type", "label": "Type Marchandise", "type": "text"},
            {"name": "quantity", "label": "Quantité", "type": "number", "required": True},
            {"name": "weight", "label": "Poids (kg)", "type": "number"},
            {"name": "notes", "label": "Notes", "type": "text"}
        ]
        
        dialog = SmartFormDialog("استلام بضاعة", schema, parent=self)
        if dialog.exec():
            data = dialog.get_results()
            success, msg, stock_id = self.service.create_stock(
                warehouse_id=wid,
                customer_id=data['customer_id'],
                container_id=data.get('container_id'),
                goods_type=data.get('goods_type', ''),
                quantity=int(data.get('quantity', 0)),
                weight=float(data.get('weight', 0)),
                notes=data.get('notes', '')
            )
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
            else:
                show_error(self, "Erreur", msg)
    
    def deliver_stock(self):
        """تسليم بضاعة للعميل"""
        if not self.selected_stock_id:
            return show_error(self, "Erreur", "Sélectionnez un stock")
        
        # Get stock info
        stocks = self.service.get_all_stocks()
        stock = next((s for s in stocks if s['id'] == self.selected_stock_id), None)
        if not stock:
            return show_error(self, "Erreur", "Stock non trouvé")
        
        schema = [
            {"name": "quantity", "label": "Quantité à livrer", "type": "number", "required": True},
            {"name": "notes", "label": "Notes", "type": "text"}
        ]
        
        dialog = SmartFormDialog("تسليم بضاعة", schema, parent=self)
        if dialog.exec():
            data = dialog.get_results()
            qty = int(data.get('quantity', 0))
            if qty <= 0 or qty > stock['quantity']:
                return show_error(self, "Erreur", f"La quantité doit être entre 1 et {stock['quantity']}")
            
            success, msg = self.service.deliver_stock(
                stock_id=self.selected_stock_id,
                quantity=qty,
                notes=data.get('notes', '')
            )
            if success:
                show_success(self, "Succès", msg)
                self.load_data()
            else:
                show_error(self, "Erreur", msg)


class MovementsTab(QWidget):
    """Tab pour les mouvements"""
    def __init__(self, service: WarehouseService):
        super().__init__()
        self.service = service
        self._setup_ui()
        self.load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Filter by warehouse
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Entrepôt:"))
        self.combo_warehouse = QComboBox()
        self.combo_warehouse.currentIndexChanged.connect(self.load_data)
        hbox.addWidget(self.combo_warehouse)
        hbox.addStretch()
        layout.addLayout(hbox)
        
        # Table
        self.table = EnhancedTableView(table_id="warehouse_movements")
        self.table.set_headers(["N°", "ID", "Date", "Type", "Client", "Quantité", "Notes"])
        layout.addWidget(self.table)
        
        self.refresh_warehouses()
    
    def refresh_warehouses(self):
        self.combo_warehouse.blockSignals(True)
        self.combo_warehouse.clear()
        for w in self.service.get_all_warehouses():
            self.combo_warehouse.addItem(w['name'], w['id'])
        self.combo_warehouse.blockSignals(False)
    
    def load_data(self):
        wid = self.combo_warehouse.currentData()
        if not wid:
            self.table.clear_rows()
            return
        
        movements = self.service.get_warehouse_movements(wid)
        self.table.clear_rows()
        for i, m in enumerate(movements, 1):
            type_str = "استلام" if m['movement_type'] == "RECEIVE" else "تسليم"
            self.table.add_row([
                str(i), str(m['id']), format_date(m['date']),
                type_str, m['customer_name'], str(m['quantity']), m['notes'] or ""
            ])
        self.table.resize_columns_to_contents()