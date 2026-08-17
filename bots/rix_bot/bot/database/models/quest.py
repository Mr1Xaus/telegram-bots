import enum
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.models.base import Base

class QuestTypeEnum(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"

class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quest_key: Mapped[str] = mapped_column(String(64), nullable=False)
    quest_type: Mapped[QuestTypeEnum] = mapped_column(Enum(QuestTypeEnum), default=QuestTypeEnum.DAILY, nullable=False)
    
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
