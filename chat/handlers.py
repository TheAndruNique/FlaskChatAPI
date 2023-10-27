from flask import Blueprint, jsonify, request
from helper import token_required
from config import BASE_PATH
from models import Users, Chats
from app import db
import uuid
from sqlalchemy import or_
from .chat import Chat, PermissionDeniedError, NotExistedChat


chattings = Blueprint('chat', __name__)

@chattings.route(f'{BASE_PATH}/chats', methods=['GET'])
@token_required
def get_chats(current_user: Users):
    chats = Chats.query.filter_by(user_id=current_user.id)
    chats_lst = []
    for item in chats:
        try:
            chats_lst.append({
                'chat_id': item.chat_id,
                'count_messages': Chat(chat_id=item.chat_id, user=current_user).get_count_chat_messages()
            })
        except NotExistedChat:
            chats_lst.append({
                'chat_id': item.chat_id,
                'status': 'Chat has been closed or deleted'
            })
            for chat in Chats.query.filter_by(chat_id=item.chat_id):
                db.session.delete(chat)
            db.session.commit()

    return jsonify({
        'chats': chats_lst
    }), 200

@chattings.route(f'{BASE_PATH}/send_message', methods=['POST'])
@token_required
def send_message(current_user: Users):
    data = request.get_json()
    required_keys = ['chat_id', 'message']

    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        return jsonify({
            'error': True, 
            'reason': f'missed follow keys: {", ".join(missing_keys)}'
        }), 400
    try:
        chat = Chat(data['chat_id'], user = current_user)
        message_id = chat.send_message(data['message'])
    except PermissionDeniedError:
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    except NotExistedChat:
        return jsonify({
            'error': True,
            'message': f'Chat with ID {data["chat_id"]} does not exist'
        }), 404

    return jsonify({
        'success': True,
        'message_id': message_id
    }), 200

@chattings.route(f'{BASE_PATH}/create_chat', methods=['POST'])
@token_required
def create_chat(current_user: Users):
    data = request.get_json()
    required_keys = ['user_id']
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        return jsonify({
            'error': True, 
            'reason': f'missed follow keys: {", ".join(missing_keys)}'
        }), 400

    chat_id = str(uuid.uuid4())
    chat1 = Chats(user_id = current_user.id, chat_id=chat_id)
    chat2 = Chats(user_id = data['user_id'], chat_id=chat_id)
    try:
        db.session.add(chat1)
        db.session.add(chat2)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to create chat'
        }), 500

    Chat(chat_id=chat_id, user=current_user, new=True)
    return jsonify({
        'success': True,
        'message': 'Chat created successfully',
        'chat_id': chat_id
    }), 200

@chattings.route(f'{BASE_PATH}/get_chat_updates', methods=['GET'])
@token_required
def get_chat_updates(current_user: Users):
    data = request.get_json()
    required_keys = ['chat_id', 'count', 'offset']
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        return jsonify({
            'error': True, 
            'reason': f'missed follow keys: {", ".join(missing_keys)}'
        }), 400

    try:
        chat = Chat(chat_id=data['chat_id'], user=current_user)
        messages = chat.get_chat_messages(count=data['count'], offset=data['offset'])
    except NotExistedChat:
        return jsonify({
            'error': True,
            'message': f'Chat with ID {data["chat_id"]} does not exist'
        }), 404

    return jsonify({
        'success': True,
        'chat_id': data['chat_id'],
        'messages': messages
    })

@chattings.route(f'{BASE_PATH}/search_users', methods=['GET'])
@token_required
def search_users(current_user):
    data = request.get_json()
    required_keys = ['search_login']
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        return jsonify({
            'error': True, 
            'reason': f'missed follow keys: {", ".join(missing_keys)}'
        }), 400
        
        
    found_users  = Users.query.filter(or_(Users.login.like(f"%{data['search_login']}%"))).all()
    found_users_lst  = []

    for user in found_users:
        found_users_lst.append({'id': user.id, 'login': user.login})

    return jsonify({
        'success': True,
        'found_users': found_users_lst
    })