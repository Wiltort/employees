class CommandLine:
    def __init__(self):
        self.commands = [
            (method, getattr(self, method).__doc__)
            for method in dir(self)
            if callable(getattr(self, method)) and not method.startswith("_")
        ]

    def reset_data(self):
        """Reset all data in database"""
        pass
    
    def list_commands(self):
        """Show avialable commands with descriptions"""
        print("Available commands:")
        for name, desc in self.commands:
            description = desc.strip() if desc else "No description available"
            print(f"- {name}: {description}")