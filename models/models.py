from app import db
from sqlalchemy.orm import composite
import uuid


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    
    def __repr__(self) -> str:
        return f'<user {self.id}>'


class Chats(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    chat_type = db.Column(db.String(10), nullable=True)
    chat_with = db.Column(db.Integer)
