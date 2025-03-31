from core.settings import settings
from core.cli.commands import CommandLine


def cli_run():
    cli = CommandLine()
    print(cli.commands)
    cli.list_commands()
