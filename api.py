from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
import hashlib
import jwt
import time
from functools import wraps
import pymongo
import uuid


app = Flask(__name__)
app.config['SECRET_KEY'] = '4e1501b865e93e5edf508935ae757a172e95a4914df6e2cad3f6cf3c4ed496e5'
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


class Chats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    chat_id = db.Column(db.String(40))


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


@app.route(f'{BASE_PATH}/login', methods=['POST'])
def auth():
    data = request.get_json()
    required_keys = ['login', 'password']
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        return jsonify({
            'error': True, 
            'reason': f'missed follow keys: {", ".join(missing_keys)}'
        }), 400

    user = Users.query.filter_by(login=data['login']).first()
    
    if user and user.password == get_password_hash(data['password']):
        time_exp = time.time() + 3600
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

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.get_json().get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'reason': 'No token provided'
            }), 403
        try:    
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
            current_user = Users.query.get(data['user_id'])
        except:
            return jsonify({
                'success': False,
                'reason': 'Invalid token'
            }), 403
            
        return f(current_user, *args, **kwargs)
    return wrapper

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

@app.route(f'{BASE_PATH}/chats', methods=['GET'])
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

@app.route(f'{BASE_PATH}/send_message', methods=['POST'])
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

@app.route(f'{BASE_PATH}/create_chat', methods=['POST'])
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

@app.route(f'{BASE_PATH}/get_chat_updates', methods=['GET'])
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

@app.route(f'{BASE_PATH}/search_users', methods=['GET'])
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
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()