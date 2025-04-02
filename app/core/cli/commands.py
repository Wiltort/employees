from typing import List
from .localization import messages
from core.database import employee_catalog
from core.settings import settings
from core.cli.views import print_employees_table

class CommandLine:
    fields = (
        'id',
        'name',
        'position',
        'date',
        'salary',
        'manager',
    )
    def __init__(self):
        self.commands = [
            (method, getattr(self, method).__doc__)
            for method in dir(self)
            if callable(getattr(self, method)) and not method.startswith("_")
        ]
        self.should_exit = False
        self.fields = (
            'id',
            'name',
            'position',
            'date',
            'salary',
            'manager',
        )

    def gendb(self, options: List[str] | None = None):
        """Reset all data in database"""
        print(messages['ui']['prompts']['gen_data'])
        if options and len(options) == 1:
            if options[0] == '-a':
                employee_catalog.init_data(reset=False)
        else:
            employee_catalog.init_data()
        print(messages['ui']['prompts']['gen_data_complete'].format(n=settings.INITIAL_DATA_COUNT))
        
    
    def help(self, options: List[str] | None = None):
        """Show avialable commands with descriptions"""
        if options and len(options) == 1:
            if '-v' == options[0]:
                print(messages['meta']['version'])
                return
            elif '-a' == options[0]:
                print(messages['disclaimer']['header'])
                print(messages['disclaimer']['title'])
                print(messages['disclaimer']['copyright'].format(
                    year=messages['meta']['year'],
                    author=messages['meta']['author']
                ))
            else:
                raise AttributeError(msg)
            print(messages['disclaimer']['description'])
            print(messages['disclaimer']['warning'])
            return
        space = ' ' * 4
        for name, desc in self.commands:
            if name in messages['commands']:
                print(messages['commands'][name]['usage'])
                print(space + messages['commands'][name]['description'])
                if 'options' in messages['commands'][name]:
                    print(space + messages['ui']['info']['options'])
                    for opt in messages['commands'][name]['options']:
                        print(space + opt)
            else:
                description = desc.strip() if desc else "No description available"
                print(name)
                print(space + description)

    def empl(self, options: List[str] | None):
        """Prints employess list"""
        sort_opt = None
        filter_opts = []
        limit_opt = 10
        arguments = {}
        if options:
            for opt in options:
                if '-s:' in opt:
                    sort_opt = opt[3:].split(':')
                    if len(sort_opt) == 1:
                        if sort_opt[0] in self.fields:
                            arguments['order_field'] = sort_opt[0]
                        else:
                            ValueError(messages['errors']['cli']['options'].format(opt=sort_opt[0]))
                    elif len(sort_opt) == 2:
                        if sort_opt[0] in self.fields:
                            arguments['order_field'] = sort_opt[0]
                        else:
                            ValueError(messages['errors']['cli']['options'].format(opt=sort_opt[0]))
                        if sort_opt[1] == '-d':
                            arguments['descending'] = True
                        else:
                            ValueError(messages['errors']['cli']['options'].format(opt=sort_opt[1]))
                    else:
                        ValueError(messages['errors']['cli']['options'].format(opt=sort_opt))
                if '-f:' in opt:
                    filter_opts.append(opt)
        print(arguments)
        empls = employee_catalog.get_employees_list(**arguments)
        print_employees_table(empls)


    def quit(self, options: None):
        """Exit the application"""
        print(messages['ui']['prompts']['exit'])
        self.should_exit = True