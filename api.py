from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import hashlib


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
BASE_PATH = '/api/v1.0'
db = SQLAlchemy(app)

MIN_LOGIN_LENGTH = 3
MAX_LOGIN_LENGTH = 50
MIN_PASSWORD_LENGTH = 5


def get_password_hash(password):
    hash = hashlib.sha256(password.encode())
    return hash.hexdigest()


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    
    def __repr__(self) -> str:
        return f'<user {self.id}>'

@app.route(f'{BASE_PATH}/register', methods=['POST'])
def register():
    data = request.get_json()
    required_keys = ['login', 'password']
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        return jsonify({
            'error': True, 
            'reason': f'missed follow keys: {", ".join(missing_keys)}'
        }), 400
        
    if len(data['login']) < MIN_LOGIN_LENGTH or len(data['login']) > MAX_LOGIN_LENGTH:
        return jsonify({
            'error': True, 
            'reason': f'Login length must be between {MIN_LOGIN_LENGTH} and {MAX_LOGIN_LENGTH} characters'
        }), 400

    if len(data['password']) < MIN_PASSWORD_LENGTH:
        return jsonify({
            'error': True, 
            'reason': f'Password length must be at least {MIN_PASSWORD_LENGTH}'
        }), 400
    
    try:
        hashed_password = get_password_hash(data['password'])
        user = Users(login=data['login'], password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'User registered successfully'
        }), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'error': True,
            'reason': 'User with this login already exists.'
        }), 400
    except:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to register user'
        }), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()