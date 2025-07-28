from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

# --- User model ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)

    # Relationship: user → messages
    messages = relationship("Message", back_populates="sender")


# --- Room model ---
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Relationship: room → messages
    messages = relationship("Message", back_populates="room")


# --- Message model ---
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships: message → sender & room
    sender = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")
