from employees.models import Employee
from core.cli.localization import messages
from typing import List, Dict
from tabulate import tabulate


def print_employees_table(employees: List[Dict]):
    """Prints employees list or one employee in table"""
    if not employees:
        msg = messages['errors']['cli']['empty_table']
        raise ValueError(msg)
        # Подготавливаем данные для таблицы
    t = 'title' if len(employees) > 1 else 'title_one'
    title = messages['ui']['views']['emps_tbl'][t]
    print(title)
    table_data = []
    for emp in employees:
        table_data.append([
                emp.id,
                emp.get_full_name(),
                emp.position.title,
                emp.hire_date.strftime('%Y-%m-%d'),
                f"${emp.salary:,.2f}",
                f"{emp.manager.get_full_name() or ''}"
            ])
    headers = messages['ui']['views']['emps_tbl']['headers']
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    