class LazyModel:
    def __init__(self, factory):
        self._factory = factory
        self._instance = None

    async def get(self):
        if self._instance is None:
            inst = self._factory()
            if callable(getattr(inst, "__await__", None)):
                self._instance = await inst
            else:
                self._instance = inst
        return self._instance

    def __getattr__(self, name):
        if self._instance is None:
            raise RuntimeError("Model not initialized yet")
        return getattr(self._instance, name)
