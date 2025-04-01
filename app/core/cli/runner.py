from core.settings import settings
from core.cli.commands import CommandLine
from .localization import messages


def cli_run():
    cli = CommandLine()
    print(messages['disclaimer']['header'])
    print(messages['disclaimer']['title'])
    print(messages['disclaimer']['help_prompt'])
    while not cli.should_exit:
        input_line = input('>>> ').split()
        input_command = input_line[0]
        if len(input_line) > 1:
            options = input_line[1:]
        else:
            options = None
        try:
            eval(f'cli.{input_command}(options={options})')
        except AttributeError as e:
            print(e)
            print(messages['errors']['cli']['command'], input_command)
