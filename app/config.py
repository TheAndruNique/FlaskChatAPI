from dotenv import load_dotenv
import os


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
MIN_LOGIN_LENGTH = os.getenv('MIN_LOGIN_LENGTH', 3)
MAX_LOGIN_LENGTH = os.getenv('MIN_LOGIN_LENGTH', 50)
MIN_PASSWORD_LENGTH = os.getenv('MIN_PASSWORD_LENGTH', 5)
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///users.db')
MONGODB_CONNECTION_URI = os.getenv('MONGODB_URI')
BASE_PATH = os.getenv('BASE_PATH', '/api/v1.0')
TOKEN_LIFETIME = os.getenv('TOKEN_LIFETIME', 3600)
PORT = os.getenv('PORT', 5000)