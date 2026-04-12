<<<<<<< HEAD
import sqlite3
import os

db_path = "shipping_company.db"

def migrate():
    if not os.path.exists(db_path):
        print("Base de données introuvable.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Début de la migration...")

    # 1. Mise à jour de currency_suppliers
    try:
        cursor.execute("ALTER TABLE currency_suppliers ADD COLUMN currency_id INTEGER REFERENCES currencies(id)")
        print("- Colonne 'currency_id' ajoutée à 'currency_suppliers'")
    except sqlite3.OperationalError:
        print("- Colonne 'currency_id' existe déjà dans 'currency_suppliers'")

    # 2. Mise à jour de container_files
    container_columns = [
        ("shipping_supplier_id", "INTEGER REFERENCES currency_suppliers(id)"),
        ("bill_number", "VARCHAR(100)"),
        ("products_type", "VARCHAR(200)"),
        ("discharge_port", "VARCHAR(100)"),
        ("shipping_date", "DATETIME"),
        ("expected_arrival_date", "DATETIME")
    ]

    for col_name, col_type in container_columns:
        try:
            cursor.execute(f"ALTER TABLE container_files ADD COLUMN {col_name} {col_type}")
            print(f"- Colonne '{col_name}' ajoutée à 'container_files'")
        except sqlite3.OperationalError:
            print(f"- Colonne '{col_name}' existe déjà dans 'container_files'")

    conn.commit()
    conn.close()
    print("Migration terminée avec succès.")

    # Migration supplémentaire: Ajouter colonne 'consumed' à currency_purchases
    print("\nMigration LOTs...")
    conn2 = sqlite3.connect(db_path)
    cursor2 = conn2.cursor()
    try:
        cursor2.execute("ALTER TABLE currency_purchases ADD COLUMN consumed FLOAT DEFAULT 0.0")
        print("- Colonne 'consumed' ajoutée à 'currency_purchases'")
        conn2.commit()
    except sqlite3.OperationalError:
        print("- Colonne 'consumed' existe déjà dans 'currency_purchases'")
    conn2.close()

    # Migration supplémentaire: Ajouter colonnes à expenses
    print("\nMigration Frais Indirects...")
    conn3 = sqlite3.connect(db_path)
    cursor3 = conn3.cursor()
    try:
        cursor3.execute("ALTER TABLE expenses ADD COLUMN commission FLOAT DEFAULT 0.0")
        print("- Colonne 'commission' ajoutée à 'expenses'")
    except sqlite3.OperationalError:
        print("- Colonne 'commission' existe déjà dans 'expenses'")
    try:
        cursor3.execute("ALTER TABLE expenses ADD COLUMN lot_id INTEGER REFERENCES currency_purchases(id)")
        print("- Colonne 'lot_id' ajoutée à 'expenses'")
    except sqlite3.OperationalError:
        print("- Colonne 'lot_id' existe déjà dans 'expenses'")
    conn3.commit()
    conn3.close()

    # Migration supplémentaire: Ajouter table Ports
    print("\nMigration Ports...")
    conn4 = sqlite3.connect(db_path)
    cursor4 = conn4.cursor()
    try:
        cursor4.execute("""
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                country VARCHAR(100),
                port_type VARCHAR(50) DEFAULT 'AUTRE',
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        print("- Table 'ports' créée ou existe déjà.")
    except Exception as e:
        print(f"- Erreur table ports: {e}")
    conn4.commit()
    conn4.close()

    # Migration supplémentaire: Ajouter tables ContainerType et Transitaire
    print("\nMigration ContainerTypes & Transitaires...")
    conn5 = sqlite3.connect(db_path)
    cursor5 = conn5.cursor()
    try:
        cursor5.execute("""
            CREATE TABLE IF NOT EXISTS container_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(50) NOT NULL UNIQUE,
                capacity_cbm FLOAT DEFAULT 0.0,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        cursor5.execute("""
            CREATE TABLE IF NOT EXISTS transitaires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                contact VARCHAR(200),
                phone VARCHAR(50),
                email VARCHAR(100),
                nif_rc VARCHAR(100),
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        print("- Tables 'container_types' et 'transitaires' créées.")
    except Exception as e:
        print(f"- Erreur migration: {e}")
    conn5.commit()
    conn5.close()

if __name__ == "__main__":
    migrate()
=======
import sqlite3
import os

db_path = "shipping_company.db"

def migrate():
    if not os.path.exists(db_path):
        print("Base de données introuvable.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Début de la migration...")

    # 1. Mise à jour de currency_suppliers
    try:
        cursor.execute("ALTER TABLE currency_suppliers ADD COLUMN currency_id INTEGER REFERENCES currencies(id)")
        print("- Colonne 'currency_id' ajoutée à 'currency_suppliers'")
    except sqlite3.OperationalError:
        print("- Colonne 'currency_id' existe déjà dans 'currency_suppliers'")

    # 2. Mise à jour de container_files
    container_columns = [
        ("shipping_supplier_id", "INTEGER REFERENCES currency_suppliers(id)"),
        ("bill_number", "VARCHAR(100)"),
        ("products_type", "VARCHAR(200)"),
        ("discharge_port", "VARCHAR(100)"),
        ("shipping_date", "DATETIME"),
        ("expected_arrival_date", "DATETIME")
    ]

    for col_name, col_type in container_columns:
        try:
            cursor.execute(f"ALTER TABLE container_files ADD COLUMN {col_name} {col_type}")
            print(f"- Colonne '{col_name}' ajoutée à 'container_files'")
        except sqlite3.OperationalError:
            print(f"- Colonne '{col_name}' existe déjà dans 'container_files'")

    conn.commit()
    conn.close()
    print("Migration terminée avec succès.")

    # Migration supplémentaire: Ajouter colonne 'consumed' à currency_purchases
    print("\nMigration LOTs...")
    conn2 = sqlite3.connect(db_path)
    cursor2 = conn2.cursor()
    try:
        cursor2.execute("ALTER TABLE currency_purchases ADD COLUMN consumed FLOAT DEFAULT 0.0")
        print("- Colonne 'consumed' ajoutée à 'currency_purchases'")
        conn2.commit()
    except sqlite3.OperationalError:
        print("- Colonne 'consumed' existe déjà dans 'currency_purchases'")
    conn2.close()

    # Migration supplémentaire: Ajouter colonnes à expenses
    print("\nMigration Frais Indirects...")
    conn3 = sqlite3.connect(db_path)
    cursor3 = conn3.cursor()
    try:
        cursor3.execute("ALTER TABLE expenses ADD COLUMN commission FLOAT DEFAULT 0.0")
        print("- Colonne 'commission' ajoutée à 'expenses'")
    except sqlite3.OperationalError:
        print("- Colonne 'commission' existe déjà dans 'expenses'")
    try:
        cursor3.execute("ALTER TABLE expenses ADD COLUMN lot_id INTEGER REFERENCES currency_purchases(id)")
        print("- Colonne 'lot_id' ajoutée à 'expenses'")
    except sqlite3.OperationalError:
        print("- Colonne 'lot_id' existe déjà dans 'expenses'")
    conn3.commit()
    conn3.close()

    # Migration supplémentaire: Ajouter table Ports
    print("\nMigration Ports...")
    conn4 = sqlite3.connect(db_path)
    cursor4 = conn4.cursor()
    try:
        cursor4.execute("""
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                country VARCHAR(100),
                port_type VARCHAR(50) DEFAULT 'AUTRE',
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        print("- Table 'ports' créée ou existe déjà.")
    except Exception as e:
        print(f"- Erreur table ports: {e}")
    conn4.commit()
    conn4.close()

if __name__ == "__main__":
    migrate()
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
