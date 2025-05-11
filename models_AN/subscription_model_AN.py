from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from db_AN.database_AN import Base

class Subscription_AN(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    schedule_hash = Column(String, nullable=False)

    user = relationship("User_AN", back_populates="subscription", uselist=False)
