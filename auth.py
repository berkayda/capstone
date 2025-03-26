import jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_jwt_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def decode_jwt_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
