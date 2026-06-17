"""Static assets (icons) bundled with the GUI dialogs."""
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent
ICON_PNG = ASSETS_DIR / "tag.png"
ICON_ICO = ASSETS_DIR / "tag.ico"
