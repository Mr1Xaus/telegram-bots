import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    BigInteger, SmallInteger, Float, Boolean, String, DateTime,
    Enum, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.models.base import Base

class GenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"

class UserRoleEnum(str, enum.Enum):
    USER = "USER"
    ADMIN_B = "ADMIN_B"
    ADMIN_A = "ADMIN_A"
    OWNER = "OWNER"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), default=GenderEnum.UNKNOWN, nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum), default=UserRoleEnum.USER, nullable=False)
    
    is_guarantor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    guarantor_mentor_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    rep_balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    custom_avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    has_polygamy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_all_in_one: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    quest_streak: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    streak_broken_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    exempt_from_quota_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("rep_balance >= 0", name="check_user_rep_non_negative"),
        CheckConstraint("level >= 0 AND level <= 5", name="check_user_level_range"),
    )

class ChatStats(Base):
    __tablename__ = "chat_stats"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    
    msg_count_week: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    msg_count_month: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    msg_count_total: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    rep_earned_week: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rep_earned_month: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rep_earned_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
