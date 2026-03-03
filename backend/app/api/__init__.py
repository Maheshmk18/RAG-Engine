from fastapi import APIRouter
from . import auth, documents, chat, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(users.router)