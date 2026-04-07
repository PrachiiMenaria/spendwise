import psycopg2

print("Starting database test...")

try:
    conn = psycopg2.connect(
        database="wardrobe_db",
        user="postgres",
        password="wardrobe123",
        host="localhost",
        port="5432"
    )

    print("Database connected successfully!")

    conn.close()

except Exception as e:
    print("Error:", e)

print("Script finished.")