# 榜单任务管理与执行逻辑（SaveDict用于任务池，任务为普通对象）
from app.models import SaveDict
from app.services.down import create_session, get_contest_problems, get_cache, process_single_submission
from app.config import config
import time
import threading

# 全局只初始化一次，避免重复请求
_standing_session = create_session()
_standing_cache = get_cache()
_problem_map_cache = {}
def get_problem_map(contest_id):
    if contest_id not in _problem_map_cache:
        _problem_map_cache[contest_id] = get_contest_problems(_standing_session, contest_id) or {}
    return _problem_map_cache[contest_id]

def standing_get(submission_id, contest_id):
    problem_map = get_problem_map(contest_id)
    result, status = process_single_submission(_standing_session, submission_id, contest_id, _standing_cache, problem_map)
    if status == 'not_found':
        return 404
    if status != 'ok':
        return None
    return result

def standing_valid(result):
    return result is not None and isinstance(result, tuple) and len(result) == 4

def standing_push(results, result):
    results.append(result)

class StandingTask:
    def __init__(self, task_id, start_id, end_id, contest_id):
        self.task_id = task_id
        self.start_id = start_id
        self.end_id = end_id
        self.contest_id = contest_id
        self.status = 'pending'  # running, paused, completed, cancelled
        self.current_id = start_id
        self.data = []
        self.results = []
        self.create_time = time.time()
        self.done_time = 1e18

    def to_dict(self):
        d = {
            'task_id': self.task_id,
            'start_id': self.start_id,
            'end_id': self.end_id,
            'contest_id': self.contest_id,
            'status': self.status,
            'current_id': self.current_id,
            'results': self.results,
            'create_time': self.create_time,
            'done_time': self.done_time
        }
        return d

    @classmethod
    def from_dict(cls, d):
        obj = cls(d['task_id'], d['start_id'], d['end_id'], d['contest_id'])
        obj.status = d.get('status', 'pending')
        obj.current_id = d.get('current_id', d['start_id'])
        obj.results = d.get('results', [])
        obj.create_time = d.get('create_time', time.time())
        return obj

    def step(self, get_func, valid_func, push_func, should_pause_func=None):
        # print(self.status)
        if self.status=='pending':
            self.status='running'
            # print(1)
        if self.status=='completed':
            if not hasattr(self,'done_time'):
                self.done_time=1e18
            self.done_time=min(self.done_time,time.time())
            return
        if self.status != 'running':
            return
        if should_pause_func and should_pause_func(self):
            self.status = 'paused'
            return
        if self.current_id > self.end_id:
            self.status = 'completed'
            self.done_time=min(self.done_time,time.time())
            return
        result = get_func(self.current_id, self.contest_id)
        if result == 404:
            return
        if valid_func(result):
            push_func(self.results, result)
        self.current_id += 1
        if self.current_id > self.end_id:
            self.done_time=min(self.done_time,time.time())
            self.status = 'completed'

    def pause(self):
        if self.status == 'running':
            self.status = 'paused'

    def resume(self):
        if self.status == 'paused':
            self.status = 'running'

    def cancel(self):
        self.status = 'cancelled'

class StandingTaskManager:
    def __init__(self, save_name='standing_tasks'):
        self.tasks = SaveDict(save_name, f'databuf/{save_name}.pkl')
        for k, v in list(self.tasks.items()):
            if not isinstance(v, StandingTask):
                self.tasks[k] = StandingTask.from_dict(v)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def add_task(self, task):
        self.tasks[task.task_id] = task
        # 自动保存由 SaveDict 后台线程负责

    def start_task(self, task_id):
        task = self.tasks.get(task_id)
        if not task or task.status not in ['pending', 'paused']:
            return
        task.status = 'running'

    def pause_task(self, task_id):
        task = self.tasks.get(task_id)
        if task and task.status == 'running':
            task.pause()

    def cancel_task(self, task_id):
        task = self.tasks.get(task_id)
        if task:
            task.cancel()

    def delete_task(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]

    def step_all(self, get_func=standing_get, valid_func=standing_valid, push_func=standing_push, should_pause_func=None):
        for task in self.tasks.values():
            task.step(get_func, valid_func, push_func, should_pause_func)
        # 自动保存由 SaveDict 后台线程负责

    def _run_loop(self):
        while not self._stop_event.is_set():
            self.step_all()
            time.sleep(1)

    def handle_exit(self, signum, frame):
        for task in self.tasks.values():
            if task.status == 'running':
                task.pause()
        print('StandingTaskManager: graceful shutdown')
        self.tasks.close()

# --------- 榜单任务定期清理机制 ---------
def _cleanup_standing_tasks_thread(manager, interval=None, savetime=None):
    if interval is None:
        interval = getattr(config.task, 'cleanup_interval', 60)
    if savetime is None:
        savetime = getattr(config.task, 'savetime', 1200)
    while True:
        now = time.time()
        to_delete = []
        for tid, task in list(manager.tasks.items()):
            # 只清理已完成/取消/错误且超时的榜单任务
            done_time = getattr(task, 'done_time', getattr(task, 'donetime', getattr(task, 'create_time', 0)))
            if getattr(task, 'status', None) in ['completed', 'cancelled', 'error']:
                if now - done_time >= savetime:
                    to_delete.append(tid)
        for tid in to_delete:
            manager.delete_task(tid)
        time.sleep(interval)

def start_standing_task_cleanup(manager=None):
    if manager is None:
        from app.services.standing import standing_task_manager
        manager = standing_task_manager
    t = threading.Thread(target=_cleanup_standing_tasks_thread, args=(manager,), daemon=True)
    t.start()
    return t

# 全局唯一榜单任务管理器实例
standing_task_manager = StandingTaskManager()
