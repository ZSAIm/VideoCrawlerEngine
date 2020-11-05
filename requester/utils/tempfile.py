import os
import shutil
from collections import defaultdict
from functools import partial
import debugger as dbg


class TemporaryFile:
    def __init__(self, filepath):
        """
        Initialize the filepath.

        Args:
            self: (todo): write your description
            filepath: (str): write your description
        """
        self.filepath = filepath
        self.fp = None

    @property
    def basename(self):
        """
        Returns the path of the file.

        Args:
            self: (todo): write your description
        """
        return os.path.basename(self.filepath)

    @property
    def dirname(self):
        """
        Returns the full path to the directory.

        Args:
            self: (todo): write your description
        """
        return os.path.dirname(self.filepath)

    def __call__(self, mode, **kwargs):
        """
        Call a file - like the given mode.

        Args:
            self: (todo): write your description
            mode: (str): write your description
        """
        fp = open(self.filepath, mode, **kwargs)
        self.fp = fp
        return fp

    open = __call__


class TemporaryDir:
    def __init__(self, tempdir):
        """
        Initialize the history.

        Args:
            self: (todo): write your description
            tempdir: (str): write your description
        """
        self.tempdir = os.path.abspath(tempdir)
        self._history = defaultdict(partial(defaultdict, list))

    def mktemp(self, extension=''):
        """
        Create a temporary directory.

        Args:
            self: (todo): write your description
            extension: (str): write your description
        """
        abcde = '-'.join(str(i) for i in dbg.abcde)
        nameonly = f"{abcde}[{len(self._history)}].{dbg.glb.script['title']}"

        filepath = os.path.realpath(os.path.join(
            self.tempdir,
            f'{nameonly}.{extension.lstrip(".")}'
        ))
        # fp = open(filepath, mode=mode, **kwargs)
        self._history[dbg.b][dbg.abcde].append(filepath)
        if not os.path.isdir(self.tempdir):
            os.makedirs(self.tempdir)
        return TemporaryFile(filepath)

    def rmdir(self):
        """ 删除整个临时目录树。"""
        shutil.rmtree(self.tempdir)

    def rmfiles(self, ignore_error=False):
        """ 删除由该对象创建的临时文件。"""
        for k, v in self._history[dbg.b].items():
            for i in v:
                try:
                    os.unlink(i)
                except:
                    from traceback import print_exc
                    if not ignore_error:
                        raise
