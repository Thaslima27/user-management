from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResponse

app = FastAPI()
@app.get("/")
def root():
    return {"message": "API running successfully"}
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(**user.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@app.get("/users", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(User).where(User.is_deleted == False)
    )

    return result.scalars().all()

@app.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(User).where(User.id == id, User.is_deleted == False)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@app.put("/users/{id}", response_model=UserResponse)
async def update_user(id: int, updated: UserUpdate, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in updated.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user

@app.delete("/users/{id}")
async def delete_user(id: int, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_deleted = True
    await db.commit()

    return {"message": "User soft deleted"}

@app.get("/users/{id}/toggle-active")
async def toggle_active(id: int, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    await db.commit()

    return {"is_active": user.is_active}