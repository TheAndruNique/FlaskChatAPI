from dotenv import load_dotenv
import os
import logging


load_dotenv()

def get_int_env_variable(env_name, default, min_value=None, max_value=None):
    env_value = os.getenv(env_name, default)
    try:
        int_value = int(env_value)
        if (min_value is not None and int_value < min_value) or (max_value is not None and int_value > max_value):
            raise ValueError("Value is outside the valid range.")
        return int_value
    except ValueError:
        logging.error(f'Error: Environment variable {env_name} must be an integer.')
        return default

SECRET_KEY = os.getenv('SECRET_KEY')

required_values = ["SECRET_KEY"]
missing_values = [value for value in required_values if os.environ.get(value) is None]
if len(missing_values) > 0:
      logging.error(f"The following environment values are missing in your .env: {', '.join(missing_values)}")
      exit(1)

MIN_LOGIN_LENGTH = get_int_env_variable('MIN_LOGIN_LENGTH', 3)
MAX_LOGIN_LENGTH = get_int_env_variable('MAX_LOGIN_LENGTH', 50)
MIN_PASSWORD_LENGTH = get_int_env_variable('MIN_PASSWORD_LENGTH', 5)
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///users.db')
MONGODB_CONNECTION_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
BASE_PATH = os.getenv('BASE_PATH', '/api/v1.0')
TOKEN_LIFETIME = get_int_env_variable('TOKEN_LIFETIME', 3600)
PORT = get_int_env_variable('PORT', 5000)
