from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def verify_password(self, password: str, pwd_context) -> bool:
        return pwd_context.verify(password, self.hashed_password)

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    query = Column(String(1000), nullable=False)
    response = Column(String(2000), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 关联用户模型
    user = relationship("User", back_populates="chat_history")