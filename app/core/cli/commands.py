from typing import List
from .localization import messages
from core.database import employee_catalog
from core.settings import settings
from core.cli.views import print_employees_table, print_hierarchy
from datetime import date


class CommandLine:
    def __init__(self):
        self.commands = [
            (method, getattr(self, method).__doc__)
            for method in dir(self)
            if callable(getattr(self, method)) and not method.startswith("_")
        ]
        self.should_exit = False
        self.fields = (
            "id",
            "name",
            "position",
            "date",
            "salary",
            "manager",
        )

    def gendb(self, options: List[str] | None = None):
        """Reset all data in database"""
        print(messages["ui"]["prompts"]["gen_data"])
        if options and len(options) == 1:
            if options[0] == "-a":
                employee_catalog.init_data(reset=False)
        else:
            employee_catalog.init_data()
        print(
            messages["ui"]["prompts"]["gen_data_complete"].format(
                n=settings.INITIAL_DATA_COUNT
            )
        )

    def help(self, options: List[str] | None = None):
        """Show avialable commands with descriptions"""
        if options and len(options) == 1:
            if "-v" == options[0]:
                print(messages["meta"]["version"])
                return
            elif "-a" == options[0]:
                print(messages["disclaimer"]["header"])
                print(messages["disclaimer"]["title"])
                print(
                    messages["disclaimer"]["copyright"].format(
                        year=messages["meta"]["year"], author=messages["meta"]["author"]
                    )
                )
            else:
                raise AttributeError('Incorrect option')
            print(messages["disclaimer"]["description"])
            print(messages["disclaimer"]["warning"])
            return
        space = " " * 4
        for name, desc in self.commands:
            if name in messages["commands"]:
                print(messages["commands"][name]["usage"])
                print(space + messages["commands"][name]["description"])
                if "options" in messages["commands"][name]:
                    print(space + messages["ui"]["info"]["options"])
                    for opt in messages["commands"][name]["options"]:
                        print(space + opt)
            else:
                description = desc.strip() if desc else "No description available"
                print(name)
                print(space + description)

    def empl(self, options: List[str] | None):
        """Prints employess list"""
        sort_opt = None
        sort_opts = []
        filter_opts = []
        arguments = {}
        if options:
            for opt in options:
                if "-s:" == opt[:3]:
                    sort_opt = opt[3:].split(":")
                    if len(sort_opt) == 1:
                        if sort_opt[0] in self.fields:
                            sort_opts.append(
                                {"order_field": sort_opt[0], "descending": False}
                            )
                        else:
                            raise ValueError(
                                messages["errors"]["cli"]["options"].format(
                                    opt=sort_opt[0]
                                )
                            )
                    elif len(sort_opt) == 2 and sort_opt[1] == "-d":
                        if sort_opt[0] in self.fields:
                            sort_opts.append(
                                {"order_field": sort_opt[0], "descending": True}
                            )
                        else:
                            raise ValueError(
                                messages["errors"]["cli"]["options"].format(
                                    opt=sort_opt[0]
                                )
                            )
                    else:
                        raise ValueError(
                            messages["errors"]["cli"]["options"].format(opt=sort_opt)
                        )
                elif "-f:" == opt[:3]:
                    filter_opt = opt[3:].split("=")
                    if len(filter_opt) != 2 or filter_opt[0] not in self.fields:
                        raise ValueError(
                            messages["errors"]["cli"]["options"].format(opt=filter_opt)
                        )
                    filter_opts.append({"field": filter_opt[0], "value": filter_opt[1].replace('_', ' ')})
                elif "-l:" == opt[:3]:
                    arguments["limit"] = int(opt[3:])
                else:
                    raise ValueError('Incorrect option')
        arguments["sort_opts"] = sort_opts
        arguments["filter_opts"] = filter_opts
        try:
            empls = employee_catalog.get_employees_list(**arguments)
        except Exception as e:
            print(e)
        else:
            if empls:
                print_employees_table(empls)
            else:
                print(messages["errors"]["cli"]["empty_table"])

    def quit(self, options: None):
        """Exit the application"""
        print(messages["ui"]["prompts"]["exit"])
        self.should_exit = True

    def tree(self, options: List[str] | None = None):
        """Prints employees hierarchy"""
        arguments = {}
        if options and len(options) == 1 and options[0][:3] == '-e:':
            arguments = {'root_id': int(options[0][3:])}
            arguments["limit"] = 30
        elif options and len(options) == 2 and options[0][:3] == '-e:':
            arguments = {'root_id': int(options[0][3:])}
            if options[1][:3] == '-l:':
                arguments["limit"] = int(options[1][3:])
        else:
            raise ValueError('Incorrect options')
        hierarchy = employee_catalog.get_hierarchy(**arguments)
        if hierarchy:
            print_hierarchy(hierarchy)
        else:
            print(messages["errors"]["cli"]["empty_hierarchy"])

    def add(self, options: List[str] | None = None):
        """Create new employee"""
        arguments = {'emp_data': {}}
        for option in options:
            if option[:3] == '-f:':
                field, value = option[3:].split('=')
                if field not in self.fields[1:]:
                    raise ValueError('Incorrect field')
                if field == 'name':
                    name_items = value.split('_')
                    name_fields = ['last_name', 'first_name', 'patronymic']
                    for i, v in enumerate(name_items):
                        arguments['emp_data'][name_fields[i]] = v
                elif field == 'salary':
                    arguments['emp_data'][field] = float(value)
                elif field == 'position':
                    arguments["emp_data"]['position_id'] = employee_catalog.get_position_id(value)
                elif field == 'manager':
                    arguments["emp_data"]['manager_id'] = int(value)
                elif field == 'date':
                    try:
                        year, month, day = map(int, value.split("-"))
                    except ValueError:
                        raise ValueError(messages['errors']['validation']['date'])
                    arguments["emp_data"]['hire_date'] = value
                else:
                    raise ValueError('Incorrect field')
        try:
            emp = employee_catalog.create_employee(**arguments)
            print(messages['success']['employee_added'].format(id=emp.id))
        except Exception as e:
            print(messages['errors']['database']['query'].format(error=e))

    def upd(self, options: List[str] | None = None):
        """Update employee"""
        arguments = {'emp_data': {}}
        for option in options:
            if option[:3] == '-e:':
                id = int(option[3:])
            if option[:3] == '-f:':
                field, value = option[3:].split('=')
                if field not in self.fields[1:]:
                    raise ValueError('Incorrect field')
                if field == 'name':
                    name_items = value.split('_')
                    name_fields = ['last_name', 'first_name', 'patronymic']
                    for i, v in enumerate(name_items):
                        arguments['emp_data'][name_fields[i]] = v
                elif field == 'salary':
                    arguments['emp_data'][field] = float(value)
                elif field == 'position':
                    arguments["emp_data"]['position_id'] = employee_catalog.get_position_id(value)
                elif field == 'manager':
                    arguments["emp_data"]['manager_id'] = int(value)
                elif field == 'date':
                    try:
                        year, month, day = map(int, value.split("-"))
                    except ValueError:
                        raise ValueError(messages['errors']['validation']['date'])
                    arguments["emp_data"]['hire_date'] = value
                else:
                    raise ValueError('Incorrect field')
        try:
            emp = employee_catalog.update_employee(id=id, **arguments)
            print(messages['success']['employee_added'].format(id=emp.id))
        except Exception as e:
            print(messages['errors']['database']['query'].format(error=e))