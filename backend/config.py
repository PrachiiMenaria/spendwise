import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        database="wardrobe_db",
        user="postgres",
        password="wardrobe123",
        host="localhost",
        port="5432"
    )
    return conn