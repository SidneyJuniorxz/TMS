"""
Migration script v2 — Adds new columns to deliveries and vehicles tables.
Run this ONCE before deploying the new backend version.

Usage:
    cd /home/reploid/Projetos/TMS/logistics_macro_planner
    .venv/bin/python3 scripts/migrate_v2.py
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logistics.db")


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"[INFO] Connected to {DB_PATH}")

    # --- DELIVERIES TABLE MIGRATION ---
    delivery_new_columns = [
        ("origem_cidade", "TEXT DEFAULT ''"),
        ("origem_cep", "TEXT DEFAULT ''"),
        ("destino_cidade", "TEXT DEFAULT ''"),
        ("destino_cep", "TEXT DEFAULT ''"),
        ("peso_kg", "REAL DEFAULT 0"),
        ("comprimento_cm", "REAL DEFAULT 0"),
        ("largura_cm", "REAL DEFAULT 0"),
        ("altura_cm", "REAL DEFAULT 0"),
        ("volume_m3", "REAL DEFAULT 0"),
        ("descricao", "TEXT DEFAULT ''"),
        ("prioridade", "TEXT DEFAULT 'media'"),
        ("observacao", "TEXT DEFAULT ''"),
    ]

    print("\n[PHASE 1] Migrating 'deliveries' table...")
    for col_name, col_def in delivery_new_columns:
        if not column_exists(cursor, "deliveries", col_name):
            sql = f"ALTER TABLE deliveries ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            print(f"  ✅ Added column: {col_name}")
        else:
            print(f"  ⏭️  Column already exists: {col_name}")

    # Migrate old data: weight -> peso_kg, volume -> volume_m3
    print("\n[PHASE 2] Migrating legacy data (weight -> peso_kg, volume -> volume_m3)...")
    cursor.execute("""
        UPDATE deliveries
        SET peso_kg = COALESCE(weight, 0),
            volume_m3 = COALESCE(volume, 0)
        WHERE peso_kg = 0 AND weight IS NOT NULL AND weight > 0
    """)
    migrated_deliveries = cursor.rowcount
    print(f"  ✅ Migrated {migrated_deliveries} delivery records")

    # Try to resolve destino_cidade from city_id
    print("\n[PHASE 3] Resolving destino_cidade from city_id...")
    cursor.execute("""
        UPDATE deliveries
        SET destino_cidade = (SELECT name FROM cities WHERE cities.id = deliveries.city_id)
        WHERE city_id IS NOT NULL AND (destino_cidade IS NULL OR destino_cidade = '')
    """)
    resolved = cursor.rowcount
    print(f"  ✅ Resolved {resolved} city names")

    # --- VEHICLES TABLE MIGRATION ---
    vehicle_new_columns = [
        ("tipo", "TEXT DEFAULT 'Truck'"),
        ("ativo", "BOOLEAN DEFAULT 1"),
    ]

    print("\n[PHASE 4] Migrating 'vehicles' table...")
    for col_name, col_def in vehicle_new_columns:
        if not column_exists(cursor, "vehicles", col_name):
            sql = f"ALTER TABLE vehicles ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            print(f"  ✅ Added column: {col_name}")
        else:
            print(f"  ⏭️  Column already exists: {col_name}")

    conn.commit()
    conn.close()

    print("\n🎉 Migration completed successfully!")


if __name__ == "__main__":
    migrate()
