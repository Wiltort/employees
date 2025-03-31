from typing import List
from .localization import messages

class CommandLine:
    def __init__(self):
        self.commands = [
            (method, getattr(self, method).__doc__)
            for method in dir(self)
            if callable(getattr(self, method)) and not method.startswith("_")
        ]
        self.should_exit = False

    def reset_data(self):
        """Reset all data in database"""
        pass
    
    def help(self, options: List[str] | None = None):
        """Show avialable commands with descriptions"""
        print("Available commands:")
        for name, desc in self.commands:
            description = desc.strip() if desc else "No description available"
            print(f"- {name}: {description}")

    def quit(self, options: None):
        """Exit the application"""
        print(messages['ui']['prompts']['exit'])
        self.should_exit = True