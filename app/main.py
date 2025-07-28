from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, date
from typing import Optional
from sqlalchemy import func
from fastapi.responses import StreamingResponse
import io
import csv
import os

from database import SessionLocal, engine
from models import User, Message, Room
from websocket_manager import manager
from auth import get_current_user, require_role, decode_token

# SQLAdmin imports
from sqladmin import Admin, ModelView
from fastapi import Depends

load_dotenv()

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


# --- Admin panel setup ---
def admin_auth_dependency(user=Depends(get_current_user)):
    """Restrict admin UI access."""
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return user


# Admin views for tables
class UserAdmin(ModelView, model=User):
    dependencies = [Depends(admin_auth_dependency)]
    column_list = ["id", "username", "role", "message_count"]

    def message_count(self, obj: User):
        return len(obj.messages)


class RoomAdmin(ModelView, model=Room):
    dependencies = [Depends(admin_auth_dependency)]
    column_list = ["id", "name", "description", "message_count"]

    def message_count(self, obj: Room):
        return len(obj.messages)


class MessageAdmin(ModelView, model=Message):
    dependencies = [Depends(admin_auth_dependency)]
    column_list = ["id", "content", "timestamp", "sender_username", "room_name"]

    def sender_username(self, obj: Message):
        return obj.sender.username if obj.sender else "Unknown"

    def room_name(self, obj: Message):
        return obj.room.name if obj.room else "Unknown"


# Register admin views
admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(RoomAdmin)
admin.add_view(MessageAdmin)


# --- Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class RoomCreate(BaseModel):
    name: Optional[str]
    description: Optional[str] = None


# --- Helpers ---
def get_db():
    """Provide DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# --- Auth routes ---
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Register user; first user becomes admin."""
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    user_count = db.query(User).count()
    assigned_role = "admin" if user_count == 0 else "user"

    hashed_pw = hash_password(user.password)
    new_user = User(username=user.username, password_hash=hashed_pw, role=assigned_role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User Created Successfully", "username": new_user.username}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT."""
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token_data = {"sub": db_user.username, "role": db_user.role}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['username']}, you are authorized!"}

@app.get("/admin-only")
def admin_route(current_user: dict = Depends(require_role("admin"))):
    return {"message": f"Welcome Admin {current_user['username']}!"}


# --- Room management ---
@app.post("/rooms")
def create_room(room: RoomCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_role("admin"))):
    """Create chat room (admin only)."""
    existing_room = db.query(Room).filter(Room.name == room.name).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Room with this name already exists")

    new_room = Room(name=room.name, description=room.description)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return {"message": "Room created successfully", "room_id": new_room.id, "name": new_room.name}

@app.get("/rooms")
def list_rooms(db: Session = Depends(get_db)):
    """List all chat rooms."""
    return db.query(Room).all()


# --- Analytics ---
@app.get("/analytics/messages-per-room")
def messages_per_room(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Message count by room with optional date filter."""
    query = db.query(Room.name, func.count(Message.id).label("message_count")).join(Message)
    if start_date:
        query = query.filter(Message.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Message.timestamp <= datetime.combine(end_date, datetime.max.time()))
    results = query.group_by(Room.id).all()
    return [{"room": r[0], "message_count": r[1]} for r in results]

@app.get("/analytics/user-activity")
def user_activity(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """User activity (messages sent) with optional date filter."""
    query = db.query(User.username, func.count(Message.id).label("messages_sent")).join(Message)
    if start_date:
        query = query.filter(Message.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Message.timestamp <= datetime.combine(end_date, datetime.max.time()))
    results = query.group_by(User.id).all()
    return [{"username": r[0], "messages_sent": r[1]} for r in results]

@app.get("/analytics/messages-per-room/csv")
def messages_per_room_csv(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Download messages-per-room analytics as CSV."""
    query = db.query(Room.name, func.count(Message.id).label("message_count")).join(Message)
    if start_date:
        query = query.filter(Message.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Message.timestamp <= datetime.combine(end_date, datetime.max.time()))
    results = query.group_by(Room.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Room", "Message Count"])
    for r in results:
        writer.writerow([r[0], r[1]])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=messages_per_room.csv"})


# --- WebSocket endpoint ---
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    """Handle real-time chat via WebSocket."""
    await websocket.accept()

    # Token check
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        current_user = decode_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        await websocket.close(code=1008)
        db.close()
        return

    await manager.connect(str(room_id), websocket)

    try:
        # Send last 20 messages
        recent_messages = (
            db.query(Message)
            .filter(Message.room_id == room_id)
            .order_by(Message.timestamp.desc())
            .limit(20)
            .all()
        )
        for msg in reversed(recent_messages):
            await websocket.send_json({
                "username": msg.sender.username,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })

        # Handle new messages
        while True:
            data = await websocket.receive_text()
            sender = db.query(User).filter(User.username == current_user["username"]).first()
            new_message = Message(room_id=room_id, sender_id=sender.id, content=data, timestamp=datetime.utcnow())
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            broadcast_data = {
                "username": sender.username,
                "content": new_message.content,
                "timestamp": new_message.timestamp.isoformat()
            }
            await manager.broadcast(str(room_id), broadcast_data)

    except WebSocketDisconnect:
        await manager.disconnect(str(room_id), websocket)
    finally:
        db.close()
