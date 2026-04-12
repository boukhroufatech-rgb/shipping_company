"""
Migration: Add sort_order and customer_id columns
"""
import sqlite3
import os

db_path = "shipping_company.db"

def upgrade():
    if not os.path.exists(db_path):
        print("Base de données introuvable.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migration: Ajout des colonnes...")

    # 1. Add sort_order to expense_types
    try:
        cursor.execute("ALTER TABLE expense_types ADD COLUMN sort_order INTEGER DEFAULT 0")
        conn.commit()
        print("- Colonne 'sort_order' ajoutée à 'expense_types'")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("- Colonne 'sort_order' existe déjà dans 'expense_types'")
        else:
            print(f"- Erreur: {e}")

    # 2. Add customer_id to expenses
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN customer_id INTEGER")
        conn.commit()
        print("- Colonne 'customer_id' ajoutée à 'expenses'")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("- Colonne 'customer_id' existe déjà dans 'expenses'")
        else:
            print(f"- Erreur: {e}")

    # 3. Insert default expense types if not exist
    from datetime import datetime
    now = datetime.now().isoformat()
    
    default_types = [
        (1, "Transport / Fret", "Frais de transport maritime ou terrestre"),
        (2, "TAXS", "Droits de douane et taxes (Dédouanement)"),
        (3, "SURISTARIE", "Frais de surestarie"),
        (4, "Magasinage", "Frais de stockage"),
        (5, "TransitAIRE", "Frais de transit"),
        (6, "Logistique / Port", "Frais de logistique portuaire"),
        (7, "Charges Globales", "Charges globales de l'entreprise"),
        (8, "Transport", "Transport local"),
        (9, "Timbre", "Timbre et frais administratifs"),
    ]
    
    for order, name, desc in default_types:
        cursor.execute("SELECT id FROM expense_types WHERE name = ?", (name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO expense_types (name, description, sort_order, created_at) VALUES (?, ?, ?, ?)", 
                          (name, desc, order, now))
            print(f"- Type '{name}' ajouté")
    
    conn.commit()
    print("- Vérification des types de dépenses terminée")

    conn.close()
    print("Migration terminée!")

def downgrade():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE expense_types DROP COLUMN sort_order")
        conn.commit()
    except:
        pass
    try:
        cursor.execute("ALTER TABLE expenses DROP COLUMN customer_id")
        conn.commit()
    except:
        pass
    conn.close()

if __name__ == "__main__":
    upgrade()