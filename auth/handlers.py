from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError
from app.config import BASE_PATH, TOKEN_LIFETIME
from db import Users
import time
import jwt
from helper import get_password_hash, validate_arguments
from app import app, db
from request_models import AuthenticationModel


auth_handler = Blueprint('auth', __name__)


@auth_handler.route(f'{BASE_PATH}/login', methods=['POST'])
@validate_arguments(AuthenticationModel)
def authentication(user_data: AuthenticationModel):

    user = Users.query.filter_by(login=user_data.login).first()
    
    if user and user.password == get_password_hash(user_data.password):
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

@auth_handler.route(f'{BASE_PATH}/register', methods=['POST'])
@validate_arguments(AuthenticationModel)
def register(user_data: AuthenticationModel):
    try:
        hashed_password = get_password_hash(user_data.password)
        user = Users(login=user_data.login, password=hashed_password)
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
            'reason': 'User with this login already exists'
        }), 400
    except:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to register user'
        }), 500