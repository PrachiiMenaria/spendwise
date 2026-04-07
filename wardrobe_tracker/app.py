from app import create_app, db

app = create_app()


@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully.")


@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok", "message": "Wardrobe Tracker API is running"}, 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Auto-create tables on first run
    app.run(debug=True, port=5000)
