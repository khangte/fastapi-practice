from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field

app = FastAPI()


# ============================================
# Pydantic 모델
# ============================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=50)

class UserUpdate(BaseModel):
    email: EmailStr|None = None
    name: str|None = Field(default=None, min_length=1, max_length=50)

class UserResponse(BaseModel):
    id: int
    email: str
    create_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# 임시 저장소와 의존성
# ============================================

fake_users_db: dict[int, dict] = {}
user_id_counter = 0

def get_db():
    """DB 의존성 (지금은 임시 dict, 이후 실제 DB로 교체)"""
    return fake_users_db


# ============================================
# API 엔드포인트
# ============================================

@app.post("/users", response_model=UserResponse, 
        status_code=status.HTTP_201_CREATED
)
async def create_user(user_data: UserCreate, db: dict = Depends(get_db)):
    global user_id_counter
    user_id_counter += 1
    new_user = {
        "id": user_id_counter,
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": f"hashed_{user_data.password}",
        "is_admin": False,
        "created_at": datetime.now(),
    }
    db[user_id_counter] = new_user
    return new_user


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: dict = Depends(get_db)):
    if user_id not in db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return db[user_id]


@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: dict = Depends(get_db),
):
    users = list(db.values())
    return users[skip : skip + limit]


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: dict = Depends(get_db)):
    if user_id not in db:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
        )
    del db[user_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
