"""
db.py — Database connection helper
wardrobe-analysis-project/backend/db.py
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url, sslmode="require")
    # Fallback for local development
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "wardrobe_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "wardrobe123"),
        port=int(os.getenv("DB_PORT", 5432))
    )