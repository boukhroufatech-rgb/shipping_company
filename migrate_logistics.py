import sqlite3
import os

db_path = "shipping_company.db"

def migrate():
    if not os.path.exists(db_path):
        print("Base de données introuvable.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Début de la migration Logistique...")

    columns = [
        ("invoice_number", "VARCHAR(100)"),
        ("cbm", "FLOAT DEFAULT 0"),
        ("cartons", "INTEGER DEFAULT 0"),
        ("transitaire", "VARCHAR(200)")
    ]

    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE container_files ADD COLUMN {col_name} {col_type}")
            print(f"- Colonne '{col_name}' ajoutée à 'container_files'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"- Colonne '{col_name}' existe déjà")
            else:
                print(f"Erreur ajout '{col_name}': {e}")

    conn.commit()
    conn.close()
    print("Migration Logistique terminée.")

if __name__ == "__main__":
    migrate()
