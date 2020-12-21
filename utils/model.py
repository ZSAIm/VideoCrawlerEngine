

from pydantic import Field
from functools import partial


DefaultField = partial(Field, default=None)