"""
Service pour le module Paramètres
"""
import os
import shutil
from datetime import datetime
from typing import List, Optional, Tuple
from pathlib import Path

from core.services import BaseService
from core.database import get_session, DB_PATH, drop_tables, create_tables
from core.init_data import initialize_system_data
from .repository import SettingRepository

class SettingsService(BaseService):
    """Service pour la gestion des réglages et de la maintenance"""
    
    def __init__(self):
        self.repo = SettingRepository()
        self.backup_dir = Path("backups")
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
    
    # ========================================================================
    # GESTION DES RÉGLAGES
    # ========================================================================
    
    def get_setting(self, key: str, default: str = "") -> str:
        """Récupère la valeur d'un réglage"""
        with get_session() as session:
            setting = self.repo.get_by_key(session, key)
            return setting.value if setting else default
            
    def get_int_setting(self, key: str, default: int = 0) -> int:
        """Récupère un réglage numérique"""
        val = self.get_setting(key, str(default))
        try:
            return int(val)
        except:
            return default
            
    def set_setting(self, key: str, value: str, 
                    description: str = None, category: str = None) -> bool:
        """Enregistre ou met à jour un réglage"""
        try:
            with get_session() as session:
                self.repo.set_value(session, key, str(value), description, category)
                return True
        except Exception:
            return False
            
    def get_all_settings(self) -> List:
        """Récupère tous les réglages"""
        with get_session() as session:
            return self.repo.get_all(session)

    # ========================================================================
    # MAINTENANCE DU SYSTÈME (BACKUP / RESET / RESTORE)
    # ========================================================================
    
    def create_backup(self, custom_name: str = None) -> Tuple[bool, str]:
        """
        Crée une copie de la base de données.
        Le nom par défaut inclut la date du jour.
        """
        try:
            if not DB_PATH.exists():
                return False, "Base de données source introuvable"
            
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = custom_name if custom_name else f"backup_{date_str}.db"
            dest_path = self.backup_dir / filename
            
            shutil.copy2(DB_PATH, dest_path)
            return True, str(dest_path)
        except Exception as e:
            return False, str(e)
            
    def perform_daily_backup(self) -> bool:
        """Crée un backup quotidien si non existant pour aujourd'hui"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"daily_backup_{date_str}.db"
        dest_path = self.backup_dir / filename
        
        if not dest_path.exists():
            success, _ = self.create_backup(filename)
            return success
        return True

    def reset_database(self) -> Tuple[bool, str]:
        """
        Vide complètement la base de données.
        Toutes les données seront perdues!
        """
        try:
            # 1. Faire un backup de sécurité avant
            self.create_backup(f"pre_reset_backup_{datetime.now().strftime('%H%M%S')}.db")
            
            # 2. Supprimer et recréer les tables
            drop_tables()
            create_tables()
            
            # 3. Ré-initialiser les données système (Devises, Comptes, etc.)
            initialize_system_data()
            
            return True, "Base de données réinitialisée avec succès."
        except Exception as e:
            return False, f"Erreur lors du reset: {str(e)}"

    def restore_database(self, backup_filename: str) -> Tuple[bool, str]:
        """Estaurer la base à partir d'un fichier backup"""
        try:
            src_path = self.backup_dir / backup_filename
            if not src_path.exists():
                return False, "Fichier backup introuvable"
            
            # 1. Backup de l'état actuel avant écrasement
            self.create_backup(f"before_restore_{datetime.now().strftime('%H%M%S')}.db")
            
            # 2. Remplacer le fichier actuel
            # Note: SQLite peut verrouiller le fichier si des sessions sont ouvertes
            # On utilise shutil.copy2
            shutil.copy2(src_path, DB_PATH)
            
            return True, "Base de données restaurée. Veuillez redémarrer l'application."
        except Exception as e:
            return False, f"Erreur lors de la restauration: {str(e)}"

    def list_backups(self) -> List[str]:
        """Liste les fichiers de backup disponibles"""
        if not self.backup_dir.exists():
            return []
        return [f.name for f in self.backup_dir.glob("*.db")]
