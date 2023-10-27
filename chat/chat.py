from models import Users, Chats
import pymongo
import time
from functools import wraps



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