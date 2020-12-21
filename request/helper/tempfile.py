import os
import shutil
from collections import defaultdict
from functools import partial
from utils.common import cat_a5g
from helper.ctxtools import ctx


class TemporaryFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.fp = None

    @property
    def basename(self):
        return os.path.basename(self.filepath)

    @property
    def dirname(self):
        return os.path.dirname(self.filepath)

    def __call__(self, mode, **kwargs):
        fp = open(self.filepath, mode, **kwargs)
        self.fp = fp
        return fp

    open = __call__


class TemporaryDir:
    def __init__(self, tempdir):
        self.tempdir = os.path.abspath(tempdir)
        self._history = defaultdict(partial(defaultdict, list))

    def mktemp(self, extension=''):
        nameonly = f"{cat_a5g(ctx.a5g)}[{len(self._history[ctx.b][ctx.a5g])}].{ctx.glb.script['title']}"

        filepath = os.path.realpath(os.path.join(
            self.tempdir,
            f'{nameonly}.{extension.lstrip(".")}'
        ))
        # fp = open(filepath, mode=mode, **kwargs)
        self._history[ctx.b][ctx.a5g].append(filepath)
        if not os.path.isdir(self.tempdir):
            os.makedirs(self.tempdir)
        return TemporaryFile(filepath)

    def rmdir(self):
        """ 删除整个临时目录树。"""
        shutil.rmtree(self.tempdir)

    def rmfiles(self, ignore_error=False):
        """ 删除由该对象创建的临时文件。"""
        for k, v in self._history[ctx.b].items():
            for i in v:
                try:
                    os.unlink(i)
                except:
                    from traceback import print_exc
                    if not ignore_error:
                        raise
