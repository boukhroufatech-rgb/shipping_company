"""Service pour la gestion des transitaires"""
from typing import Tuple, List, Optional
from core.database import get_session
from core.models import Transitaire
from core.repositories import BaseRepository

class TransitaireRepository(BaseRepository):
    def __init__(self):
        super().__init__(Transitaire)

class TransitaireService:
    def __init__(self):
        self.repo = TransitaireRepository()

    def get_all_transitaires(self, include_inactive: bool = False) -> List[dict]:
        with get_session() as session:
            query = session.query(self.repo.model)
            if not include_inactive:
                query = query.filter_by(is_active=True)
            items = query.order_by(self.repo.model.name).all()
            return [{
                'id': t.id, 'name': t.name, 'contact': t.contact or '', 'phone': t.phone or '',
                'email': t.email or '', 'nif_rc': t.nif_rc or '', 'description': t.description or '',
                'is_active': t.is_active
            } for t in items]

    def create_transitaire(self, name: str, contact: str = '', phone: str = '', email: str = '', nif_rc: str = '', description: str = '') -> Tuple[bool, str, Optional[int]]:
        with get_session() as session:
            try:
                t = Transitaire(name=name, contact=contact, phone=phone, email=email, nif_rc=nif_rc, description=description)
                session.add(t)
                session.commit()
                return True, 'Transitaire ajouté', t.id
            except Exception as e:
                return False, str(e), None

    def update_transitaire(self, t_id: int, name: str, contact: str, phone: str, email: str, nif_rc: str, description: str) -> Tuple[bool, str]:
        with get_session() as session:
            try:
                t = session.query(Transitaire).get(t_id)
                if not t: return False, 'Transitaire introuvable'
                t.name = name
                t.contact = contact
                t.phone = phone
                t.email = email
                t.nif_rc = nif_rc
                t.description = description
                session.commit()
                return True, 'Transitaire mis à jour'
            except Exception as e:
                return False, str(e)

    def delete_transitaire(self, t_id: int) -> Tuple[bool, str]:
        with get_session() as session:
            try:
                t = session.query(Transitaire).get(t_id)
                if not t: return False, 'Transitaire introuvable'
                t.is_active = False
                session.commit()
                return True, 'Transitaire archivé'
            except Exception as e:
                return False, str(e)

    def restore_transitaire(self, t_id: int) -> Tuple[bool, str]:
        with get_session() as session:
            try:
                t = session.query(Transitaire).get(t_id)
                if not t: return False, 'Transitaire introuvable'
                t.is_active = True
                session.commit()
                return True, 'Transitaire restauré'
            except Exception as e:
                return False, str(e)
