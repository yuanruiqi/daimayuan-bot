# app/config.py
import yaml
from pathlib import Path

CONFIG = yaml.safe_load(Path('config.yaml').read_text())

# 是否要改成 CONFIG.general.... 的形式？
