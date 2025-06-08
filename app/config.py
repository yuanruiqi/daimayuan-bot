# app/config.py
import yaml
from pathlib import Path

CONFIG = yaml.safe_load(Path('config.yaml').read_text())

# 使用方式
# from app.config import CONFIG
# print(CONFIG['database']['host'])