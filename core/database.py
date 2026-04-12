"""
Gestion de la connexion à la base de données SQLite avec SQLAlchemy
"""
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
import logging

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

# Configuration du logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

# Chemin de la base de données
DB_PATH = Path("shipping_company.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine SQLAlchemy
engine = None
SessionLocal = None


def init_database(db_path: str = None):
    """
    Initialise la connexion à la base de données.
    
    Args:
        db_path: Chemin personnalisé pour la base de données (optionnel)
    """
    global engine, SessionLocal
    
    if db_path:
        database_url = f"sqlite:///{db_path}"
    else:
        database_url = DATABASE_URL
    
    # Créer l'engine avec support des threads
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Mettre à True pour debug SQL
    )
    
    # Activer les contraintes de clés étrangères pour SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Créer la session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info(f"Base de données initialisée: {database_url}")


def create_tables():
    """
    Crée toutes les tables dans la base de données.
    """
    if engine is None:
        raise RuntimeError("La base de données n'est pas initialisée. Appelez init_database() d'abord.")
    
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées avec succès")


def sync_database_schema():
    """
    Synchronise le schéma de la base de données en ajoutant les colonnes manquantes.
    Évite l'erreur 'no such column' lors des mises à jour de modèles.
    """
    if engine is None:
        return

    inspector = inspect(engine)
    
    # On itère sur toutes les tables définir dans le Base.metadata
    for table_name, table in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue
            
        # Colonnes physiques dans la DB
        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # Colonnes définies dans le modèle
        for column in table.columns:
            if column.name not in existing_columns:
                # Ajout de la colonne manquante
                column_type = str(column.type.compile(engine.dialect))
                # Simplification du type pour SQLite
                if 'VARCHAR' in column_type or 'TEXT' in column_type:
                    column_type = 'TEXT'
                elif 'FLOAT' in column_type or 'DECIMAL' in column_type:
                    column_type = 'REAL'
                elif 'INTEGER' in column_type:
                    column_type = 'INTEGER'
                elif 'BOOLEAN' in column_type:
                    column_type = 'BOOLEAN'
                elif 'DATETIME' in column_type:
                    column_type = 'DATETIME'
                
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type}'))
                    logger.info(f"✓ Colonne ajoutée: {table_name}.{column.name} ({column_type})")
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de la colonne {table_name}.{column.name}: {e}")


def drop_tables():
    """
    Supprime toutes les tables de la base de données.
    ATTENTION: Cette opération est irréversible!
    """
    if engine is None:
        raise RuntimeError("La base de données n'est pas initialisée. Appelez init_database() d'abord.")
    
    Base.metadata.drop_all(bind=engine)
    logger.warning("Toutes les tables ont été supprimées")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager pour obtenir une session de base de données.
    
    Usage:
        with get_session() as session:
            # Utiliser la session
            session.query(...)
    
    Yields:
        Session SQLAlchemy
    """
    if SessionLocal is None:
        raise RuntimeError("La base de données n'est pas initialisée. Appelez init_database() d'abord.")
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erreur de base de données: {e}")
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """
    Obtient une nouvelle session de base de données.
    IMPORTANT: L'appelant est responsable de fermer la session.
    
    Returns:
        Session SQLAlchemy
    """
    if SessionLocal is None:
        raise RuntimeError("La base de données n'est pas initialisée. Appelez init_database() d'abord.")
    
    return SessionLocal()
