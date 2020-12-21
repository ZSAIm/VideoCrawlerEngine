

class BaseLayer:
    """ """
    NAME: str

    async def run(self, *args, **kwargs):
        raise NotImplementedError

    async def stop(self):
        raise NotImplementedError

    def setpoint(self):
        raise NotImplementedError

    def __enter__(self):
        self.setpoint()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if any([exc_type, exc_val, exc_tb]):
            raise