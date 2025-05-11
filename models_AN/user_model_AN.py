from sqlalchemy import Column, Integer, String
from db_AN.database_AN import Base
from sqlalchemy.orm import relationship
from .subscription_model_AN import Subscription_AN

class User_AN(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    subscription = relationship("Subscription_AN", back_populates="user", uselist=False)