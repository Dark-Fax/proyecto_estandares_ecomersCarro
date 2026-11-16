from app import create_app, db
from app.seed import seed

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed()  # admin (admin / Admin1234) + catálogo inicial
    app.run(debug=True)
