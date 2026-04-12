"""
Pattern Repository - Couche d'accès aux données
"""
from typing import List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import get_session, Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Repository de base avec opérations CRUD génériques.
    """
    
    def __init__(self, model: Type[T]):
        """
        Initialise le repository avec le modèle.
        
        Args:
            model: Classe du modèle SQLAlchemy
        """
        self.model = model
    
    def get_session(self):
        """
        الوصول الموحد لجلسة قاعدة البيانات (Purification Helper)
        """
        return get_session()
    
    def create(self, session: Session, **kwargs) -> T:
        """
        Crée une nouvelle entité.
        """
        instance = self.model(**kwargs)
        session.add(instance)
        session.flush()
        session.refresh(instance)
        return instance
    
    def get_by_id(self, session: Session, id: int) -> Optional[T]:
        """
        Récupère une entité par son ID.
        """
        return session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, session: Session, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[T]:
        """
        يسترجع جميع الكيانات بترتيب تصاعدي (الأقدم أولاً) آلياً
        """
        query = session.query(self.model)
        
        if not include_inactive and hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)
        
        # Nettoyage centralisé: le plus ancien toujours en haut (ordre ascendant)
        if hasattr(self.model, 'id'):
            query = query.order_by(self.model.id)
            
        return query.offset(skip).limit(limit).all()
    
    def get_active(self, session: Session, skip: int = 0, limit: int = 100) -> List[T]:
        """يسترجع العناصر النشطة فقط بترتيب تصاعدي"""
        return self.get_all(session, skip, limit, include_inactive=False)
    
    def get_inactive(self, session: Session, skip: int = 0, limit: int = 100) -> List[T]:
        """يسترجع العناصر غير النشطة فقط بترتيب تصاعدي"""
        if not hasattr(self.model, 'is_active'):
            return []
            
        query = session.query(self.model).filter(self.model.is_active == False)
        
        if hasattr(self.model, 'id'):
            query = query.order_by(self.model.id)
            
        return query.offset(skip).limit(limit).all()
    
    def update(self, session: Session, id: int, **kwargs) -> Optional[T]:
        """
        Met à jour une entité.
        """
        instance = self.get_by_id(session, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            session.flush()
            session.refresh(instance)
        return instance
    
    def delete(self, session: Session, id: int) -> bool:
        """
        Supprime une entité (hard delete).
        """
        instance = self.get_by_id(session, id)
        if instance:
            session.delete(instance)
            session.flush()
            return True
        return False
    
    def soft_delete(self, session: Session, id: int) -> bool:
        """
        حذف ناعم: يضع is_active = False
        """
        if not hasattr(self.model, 'is_active'):
            return False
        
        instance = self.get_by_id(session, id)
        if instance:
            instance.is_active = False
            session.flush()
            return True
        return False

    def restore(self, session: Session, id: int) -> bool:
        """
        استعادة: يضع is_active = True
        """
        if not hasattr(self.model, 'is_active'):
            return False
            
        instance = self.get_by_id(session, id)
        if instance:
            instance.is_active = True
            session.flush()
            return True
        return False
    
    def count(self, session: Session, include_inactive: bool = False) -> int:
        """
        يحسب عدد الكيانات.
        """
        query = session.query(self.model)
        if not include_inactive and hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)
        return query.count()
    
    def get_recent(self, session: Session, limit: int = 10, include_inactive: bool = False) -> List[T]:
        """
        يسترجع الكيانات الأقدم/الأحدث بترتيب تصاعدي من المصدر
        """
        query = session.query(self.model)
        
        if not include_inactive and hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)
            
        if hasattr(self.model, 'id'):
            query = query.order_by(self.model.id)
            
        return query.limit(limit).all()
