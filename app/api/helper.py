

from functools import lru_cache


@lru_cache()
def read_html_file(file, encoding='utf-8'):
    with open(file, 'r', encoding=encoding) as f:
        return f.read()

