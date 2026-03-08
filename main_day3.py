import os
from datetime import datetime
from enum import Enum
from fastapi import (
    FastAPI, HTTPException, Response, status, Query, Path, Security
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

security = HTTPBearer()

app = FastAPI(
    title="User Management API",
    description="사용자 관리를 위한 REST API",
    version="1.0.0",
    
    docs_url = "/docs" if DEBUG else None,
    redoc_url = "/redoc" if DEBUG else None
)

# ============================================
# Enum & Pydantic 모델
# ============================================
class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class UserCreate(BaseModel):
    """사용자 생성 요청"""
    email: EmailStr = Field(description="이메일 주소",
                            examples=["user@example.com"])
    password: str = Field(min_length=8, description="비밀번호 (8자 이상)")
    name: str = Field(min_length=1, max_length=50, description="이름")
    role: UserRole = Field(default=UserRole.user, description="권한")

class UserUpdate(BaseModel):
    """사용자 수정 요청"""
    name: str|None = Field(default=None, min_length=1, max_length=50, description="이름")
    role: UserRole|None = Field(default=None, description="권한")

class UserResponse(BaseModel):
    """사용자 응답"""
    id: int = Field(description="사용자 ID")
    email: str = Field(description="이메일")
    name: str = Field(description="이름")
    role: UserRole = Field(description="권한")
    created_at: datetime = Field(description="가입일시")
    
    model_config = {"from_attributes": True}

class ErrorResponse(BaseModel):
    """에러 응답"""
    detail: str = Field(description="에러 메시지")

class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    items: list[UserResponse]
    total: int

# ============================================
# 임시 DB
# ============================================

fake_db: dict[int, dict] = {}
counter = 0

# ============================================
# API 엔드포인트
# ============================================

@app.get("protected", summary="보호된 리소스")
async def protected_route(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    인증이 필요한 엔드포인트입니다.
    Authorization 헤더에 Bearer 토큰을 포함해야 합니다.
    """
    return {"token": credentials.credentials}

@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 생생",
    tags=["Users"],
    responses={
        201: {"description": "생성 성공"},
        409: {"model": ErrorResponse, "description": "이메일 중복"},
        422: {"description": "입력 검증 실패"},
    }
)
async def create_user(user: UserCreate):
    """
     새 사용자를 생성합니다.
        - 이메일은 중복될 수 없습니다
        - 비밀번호는 8자 이상이어야 합니다
    """
    global counter

    for u in fake_db.values():
        if u["email"] == user.email:
            raise HTTPException(status_code=409, detail="Email already exists")

        counter += 1
        new_user = {
            "id": counter,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "hashed_password": f"hashed_{user.password}",
            "created_at": datetime.now()
        }

        fake_db[counter] = new_user
        return new_user
    
@app.get(
    "/users",
    response_model=UserListResponse,
    summary="사용자 목록",
    tags=["Users"],
)
async def list_users(
    skip: int = Query(default=0, ge=0, description="건너뛸 개수"),
    limit: int = Query(default=10, ge=1, le=100, description="가져올 개수"),
    role: UserRole | None = Query(default=None, description="권한 필터")
):
    """
    사용자 목록을 조회합니다.
        - **skip**: 페이지네이션용 오프셋
        - **limit**: 최대 100개까지
        - **role**: 특정 권한 사용자만 필터링
    """
    users = list(fake_db.values())

    if role:
        users = [u for u in users if u["role"]==role]
    return {
        "items": users[skip: skip+limit],
        "total": len(users)
    }

@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="사용자 조회",
    tags=["Users"],
    responses={
        200: {"description": "조회 성공"},
        404: {"model": ErrorResponse, "description": "사용자 없음"}
    }
)
async def get_user(
    user_id: int = Path(description="사용자 ID", gt=0)
):
    """user_id 로 단일 사용자를 조회합니다."""
    if user_id not in fake_db:
        raise HTTPException(status_code=404, detail="User not found")
    return fake_db[user_id]

@app.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="사용자 수정",
    tags=["Users"],
    responses={
        200: {"description": "수정 성공"},
        404: {"model": ErrorResponse, "description": "사용자 없음"},
    },
)
async def update_user(
    user_data: UserUpdate,
    user_id: int = Path(description="사용자 ID", gt=0),
):
    """사용자 정보를 부분 수정합니다."""
    if user_id not in fake_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = fake_db[user_id]
    update_dict = user_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        user[key] = value
    return user

@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="사용자 삭제",
    tags=["Users"],
    responses={
        204: {"description": "삭제 성공"},
        404: {"model": ErrorResponse, "description": "사용자 없음"},
    },
)
async def delete_user(
    user_id: int = Path(description="사용자 ID", gt=0),
):
    """사용자를 삭제합니다."""
    if user_id not in fake_db:
        raise HTTPException(status_code=404, detail="User not found")

    del fake_db[user_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
