from config import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = '4e1501b865e93e5edf508935ae757a172e95a4914df6e2cad3f6cf3c4ed496e5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
