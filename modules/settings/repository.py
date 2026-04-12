"""
Repository pour le module Paramètres
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from core.repositories import BaseRepository
from core.models import AppSetting

class SettingRepository(BaseRepository[AppSetting]):
    """Repository pour les réglages de l'application"""
    
    def __init__(self):
        super().__init__(AppSetting)
    
    def get_by_key(self, session: Session, key: str) -> Optional[AppSetting]:
        """Récupère un réglage par sa clé"""
        return session.query(AppSetting).filter(AppSetting.key == key).first()
    
    def get_by_category(self, session: Session, category: str) -> List[AppSetting]:
        """Récupère les réglages d'une catégorie"""
        return session.query(AppSetting).filter(AppSetting.category == category).all()

    def set_value(self, session: Session, key: str, value: str, 
                  description: str = None, category: str = None) -> AppSetting:
        """Définit ou met à jour la valeur d'un réglage"""
        setting = self.get_by_key(session, key)
        if setting:
            setting.value = value
            if description: setting.description = description
            if category: setting.category = category
        else:
            setting = AppSetting(
                key=key, 
                value=value, 
                description=description, 
                category=category
            )
            session.add(setting)
        
        session.flush()
        return setting
