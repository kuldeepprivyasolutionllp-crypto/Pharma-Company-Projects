"""
Create the application database, schema, migration, and dummy account.

The script is safe to run repeatedly. It is used by Docker startup and can
also be run directly against a local PostgreSQL installation.
"""

import os
import time

import psycopg
from psycopg.sql import Identifier, SQL
from pwdlib import PasswordHash

DB_NAME = os.getenv("POSTGRES_DB", "amneal")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")


def connect(database: str):
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=database,
        autocommit=True,
    )


def ensure_database():
    for attempt in range(15):
        try:
            with connect("postgres") as connection, connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
                if cursor.fetchone() is None:
                    cursor.execute(SQL("CREATE DATABASE {}").format(Identifier(DB_NAME)))
            return
        except psycopg.OperationalError:
            if attempt == 14:
                raise
            time.sleep(2)


def ensure_schema():
    with connect(DB_NAME) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(150) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'operator',
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_login TIMESTAMPTZ
            )
            """ 
        )
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50)")
        cursor.execute("UPDATE users SET role = 'operator' WHERE role IS NULL OR role = ''")

        password_hash = PasswordHash.recommended()
        dummy_users = [
            ("demo@amneal.com", password_hash.hash("Demo@123"), "Demo Amneal User", "admin"),
            ("operator@amneal.com", password_hash.hash("Operator@123"), "Riya Patel", "operator"),
            ("supervisor@amneal.com", password_hash.hash("Supervisor@123"), "Amit Sharma", "supervisor"),
            ("manager@amneal.com", password_hash.hash("Manager@123"), "Nisha Verma", "manager"),
            ("admin@amneal.com", password_hash.hash("Admin@123"), "Sanjay Mehta", "admin"),
        ]

        for email, password, full_name, role in dummy_users:
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    full_name = EXCLUDED.full_name,
                    role = EXCLUDED.role,
                    is_active = TRUE
                """,
                (email, password, full_name, role),
            )


if __name__ == "__main__":
    ensure_database()
    ensure_schema()
    print(f"Database '{DB_NAME}' and users schema are ready.")
