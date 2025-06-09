# app/config.py
import yaml
from pathlib import Path
from box import Box
from typing import cast

CONFIG = yaml.safe_load(Path('config.yaml').read_text())

config = cast(Box, Box(CONFIG))  # type: ignore
