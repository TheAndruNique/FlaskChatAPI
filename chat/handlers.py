from flask import Blueprint, jsonify, request
from helper import token_required, check_required_keys
from db import Users, Chats
from app import db
from app.config import BASE_PATH
import uuid
from sqlalchemy import or_
from .mongo_models import Chat
from .exc import PermissionDeniedError, NotExistedChat


chat_handler = Blueprint('chat', __name__)

@chat_handler.route(f'{BASE_PATH}/chats', methods=['GET'])
@token_required
def get_chats(current_user: Users):
    chats = Chats.query.filter_by(user_id=current_user.id)
    chats_lst = []
    for item in chats:
        try:
            chat = Chat(chat_id=item.id, user=current_user)
            chats_lst.append({
                'chat_id': item.id,
                'messages_count': chat.get_count_chat_messages(),
                'chat_config': chat.get_config()
            })
        except NotExistedChat:
            chats_lst.append({
                'chat_id': item.id,
                'status': 'Chat has been closed or deleted'
            })
            for chat in Chats.query.filter_by(id=item.id):
                db.session.delete(chat)
            db.session.commit()

    return jsonify({
        'chats': chats_lst
    }), 200

@chat_handler.route(f'{BASE_PATH}/send_message', methods=['POST'])
@token_required
@check_required_keys({'chat_id': str, 'message': str})
def send_message(current_user: Users):
    data = request.get_json()

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

@chat_handler.route(f'{BASE_PATH}/create_private_chat', methods=['POST'])
@token_required
@check_required_keys({'user_id': int})
def create_private_chat(current_user: Users):
    data = request.get_json()

    existed_chat = Chats.query.filter_by(user_id=current_user.id, chat_with=data['user_id']).first()
    if existed_chat:
        return jsonify({
            'success': False,
            'message': f'Private chat with user {data["user_id"]} already exists',
            'chat_id': existed_chat.id
        }), 400
        
    chat_id = str(uuid.uuid4())
    chat = Chats(id=chat_id, user_id = current_user.id, chat_with=data['user_id'], chat_type='private')
    a_chat = Chats(id = chat.id, user_id = data['user_id'], chat_with=current_user.id, chat_type='private')
    db.session.add(chat)
    db.session.add(a_chat)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to create chat'
        }), 500

    Chat(chat_id=chat.id, user=current_user, chat_type='private', new=True)
    return jsonify({
        'success': True,
        'message': 'Private chat created successfully',
        'chat_id': chat.id
    }), 200


@chat_handler.route(f'{BASE_PATH}/create_group_chat', methods=['POST'])
@token_required
def create_group_chat(current_user: Users):
    data = request.get_json()

    chat_id = str(uuid.uuid4())

    chat = Chats(id=chat_id, user_id=current_user.id, chat_type='group')
    db.session.add(chat)

    users_id = data.get('users_id')
    if users_id:
        if isinstance(users_id, list):
            for item in users_id:
                a_chat = Chats(id=chat.id, user_id=item, chat_type='group')
                db.session.add(a_chat)
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid users_id data in the request.'
            }), 400
    
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to create chat'
        }), 500

    Chat(chat_id=chat.id, user=current_user, chat_type='group', new=True)
    return jsonify({
        'success': True,
        'message': 'Group chat created successfully',
        'chat_id': chat.id
    }), 200

@chat_handler.route(f'{BASE_PATH}/get_chat_updates', methods=['GET'])
@token_required
@check_required_keys({'chat_id': str, 'count': int, 'offset': int})
def get_chat_updates(current_user: Users):
    data = request.get_json()

    try:
        chat = Chat(chat_id=data['chat_id'], user=current_user)
        messages = chat.get_chat_messages(count=data['count'], offset=data['offset'])
    except NotExistedChat:
        return jsonify({
            'error': True,
            'message': f'Chat with ID {data["chat_id"]} does not exist'
        }), 404

    total = 0
    if messages:
        total = messages[0].get('message_id')
    
    return jsonify({
        'success': True,
        'chat_id': data['chat_id'],
        'messages': messages,
        'messages_count': total 
    })

@chat_handler.route(f'{BASE_PATH}/search_users', methods=['GET'])
@token_required
@check_required_keys({'search_login': str})
def search_users(current_user):
    data = request.get_json()
  
    found_users  = Users.query.filter(or_(Users.login.like(f"%{data['search_login']}%"))).all()
    found_users_lst  = []

    for user in found_users:
        found_users_lst.append({'id': user.id, 'login': user.login})

    return jsonify({
        'success': True,
        'found_users': found_users_lst
    })