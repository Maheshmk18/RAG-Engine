from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserOut, UserUpdate
from ..utils.dependencies import get_current_admin_user
from ..utils.auth import get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_in.email:
        existing = db.query(User).filter(User.email == user_in.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.role is not None:
        user.role = user_in.role
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    if user_id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}