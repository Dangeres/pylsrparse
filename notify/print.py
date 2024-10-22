from notify.notify import Notify


class Print(Notify):
    async def message(self, *args, **kwargs) -> bool:
        print(f'{args=} {kwargs=}')

        return True
    