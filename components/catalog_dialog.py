from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QDialogButtonBox, QLabel
)
from components.enhanced_table import EnhancedTableView
from components.dialogs import show_error, show_success

class GenericCatalogDialog(QDialog):
    """
    Composant réutilisable pour la gestion de catalogues simples (CRUD).
    Idéal pour des listes de références (Marchandises, Types de frais, etc.).
    """
    def __init__(self, title: str, 
                 get_data_func, create_data_func, delete_data_func, restore_data_func,
                 primary_placeholder="Nom de l'élément", 
                 secondary_placeholder="Description (optionnel)",
                 headers=["N°", "ID", "Nom", "Description"],
                 edit_data_func=None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 420)

        # Callbacks
        self.get_data_func = get_data_func
        self.create_data_func = create_data_func
        self.delete_data_func = delete_data_func
        self.restore_data_func = restore_data_func
        self.edit_data_func = edit_data_func  # Optional edit function

        self.primary_placeholder = primary_placeholder
        self.secondary_placeholder = secondary_placeholder
        self.headers = headers

        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar d'ajout
        toolbar = QHBoxLayout()
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(self.primary_placeholder)
        
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText(self.secondary_placeholder)
        
        btn_add = QPushButton("+ Ajouter")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._add_item)
        
        toolbar.addWidget(self.inp_name, 3)
        if self.secondary_placeholder:
            toolbar.addWidget(self.inp_desc, 2)
        toolbar.addWidget(btn_add)
        
        layout.addLayout(toolbar)

        # Table des données
        table_id = "catalog_" + self.windowTitle().lower().replace(" ", "_").replace("-", "")
        self.table = EnhancedTableView(table_id=table_id)
        self.table.set_headers(self.headers)
        self.table.hide_column(1)  # Cacher l'ID

        self.table.addClicked.connect(self._add_item)
        
        # Masquer le bouton Éditer si la fonctionnalité n'est pas fournie
        if self.edit_data_func:
            self.table.editClicked.connect(self._edit_item)
        else:
            self.table.edit_action.setVisible(False)
            
        self.table.deleteClicked.connect(self._delete_item)
        self.table.restoreClicked.connect(self._restore_item)
        self.table.refreshClicked.connect(self.load_data)
        self.table.status_filter.statusChanged.connect(self.load_data)
        
        layout.addWidget(self.table)

        # Bouton fermer
        btn_close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_close.rejected.connect(self.reject)
        layout.addWidget(btn_close)

    def load_data(self):
        filter_status = self.table.status_filter.get_filter()
        self.table.update_actions_for_status(filter_status)
        
        # Le callback doit accepter "include_inactive"
        include_inactive = filter_status != "active"
        items = self.get_data_func(include_inactive=include_inactive)
        
        if filter_status == "inactive":
            items = [item for item in items if not item.get('is_active', True)]
            
        self.table.clear_rows()
        for item in items:
            desc = item.get('description', '')
            self.table.add_row(
                [None, str(item['id']), item.get('name', ''), desc], 
                is_active=item.get('is_active', True)
            )
        self.table.resize_columns_to_contents()

    def _add_item(self):
        name = self.inp_name.text().strip()
        desc = self.inp_desc.text().strip()
        
        if not name:
            return show_error(self, "Erreur", "Le champ principal est obligatoire")
            
        success, message, new_id = self.create_data_func(name, desc)
        if success:
            show_success(self, "Succès", message)
            self.inp_name.clear()
            self.inp_desc.clear()
            self.load_data()
        else:
            show_error(self, "Erreur", message)

    def _edit_item(self, row_idx):
        if not hasattr(self, 'edit_data_func'):
            show_error(self, "Erreur", "Fonction d'édition non disponible")
            return
        
        item_id = int(self.table.get_row_data(row_idx)[1])
        item_data = self.get_data_func(include_inactive=True)
        
        if not item_data:
            show_error(self, "Erreur", "Élément introuvable")
            return
        
        item = next((x for x in item_data if x.get('id') == item_id), None)
        if not item:
            show_error(self, "Erreur", "Élément introuvable")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "Modifier le nom", "Nouveau nom:", 
                                           text=item.get('name', ''))
        if ok and new_name.strip():
            if not self.edit_data_func:
                return show_error(self, "Erreur", "L'édition n'est pas disponible pour cet élément.")
            
            success, message = self.edit_data_func(item_id, new_name.strip())
            if success:
                show_success(self, "Succès", message)
                self.load_data()
            else:
                show_error(self, "Erreur", message)

    def _delete_item(self, row_idx):
        if not self.delete_data_func:
            return show_error(self, "Erreur", "La suppression n'est pas disponible.")
        item_id = int(self.table.get_row_data(row_idx)[1])
        success, message = self.delete_data_func(item_id)
        if success:
            show_success(self, "Succès", message)
            self.load_data()
        else:
            show_error(self, "Erreur", message)

    def _restore_item(self, row_idx):
        if not self.restore_data_func:
            return show_error(self, "Erreur", "La restauration n'est pas disponible.")
        item_id = int(self.table.get_row_data(row_idx)[1])
        success, message = self.restore_data_func(item_id)
        if success:
            show_success(self, "Succès", message)
            self.load_data()
        else:
            show_error(self, "Erreur", message)