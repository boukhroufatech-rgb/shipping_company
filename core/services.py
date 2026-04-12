"""
Couche de services - Logique métier
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from .database import get_session
from utils.validators import validate_amount, validate_required_field


class BaseService:
    """
    Service de base avec logique métier commune.
    """
    
    def __init__(self, repository):
        """
        Initialise le service avec son repository.
        
        Args:
            repository: Instance du repository
        """
        self.repository = repository
    
    def validate_operation(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Valide une opération.
        
        Args:
            **kwargs: Paramètres de l'opération
            
        Returns:
            Tuple (est_valide, message_erreur)
        """
        # À implémenter dans les classes dérivées
        return True, None
    
    def get_by_id(self, id: int):
        """
        Récupère une entité par son ID.
        
        Args:
            id: ID de l'entité
            
        Returns:
            Entité ou None
        """
        with get_session() as session:
            return self.repository.get_by_id(session, id)
    
    def get_all(self, skip: int = 0, limit: int = 100):
        """
        Récupère toutes les entités.
        
        Args:
            skip: Nombre d'entités à sauter
            limit: Nombre maximum d'entités
            
        Returns:
            Liste des entités
        """
        with get_session() as session:
            return self.repository.get_all(session, skip, limit)
    
    def delete(self, id: int) -> Tuple[bool, Optional[str]]:
        """
        Supprime une entité.
        
        Args:
            id: ID de l'entité
            
        Returns:
            Tuple (succès, message_erreur)
        """
        try:
            with get_session() as session:
                success = self.repository.delete(session, id)
                if success:
                    return True, None
                else:
                    return False, "Élément introuvable"
        except Exception as e:
            return False, str(e)
