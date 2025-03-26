from fastapi import FastAPI, HTTPException, Depends, Header
from contextlib import asynccontextmanager
from auth import hash_password, verify_password, create_jwt_token, decode_jwt_token
from database import *
from pydantic import BaseModel
from models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str


@app.post("/auth/register")
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    if not user.email.strip():  # Boş e-posta engelleme
        raise HTTPException(status_code=400, detail="E-posta adresi boş olamaz!")

    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı.")

    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    return {"message": "Kullanıcı başarıyla kaydedildi!"}

@app.post("/auth/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/user/me")
async def get_user_info(Authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Token eksik!")

    scheme, _, token = Authorization.partition(" ")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")

    token_data = decode_jwt_token(token)

    result = await db.execute(select(User).where(User.email == token_data["sub"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı!")

    return {"email": user.email, "created_at": str(user.created_at)}
