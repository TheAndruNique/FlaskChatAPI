from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from config import BASE_PATH, MAX_LOGIN_LENGTH, MIN_LOGIN_LENGTH,  MIN_PASSWORD_LENGTH, TOKEN_LIFETIME
from models import Users
import time
import jwt
from helper import get_password_hash, check_required_keys
from app import app, db


auth = Blueprint('auth', __name__)


@auth.route(f'{BASE_PATH}/login', methods=['POST'])
@check_required_keys(['login', 'password'])
def authentication():
    data = request.get_json()

    user = Users.query.filter_by(login=data['login']).first()
    
    if user and user.password == get_password_hash(data['password']):
        time_exp = time.time() + TOKEN_LIFETIME
        token = jwt.encode({'user_id': user.id, 'exp': time_exp}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({
            'success': True,
            'token': token,
            'exp': time_exp
        }), 200
    else:
        return jsonify({
            'success': False,
            'reason': 'Unauthorized'
        }), 401

@auth.route(f'{BASE_PATH}/register', methods=['POST'])
@check_required_keys(['login', 'password'])
def register():
    data = request.get_json()
        
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