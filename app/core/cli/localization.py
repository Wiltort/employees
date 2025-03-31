import yaml
from pathlib import Path
from typing import Dict, Any
from core.settings import settings


def load_messages() -> Dict[str, Any]:
    """Returns dict of text message patterns"""
    path = Path(__file__).parent.parent.parent / "locales"
    if not path.exists():
        raise FileNotFoundError("Folder 'locales' is not found")
    file = path / f'messages_{settings.LANGUAGE}.yml'
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise RuntimeError(f"File {file} not found")
