from core.cli.localization import messages
from typing import List, Dict
from tabulate import tabulate


def print_employees_table(employees: List[Dict]):
    """Prints employees list or one employee in table"""
    if not employees:
        msg = messages["errors"]["cli"]["empty_table"]
        raise ValueError(msg)
        # Подготавливаем данные для таблицы
    t = "title" if len(employees) > 1 else "title_one"
    title = messages["ui"]["views"]["emps_tbl"][t]
    print(title)
    table_data = []
    for emp in employees:
        table_data.append(
            [
                emp.id,
                emp.get_full_name(),
                emp.position.title,
                emp.hire_date.strftime("%Y-%m-%d"),
                f"{emp.salary:,.2f}",
                emp.manager.get_full_name() if emp.manager else "",
            ]
        )
    headers = messages["ui"]["views"]["emps_tbl"]["headers"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def print_hierarchy(hierarchy: dict):
    """Prints employee hierarchy in a formatted tree structure using recursion"""

    def gen_str(hierarchy: dict, indent: str = "", sep: str = ""):
        result = ""
        employee = hierarchy
        result += f"{indent}{sep}{employee['full_name']} ({employee['position']})\n"
        subordinates = employee["subordinates"]
        if not subordinates:
            return result
        if sep == "└── ":
            indent += "    "
        elif sep == "├── ":
            indent += "│   "
        for i, sb in enumerate(subordinates):
            is_last = i == len(subordinates) - 1
            if is_last:
                result += gen_str(hierarchy=sb, indent=indent, sep="└── ")
            else:
                result += gen_str(hierarchy=sb, indent=indent, sep="├── ")
        return result

    if not hierarchy:
        print(messages["errors"]["cli"]["empty_hierarchy"])
        return
    print(gen_str(hierarchy=hierarchy) + " ...")
