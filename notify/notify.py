class Notify:
    def __init__(self, *args, **kwargs):
        pass

    async def message(self, *args, text: str, **kwargs) -> bool:
        raise Exception("UnImplemented")
    