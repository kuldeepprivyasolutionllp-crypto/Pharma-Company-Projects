from urllib.parse import urlparse

import psycopg
from pwdlib import PasswordHash
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def ensure_database_and_schema() -> None:
    parsed = urlparse(settings.database_url)
    db_name = parsed.path.lstrip("/") or "amneal"
    username = parsed.username or "postgres"
    password = parsed.password or "postgres"
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        with psycopg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            dbname="postgres",
            autocommit=True,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                if cursor.fetchone() is None:
                    cursor.execute(f'CREATE DATABASE "{db_name}"')

    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'operator'"))
        conn.execute(text("UPDATE users SET is_active = TRUE WHERE is_active IS NULL"))
        conn.execute(text("UPDATE users SET role = 'operator' WHERE role IS NULL OR role = ''"))

        seed_roles = [
            ("superuser", "Unrestricted system access", "All facilities"),
            ("admin", "Full system access", "All facilities"),
            ("manager", "Operations and reporting", "Assigned facilities"),
            ("supervisor", "Team and batch oversight", "Assigned department"),
            ("operator", "Daily production tasks", "Assigned line"),
        ]
        for name, description, scope in seed_roles:
            conn.execute(
                text(
                    "INSERT INTO roles (name, description, scope, is_active) VALUES (:name, :description, :scope, TRUE) "
                    "ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, scope = EXCLUDED.scope, is_active = TRUE"
                ),
                {"name": name, "description": description, "scope": scope},
            )

        seed_permissions = [
            ("dashboard", "Dashboard overview", "View operational KPIs"),
            ("inventory", "Inventory", "View and update stock"),
            ("production", "Production", "Manage production batches"),
            ("distribution", "Distribution", "Track shipments"),
            ("reports", "Reports", "Create and export reports"),
            ("users", "User management", "Manage accounts and roles"),
            ("users_read", "Read users", "View user accounts"),
            ("users_create", "Create users", "Add user accounts"),
            ("users_update", "Update users", "Edit user accounts"),
            ("users_delete", "Delete users", "Remove user accounts"),
            ("equipment_read", "Read equipment", "View pharma equipment"),
            ("equipment_create", "Create equipment", "Add pharma equipment"),
            ("equipment_update", "Update equipment", "Edit pharma equipment"),
            ("equipment_delete", "Delete equipment", "Remove pharma equipment"),
        ]
        for code, name, description in seed_permissions:
            conn.execute(
                text(
                    "INSERT INTO permissions (name, description) VALUES (:name, :description) "
                    "ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description"
                ),
                {"name": code, "description": description},
            )
        conn.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r CROSS JOIN permissions p
            WHERE r.name IN ('superuser', 'admin')
            ON CONFLICT (role_id, permission_id) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r JOIN permissions p ON p.name IN ('dashboard', 'inventory', 'production', 'distribution', 'reports')
            WHERE r.name = 'manager'
            ON CONFLICT (role_id, permission_id) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r JOIN permissions p ON p.name IN ('dashboard', 'production')
            WHERE r.name = 'supervisor'
            ON CONFLICT (role_id, permission_id) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r JOIN permissions p ON p.name IN ('dashboard', 'production')
            WHERE r.name = 'operator'
            ON CONFLICT (role_id, permission_id) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r JOIN permissions p ON p.name IN
            ('users_read', 'users_create', 'users_update', 'users_delete', 'equipment_read', 'equipment_create', 'equipment_update', 'equipment_delete')
            WHERE r.name IN ('superuser', 'admin')
            ON CONFLICT (role_id, permission_id) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id FROM roles r JOIN permissions p ON p.name IN ('users_read', 'equipment_read', 'equipment_update')
            WHERE r.name = 'manager'
            ON CONFLICT (role_id, permission_id) DO NOTHING
        """))

        seed_equipment = [
            ("EQ-1001", "HPLC Analyzer", "Analytical", "QC Lab 1", "Operational", "2027-02-15"),
            ("EQ-1002", "Tablet Compression Machine", "Production", "Line A", "Operational", "2026-12-08"),
            ("EQ-1003", "Dissolution Tester", "Quality Control", "QC Lab 2", "Maintenance", "2026-11-20"),
            ("EQ-1004", "Stability Chamber", "Storage", "Stability Room", "Operational", "2027-01-30"),
            ("EQ-1005", "Automatic Filling Unit", "Packaging", "Line B", "Calibration due", "2026-10-12"),
        ]
        for asset_tag, name, category, location, status, calibration_due in seed_equipment:
            conn.execute(
                text(
                    "INSERT INTO equipment (asset_tag, name, category, location, status, calibration_due) "
                    "VALUES (:asset_tag, :name, :category, :location, :status, :calibration_due) "
                    "ON CONFLICT (asset_tag) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category, "
                    "location = EXCLUDED.location, status = EXCLUDED.status, calibration_due = EXCLUDED.calibration_due"
                ),
                {"asset_tag": asset_tag, "name": name, "category": category, "location": location, "status": status, "calibration_due": calibration_due},
            )

        password_hash = PasswordHash.recommended()
        dummy_users = [
            ("demo@amneal.com", password_hash.hash("Demo@123"), "Demo Amneal User", "admin"),
            ("superuser@amneal.com", password_hash.hash("Superuser@123"), "Amneal Superuser", "superuser"),
            ("operator@amneal.com", password_hash.hash("Operator@123"), "Riya Patel", "operator"),
            ("supervisor@amneal.com", password_hash.hash("Supervisor@123"), "Amit Sharma", "supervisor"),
            ("manager@amneal.com", password_hash.hash("Manager@123"), "Nisha Verma", "manager"),
            ("admin@amneal.com", password_hash.hash("Admin@123"), "Sanjay Mehta", "admin"),
        ]

        for email, hashed_password, full_name, role in dummy_users:
            conn.execute(
                text(
                    "INSERT INTO users (email, password_hash, full_name, role, is_active) VALUES (:email, :password_hash, :full_name, :role, :is_active) "
                    "ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash, full_name = EXCLUDED.full_name, role = EXCLUDED.role, is_active = TRUE"
                ),
                {
                    "email": email,
                    "password_hash": hashed_password,
                    "full_name": full_name,
                    "role": role,
                    "is_active": True,
                },
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
