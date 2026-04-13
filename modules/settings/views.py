"""
Vues pour le module Parametres
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFormLayout, QGroupBox, QGridLayout,
    QMessageBox, QListWidget, QFileDialog, QCheckBox,
    QTabWidget, QScrollArea, QFrame, QComboBox,
    QSpinBox, QColorDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
import os
from datetime import datetime

from components.dialogs import show_error, show_success, confirm_action
from .service import SettingsService
from core.themes import THEMES, get_theme_qss, get_active_colors
from PyQt6.QtWidgets import QApplication


class SettingsView(QWidget):
    """Vue principale des parametres"""

    def __init__(self):
        super().__init__()
        self.service = SettingsService()
        self._setup_ui()
        self.load_settings()

    def _create_save_button(self, text: str, callback) -> QPushButton:
        """[TREE] Bouton de sauvegarde unifié - thème actif"""
        c = get_active_colors()
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setMinimumWidth(200)
        btn.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold; font-size: 13px;
                background-color: {c['accent']}; color: #ffffff;
                border-radius: 6px; padding: 8px 20px;
            }}
            QPushButton:hover {{ background-color: {c['accent_hover']}; }}
            QPushButton:pressed {{ background-color: {c['selection']}; }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # TAB 1: Institution
        self.tab_info = QWidget()
        self._setup_info_tab()
        self.tabs.addTab(self.tab_info, "Institution")

        # TAB 2: Regles de Gestion
        self.tab_rules = QWidget()
        self._setup_rules_tab()
        self.tabs.addTab(self.tab_rules, "Regles de Gestion")

        # TAB 3: Interface
        self.tab_interface = QWidget()
        self._setup_interface_tab()
        self.tabs.addTab(self.tab_interface, "Interface")

        # TAB 4: Sauvegarde Auto
        self.tab_auto_backup = QWidget()
        self._setup_auto_backup_tab()
        self.tabs.addTab(self.tab_auto_backup, "Sauvegarde Auto")

        # TAB 5: Impression & Export
        self.tab_print = QWidget()
        self._setup_print_tab()
        self.tabs.addTab(self.tab_print, "Impression & Export")

        # TAB 6: Base de Donnees
        self.tab_db = QWidget()
        self._setup_db_tab()
        self.tabs.addTab(self.tab_db, "Base de Donnees")

        # TAB 7: Theme
        self.tab_theme = QWidget()
        self._setup_theme_tab()
        self.tabs.addTab(self.tab_theme, "Theme")

    # ========================================================================
    # TAB 1: INSTITUTION
    # ========================================================================

    def _setup_info_tab(self):
        layout = QVBoxLayout(self.tab_info)
        
        # Use QScrollArea to ensure nothing is hidden on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 20, 30, 20)

        # Two-column layout wrapper
        cols_widget = QWidget()
        cols_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(40)  # More spacing between columns
        cols_layout.setContentsMargins(30, 0, 30, 0)
        cols_layout.setStretch(0, 1)
        cols_layout.setStretch(1, 1)

        # Left column - Basic information
        group_left = QGroupBox("Informations Générales")
        form_left = QFormLayout(group_left)
        form_left.setSpacing(10)
        form_left.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_left.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Define max width for input fields
        FIELD_MAX_WIDTH = 500  # [UNIFIED] 2026-04-08 - Increased width

        def make_input():
            w = QLineEdit()
            w.setMaximumWidth(FIELD_MAX_WIDTH)
            return w

        self.inp_nom_magasin = make_input()
        self.inp_adresse = make_input()
        self.inp_ville = make_input()
        self.inp_tel = make_input()
        self.inp_fixe = make_input()
        self.inp_fax = make_input()
        self.inp_email = make_input()
        self.inp_site_web = make_input()
        self.inp_activite = make_input()

        form_left.addRow("Nom Magasin:", self.inp_nom_magasin)
        form_left.addRow("Adresse:", self.inp_adresse)
        form_left.addRow("Ville:", self.inp_ville)
        form_left.addRow("Tel:", self.inp_tel)
        form_left.addRow("Fixe:", self.inp_fixe)
        form_left.addRow("Fax:", self.inp_fax)
        form_left.addRow("Email:", self.inp_email)
        form_left.addRow("Site Web:", self.inp_site_web)
        form_left.addRow("Activité:", self.inp_activite)

        cols_layout.addWidget(group_left, 1)

        # Right column - Legal information
        group_right = QGroupBox("Informations Juridiques & Fiscales")
        form_right = QFormLayout(group_right)
        form_right.setSpacing(10)
        form_right.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_right.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.inp_rc = make_input()
        self.inp_nif = make_input()
        self.inp_nis = make_input()
        self.inp_rib = make_input()
        self.inp_nom_banque = make_input()
        self.inp_article = make_input()
        self.inp_capital = make_input()
        self.inp_ice = make_input()
        self.inp_cnss = make_input()
        self.inp_taxe_pro = make_input()

        form_right.addRow("R.C:", self.inp_rc)
        form_right.addRow("NIF:", self.inp_nif)
        form_right.addRow("NIS:", self.inp_nis)
        form_right.addRow("RIB:", self.inp_rib)
        form_right.addRow("Nom Banque:", self.inp_nom_banque)
        form_right.addRow("Article:", self.inp_article)
        form_right.addRow("Capital:", self.inp_capital)
        form_right.addRow("ICE:", self.inp_ice)
        form_right.addRow("CNSS:", self.inp_cnss)
        form_right.addRow("Taxe Professionnelle:", self.inp_taxe_pro)

        cols_layout.addWidget(group_right, 1)

        # Add columns to main container with stretch to push button to bottom
        container_layout.addWidget(cols_widget, 1)  # Stretch factor = 1

        # Save button at the bottom
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_company_info))
        container_layout.addLayout(btn_layout)

        # Finalize scroll
        scroll.setWidget(container)
        
        # Load existing data
        self._load_company_info()

    # ========================================================================
    # TAB 2: REGLES DE GESTION
    # ========================================================================

    def _setup_rules_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout = QVBoxLayout(self.tab_rules)
        layout.addWidget(scroll)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 20, 30, 20)

        # Two-column wrapper
        cols_widget = QWidget()
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(30)
        cols_layout.setContentsMargins(0, 0, 0, 0)
        cols_layout.setStretch(0, 1)
        cols_layout.setStretch(1, 1)

        FIELD_MAX_WIDTH = 350
        def make_input():
            w = QLineEdit()
            w.setMaximumWidth(FIELD_MAX_WIDTH)
            return w

        # --- Left Column: Trésorerie & Risques ---
        group_balance = QGroupBox("Trésorerie & Risques")
        vbox_balance = QVBoxLayout(group_balance)

        desc_balance = QLabel(
            "Contrôle l'autorisation des opérations à découvert (Solde Négatif)."
        )
        desc_balance.setWordWrap(True)
        desc_balance.setStyleSheet("color: #8b949e; padding: 5px 0; margin-bottom: 10px;")
        vbox_balance.addWidget(desc_balance)

        self.allow_negative_treasury = QCheckBox("Autoriser le solde négatif en Trésorerie (DA)")
        self.allow_negative_treasury.setStyleSheet("font-size: 13px; padding: 5px 0;")
        self.allow_negative_treasury.setToolTip(
            "Si active, les débits seront autorisés même si le solde est insuffisant."
        )
        vbox_balance.addWidget(self.allow_negative_treasury)

        self.allow_negative_currency = QCheckBox("Autoriser le solde négatif en Devises")
        self.allow_negative_currency.setStyleSheet("font-size: 13px; padding: 5px 0;")
        self.allow_negative_currency.setToolTip(
            "Si active, les paiements en devise seront autorisés même si le solde est insuffisant."
        )
        vbox_balance.addWidget(self.allow_negative_currency)
        
        vbox_balance.addStretch() # Push content to top
        cols_layout.addWidget(group_balance, 1)

        # --- Right Column: Facturation & Logistique ---
        group_billing = QGroupBox("Facturation & Numérotation")
        form_billing = QFormLayout(group_billing)
        form_billing.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_billing.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        desc_bill = QLabel(
            "Règles de génération automatique des documents."
        )
        desc_bill.setWordWrap(True)
        desc_bill.setStyleSheet("color: #8b949e; padding: 5px 0; margin-bottom: 10px;")
        # Add description to layout
        grid_bill = QGridLayout()
        grid_bill.addWidget(desc_bill)
        # Use a container widget to mix Form and other layouts if needed, 
        # but for simplicity, let's just use form rows for the settings.
        
        # Auto-Increment Invoices
        self.auto_invoice_number = QCheckBox("Numérotation automatique des factures")
        self.auto_invoice_number.setChecked(True)
        form_billing.addRow("", self.auto_invoice_number)

        # Invoice Prefix
        self.invoice_prefix = make_input()
        self.invoice_prefix.setText("FAC")
        form_billing.addRow("Préfixe Facture:", self.invoice_prefix)

        # Tolerance (Numeric example for the column)
        self.tolerance_ecart = make_input()
        self.tolerance_ecart.setPlaceholderText("0.00")
        # form_billing.addRow("Tolérance Écart (DA):", self.tolerance_ecart) # Placeholder for future

        cols_layout.addWidget(group_billing, 1)

        container_layout.addWidget(cols_widget)
        container_layout.addStretch()
        
        # Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_rules_settings))
        container_layout.addLayout(btn_layout)

        scroll.setWidget(container)

    # ========================================================================
    # TAB 3: INTERFACE
    # ========================================================================

    def _setup_interface_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout = QVBoxLayout(self.tab_interface)
        layout.addWidget(scroll)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 20, 30, 20)

        # Two-column wrapper
        cols_widget = QWidget()
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(30)
        cols_layout.setContentsMargins(0, 0, 0, 0)

        # --- Right Column: Formats & Affichage ---
        group_formats = QGroupBox("Formats des Nombres & Dates")
        form_formats = QFormLayout(group_formats)
        form_formats.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_formats.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        FIELD_MAX_WIDTH = 350
        def make_input():
            w = QLineEdit()
            w.setMaximumWidth(FIELD_MAX_WIDTH)
            return w

        def make_combo():
            w = QComboBox()
            w.setMaximumWidth(FIELD_MAX_WIDTH)
            return w

        self.amount_format_combo = make_combo()
        self.amount_format_combo.addItem("Espace (1 000.00) - Français", "space")
        self.amount_format_combo.addItem("Point (1.000,00) - Windows", "dot")
        form_formats.addRow("Format des montants:", self.amount_format_combo)

        self.rows_per_page = make_combo()
        self.rows_per_page.addItems(["20", "50", "100"])
        form_formats.addRow("Lignes par page:", self.rows_per_page)

        cols_layout.addWidget(group_formats, 1)

        # --- Left Column: Apparence Visuelle ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)

        # Colors
        group_colors = QGroupBox("Couleurs des Soldes")
        vbox_colors = QVBoxLayout(group_colors)
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Positif:"))
        self.color_positive_btn = QPushButton("#238636")
        self.color_positive_btn.setStyleSheet("background-color: #238636; color: white; padding: 8px; border-radius: 4px;")
        self.color_positive_btn.setFixedWidth(120)
        self.color_positive_btn.clicked.connect(lambda: self._pick_color("positive"))
        pos_layout.addWidget(self.color_positive_btn)
        pos_layout.addStretch()
        vbox_colors.addLayout(pos_layout)

        neg_layout = QHBoxLayout()
        neg_layout.addWidget(QLabel("Négatif:"))
        self.color_negative_btn = QPushButton("#f85149")
        self.color_negative_btn.setStyleSheet("background-color: #f85149; color: white; padding: 8px; border-radius: 4px;")
        self.color_negative_btn.setFixedWidth(120)
        self.color_negative_btn.clicked.connect(lambda: self._pick_color("negative"))
        neg_layout.addWidget(self.color_negative_btn)
        neg_layout.addStretch()
        vbox_colors.addLayout(neg_layout)

        left_layout.addWidget(group_colors)

        # Dashboard & Window
        group_sys = QGroupBox("Paramètres Système & Dashboard")
        form_sys = QFormLayout(group_sys)
        form_sys.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.dashboard_recent_limit = make_combo()
        self.dashboard_recent_limit.addItems(["5", "10", "20", "50"])
        form_sys.addRow("Dernières opérations:", self.dashboard_recent_limit)

        self.window_mode_combo = make_combo()
        self.window_mode_combo.addItem("Normal", 1)
        self.window_mode_combo.addItem("Agrandie (Maximized)", 2)
        self.window_mode_combo.addItem("Plein écran", 3)
        form_sys.addRow("Mode fenêtre au démarrage:", self.window_mode_combo)

        left_layout.addWidget(group_sys)
        left_layout.addStretch()

        cols_layout.addWidget(left_widget, 1)

        # Finalize layout
        container_layout.addWidget(cols_widget)
        container_layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_interface_settings))
        container_layout.addLayout(btn_layout)

        scroll.setWidget(container)

    def _pick_color(self, color_type):
        if color_type == "positive":
            btn = self.color_positive_btn
        elif color_type == "negative":
            btn = self.color_negative_btn
        else:
            return
        
        current = btn.text()
        color = QColorDialog.getColor(QColor(current), self, "Choisir une couleur")
        if color.isValid():
            hex_color = color.name()
            btn.setText(hex_color)
            btn.setStyleSheet(f"background-color: {hex_color}; color: white; padding: 12px 24px; border-radius: 4px;")

    # ========================================================================
    # TAB 4: SAUVEGARDE AUTO
    # ========================================================================

    def _setup_auto_backup_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout = QVBoxLayout(self.tab_auto_backup)
        layout.addWidget(scroll)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 20, 30, 20)

        # Two-column wrapper
        cols_widget = QWidget()
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(30)
        cols_layout.setContentsMargins(0, 0, 0, 0)

        # --- Right Column: Configuration ---
        group_config = QGroupBox("Configuration de la Sauvegarde")
        form_config = QFormLayout(group_config)
        form_config.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_config.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        desc_config = QLabel(
            "Configurez la sauvegarde automatique. Les anciennes sauvegardes seront "
            "supprimées selon le nombre maximum défini."
        )
        desc_config.setWordWrap(True)
        desc_config.setStyleSheet("color: #8b949e; padding: 5px 0; margin-bottom: 10px;")
        form_config.addRow(desc_config)

        FIELD_MAX_WIDTH = 300
        def make_combo():
            w = QComboBox()
            w.setMaximumWidth(FIELD_MAX_WIDTH)
            return w
        def make_spin():
            w = QSpinBox()
            w.setMaximumWidth(FIELD_MAX_WIDTH)
            w.setRange(1, 100)
            return w

        self.auto_backup_freq = make_combo()
        self.auto_backup_freq.addItem("Désactivée", "none")
        self.auto_backup_freq.addItem("À la fermeture", "on_close")
        self.auto_backup_freq.addItem("Quotidienne", "daily")
        self.auto_backup_freq.addItem("Hebdomadaire", "weekly")
        form_config.addRow("Fréquence:", self.auto_backup_freq)

        self.max_backup_count = make_spin()
        self.max_backup_count.setValue(10)
        self.max_backup_count.setSuffix(" fichiers")
        form_config.addRow("Nombre max de sauvegardes:", self.max_backup_count)

        self.next_backup_label = QLabel("En attente de configuration...")
        self.next_backup_label.setStyleSheet("color: #8b949e; font-style: italic; padding: 5px 0;")
        form_config.addRow("Prochaine sauvegarde:", self.next_backup_label)

        cols_layout.addWidget(group_config, 1)

        # --- Left Column: Gestion & Maintenance ---
        group_maint = QGroupBox("Gestion des Données & Maintenance")
        vbox_maint = QVBoxLayout(group_maint)

        self.btn_clear_cache = QPushButton("🗑️ Vider le Cache Python")
        self.btn_clear_cache.setMaximumWidth(280)
        self.btn_clear_cache.setStyleSheet("padding: 8px 16px; font-weight: bold; background-color: #6e7681; color: white; border-radius: 4px;")
        self.btn_clear_cache.clicked.connect(self.clear_pycache)
        vbox_maint.addWidget(self.btn_clear_cache, alignment=Qt.AlignmentFlag.AlignLeft)

        cache_hint = QLabel("Nettoie les fichiers temporaires pour appliquer les mises à jour.")
        cache_hint.setWordWrap(True)
        cache_hint.setStyleSheet("color: #8b949e; font-size: 11px; margin-top: 4px;")
        vbox_maint.addWidget(cache_hint)

        vbox_maint.addSpacing(15)

        self.btn_reset = QPushButton("⚠️ Réinitialiser la Base")
        self.btn_reset.setMaximumWidth(280)
        self.btn_reset.setStyleSheet("padding: 8px 16px; font-weight: bold; background-color: #f85149; color: white; border-radius: 4px;")
        self.btn_reset.clicked.connect(self.reset_system)
        vbox_maint.addWidget(self.btn_reset, alignment=Qt.AlignmentFlag.AlignLeft)

        reset_hint = QLabel("Supprime toutes les données. Une sauvegarde est créée avant.")
        reset_hint.setWordWrap(True)
        reset_hint.setStyleSheet("color: #8b949e; font-size: 11px; margin-top: 4px;")
        vbox_maint.addWidget(reset_hint)

        vbox_maint.addStretch() # Push buttons to top
        cols_layout.addWidget(group_maint, 1)

        container_layout.addWidget(cols_widget)
        container_layout.addStretch()

        # Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_auto_backup_settings))
        container_layout.addLayout(btn_layout)

        scroll.setWidget(container)

    # ========================================================================
    # TAB 5: IMPRESSION & EXPORT
    # ========================================================================

    def _setup_print_tab(self):
        layout = QVBoxLayout(self.tab_print)

        group = QGroupBox("Configuration de l'Impression et de l'Export")
        form = QFormLayout(group)

        # Logo
        logo_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setPlaceholderText("Aucun logo selectionne...")
        logo_layout.addWidget(self.logo_path_input)

        btn_browse = QPushButton("Parcourir")
        btn_browse.setStyleSheet("padding: 12px 24px;")
        btn_browse.clicked.connect(self._browse_logo)
        logo_layout.addWidget(btn_browse)
        form.addRow("Logo de l'entreprise:", logo_layout)

        logo_hint = QLabel("Formats acceptes: PNG, JPG, SVG. Taille recommandee: 200x200px max.")
        logo_hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        form.addRow("", logo_hint)

        # Footer PDF
        self.pdf_footer_input = QLineEdit()
        self.pdf_footer_input.setPlaceholderText("Ex: Societe XYZ - Registre de Commerce: 12345")
        form.addRow("Pied de page PDF:", self.pdf_footer_input)

        # Company name in header
        self.pdf_use_company_name = QCheckBox("Inclure le nom de l'entreprise dans l'en-tete des rapports")
        self.pdf_use_company_name.setChecked(True)
        form.addRow("", self.pdf_use_company_name)

        btn = self._create_save_button("Enregistrer", self.save_print_settings)
        form.addRow("", btn)

        layout.addWidget(group)
        layout.addStretch()

    def _browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selectionner un logo", "",
            "Images (*.png *.jpg *.jpeg *.svg);;Tous les fichiers (*)"
        )
        if file_path:
            self.logo_path_input.setText(file_path)

    # ========================================================================
    # TAB 6: BASE DE DONNEES
    # ========================================================================

    def _setup_db_tab(self):
        layout = QVBoxLayout(self.tab_db)
        layout.setSpacing(15)

        # --- Sauvegardes ---
        backup_group = QGroupBox("Gestion des Sauvegardes")
        backup_layout = QVBoxLayout(backup_group)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Dossier:"))
        self.backup_path_label = QLabel(os.path.abspath("backups"))
        self.backup_path_label.setStyleSheet("color: #58a6ff; font-family: monospace; font-weight: bold;")
        path_layout.addWidget(self.backup_path_label)
        path_layout.addStretch()

        self.backup_count_label = QLabel("")
        self.backup_count_label.setStyleSheet("color: #8b949e;")
        path_layout.addWidget(self.backup_count_label)
        backup_layout.addLayout(path_layout)

        self.backup_list = QListWidget()
        self.backup_list.setStyleSheet("min-height: 180px;")
        backup_layout.addWidget(self.backup_list)

        btn_layout = QHBoxLayout()

        _c = get_active_colors()
        self.btn_backup = QPushButton("Nouvelle Sauvegarde")
        self.btn_backup.setStyleSheet(f"padding: 12px 24px; font-weight: bold; background-color: {_c['accent']}; color: #ffffff;")
        self.btn_backup.clicked.connect(self.create_backup)

        self.btn_restore = QPushButton("Restaurer la selection")
        self.btn_restore.setStyleSheet("padding: 12px 24px;")
        self.btn_restore.clicked.connect(self.restore_backup)

        btn_layout.addWidget(self.btn_backup)
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addStretch()
        backup_layout.addLayout(btn_layout)

        layout.addWidget(backup_group)

        # --- Maintenance ---
        maint_group = QGroupBox("Maintenance")
        maint_layout = QVBoxLayout(maint_group)

        desc = QLabel(
            "La reinitialisation supprime toutes les donnees (comptes, transactions, clients, "
            "licences, conteneurs, dettes) et restaure les parametres par defaut. "
            "Une sauvegarde automatique est creee avant chaque operation destructive."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8b949e; padding: 5px 0;")
        maint_layout.addWidget(desc)

        # Bouton Vider le Cache
        self.btn_clear_cache = QPushButton("🗑️ Vider le Cache de Python (__pycache__)")
        self.btn_clear_cache.setStyleSheet(
            "padding: 12px 24px; font-weight: bold; background-color: #6e7681; color: white; border-radius: 4px;"
        )
        self.btn_clear_cache.clicked.connect(self.clear_pycache)
        maint_layout.addWidget(self.btn_clear_cache)

        self.btn_reset = QPushButton("Reinitialiser toute la base de donnees")
        self.btn_reset.setStyleSheet(
            "padding: 12px 24px; font-weight: bold; background-color: #f85149; color: white; border-radius: 4px;"
        )
        self.btn_reset.clicked.connect(self.reset_system)
        maint_layout.addWidget(self.btn_reset)

        layout.addWidget(maint_group)
        layout.addStretch()

        # [UNIFIED] 2026-04-08 - Save button for DB tab
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_db_settings))
        layout.addLayout(btn_layout)

    def save_db_settings(self):
        """Save database settings - currently no specific settings to save"""
        show_success(self, "Succès", "Paramètres de base de données sauvegardés.")

    def _setup_theme_tab(self):
        layout = QVBoxLayout(self.tab_theme)

        group = QGroupBox("Apparence Visuelle")
        vbox = QVBoxLayout(group)

        current_theme_id = self.service.get_setting("active_theme", "emerald")
        theme_info_data = THEMES.get(current_theme_id, THEMES["emerald"])

        self.theme_info_lbl = QLabel(f"Theme Actuel : {theme_info_data['name']}")
        self.theme_info_lbl.setStyleSheet("font-size: 16px; color: #58a6ff; margin-bottom: 5px;")
        vbox.addWidget(self.theme_info_lbl)

        self.theme_desc_lbl = QLabel(
            "Personnalisez l'apparence de votre application pour un confort visuel optimal."
        )
        self.theme_desc_lbl.setStyleSheet("color: #8b949e; line-height: 150%;")
        vbox.addWidget(self.theme_desc_lbl)

        vbox.addSpacing(20)

        vbox.addWidget(QLabel("Choisir un Style :"))
        self.theme_selector = QComboBox()
        for tid in sorted(THEMES.keys(), key=lambda x: x != "emerald"):
            self.theme_selector.addItem(THEMES[tid]["name"], tid)

        idx = self.theme_selector.findData(current_theme_id)
        if idx >= 0:
            self.theme_selector.setCurrentIndex(idx)

        vbox.addWidget(self.theme_selector)

        btn_apply = QPushButton("Appliquer le Theme")
        _tc = get_active_colors()
        btn_apply.setStyleSheet(f"""
            QPushButton {{
                padding: 12px 24px;
                background-color: {_tc['accent']}; color: #ffffff;
                font-weight: bold; border-radius: 8px;
            }}
            QPushButton:hover {{ background-color: {_tc['accent_hover']}; }}
        """)
        btn_apply.clicked.connect(self._apply_theme)
        vbox.addWidget(btn_apply)

        layout.addWidget(group)
        layout.addStretch()

        # [UNIFIED] 2026-04-08 - Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_theme_settings))
        layout.addLayout(btn_layout)

    # ========================================================================
    # ACTIONS
    # ========================================================================

    def _apply_theme(self):
        theme_id = self.theme_selector.currentData()
        self.service.set_setting("active_theme", theme_id)
        qss = get_theme_qss(theme_id)
        QApplication.instance().setStyleSheet(qss)
        self.theme_info_lbl.setText(f"Theme Actuel : {THEMES[theme_id]['name']}")
        show_success(self, "Theme Applique", f"Le style '{THEMES[theme_id]['name']}' a ete active.")

    def save_theme_settings(self):
        """Save theme settings (calls _apply_theme)"""
        self._apply_theme()

    def load_settings(self):
        # Institution
        self._load_company_info()

        # Regles de Gestion
        self.allow_negative_treasury.setChecked(
            self.service.get_setting("allow_negative_treasury", "False") == "True"
        )
        self.allow_negative_currency.setChecked(
            self.service.get_setting("allow_negative_currency", "False") == "True"
        )

        # Facturation
        self.auto_invoice_number.setChecked(
            self.service.get_setting("auto_invoice_number", "True") == "True"
        )
        self.invoice_prefix.setText(self.service.get_setting("invoice_prefix", "FAC"))

        # Interface
        rpp = self.service.get_setting("rows_per_page", "20")
        idx = self.rows_per_page.findText(rpp)
        if idx >= 0: self.rows_per_page.setCurrentIndex(idx)

        # [UNIFIED] 2026-04-08 - Window mode default to Maximized (2)
        window_mode = self.service.get_setting("window_mode", "2")
        idx = self.window_mode_combo.findData(int(window_mode) if window_mode.isdigit() else 2)
        if idx >= 0: self.window_mode_combo.setCurrentIndex(idx)

        color_pos = self.service.get_setting("color_positive_balance", "#238636")
        self.color_positive_btn.setText(color_pos)
        self.color_positive_btn.setStyleSheet(
            f"background-color: {color_pos}; color: white; padding: 12px 24px; border-radius: 4px;"
        )

        color_neg = self.service.get_setting("color_negative_balance", "#f85149")
        self.color_negative_btn.setText(color_neg)
        self.color_negative_btn.setStyleSheet(
            f"background-color: {color_neg}; color: white; padding: 12px 24px; border-radius: 4px;"
        )

        # [UNIFIED] 2026-04-08 - Format des montants
        amount_fmt = self.service.get_setting("amount_format", "dot")
        idx = self.amount_format_combo.findData(amount_fmt)
        if idx >= 0: self.amount_format_combo.setCurrentIndex(idx)

        dash_limit = self.service.get_setting("dashboard_recent_limit", "10")
        idx = self.dashboard_recent_limit.findText(dash_limit)
        if idx >= 0: self.dashboard_recent_limit.setCurrentIndex(idx)

        # Sauvegarde Auto
        freq = self.service.get_setting("auto_backup_frequency", "on_close")
        idx = self.auto_backup_freq.findData(freq)
        if idx >= 0: self.auto_backup_freq.setCurrentIndex(idx)

        max_count = int(self.service.get_setting("max_backup_count", "10"))
        self.max_backup_count.setValue(max_count)
        self._update_next_backup_label()

        # Impression & Export
        self.logo_path_input.setText(self.service.get_setting("company_logo_path", ""))
        self.pdf_footer_input.setText(self.service.get_setting("pdf_footer_text", ""))
        self.pdf_use_company_name.setChecked(
            self.service.get_setting("pdf_use_company_name", "True") == "True"
        )

        # DB
        self.refresh_backup_list()

    def save_company_info(self):
        # Informations Générales
        self.service.set_setting("nom_magasin", self.inp_nom_magasin.text(), "Nom du magasin", "COMPANY")
        self.service.set_setting("adresse", self.inp_adresse.text(), "Adresse", "COMPANY")
        self.service.set_setting("ville", self.inp_ville.text(), "Ville", "COMPANY")
        self.service.set_setting("tel", self.inp_tel.text(), "Telephone", "COMPANY")
        self.service.set_setting("fixe", self.inp_fixe.text(), "Telephone fixe", "COMPANY")
        self.service.set_setting("fax", self.inp_fax.text(), "Fax", "COMPANY")
        self.service.set_setting("email", self.inp_email.text(), "Email", "COMPANY")
        self.service.set_setting("site_web", self.inp_site_web.text(), "Site web", "COMPANY")
        self.service.set_setting("activite", self.inp_activite.text(), "Activite", "COMPANY")
        
        # Informations Juridiques & Fiscales
        self.service.set_setting("rc", self.inp_rc.text(), "Registre de Commerce", "COMPANY")
        self.service.set_setting("nif", self.inp_nif.text(), "NIF", "COMPANY")
        self.service.set_setting("nis", self.inp_nis.text(), "NIS", "COMPANY")
        self.service.set_setting("rib", self.inp_rib.text(), "RIB", "COMPANY")
        self.service.set_setting("nom_banque", self.inp_nom_banque.text(), "Nom banque", "COMPANY")
        self.service.set_setting("article", self.inp_article.text(), "Article", "COMPANY")
        self.service.set_setting("capital", self.inp_capital.text(), "Capital", "COMPANY")
        self.service.set_setting("ice", self.inp_ice.text(), "ICE", "COMPANY")
        self.service.set_setting("cnss", self.inp_cnss.text(), "CNSS", "COMPANY")
        self.service.set_setting("taxe_pro", self.inp_taxe_pro.text(), "Taxe professionnelle", "COMPANY")
        
        show_success(self, "Succes", "Informations de l'entreprise mises a jour.")
    
    def _load_company_info(self):
        # Informations Générales
        self.inp_nom_magasin.setText(self.service.get_setting("nom_magasin", ""))
        self.inp_adresse.setText(self.service.get_setting("adresse", ""))
        self.inp_ville.setText(self.service.get_setting("ville", ""))
        self.inp_tel.setText(self.service.get_setting("tel", ""))
        self.inp_fixe.setText(self.service.get_setting("fixe", ""))
        self.inp_fax.setText(self.service.get_setting("fax", ""))
        self.inp_email.setText(self.service.get_setting("email", ""))
        self.inp_site_web.setText(self.service.get_setting("site_web", ""))
        self.inp_activite.setText(self.service.get_setting("activite", ""))
        
        # Informations Juridiques & Fiscales
        self.inp_rc.setText(self.service.get_setting("rc", ""))
        self.inp_nif.setText(self.service.get_setting("nif", ""))
        self.inp_nis.setText(self.service.get_setting("nis", ""))
        self.inp_rib.setText(self.service.get_setting("rib", ""))
        self.inp_nom_banque.setText(self.service.get_setting("nom_banque", ""))
        self.inp_article.setText(self.service.get_setting("article", ""))
        self.inp_capital.setText(self.service.get_setting("capital", ""))
        self.inp_ice.setText(self.service.get_setting("ice", ""))
        self.inp_cnss.setText(self.service.get_setting("cnss", ""))
        self.inp_taxe_pro.setText(self.service.get_setting("taxe_pro", ""))

    def save_rules_settings(self):
        val_treasury = "True" if self.allow_negative_treasury.isChecked() else "False"
        val_currency = "True" if self.allow_negative_currency.isChecked() else "False"
        self.service.set_setting("allow_negative_treasury", val_treasury,
                                 "Autoriser solde negatif en Tresorerie", "RULES")
        self.service.set_setting("allow_negative_currency", val_currency,
                                 "Autoriser solde negatif en Devise", "RULES")
        
        # Facturation
        val_auto_inv = "True" if self.auto_invoice_number.isChecked() else "False"
        self.service.set_setting("auto_invoice_number", val_auto_inv,
                                 "Numérotation auto factures", "RULES")
        self.service.set_setting("invoice_prefix", self.invoice_prefix.text(),
                                 "Préfixe facturation", "RULES")

        show_success(self, "Succes", "Regles de gestion mises a jour.")

    def save_interface_settings(self):
        self.service.set_setting("rows_per_page", self.rows_per_page.currentText(),
                                 "Lignes par page", "INTERFACE")
        self.service.set_setting("color_positive_balance", self.color_positive_btn.text(),
                                 "Couleur solde positif", "INTERFACE")
        self.service.set_setting("color_negative_balance", self.color_negative_btn.text(),
                                 "Couleur solde negatif", "INTERFACE")
        # [UNIFIED] 2026-04-08 - Default search highlight color
        self.service.set_setting("color_search_highlight", "#ffe000",
                                 "Couleur surbrillance recherche", "INTERFACE")
        # [UNIFIED] 2026-04-08 - Format des montants
        amount_format = self.amount_format_combo.currentData()
        self.service.set_setting("amount_format", amount_format,
                                 "Format des montants (space/dot)", "INTERFACE")
        
        # 🚀 APPLY IMMEDIATELY (Instant update across the app)
        from utils.formatters import set_amount_format
        set_amount_format(amount_format)
        # Notify the main app to refresh views (if parent has refresh_all)
        if hasattr(self.parent(), 'refresh_all'):
            self.parent().refresh_all()

        # [CUSTOM] 2026-04-03 - Window mode
        window_mode = self.window_mode_combo.currentData()
        self.service.set_setting("window_mode", str(window_mode),
                                 "Mode de la fenetre (1=normal, 2=max, 3=fullscreen)", "INTERFACE")
        self.service.set_setting("dashboard_recent_limit", self.dashboard_recent_limit.currentText(),
                                 "Limite dernieres operations", "DASHBOARD")
        
        show_success(self, "Succes", f"Parametres d'interface enregistres.\nMode fenetre: {['Normal', 'Agrandie', 'Plein ecran'][window_mode-1]}")

    def save_auto_backup_settings(self):
        freq = self.auto_backup_freq.currentData()
        self.service.set_setting("auto_backup_frequency", freq,
                                 "Frequence sauvegarde auto", "BACKUP")
        self.service.set_setting("max_backup_count", str(self.max_backup_count.value()),
                                 "Nombre max de sauvegardes", "BACKUP")
        self._update_next_backup_label()
        self._cleanup_old_backups()
        show_success(self, "Succes", "Configuration de sauvegarde enregistree.")

    def save_print_settings(self):
        self.service.set_setting("company_logo_path", self.logo_path_input.text(),
                                 "Chemin du logo", "PRINT")
        self.service.set_setting("pdf_footer_text", self.pdf_footer_input.text(),
                                 "Pied de page PDF", "PRINT")
        val = "True" if self.pdf_use_company_name.isChecked() else "False"
        self.service.set_setting("pdf_use_company_name", val,
                                 "Nom entreprise dans en-tete", "PRINT")
        show_success(self, "Succes", "Parametres d'impression enregistres.")

    def _update_next_backup_label(self):
        freq = self.auto_backup_freq.currentData()
        if freq == "none":
            self.next_backup_label.setText("Sauvegarde automatique desactivee")
            self.next_backup_label.setStyleSheet("color: #8b949e;")
        elif freq == "on_close":
            self.next_backup_label.setText("A la prochaine fermeture de l'application")
            self.next_backup_label.setStyleSheet("color: #238636; font-weight: bold;")
        elif freq == "daily":
            self.next_backup_label.setText("Demain a 00:00")
            self.next_backup_label.setStyleSheet("color: #238636; font-weight: bold;")
        elif freq == "weekly":
            self.next_backup_label.setText("Lundi prochain a 00:00")
            self.next_backup_label.setStyleSheet("color: #238636; font-weight: bold;")

    def _cleanup_old_backups(self):
        max_count = self.max_backup_count.value()
        backups = sorted(self.service.list_backups(), reverse=True)
        if len(backups) > max_count:
            for old_file in backups[max_count:]:
                try:
                    os.remove(os.path.join("backups", old_file))
                except OSError:
                    pass
            self.refresh_backup_list()

    def refresh_backup_list(self):
        self.backup_list.clear()
        backups = self.service.list_backups()
        sorted_backups = sorted(backups, reverse=True)
        self.backup_list.addItems(sorted_backups)
        self.backup_count_label.setText(f"{len(sorted_backups)} sauvegarde(s)")

    def create_backup(self):
        success, path = self.service.create_backup()
        if success:
            show_success(self, "Succes", f"Sauvegarde creee:\n{path}")
            self.refresh_backup_list()
        else:
            show_error(self, "Erreur", f"Echec de la sauvegarde: {path}")

    def reset_system(self):
        if not confirm_action(
            self, "ATTENTION - Action Destructrice",
            "Voulez-vous vraiment REINITIALISER toute la base de donnees ?\n\n"
            "CETTE ACTION EST IRREVERSIBLE ET SUPPRIMERA TOUT:\n"
            "  - Comptes et Tresorerie\n"
            "  - Transactions\n"
            "  - Clients et Dettes\n"
            "  - Licences et Conteneurs\n"
            "  - Devises et Mises a jour\n\n"
            "Une sauvegarde de securite sera creee automatiquement avant."
        ):
            return

        success, msg = self.service.reset_database()
        if success:
            show_success(self, "Reinitialisation", "Toutes les donnees ont ete effacees.")
            self.load_settings()
        else:
            show_error(self, "Erreur", msg)

    def clear_pycache(self):
        import shutil
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        count = 0
        errors = []

        # On parcourt l'arborescence pour trouver tous les dossiers __pycache__
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # On cherche les dossiers nommés exactement '__pycache__'
            for dirname in dirnames:
                if dirname == '__pycache__':
                    cache_path = os.path.join(dirpath, dirname)
                    try:
                        shutil.rmtree(cache_path)
                        count += 1
                    except Exception as e:
                        errors.append(f"{os.path.basename(dirpath)}: {str(e)}")

        if errors:
            show_error(self, "Erreur partielle", 
                       f"Certains caches n'ont pas pu être supprimés (accès refusé) :\n" + "\n".join(errors[:3]))
        else:
            show_success(self, "Succès", 
                         f"{count} dossier(s) de cache supprimés avec succès.\n"
                         "Pour appliquer les changements, redémarrez l'application.")
        self.refresh()

    def restore_backup(self):
        item = self.backup_list.currentItem()
        if not item:
            show_error(self, "Erreur", "Veuillez selectionner un fichier dans la liste.")
            return

        backup_name = item.text()
        if not confirm_action(
            self, "Restauration",
            f"Voulez-vous restaurer la base a partir de :\n\n{backup_name}\n\n"
            "L'etat actuel sera remplace. L'application va redemarrer."
        ):
            return

        success, msg = self.service.restore_database(backup_name)
        if success:
            QMessageBox.information(
                self, "Succes",
                f"{msg}\n\nL'application va se fermer pour appliquer les changements."
            )
            QApplication.instance().quit()
        else:
            show_error(self, "Erreur", msg)

    def refresh(self):
        self.load_settings()
