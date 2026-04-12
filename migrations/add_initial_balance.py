"""
Migration: Ajout du champ initial_balance dans la table accounts
Date: 2026-04-07
Description: Ajout de la colonne initial_balance pour le solde initial des comptes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from pathlib import Path

def migrate():
    """Exécute la migration pour ajouter le champ initial_balance dans accounts"""
    
    DB_PATH = Path(__file__).parent.parent / "shipping_company.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    sql = "ALTER TABLE accounts ADD COLUMN initial_balance FLOAT DEFAULT 0.0 NOT NULL"
    
    print("[MIGRATION] Ajout du champ initial_balance dans la table accounts...")
    
    with engine.connect() as conn:
        try:
            conn.execute(text(sql))
            conn.commit()
            print("[OK] Champ initial_balance ajouté avec succès!")
        except Exception as e:
            error_msg = str(e)
            if "duplicate column" in error_msg.lower() or "already exists" in error_msg.lower():
                print("[INFO] Champ initial_balance déjà existant, ignoré")
            else:
                print(f"[WARN] Erreur: {error_msg}")
    
    print("[OK] Migration terminée!")


if __name__ == "__main__":
    migrate()