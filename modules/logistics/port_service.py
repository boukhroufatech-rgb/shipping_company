"""
Service pour la gestion des ports et destinations
"""
from typing import Tuple, List, Optional
from core.database import get_session
from core.models import Port
from core.repositories import BaseRepository

class PortRepository(BaseRepository):
    def __init__(self):
        super().__init__(Port)

class PortService:
    def __init__(self):
        self.repo = PortRepository()

    def get_all_ports(self, include_inactive: bool = False) -> List[dict]:
        """Récupère tous les ports"""
        with get_session() as session:
            query = session.query(self.repo.model)
            if not include_inactive:
                query = query.filter_by(is_active=True)
            ports = query.order_by(self.repo.model.name).all()
            return [{
                'id': p.id, 'name': p.name, 'country': p.country or '',
                'port_type': p.port_type or 'AUTRE', 'description': p.description or '',
                'is_active': p.is_active
            } for p in ports]

    def create_port(self, name: str, country: str = '', port_type: str = 'AUTRE', description: str = '') -> Tuple[bool, str, Optional[int]]:
        """Ajoute un nouveau port"""
        with get_session() as session:
            try:
                existing = session.query(Port).filter_by(name=name).first()
                if existing: return False, 'Ce port existe déjà', None
                p = Port(name=name, country=country, port_type=port_type, description=description)
                session.add(p)
                session.commit()
                return True, 'Port ajouté', p.id
            except Exception as e:
                return False, str(e), None

    def update_port(self, port_id: int, name: str, country: str, port_type: str, description: str) -> Tuple[bool, str]:
        """Met à jour un port"""
        with get_session() as session:
            try:
                p = session.query(Port).get(port_id)
                if not p: return False, 'Port introuvable'
                p.name = name
                p.country = country
                p.port_type = port_type
                p.description = description
                session.commit()
                return True, 'Port mis à jour'
            except Exception as e:
                return False, str(e)

    def delete_port(self, port_id: int) -> Tuple[bool, str]:
        """Archive un port (Soft Delete)"""
        with get_session() as session:
            try:
                p = session.query(Port).get(port_id)
                if not p: return False, 'Port introuvable'
                p.is_active = False
                session.commit()
                return True, 'Port archivé'
            except Exception as e:
                return False, str(e)

    def restore_port(self, port_id: int) -> Tuple[bool, str]:
        """Restaure un port archivé"""
        with get_session() as session:
            try:
                p = session.query(Port).get(port_id)
                if not p: return False, 'Port introuvable'
                p.is_active = True
                session.commit()
                return True, 'Port restauré'
            except Exception as e:
                return False, str(e)
