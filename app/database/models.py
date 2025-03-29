from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column



POSITION_HIERARCHY = [
    ("CEO", 1),
    ("Manager", 2),
    ("Team Lead", 3),
    ("Senior Developer", 4),
    ("Developer", 5),
]


class Base(DeclarativeBase):
    pass


class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        CheckConstraint('level >= 1 AND level <= 5', name='level_range_check'),
    )