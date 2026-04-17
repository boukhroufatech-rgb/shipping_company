"""
Vues pour le module Paramètres
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFormLayout, QGroupBox,
    QMessageBox, QListWidget, QFileDialog, QCheckBox,
    QTabWidget, QScrollArea, QComboBox,
    QSpinBox, QColorDialog, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import os

from components.dialogs import show_error, show_success, confirm_action
from modules.settings.service import SettingsService
from core.themes import THEMES, get_theme_qss, get_active_colors
from PyQt6.QtWidgets import QApplication


class SettingsView(QWidget):
    """Vue principale des paramètres"""

    def __init__(self):
        super().__init__()
        self.service = SettingsService()
        self._setup_ui()
        self.load_settings()

    def _create_save_button(self, text: str, callback) -> QPushButton:
        """Bouton de sauvegarde unifié - ألوان الثيم النشط"""
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

    def _danger_button(self, text: str, callback) -> QPushButton:
        """زر الإجراءات الخطرة (أحمر - دلالي وليس ثيماً)"""
        btn = QPushButton(text)
        btn.setStyleSheet(
            "padding: 10px 20px; font-weight: bold; "
            "background-color: #c0392b; color: white; border-radius: 4px;"
        )
        btn.clicked.connect(callback)
        return btn

    def _neutral_button(self, text: str, callback) -> QPushButton:
        """زر الإجراءات المحايدة"""
        c = get_active_colors()
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 20px; font-weight: bold;
                background-color: {c['bg_secondary']}; color: {c['text_main']};
                border: 1px solid {c['border']}; border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {c['bg_tertiary']}; }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_info = QWidget()
        self._setup_info_tab()
        self.tabs.addTab(self.tab_info, "Institution")

        self.tab_rules = QWidget()
        self._setup_rules_tab()
        self.tabs.addTab(self.tab_rules, "Règles de Gestion")

        self.tab_interface = QWidget()
        self._setup_interface_tab()
        self.tabs.addTab(self.tab_interface, "Interface")

        self.tab_auto_backup = QWidget()
        self._setup_auto_backup_tab()
        self.tabs.addTab(self.tab_auto_backup, "Sauvegarde Auto")

        self.tab_print = QWidget()
        self._setup_print_tab()
        self.tabs.addTab(self.tab_print, "Impression & Export")

        self.tab_db = QWidget()
        self._setup_db_tab()
        self.tabs.addTab(self.tab_db, "Base de Données")

        self.tab_theme = QWidget()
        self._setup_theme_tab()
        self.tabs.addTab(self.tab_theme, "Thème")

    # =========================================================================
    # TAB 1 - INSTITUTION
    # =========================================================================

    def _setup_info_tab(self):
        layout = QVBoxLayout(self.tab_info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(30, 20, 30, 20)

        cols_widget = QWidget()
        cols_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(40)
        cols_layout.setContentsMargins(30, 0, 30, 0)

        def make_input():
            w = QLineEdit()
            w.setMaximumWidth(500)
            return w

        # Left column
        group_left = QGroupBox("Informations Générales")
        form_left = QFormLayout(group_left)
        form_left.setSpacing(10)
        form_left.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_left.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

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
        form_left.addRow("Tél:", self.inp_tel)
        form_left.addRow("Fixe:", self.inp_fixe)
        form_left.addRow("Fax:", self.inp_fax)
        form_left.addRow("Email:", self.inp_email)
        form_left.addRow("Site Web:", self.inp_site_web)
        form_left.addRow("Activité:", self.inp_activite)
        cols_layout.addWidget(group_left, 1)

        # Right column
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

        container_layout.addWidget(cols_widget, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_company_info))
        container_layout.addLayout(btn_layout)

        scroll.setWidget(container)

    # =========================================================================
    # TAB 2 - RÈGLES DE GESTION
    # =========================================================================

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

        cols_widget = QWidget()
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(30)
        cols_layout.setContentsMargins(0, 0, 0, 0)

        def make_input():
            w = QLineEdit()
            w.setMaximumWidth(350)
            return w

        # Left - Trésorerie & Risques
        group_balance = QGroupBox("Trésorerie & Risques")
        vbox_balance = QVBoxLayout(group_balance)

        desc_balance = QLabel("Contrôle l'autorisation des opérations à découvert (Solde Négatif).")
        desc_balance.setWordWrap(True)
        vbox_balance.addWidget(desc_balance)

        self.allow_negative_treasury = QCheckBox("Autoriser le solde négatif en Trésorerie (DA)")
        self.allow_negative_treasury.setToolTip(
            "Si active, les débits seront autorisés même si le solde est insuffisant."
        )
        vbox_balance.addWidget(self.allow_negative_treasury)

        self.allow_negative_currency = QCheckBox("Autoriser le solde négatif en Devises")
        self.allow_negative_currency.setToolTip(
            "Si active, les paiements en devise seront autorisés même si le solde est insuffisant."
        )
        vbox_balance.addWidget(self.allow_negative_currency)
        vbox_balance.addStretch()
        cols_layout.addWidget(group_balance, 1)

        # Right - Facturation & Numérotation
        group_billing = QGroupBox("Facturation & Numérotation")
        form_billing = QFormLayout(group_billing)
        form_billing.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_billing.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        self.auto_invoice_number = QCheckBox("Numérotation automatique des factures")
        self.auto_invoice_number.setChecked(True)
        form_billing.addRow("", self.auto_invoice_number)

        self.invoice_prefix = make_input()
        self.invoice_prefix.setText("FAC")
        form_billing.addRow("Préfixe Facture:", self.invoice_prefix)
        cols_layout.addWidget(group_billing, 1)

        container_layout.addWidget(cols_widget)
        container_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_rules_settings))
        container_layout.addLayout(btn_layout)

        scroll.setWidget(container)

    # =========================================================================
    # TAB 3 - INTERFACE
    # =========================================================================

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

        cols_widget = QWidget()
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(30)

        def make_combo():
            w = QComboBox()
            w.setMaximumWidth(350)
            return w

        # Left - Formats
        group_formats = QGroupBox("Formats des Nombres")
        form_formats = QFormLayout(group_formats)
        form_formats.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.amount_format_combo = make_combo()
        self.amount_format_combo.addItem("Espace (1 000.00) - Français", "space")
        self.amount_format_combo.addItem("Point (1.000,00) - Windows", "dot")
        form_formats.addRow("Format des montants:", self.amount_format_combo)

        self.rows_per_page = make_combo()
        self.rows_per_page.addItems(["20", "50", "100"])
        form_formats.addRow("Lignes par page:", self.rows_per_page)
        cols_layout.addWidget(group_formats, 1)

        # Right - Apparence & Système
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)

        group_colors = QGroupBox("Couleurs des Soldes")
        vbox_colors = QVBoxLayout(group_colors)

        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Positif:"))
        self.color_positive_btn = QPushButton("#238636")
        self.color_positive_btn.setFixedWidth(120)
        self.color_positive_btn.clicked.connect(lambda: self._pick_color("positive"))
        pos_layout.addWidget(self.color_positive_btn)
        pos_layout.addStretch()
        vbox_colors.addLayout(pos_layout)

        neg_layout = QHBoxLayout()
        neg_layout.addWidget(QLabel("Négatif:"))
        self.color_negative_btn = QPushButton("#f85149")
        self.color_negative_btn.setFixedWidth(120)
        self.color_negative_btn.clicked.connect(lambda: self._pick_color("negative"))
        neg_layout.addWidget(self.color_negative_btn)
        neg_layout.addStretch()
        vbox_colors.addLayout(neg_layout)

        right_layout.addWidget(group_colors)

        group_sys = QGroupBox("Paramètres Système")
        form_sys = QFormLayout(group_sys)
        form_sys.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.dashboard_recent_limit = make_combo()
        self.dashboard_recent_limit.addItems(["5", "10", "20", "50"])
        form_sys.addRow("Dernières opérations:", self.dashboard_recent_limit)

        self.window_mode_combo = make_combo()
        self.window_mode_combo.addItem("Normal", 1)
        self.window_mode_combo.addItem("Agrandie (Maximized)", 2)
        self.window_mode_combo.addItem("Plein écran", 3)
        form_sys.addRow("Mode fenêtre:", self.window_mode_combo)

        right_layout.addWidget(group_sys)
        right_layout.addStretch()
        cols_layout.addWidget(right_widget, 1)

        container_layout.addWidget(cols_widget)
        container_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_interface_settings))
        container_layout.addLayout(btn_layout)

        scroll.setWidget(container)

    def _pick_color(self, color_type):
        btn = self.color_positive_btn if color_type == "positive" else self.color_negative_btn
        color = QColorDialog.getColor(QColor(btn.text()), self, "Choisir une couleur")
        if color.isValid():
            hex_color = color.name()
            btn.setText(hex_color)
            btn.setStyleSheet(
                f"background-color: {hex_color}; color: white; padding: 8px; border-radius: 4px;"
            )

    # =========================================================================
    # TAB 4 - SAUVEGARDE AUTO
    # =========================================================================

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

        cols_widget = QWidget()
        cols_layout = QHBoxLayout(cols_widget)
        cols_layout.setSpacing(30)

        def make_combo():
            w = QComboBox()
            w.setMaximumWidth(300)
            return w

        def make_spin():
            w = QSpinBox()
            w.setMaximumWidth(300)
            w.setRange(1, 100)
            return w

        # Left - Configuration
        group_config = QGroupBox("Configuration de la Sauvegarde")
        form_config = QFormLayout(group_config)
        form_config.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.auto_backup_freq = make_combo()
        self.auto_backup_freq.addItem("Désactivée", "none")
        self.auto_backup_freq.addItem("À la fermeture", "on_close")
        self.auto_backup_freq.addItem("Quotidienne", "daily")
        self.auto_backup_freq.addItem("Hebdomadaire", "weekly")
        form_config.addRow("Fréquence:", self.auto_backup_freq)

        self.max_backup_count = make_spin()
        self.max_backup_count.setValue(10)
        self.max_backup_count.setSuffix(" fichiers")
        form_config.addRow("Nombre max:", self.max_backup_count)

        self.next_backup_label = QLabel("En attente...")
        form_config.addRow("Prochaine sauvegarde:", self.next_backup_label)
        cols_layout.addWidget(group_config, 1)

        # Right - Maintenance
        group_maint = QGroupBox("Maintenance")
        vbox_maint = QVBoxLayout(group_maint)

        btn_cache = self._neutral_button("🗑️ Vider le Cache Python", self.clear_pycache)
        btn_cache.setMaximumWidth(280)
        vbox_maint.addWidget(btn_cache, alignment=Qt.AlignmentFlag.AlignLeft)

        hint_cache = QLabel("Nettoie les fichiers temporaires pour appliquer les mises à jour.")
        hint_cache.setWordWrap(True)
        vbox_maint.addWidget(hint_cache)

        vbox_maint.addSpacing(15)

        btn_reset = self._danger_button("⚠️ Réinitialiser la Base", self.reset_system)
        btn_reset.setMaximumWidth(280)
        vbox_maint.addWidget(btn_reset, alignment=Qt.AlignmentFlag.AlignLeft)

        hint_reset = QLabel("Supprime toutes les données. Une sauvegarde est créée avant.")
        hint_reset.setWordWrap(True)
        vbox_maint.addWidget(hint_reset)
        vbox_maint.addStretch()
        cols_layout.addWidget(group_maint, 1)

        container_layout.addWidget(cols_widget)
        container_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_save_button("Enregistrer", self.save_auto_backup_settings))
        container_layout.addLayout(btn_layout)

        scroll.setWidget(container)

    # =========================================================================
    # TAB 5 - IMPRESSION & EXPORT
    # =========================================================================

    def _setup_print_tab(self):
        layout = QVBoxLayout(self.tab_print)

        group = QGroupBox("Configuration de l'Impression et de l'Export")
        form = QFormLayout(group)

        logo_layout = QHBoxLayout()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setPlaceholderText("Aucun logo sélectionné...")
        logo_layout.addWidget(self.logo_path_input)

        btn_browse = self._neutral_button("Parcourir", self._browse_logo)
        logo_layout.addWidget(btn_browse)
        form.addRow("Logo de l'entreprise:", logo_layout)

        logo_hint = QLabel("Formats acceptés: PNG, JPG, SVG. Taille recommandée: 200x200px max.")
        form.addRow("", logo_hint)

        self.pdf_footer_input = QLineEdit()
        self.pdf_footer_input.setPlaceholderText("Ex: Société XYZ - Registre de Commerce: 12345")
        form.addRow("Pied de page PDF:", self.pdf_footer_input)

        self.pdf_use_company_name = QCheckBox("Inclure le nom de l'entreprise dans l'en-tête des rapports")
        self.pdf_use_company_name.setChecked(True)
        form.addRow("", self.pdf_use_company_name)

        form.addRow("", self._create_save_button("Enregistrer", self.save_print_settings))

        layout.addWidget(group)
        layout.addStretch()

    def _browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un logo", "",
            "Images (*.png *.jpg *.jpeg *.svg);;Tous les fichiers (*)"
        )
        if file_path:
            self.logo_path_input.setText(file_path)

    # =========================================================================
    # TAB 6 - BASE DE DONNÉES
    # =========================================================================

    def _setup_db_tab(self):
        layout = QVBoxLayout(self.tab_db)
        layout.setSpacing(15)

        # Sauvegardes
        backup_group = QGroupBox("Gestion des Sauvegardes")
        backup_layout = QVBoxLayout(backup_group)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Dossier:"))
        self.backup_path_label = QLabel(os.path.abspath("backups"))
        path_layout.addWidget(self.backup_path_label)
        path_layout.addStretch()

        self.backup_count_label = QLabel("")
        path_layout.addWidget(self.backup_count_label)
        backup_layout.addLayout(path_layout)

        self.backup_list = QListWidget()
        self.backup_list.setMinimumHeight(180)
        backup_layout.addWidget(self.backup_list)

        btn_layout = QHBoxLayout()
        self.btn_backup = self._create_save_button("Nouvelle Sauvegarde", self.create_backup)
        self.btn_restore = self._neutral_button("Restaurer la sélection", self.restore_backup)
        btn_layout.addWidget(self.btn_backup)
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addStretch()
        backup_layout.addLayout(btn_layout)

        layout.addWidget(backup_group)

        # Maintenance
        maint_group = QGroupBox("Maintenance")
        maint_layout = QVBoxLayout(maint_group)

        desc = QLabel(
            "La réinitialisation supprime toutes les données (comptes, transactions, clients, "
            "licences, conteneurs, dettes) et restaure les paramètres par défaut. "
            "Une sauvegarde automatique est créée avant chaque opération destructive."
        )
        desc.setWordWrap(True)
        maint_layout.addWidget(desc)

        btn_clear = self._neutral_button("🗑️ Vider le Cache Python (__pycache__)", self.clear_pycache)
        maint_layout.addWidget(btn_clear)

        btn_reset = self._danger_button("Réinitialiser toute la base de données", self.reset_system)
        maint_layout.addWidget(btn_reset)

        layout.addWidget(maint_group)
        layout.addStretch()

    # =========================================================================
    # TAB 7 - THÈME
    # =========================================================================

    def _setup_theme_tab(self):
        layout = QVBoxLayout(self.tab_theme)

        group = QGroupBox("Apparence Visuelle")
        vbox = QVBoxLayout(group)

        current_theme_id = self.service.get_setting("active_theme", "emerald")
        theme_data = THEMES.get(current_theme_id, THEMES["emerald"])

        self.theme_info_lbl = QLabel(f"Thème Actuel : {theme_data['name']}")
        self.theme_info_lbl.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        vbox.addWidget(self.theme_info_lbl)

        vbox.addSpacing(10)
        vbox.addWidget(QLabel("Choisir un Style :"))

        self.theme_selector = QComboBox()
        for tid in sorted(THEMES.keys(), key=lambda x: x != "emerald"):
            self.theme_selector.addItem(THEMES[tid]["name"], tid)

        idx = self.theme_selector.findData(current_theme_id)
        if idx >= 0:
            self.theme_selector.setCurrentIndex(idx)
        vbox.addWidget(self.theme_selector)

        btn_apply = self._create_save_button("Appliquer le Thème", self._apply_theme)
        vbox.addSpacing(10)
        vbox.addWidget(btn_apply)

        layout.addWidget(group)
        layout.addStretch()

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _apply_theme(self):
        theme_id = self.theme_selector.currentData()
        self.service.set_setting("active_theme", theme_id)
        QApplication.instance().setStyleSheet(get_theme_qss(theme_id))
        self.theme_info_lbl.setText(f"Thème Actuel : {THEMES[theme_id]['name']}")
        show_success(self, "Thème Appliqué", f"Le style '{THEMES[theme_id]['name']}' a été activé.")

    def save_theme_settings(self):
        self._apply_theme()

    def _load_company_info(self):
        fields = [
            ("nom_magasin", self.inp_nom_magasin), ("adresse", self.inp_adresse),
            ("ville", self.inp_ville), ("tel", self.inp_tel), ("fixe", self.inp_fixe),
            ("fax", self.inp_fax), ("email", self.inp_email), ("site_web", self.inp_site_web),
            ("activite", self.inp_activite), ("rc", self.inp_rc), ("nif", self.inp_nif),
            ("nis", self.inp_nis), ("rib", self.inp_rib), ("nom_banque", self.inp_nom_banque),
            ("article", self.inp_article), ("capital", self.inp_capital),
            ("ice", self.inp_ice), ("cnss", self.inp_cnss), ("taxe_pro", self.inp_taxe_pro),
        ]
        for key, widget in fields:
            widget.setText(self.service.get_setting(key, ""))

    def save_company_info(self):
        mappings = [
            ("nom_magasin", self.inp_nom_magasin, "Nom du magasin"),
            ("adresse", self.inp_adresse, "Adresse"),
            ("ville", self.inp_ville, "Ville"),
            ("tel", self.inp_tel, "Téléphone"),
            ("fixe", self.inp_fixe, "Téléphone fixe"),
            ("fax", self.inp_fax, "Fax"),
            ("email", self.inp_email, "Email"),
            ("site_web", self.inp_site_web, "Site web"),
            ("activite", self.inp_activite, "Activité"),
            ("rc", self.inp_rc, "Registre de Commerce"),
            ("nif", self.inp_nif, "NIF"),
            ("nis", self.inp_nis, "NIS"),
            ("rib", self.inp_rib, "RIB"),
            ("nom_banque", self.inp_nom_banque, "Nom banque"),
            ("article", self.inp_article, "Article"),
            ("capital", self.inp_capital, "Capital"),
            ("ice", self.inp_ice, "ICE"),
            ("cnss", self.inp_cnss, "CNSS"),
            ("taxe_pro", self.inp_taxe_pro, "Taxe professionnelle"),
        ]
        for key, widget, label in mappings:
            self.service.set_setting(key, widget.text(), label, "COMPANY")
        show_success(self, "Succès", "Informations de l'entreprise mises à jour.")

    def save_rules_settings(self):
        self.service.set_setting(
            "allow_negative_treasury",
            "True" if self.allow_negative_treasury.isChecked() else "False",
            "Autoriser solde négatif en Trésorerie", "RULES"
        )
        self.service.set_setting(
            "allow_negative_currency",
            "True" if self.allow_negative_currency.isChecked() else "False",
            "Autoriser solde négatif en Devise", "RULES"
        )
        self.service.set_setting(
            "auto_invoice_number",
            "True" if self.auto_invoice_number.isChecked() else "False",
            "Numérotation auto factures", "RULES"
        )
        self.service.set_setting("invoice_prefix", self.invoice_prefix.text(), "Préfixe facturation", "RULES")
        show_success(self, "Succès", "Règles de gestion mises à jour.")

    def save_interface_settings(self):
        self.service.set_setting("rows_per_page", self.rows_per_page.currentText(), "Lignes par page", "INTERFACE")
        self.service.set_setting("color_positive_balance", self.color_positive_btn.text(), "Couleur solde positif", "INTERFACE")
        self.service.set_setting("color_negative_balance", self.color_negative_btn.text(), "Couleur solde négatif", "INTERFACE")
        self.service.set_setting("color_search_highlight", "#ffe000", "Couleur surbrillance recherche", "INTERFACE")

        amount_format = self.amount_format_combo.currentData()
        self.service.set_setting("amount_format", amount_format, "Format des montants", "INTERFACE")
        from utils.formatters import set_amount_format
        set_amount_format(amount_format)
        if hasattr(self.parent(), 'refresh_all'):
            self.parent().refresh_all()

        window_mode = self.window_mode_combo.currentData()
        self.service.set_setting("window_mode", str(window_mode), "Mode fenêtre", "INTERFACE")
        self.service.set_setting("dashboard_recent_limit", self.dashboard_recent_limit.currentText(), "Limite dashboard", "DASHBOARD")

        show_success(self, "Succès", "Paramètres d'interface enregistrés.")

    def save_auto_backup_settings(self):
        freq = self.auto_backup_freq.currentData()
        self.service.set_setting("auto_backup_frequency", freq, "Fréquence sauvegarde auto", "BACKUP")
        self.service.set_setting("max_backup_count", str(self.max_backup_count.value()), "Nombre max sauvegardes", "BACKUP")
        self._update_next_backup_label()
        self._cleanup_old_backups()
        show_success(self, "Succès", "Configuration de sauvegarde enregistrée.")

    def save_print_settings(self):
        self.service.set_setting("company_logo_path", self.logo_path_input.text(), "Chemin du logo", "PRINT")
        self.service.set_setting("pdf_footer_text", self.pdf_footer_input.text(), "Pied de page PDF", "PRINT")
        self.service.set_setting(
            "pdf_use_company_name",
            "True" if self.pdf_use_company_name.isChecked() else "False",
            "Nom entreprise dans en-tête", "PRINT"
        )
        show_success(self, "Succès", "Paramètres d'impression enregistrés.")

    def _update_next_backup_label(self):
        freq = self.auto_backup_freq.currentData()
        messages = {
            "none": "Sauvegarde automatique désactivée",
            "on_close": "À la prochaine fermeture de l'application",
            "daily": "Demain à 00:00",
            "weekly": "Lundi prochain à 00:00",
        }
        self.next_backup_label.setText(messages.get(freq, ""))

    def _cleanup_old_backups(self):
        max_count = self.max_backup_count.value()
        backups = sorted(self.service.list_backups(), reverse=True)
        for old_file in backups[max_count:]:
            try:
                os.remove(os.path.join("backups", old_file))
            except OSError:
                pass
        if len(backups) > max_count:
            self.refresh_backup_list()

    def refresh_backup_list(self):
        self.backup_list.clear()
        backups = sorted(self.service.list_backups(), reverse=True)
        self.backup_list.addItems(backups)
        self.backup_count_label.setText(f"{len(backups)} sauvegarde(s)")

    def create_backup(self):
        success, path = self.service.create_backup()
        if success:
            show_success(self, "Succès", f"Sauvegarde créée:\n{path}")
            self.refresh_backup_list()
        else:
            show_error(self, "Erreur", f"Échec de la sauvegarde: {path}")

    def restore_backup(self):
        item = self.backup_list.currentItem()
        if not item:
            show_error(self, "Erreur", "Veuillez sélectionner un fichier dans la liste.")
            return
        if not confirm_action(
            self, "Restauration",
            f"Voulez-vous restaurer la base à partir de:\n\n{item.text()}\n\n"
            "L'état actuel sera remplacé. L'application va redémarrer."
        ):
            return
        success, msg = self.service.restore_database(item.text())
        if success:
            QMessageBox.information(self, "Succès", f"{msg}\n\nL'application va se fermer.")
            QApplication.instance().quit()
        else:
            show_error(self, "Erreur", msg)

    def reset_system(self):
        if not confirm_action(
            self, "ATTENTION - Action Destructrice",
            "Voulez-vous vraiment RÉINITIALISER toute la base de données?\n\n"
            "CETTE ACTION EST IRRÉVERSIBLE ET SUPPRIMERA TOUT:\n"
            "  - Comptes et Trésorerie\n  - Transactions\n  - Clients et Dettes\n"
            "  - Licences et Conteneurs\n  - Devises\n\n"
            "Une sauvegarde de sécurité sera créée automatiquement avant."
        ):
            return
        success, msg = self.service.reset_database()
        if success:
            show_success(self, "Réinitialisation", "Toutes les données ont été effacées.")
            self.load_settings()
        else:
            show_error(self, "Erreur", msg)

    def clear_pycache(self):
        import shutil
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        count = 0
        errors = []
        for dirpath, dirnames, _ in os.walk(root_dir):
            for dirname in dirnames:
                if dirname == '__pycache__':
                    try:
                        shutil.rmtree(os.path.join(dirpath, dirname))
                        count += 1
                    except Exception as e:
                        errors.append(f"{os.path.basename(dirpath)}: {str(e)}")
        if errors:
            show_error(self, "Erreur partielle",
                       "Certains caches n'ont pas pu être supprimés:\n" + "\n".join(errors[:3]))
        else:
            show_success(self, "Succès",
                         f"{count} dossier(s) de cache supprimés.\nRedémarrez l'application.")

    def load_settings(self):
        self._load_company_info()

        self.allow_negative_treasury.setChecked(
            self.service.get_setting("allow_negative_treasury", "False") == "True"
        )
        self.allow_negative_currency.setChecked(
            self.service.get_setting("allow_negative_currency", "False") == "True"
        )
        self.auto_invoice_number.setChecked(
            self.service.get_setting("auto_invoice_number", "True") == "True"
        )
        self.invoice_prefix.setText(self.service.get_setting("invoice_prefix", "FAC"))

        rpp = self.service.get_setting("rows_per_page", "20")
        idx = self.rows_per_page.findText(rpp)
        if idx >= 0:
            self.rows_per_page.setCurrentIndex(idx)

        window_mode = self.service.get_setting("window_mode", "2")
        idx = self.window_mode_combo.findData(int(window_mode) if window_mode.isdigit() else 2)
        if idx >= 0:
            self.window_mode_combo.setCurrentIndex(idx)

        color_pos = self.service.get_setting("color_positive_balance", "#238636")
        self.color_positive_btn.setText(color_pos)
        self.color_positive_btn.setStyleSheet(
            f"background-color: {color_pos}; color: white; padding: 8px; border-radius: 4px;"
        )

        color_neg = self.service.get_setting("color_negative_balance", "#f85149")
        self.color_negative_btn.setText(color_neg)
        self.color_negative_btn.setStyleSheet(
            f"background-color: {color_neg}; color: white; padding: 8px; border-radius: 4px;"
        )

        amount_fmt = self.service.get_setting("amount_format", "dot")
        idx = self.amount_format_combo.findData(amount_fmt)
        if idx >= 0:
            self.amount_format_combo.setCurrentIndex(idx)

        dash_limit = self.service.get_setting("dashboard_recent_limit", "10")
        idx = self.dashboard_recent_limit.findText(dash_limit)
        if idx >= 0:
            self.dashboard_recent_limit.setCurrentIndex(idx)

        freq = self.service.get_setting("auto_backup_frequency", "on_close")
        idx = self.auto_backup_freq.findData(freq)
        if idx >= 0:
            self.auto_backup_freq.setCurrentIndex(idx)

        self.max_backup_count.setValue(int(self.service.get_setting("max_backup_count", "10")))
        self._update_next_backup_label()

        self.logo_path_input.setText(self.service.get_setting("company_logo_path", ""))
        self.pdf_footer_input.setText(self.service.get_setting("pdf_footer_text", ""))
        self.pdf_use_company_name.setChecked(
            self.service.get_setting("pdf_use_company_name", "True") == "True"
        )

        self.refresh_backup_list()

    def refresh(self):
        self.load_settings()
