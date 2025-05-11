from sqlalchemy import Column, Integer, ForeignKey
from db_AN.database_AN import Base

class ReminderSetting_AN(Base):
    __tablename__ = "reminder_settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    remind_30 = Column(Integer, default=0)
    remind_10 = Column(Integer, default=0)
