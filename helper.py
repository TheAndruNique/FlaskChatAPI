from functools import wraps
from flask import request, jsonify
import hashlib
from models import Users
from app import app
import jwt


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.get_json().get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'reason': 'No token provided'
            }), 401
        try:    
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
            current_user = Users.query.get(data['user_id'])
        except:
            return jsonify({
                'success': False,
                'reason': 'Invalid token'
            }), 401
            
        return f(current_user, *args, **kwargs)
    return wrapper

def get_password_hash(password):
    hash = hashlib.sha256(password.encode())
    return hash.hexdigest()
