from sqlalchemy import (
    ForeignKey,
    CheckConstraint,
    event,
    Index,
    func,
    String,
    Date,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase, Session


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
        CheckConstraint("level >= 1 AND level <= 5", name="level_range_check"),
    )


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    patronymic: Mapped[str] = mapped_column(String(50))
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    hire_date: Mapped[str] = mapped_column(Date, nullable=False)
    salary: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    manager_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))

    position: Mapped["Position"] = relationship(back_populates="employees")
    manager = relationship("Employee", remote_side=[id], foreign_keys=[manager_id])

    @property
    def position_level(self):
        return self.position.level

    @property
    def manager_position_level(self):
        return self.manager.position.level if self.manager else None

    __table_args__ = (
        CheckConstraint("hire_date <= CURRENT_DATE", name="valid_hire_date"),
        CheckConstraint("manager_id != id OR manager_id IS NULL", name="valid_manager"),
        CheckConstraint("salary > 0", name="positive_salary"),
        Index("idx_emp_manager", manager_id),
        Index("idx_emp_position", position_id),
        Index("idx_emp_name", last_name, first_name),
        Index("idx_emp_hire_date", hire_date),
        Index("idx_emp_salary", salary),
        Index("idx_emp_name_lower", func.lower(last_name), func.lower(first_name)),
    )


# Добавляем валидацию через event handler
@event.listens_for(Session, "before_flush")
def validate_manager_level(session, flush_context, instances):
    for obj in session.new.union(session.dirty):
        if isinstance(obj, Employee) and obj.manager:
            if obj.manager.position.level > obj.position.level:
                raise ValueError(
                    f"Менеджер {obj.manager.id} ({obj.manager.position.title}) "
                    f"имеет более низкую позицию, чем сотрудник {obj.id} ({obj.position.title})"
                )
