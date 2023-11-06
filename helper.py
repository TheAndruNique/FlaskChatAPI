from functools import wraps
from flask import request, jsonify
import hashlib
from db import Users
from app import app
import jwt
from pydantic import ValidationError


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

def check_required_keys(required_keys: dict):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            
            missing_keys = []

            for key, expected_type in required_keys.items():
                if key not in data:
                    missing_keys.append(key)
                elif not isinstance(data[key], expected_type):
                    return jsonify({
                        'error': True,
                        'reason': f'Invalid data type for key {key}'
                    }), 400

            if missing_keys:
                return jsonify({
                    'error': True, 
                    'reason': f'missed follow keys: {", ".join(missing_keys)}'
                }), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_arguments(model):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = model(**request.get_json())
            except ValidationError as e:
                return jsonify({
                    'error': True,
                    'reason': 'Validation error',
                    'errors': e.errors()
                }), 400
            
            return f(data, *args, **kwargs)
        return wrapper
    return decorator

def get_password_hash(password):
    hash = hashlib.sha256(password.encode())
    return hash.hexdigest()
