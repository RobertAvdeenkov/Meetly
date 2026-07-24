from sqlalchemy import Column,String,Integer,ForeignKey,create_engine,DateTime, Table, BLOB
from sqlalchemy.orm import DeclarativeBase,relationship
from sqlalchemy import func


class Base(DeclarativeBase):pass

participants = Table(
    "participants",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("event_id", Integer, ForeignKey("events.id"), primary_key=True),
)

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String)
    password=Column(BLOB)
    role=Column(String,default='user')
    events=relationship('Event', secondary=participants, back_populates='users')
    audit_logs = relationship("AutLog", back_populates="user")
    created_events = relationship('Event', back_populates='creator')
    messages=relationship('Message', back_populates='user')

class Event(Base):
    __tablename__='events'
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String)
    type=Column(String)
    desc=Column(String)
    end_at=Column(String)
    place=Column(String)
    tags=Column(String, default='')

    creator_id = Column(Integer, ForeignKey('users.id'))
    creator = relationship("User", back_populates="created_events")

    users=relationship('User', secondary=participants, back_populates='events')

class AutLog(Base):
    __tablename__='log'
    id=Column(Integer,primary_key=True, index=True)
    user_id=Column(Integer, ForeignKey('users.id'))
    entity=Column(String)
    info=Column(String, default='')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="audit_logs")

class Message(Base):
    __tablename__='messages'
    id=Column(Integer, primary_key=True, index=True)
    sender_name=Column(String)
    info=Column(String)
    to_id=Column(Integer, ForeignKey('users.id'))
    user=relationship('User', back_populates='messages')
    created_at = Column(DateTime(timezone=True), server_default=func.now())