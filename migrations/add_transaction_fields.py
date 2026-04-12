"""
Migration: Ajout des nouveaux champs dans la table transactions
Date: 2026-04-01
Description: Ajout des colonnes source, source_id, payment_method, category, status, created_by
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from pathlib import Path

def migrate():
    """Exécute la migration pour ajouter les nouveaux champs dans transactions"""
    
    # Connexion directe à la base de données
    DB_PATH = Path(__file__).parent.parent / "shipping_company.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    migrations = [
        # 1. Ajout du champ source
        "ALTER TABLE transactions ADD COLUMN source VARCHAR(50) DEFAULT 'CAISSE' NOT NULL",
        
        # 2. Ajout du champ source_id
        "ALTER TABLE transactions ADD COLUMN source_id INTEGER",
        
        # 3. Ajout du champ payment_method
        "ALTER TABLE transactions ADD COLUMN payment_method VARCHAR(50) DEFAULT 'ESPECES'",
        
        # 4. Ajout du champ category
        "ALTER TABLE transactions ADD COLUMN category VARCHAR(50) DEFAULT 'DIVERS'",
        
        # 5. Ajout du champ status
        "ALTER TABLE transactions ADD COLUMN status VARCHAR(20) DEFAULT 'VALIDEE'",
        
        # 6. Ajout du champ created_by
        "ALTER TABLE transactions ADD COLUMN created_by VARCHAR(100) DEFAULT 'system'",
    ]
    
    print("[MIGRATION] Demarrage de la migration: Ajout des nouveaux champs dans transactions...")
    
    with engine.connect() as conn:
        for i, sql in enumerate(migrations, 1):
            try:
                print(f"  [{i}/{len(migrations)}] Execution: {sql[:50]}...")
                conn.execute(text(sql))
                conn.commit()
                print(f"  [OK] Succes")
            except Exception as e:
                error_msg = str(e)
                if "duplicate column" in error_msg.lower() or "already exists" in error_msg.lower():
                    print(f"  [INFO] Colonne deja existante, ignoree")
                else:
                    print(f"  [WARN] Erreur: {error_msg[:100]}")
    
    print("[OK] Migration terminee avec succes!")


if __name__ == "__main__":
    migrate()
