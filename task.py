

from hashlib import md5
from request import TaskRequest

tasks = {}


class Task:
    def __init__(self, key, url, **kwargs):
        self.key = key
        self.request = TaskRequest(url, **kwargs)

    def get_key(self):
        return self.key

    def __repr__(self):
        return f'<Task key={self.key}>'


def new_task(url, **kwargs):
    global tasks

    key = md5(url.encode('utf-8')).hexdigest()
    if key in tasks:
        return None
    tasks[key] = Task(key, url, **kwargs)
    return key




