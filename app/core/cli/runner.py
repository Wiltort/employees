from core.settings import settings
from core.cli.commands import CommandLine
from .localization import load_messages


def cli_run():
    messages = load_messages()
    cli = CommandLine()
    print(messages['disclaimer']['header'])
    print(messages['disclaimer']['title'])
    print(messages['disclaimer']['copyright'].format(
        year=messages['meta']['year'],
        author=messages['meta']['author']
    ))
    print(messages['disclaimer']['description'])
    print(messages['disclaimer']['warning'])
    print(messages['disclaimer']['help_prompt'])