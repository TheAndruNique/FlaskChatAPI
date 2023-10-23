from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
BASE_PATH = '/api/v1.0'
db = SQLAlchemy(app)


def get_password_hash(password):
    hash = hashlib.sha256(password.encode())
    return str(hash)


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
            'error': 'true', 
            'reason': f'missed follow keys: {", ".join(missing_keys)}'
        }), 400
    try:
        hashed_password = get_password_hash(data['password'])
        user = Users(login=data['login'], password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'success': 'true',
            'message': 'User registered successfully'
        })
    except:
        db.session.rollback()
        return jsonify({
            'success': 'false',
            'message': 'Failed to register user'
        })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()