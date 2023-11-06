from app import app, db
from app.config import PORT
from auth import auth_handler
from chat import chat_handler


app.register_blueprint(auth_handler)
app.register_blueprint(chat_handler)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=PORT)