from app import app, db
from auth import auth
from chattings import chattings


app.register_blueprint(auth)
app.register_blueprint(chattings)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()