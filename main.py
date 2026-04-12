import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout,
    QWidget, QStatusBar, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QLocale
from PyQt6.QtGui import QAction

# Configuration de l'environnement
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import init_database, create_tables, sync_database_schema
from core.themes import get_theme_qss, THEMES
from modules.settings.service import SettingsService
from utils.icon_manager import IconManager
from utils.logger import logger, log_error, log_info
from components.error_dialog import show_error

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_service = SettingsService()
        self.active_theme = self.settings_service.get_setting("active_theme", "emerald")
        self.accent_color = THEMES.get(self.active_theme, THEMES["emerald"])["colors"]["accent"]
        
<<<<<<< HEAD
        # [UNIFIED] 2026-04-08 - Initialize amount format from settings
        from utils.formatters import set_amount_format
        from utils.constants import AMOUNT_FORMAT_DEFAULT
        amount_fmt = self.settings_service.get_setting("amount_format", AMOUNT_FORMAT_DEFAULT)
        set_amount_format(amount_fmt)
        
=======
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        self.setWindowTitle("Shipping Company - Système de Gestion Import-Export")
        self.setMinimumSize(1200, 800)
        
        # État de rafraîchissement (doit être défini avant _init_ui)
        self._is_refreshing = False
        
        # Initialisation de l'UI
        self._init_ui()
        self._create_menu()
        self._create_status_bar()
        
        # État de rafraîchissement
        self._is_refreshing = False

    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Création des onglets principaux
        self.tabs = QTabWidget()
<<<<<<< HEAD
        self.tabs.currentChanged.connect(self._on_tab_changed) # Lazy Loading Trigger
        self.layout.addWidget(self.tabs)

=======
        self.layout.addWidget(self.tabs)
        
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        # 🎨 ACCENT COLOR FOR ICONS
        color = self.accent_color

        # 1. Dashboard
        from modules.dashboard.views import DashboardView
        self.dashboard_view = DashboardView()
<<<<<<< HEAD
        self.dashboard_view.loaded = False # Will be loaded immediately as it's tab 0
=======
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        self.tabs.addTab(self.dashboard_view, "Tableau de Bord")

        # 2. Trésorerie
        from modules.treasury.views import TreasuryView
        self.treasury_view = TreasuryView()
<<<<<<< HEAD
        self.treasury_view.loaded = False
=======
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        self.treasury_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.treasury_view, "Trésorerie")

        # 3. Devises
        from modules.currency.views import CurrencyView
        self.currency_view = CurrencyView()
<<<<<<< HEAD
        self.currency_view.loaded = False
=======
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        self.currency_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.currency_view, "Devises")

        # 4. Clients
        from modules.customers.views import CustomersView
        self.customers_view = CustomersView()
<<<<<<< HEAD
        self.customers_view.loaded = False
        self.customers_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.customers_view, "Clients")

        # 5. Licences
        from modules.licenses.views import LicensesView
        self.licenses_view = LicensesView()
        self.licenses_view.loaded = False
        self.licenses_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.licenses_view, "Licences")

        # 6. Logistique
        from modules.logistics.views import LogisticsView
        self.logistics_view = LogisticsView()
        self.logistics_view.loaded = False
        self.logistics_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.logistics_view, "Logistique")

        # 7. Dettes
        from modules.external_debt.views import ExternalDebtView
        self.debt_view = ExternalDebtView()
        self.debt_view.loaded = False
        self.debt_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.debt_view, "Dettes")

        # 8. Associés
        from modules.partners.views import PartnersView
        self.partners_view = PartnersView(self.treasury_view.service)
        self.partners_view.loaded = False
        self.partners_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.partners_view, "Associés")

        # 9. Entrepôts (Warehouse)
        from modules.warehouse.views import WarehouseView
        self.warehouse_view = WarehouseView()
        self.warehouse_view.loaded = False
=======
        self.customers_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.customers_view, "Clients")
        
        # 5. Licences
        from modules.licenses.views import LicensesView
        self.licenses_view = LicensesView()
        self.licenses_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.licenses_view, "Licences")
        
        # 6. Logistique
        from modules.logistics.views import LogisticsView
        self.logistics_view = LogisticsView()
        self.logistics_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.logistics_view, "Logistique")
        
        # 7. Dettes
        from modules.external_debt.views import ExternalDebtView
        self.debt_view = ExternalDebtView()
        self.debt_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.debt_view, "Dettes")
        
        # 8. Associés
        from modules.partners.views import PartnersView
        self.partners_view = PartnersView(self.treasury_view.service)
        self.partners_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.partners_view, "Associés")
        
        # 9. Entrepôts (Warehouse)
        from modules.warehouse.views import WarehouseView
        self.warehouse_view = WarehouseView()
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        self.warehouse_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.warehouse_view, "Entrepôts")

        # 10. Catalog Management (TEST)
        from modules.catalog_management.views import CatalogManagementView
        self.catalog_view = CatalogManagementView()
<<<<<<< HEAD
        self.catalog_view.loaded = False
=======
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        self.catalog_view.dataChanged.connect(self.refresh_all)
        self.tabs.addTab(self.catalog_view, "Catalog Management")

        # 11. Paramètres
        from modules.settings.views import SettingsView
        self.settings_view = SettingsView()
        self.tabs.addTab(self.settings_view, "Paramètres")

    def _create_menu(self):
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        exit_action = QAction("Quitter", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Action
        action_menu = menubar.addMenu("Actions")
        
        refresh_action = QAction("Rafraîchir tout", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        action_menu.addAction(refresh_action)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Système prêt")
        
        # Widget Horloge
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_status_time)
        self.timer.start(1000)
        
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)

    def _update_status_time(self):
        current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        self.time_label.setText(current_time)

<<<<<<< HEAD
    def _on_tab_changed(self, index):
        """Lazy Loading: Charger les données uniquement lors de la première visite"""
        widget = self.tabs.widget(index)
        if widget and hasattr(widget, 'loaded') and not widget.loaded:
            # Utiliser QTimer pour ne pas bloquer le rendu de l'UI
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, lambda: self._load_tab_data(widget))

    def _load_tab_data(self, widget):
        try:
            if hasattr(widget, 'load_data'):
                widget.load_data()
            elif hasattr(widget, 'refresh'):
                widget.refresh()
            widget.loaded = True
        except Exception as e:
            # En cas d'erreur, on marque quand même comme chargé pour éviter une boucle
            widget.loaded = True
            print(f"Erreur chargement lazy: {e}")

=======
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
    def refresh_all(self):
        """Rafraîchit les données de tous les onglets de manière sécurisée"""
        if self._is_refreshing or not hasattr(self, 'status_bar'):
            return

        self._is_refreshing = True
        try:
            self.status_bar.showMessage("🔄 Rafraîchissement des données...")
            log_info("Démarrage du rafraîchissement général", context="MainApp.refresh_all")

            # Liste des vues à rafraîchir avec leur nom pour le logging
            views = [
                ("Dashboard", self.dashboard_view),
                ("Trésorerie", self.treasury_view),
                ("Devises", self.currency_view),
                ("Clients", self.customers_view),
                ("Licences", self.licenses_view),
                ("Logistique", self.logistics_view),
                ("Dettes", self.debt_view),
                ("Associés", self.partners_view),
                ("Entrepôts", self.warehouse_view)
            ]

            # Rafraîchir chaque vue individuellement avec protection
            for view_name, view in views:
                try:
                    view.refresh()
                    log_info(f"✓ {view_name} rafraîchi avec succès", context="MainApp.refresh_all")
                except Exception as e:
                    log_error(e, context=f"MainApp.refresh_all.{view_name}")
                    # On continue avec les autres vues même si une échoue

            self.status_bar.showMessage("✅ Données à jour", 3000)
            log_info("Rafraîchissement général terminé avec succès", context="MainApp.refresh_all")
            
        except Exception as e:
            log_error(e, context="MainApp.refresh_all")
            show_error(self, "Une erreur est survenue lors du rafraîchissement des données", exception=e)
            self.status_bar.showMessage("❌ Erreur lors du rafraîchissement", 5000)
        finally:
            self._is_refreshing = False

    def closeEvent(self, event):
<<<<<<< HEAD
        """Confirmation dialog + auto backup on close"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirmation - Confirmer",
            "Êtes-vous sûr de vouloir fermer le programme?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            event.ignore()
            return
        
        # Auto backup if configured
=======
        """Sauvegarde automatique a la fermeture si configuree"""
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        try:
            freq = self.settings_service.get_setting("auto_backup_frequency", "none")
            if freq == "on_close":
                from modules.settings.service import SettingsService
                settings_svc = SettingsService()
                success, path = settings_svc.create_backup()
                if success:
                    log_info(f"Sauvegarde automatique creee: {path}", context="MainApp.closeEvent")
        except Exception as e:
            log_error(e, context="MainApp.closeEvent.auto_backup")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 1. Initialisation de la base de données
    import core.models  # Import pour enregistrer les modèles auprès de Base.metadata
    
    try:
        log_info("Initialisation de la base de données...", context="MainApp.__main__")
        init_database()
        create_tables()
        sync_database_schema()
        log_info("Base de données initialisée avec succès", context="MainApp.__main__")
    except Exception as e:
        log_error(e, context="MainApp.__main__.init_database")
        print(f"❌ Erreur critique lors de l'initialisation de la base de données: {e}")
        sys.exit(1)

    # Validation et insertion des données de base du système (Devises, Comptes)
    try:
        from core.init_data import initialize_system_data
        log_info("Initialisation des données système...", context="MainApp.__main__")
        initialize_system_data()
        log_info("Données système initialisées avec succès", context="MainApp.__main__")
    except Exception as e:
        log_error(e, context="MainApp.__main__.initialize_system_data")
        print(f"⚠️ Erreur lors de l'initialisation des données système: {e}")

    # 1.5. Sauvegarde automatique au demarrage (si configuree)
    try:
        from modules.settings.service import SettingsService as _SS
        _ss = _SS()
        _freq = _ss.get_setting("auto_backup_frequency", "none")
        if _freq in ("daily", "weekly"):
            _ss.perform_daily_backup()
            log_info(f"Sauvegarde automatique ({_freq}) effectuee", context="MainApp.__main__")
    except Exception as e:
        log_error(e, context="MainApp.__main__.auto_backup")

    # 2. Chargement du thème préféré (Emerald par défaut)
    try:
        settings = SettingsService()
        active_theme = settings.get_setting("active_theme", "emerald")
        log_info(f"Chargement du thème: {active_theme}", context="MainApp.__main__")
        app.setStyleSheet(get_theme_qss(active_theme))
    except Exception as e:
        log_error(e, context="MainApp.__main__.load_theme")
        print(f"⚠️ Erreur lors du chargement du thème: {e}. Utilisation du thème Emerald par défaut.")
        app.setStyleSheet(get_theme_qss("emerald"))

    # 3. Lancement
    try:
        log_info("Lancement de l'application...", context="MainApp.__main__")
        main_window = MainApp()
        
        # [CUSTOM] 2026-04-03 - Window mode (1=normal, 2=maximized, 3=fullscreen)
        from modules.settings.service import SettingsService
        settings = SettingsService()
<<<<<<< HEAD
        window_mode = settings.get_int_setting("window_mode", 2)  # [UNIFIED] 2026-04-08 - Default to Maximized
=======
        window_mode = settings.get_int_setting("window_mode", 1)
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        
        if window_mode == 2:
            main_window.showMaximized()
        elif window_mode == 3:
            main_window.showFullScreen()
        else:
            main_window.show()
<<<<<<< HEAD

        # 🚀 Lazy Load: Charger uniquement le premier onglet (Dashboard) au démarrage
        # Les autres onglets se chargeront uniquement lorsqu'on clique dessus
        main_window._load_tab_data(main_window.dashboard_view)

=======
        
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
        log_info("Application lancée avec succès", context="MainApp.__main__")
    except Exception as e:
        log_error(e, context="MainApp.__main__.launch")
        show_error(None, "Une erreur critique est survenue au lancement de l'application", exception=e)
        sys.exit(1)
    
    sys.exit(app.exec())
