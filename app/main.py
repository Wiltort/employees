from core.database import EmployeeCatalog
from core.settings import Settings
from core.cli.runner import cli_run


def main():
    catalog = EmployeeCatalog()
    cli_run()


if __name__ == "__main__":
    main()
