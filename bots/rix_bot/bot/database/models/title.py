import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    BigInteger, Integer, Boolean, String, DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column
from bot.database.models.base import Base

class TitleTypeEnum(str, enum.Enum):
    RNG = "RNG"
    ACHIEVEMENT = "ACHIEVEMENT"
    SECRET = "SECRET"

class Title(Base):
    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    type: Mapped[TitleTypeEnum] = mapped_column(Enum(TitleTypeEnum), default=TitleTypeEnum.RNG, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class UserTitle(Base):
    __tablename__ = "user_titles"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    title_id: Mapped[int] = mapped_column(Integer, ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class MarketListing(Base):
    __tablename__ = "market_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[int] = mapped_column(Integer, ForeignKey("titles.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
