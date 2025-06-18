# app/config.py
import yaml
from pathlib import Path
from box import Box
from typing import cast

# 加载YAML配置为字典
CONFIG = cast(dict,yaml.safe_load(Path('config.yaml').read_text()))

# 转为Box对象，支持点操作
config = cast(Box, Box(CONFIG))  # type: ignore
