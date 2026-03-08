from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="TODO API", 
    description="Day 1 실습용 TODO API",
    version="1.0.0",
)

# ============================================
# 모델 정의
# ============================================

class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str|None = Field(default=None, max_length=500)
    completed: bool = False

class TodoUpdate(BaseModel):
    title: str|None = Field(default=None, min_length=1, max_length=100)
    description: str|None = Field(default=None, max_length=500)
    completed: bool|None = None

class TodoResponse(BaseModel):
    id: int 
    title: str
    description: str|None
    completed: bool

# ============================================
# 임시 저장소 (실제로는 DB 사용)
# ============================================

todos: dict[int, dict] = {}
todo_id_counter = 0

# ============================================
# API 엔드포인트
# ============================================

@app.get("/")
async def root():
    return {"message": "Welcome to TODO API", "docs": "/docs"}

@app.get("/todos", response_model=list[TodoResponse])
async def list_todos(
    completed: bool|None = None,
    skip: int=0,
    limit: int=10,
):
    """
    TODO 목록 조회
        - completed: 완료 여부 필터
        - skip: 건너뛸 개수
        - limit: 가져올 개수
    """
    result = list(todos.values())

    if completed is not None:
        result = [t for t in result if t["completed"] == completed]

    return result[skip :skip + limit]

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int):
    """특정 TODO 조회"""
    if todo_id not in todos:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"TODO with id {todo_id} not found",
        )
    return todos[todo_id]

@app.post(
    "/todos",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_todo(todo: TodoCreate):
    """새 TODO 생성"""
    global todo_id_counter
    todo_id_counter += 1

    new_todo = {
        "id": todo_id_counter,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
    }
    todos[todo_id_counter] = new_todo
    return new_todo

@app.patch("todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo: TodoUpdate):
    """TODO 부분 수정"""
    if todo_id not in todos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO with id {todo_id} not found"
        )
    
    stored_todo = todos[todo_id]
    update_data = todo.model_dump(exclude_upset=True)

    for key, value in update_data.items():
        stored_todo[key] = value
    
    return stored_todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    """TODO 삭제"""
    if todo_id not in todos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO with id {todo_id} not found"
        )
    del todos[todo_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
