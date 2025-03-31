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
from core.cli.localization import messages


POSITION_HIERARCHY = [
    ("CEO", 1),
    ("Manager", 2),
    ("Team Lead", 3),
    ("Senior Developer", 4),
    ("Developer", 5),
    ("Analyst", 5),
    ("Designer", 5),
    ("HR Specialist", 5),
    ("Tester", 5),
]


class Base(DeclarativeBase):
    pass


class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[int] = mapped_column(nullable=False)

    employees: Mapped[list["Employee"]] = relationship(back_populates="position")

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
    manager_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=True)

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
        CheckConstraint("manager_id != id", name="valid_manager"),
        CheckConstraint("salary > 0", name="positive_salary"),
        Index("idx_emp_manager", manager_id),
        Index("idx_emp_position", position_id),
        Index("idx_emp_name", last_name, first_name),
        Index("idx_emp_hire_date", hire_date),
        Index("idx_emp_salary", salary),
        Index("idx_emp_name_lower", func.lower(last_name), func.lower(first_name)),
    )

    def get_full_name(self) -> str:
        if self.patronymic:
            return f"{self.last_name} {self.first_name} {self.patronymic}"
        return f"{self.last_name} {self.first_name}"

    def get_short_name(self) -> str:
        if self.patronymic:
            return f"{self.last_name} {self.first_name[0]}. {self.patronymic[0]}."
        return f"{self.last_name} {self.first_name[0]}."

    def __repr__(self) -> str:
        return f"<Employee id={self.id!r} name={self.get_full_name}"


# Добавляем валидацию через event handler
@event.listens_for(Session, "before_flush")
def validate_employee_relations(session, flush_context, instances):
    for obj in session.new.union(session.dirty):
        if not isinstance(obj, Employee):
            continue

        # Check for required fields
        if not obj.position_id:
            raise ValueError("Employee must have a position")
            
        # Get position from database directly
        position = session.get(Position, obj.position_id)
        if not position:
            raise ValueError(f"Invalid position ID: {obj.position_id}")

        # CEO validation
        if position.level == 1:
            if obj.manager_id:
                raise ValueError("CEO cannot have a manager")
            return

        # Manager validation for other levels
        if not obj.manager_id:
            raise ValueError("Non-CEO employees must have a manager")
            
        # Get manager from database
        manager = session.get(Employee, obj.manager_id)
        if not manager:
            raise ValueError(f"Invalid manager ID: {obj.manager_id}")
            
        # Get manager's position
        manager_position = session.get(Position, manager.position_id)
        if not manager_position:
            raise ValueError(f"Manager {manager.id} has invalid position")
            
        # Hierarchy check
        if manager_position.level >= position.level:
            raise ValueError(
                f"Manager's level ({manager_position.level}) must be "
                f"lower than employee's level ({position.level})"
            )
