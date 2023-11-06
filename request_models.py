from pydantic import BaseModel, Field
from app.config import MAX_LOGIN_LENGTH, MIN_LOGIN_LENGTH, MIN_PASSWORD_LENGTH


class AuthenticationModel(BaseModel):
    login: str = Field(
        min_length=MIN_LOGIN_LENGTH, 
        max_length=MAX_LOGIN_LENGTH
    )
    password: str = Field(
        min_length=MIN_PASSWORD_LENGTH
    )