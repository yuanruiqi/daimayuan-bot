import os
import pickle
import threading
import logging
from datetime import timedelta
from collections.abc import MutableMapping
from app.config import CONFIG

logger = logging.getLogger(__name__)

class SaveDict(MutableMapping):#线程安全&保存
    def __init__(self, name: str, filepath: str, interval_minutes: float = CONFIG['models']['save_minute']):
        self.name = name
        self.filepath = filepath
        self._data = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._interval = timedelta(minutes=interval_minutes).total_seconds()
        
        self._load_data()
        # 启动后台线程，延迟 interval 后首次保存
        self._thread = threading.Thread(target=self._run_saver, daemon=True)
        self._thread.start()
        self._isclosed = False

    # —— MutableMapping 接口 —— #
    def __getitem__(self, key):
        with self._lock:
            return self._data[key]  # KeyError 会自然抛出

    def __setitem__(self, key, value):
        with self._lock:
            self._data[key] = value

    def __delitem__(self, key):
        with self._lock:
            del self._data[key]

    def __iter__(self):
        with self._lock:
            return iter(self._data.copy())

    def __len__(self):
        with self._lock:
            return len(self._data)

    def __contains__(self, key):
        with self._lock:
            return key in self._data

    # —— 其他可选扩展方法 —— #
    def clear(self):
        with self._lock:
            self._data.clear()

    def update(self, *args, **kwargs):
        with self._lock:
            self._data.update(*args, **kwargs)

    # —— 上下文管理 & 关闭 —— #
    def close(self):
        if not self._isclosed:
            """手动关闭：保存一次并停止后台线程。"""
            print(f"{self.name}: Shutting down; saving data and stopping thread.")
            self._stop_event.set()
            self._thread.join()
            self._save_data()
            try:
                self._save_data()
            except NameError:
                # 解析器关机阶段，builtins 里 open 已经不存在了
                print(f"{self.name}: Skipping save on shutdown (open() gone).")
            self._isclosed = True   
        else:
            print("Waring:save after closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        
    def __del__(self):
        self.close()

    # —— 背景持久化 —— #
    def _run_saver(self):
        # 第一次等完全周期后才第一次保存
        while not self._stop_event.wait(self._interval):
            self._save_data()

    def _save_data(self):
        # 拷贝数据，减少锁持有时长
        with self._lock:
            snapshot = dict(self._data)
        tmp_path = f"{self.filepath}.tmp"
        try:
            with open(tmp_path, 'wb') as f:
                pickle.dump(snapshot, f)
            os.replace(tmp_path, self.filepath)
            logger.info(f"{self.name}: Data atomically saved to {self.filepath}.")
        except Exception:
            logger.exception(f"{self.name}: Failed to save data to {self.filepath}.")

    def _load_data(self):
        if not os.path.exists(self.filepath):
            logger.info(f"{self.name}: No existing data file; starting fresh.")
            return
        try:
            with open(self.filepath, 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, dict):
                self._data = data
                logger.info(f"{self.name}: Data loaded from {self.filepath}.")
            else:
                logger.warning(f"{self.name}: Data file does not contain a dict; ignored.")
        except Exception:
            logger.exception(f"{self.name}: Failed to load data from {self.filepath}.") 