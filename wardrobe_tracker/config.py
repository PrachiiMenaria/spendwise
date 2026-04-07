import os

class Config:
    # PostgreSQL connection string
    # Format: postgresql://username:password@host:port/database_name
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/wardrobe_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
