# 榜单任务管理与执行逻辑（SaveDict用于任务池，任务为普通对象）
from app.models import SaveDict
import signal

class StandingTask:
    def __init__(self, task_id, start_id, end_id, contest_id):
        self.task_id = task_id
        self.start_id = start_id
        self.end_id = end_id
        self.contest_id = contest_id
        self.status = 'pending'  # running, paused, finished, cancelled
        self.current_id = start_id
        self.results = []

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'start_id': self.start_id,
            'end_id': self.end_id,
            'contest_id': self.contest_id,
            'status': self.status,
            'current_id': self.current_id,
            'results': self.results,
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls(d['task_id'], d['start_id'], d['end_id'], d['contest_id'])
        obj.status = d.get('status', 'pending')
        obj.current_id = d.get('current_id', d['start_id'])
        obj.results = d.get('results', [])
        return obj

    def step(self, get_func, valid_func, push_func, should_pause_func=None):
        if self.status != 'running':
            return
        if should_pause_func and should_pause_func(self):
            self.status = 'paused'
            return
        if self.current_id > self.end_id:
            self.status = 'finished'
            return
        result = get_func(self.current_id, self.contest_id)
        if result != 404 and valid_func(result):
            push_func(self.results, result)
        self.current_id += 1
        if self.current_id > self.end_id:
            self.status = 'finished'

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
        self.tasks = SaveDict(save_name, f'cache/{save_name}.pkl')
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)
        # 恢复任务对象
        for k, v in list(self.tasks.items()):
            if not isinstance(v, StandingTask):
                self.tasks[k] = StandingTask.from_dict(v)

    def add_task(self, task):
        self.tasks[task.task_id] = task

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

    def step_all(self, get_func, valid_func, push_func, should_pause_func=None):
        for task in self.tasks.values():
            if task.status == 'running':
                task.step(get_func, valid_func, push_func, should_pause_func)

    def handle_exit(self, signum, frame):
        for task in self.tasks.values():
            if task.status == 'running':
                task.pause()
        print('StandingTaskManager: graceful shutdown')
        self.tasks.close()
