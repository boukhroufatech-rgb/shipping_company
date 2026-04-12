"""
Repositories pour le module Logistique
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.repositories import BaseRepository
from core.models import ImportLicense, ContainerFile, ContainerExpense


class LicenseRepository(BaseRepository[ImportLicense]):
    """Repository pour les licences d'importation"""
    
    def __init__(self):
        super().__init__(ImportLicense)

    def get_active_licenses(self, session: Session) -> List[ImportLicense]:
        """Récupère les licences actives avec solde positif (Purified Sort)"""
        # Cleanup: Use central order (oldest first)
        return session.query(ImportLicense).filter(
            and_(
                ImportLicense.is_active == True,
                ImportLicense.total_usd > ImportLicense.used_usd
            )
        ).order_by(ImportLicense.id).all()


class ContainerRepository(BaseRepository[ContainerFile]):
    """Repository pour les dossiers de conteneurs"""
    
    def __init__(self):
        super().__init__(ContainerFile)

    def get_by_license(self, session: Session, license_id: int) -> List[ContainerFile]:
        """Récupère les dossiers liés à une licence (Purified Sort)"""
        return session.query(ContainerFile).filter(
            and_(
                ContainerFile.license_id == license_id,
                ContainerFile.is_active == True
            )
        ).order_by(ContainerFile.id).all()


class ExpenseRepository(BaseRepository[ContainerExpense]):
    """Repository pour les dépenses de conteneurs"""
    
    def __init__(self):
        super().__init__(ContainerExpense)

    def get_by_container(self, session: Session, container_id: int) -> List[ContainerExpense]:
        """Récupère les dépenses liées à un conteneur (Purified Sort)"""
        return session.query(ContainerExpense).filter(
            and_(
                ContainerExpense.container_id == container_id,
                ContainerExpense.is_active == True
            )
        ).order_by(ContainerExpense.id).all()
