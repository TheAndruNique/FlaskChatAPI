from flask import Blueprint, jsonify, request
from helper import token_required
from config import BASE_PATH
from models import Users, Chats
from functools import wraps
import pymongo
import time
from app import db
import uuid
from sqlalchemy import or_


chattings = Blueprint('chat', __name__)

class PermissionDeniedError(Exception):
    def __init__(self, message="Permission denied. User does not have the required permissions."):
        self.message = message
        super().__init__(self.message)


class Chat:
    def __init__(self, chat_id, user: Users) -> None:
        self.client = pymongo.MongoClient('mongodb://localhost:27017')
        self.db = self.client['chats']
        self.collection = self.db[chat_id]
        self.user = user
        self.chat_id = chat_id
        self.check_rights()
    
    def add_rights(self):
        users = Chats.query.filter_by(chat_id=self.chat_id)
        user_ids = []
        for item in users:
            user_ids.append(item.user_id)

        rights = {
            'chat_config': {
                'users': user_ids,
                'data': {
                    'title': self.chat_id
                }
            }
        }
        self.collection.insert_one(rights)

    def check_rights(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            result = self.collection.find_one({'chat_config': {'$exists': True}})
            if result:
                chat_config = result.get('chat_config')
                users = chat_config.get('users')
                if self.user.id in users:
                    return f(self, *args, **kwargs)
                else:
                    raise PermissionDeniedError()
            else:
                self.add_rights()
        return wrapper

    @check_rights
    def send_message(self, message):
        last_message = next(self.collection.find({'message': {'$exists': True}}).sort([("message_id", -1)]).limit(1), None)
        next_message_id = 1
        if last_message:
            next_message_id = last_message.get('message_id') + 1
            
        current_time = time.time()
        self.collection.insert_one({
            'from': self.user.login,
            'from_id': self.user.id,
            'message': message,
            'time': current_time,
            'message_id': next_message_id
        })
        return next_message_id

    @check_rights
    def get_count_chat_messages(self):
        return self.collection.count_documents({'message': {'$exists': True}})
    
    @check_rights
    def get_chat_messages(self, count=20, offset=0):
        cursor = self.collection.find({'message': {'$exists': True}}).sort([("message_id", -1)]).limit(count).skip(offset)
        messages = []
        
        for document in cursor:
            document.pop("_id", None)
            messages.append(document)
            
        return messages


@chattings.route(f'{BASE_PATH}/chats', methods=['GET'])
@token_required
def get_chats(current_user: Users):
    chats = Chats.query.filter_by(user_id=current_user.id)
    chats_lst = []
    for item in chats:
        chats_lst.append({
            'chat_id': item.chat_id,
            'count_messages': Chat(chat_id=item.chat_id, user=current_user).get_count_chat_messages()
        })

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
    
    chat = Chat(data['chat_id'], user = current_user)
    try:
        message_id = chat.send_message(data['message'])
    except PermissionDeniedError:
        return jsonify({
            'success': False,
            'message': 'Permission denied'
        }), 403
    
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

    Chat(chat_id=chat_id, user=current_user)
    return jsonify({
        'success': True,
        'message': 'Chat created successfully',
        'chat_id': chat_id
    })

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

    chat = Chat(chat_id=data['chat_id'], user=current_user)
    messages = chat.get_chat_messages(count=data['count'], offset=data['offset'])
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