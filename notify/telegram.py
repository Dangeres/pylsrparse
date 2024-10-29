import aiohttp

from notify.notify import Notify


class Telegram(Notify):
    def __init__(
            self,
            *args,
            client: aiohttp.ClientSession | None = None,
            service_url: str | None = None,
            service_src: str | None = None,
            service_token: str | None = None,
            **kwargs,
    ):
        self.client = client
        self.service_url = service_url
        self.service_src = service_src
        self.service_token = service_token


    async def message(self, *args, text: str, channel: int | None = None, **kwargs) -> bool:
        if (
            self.client is None or 
            self.service_token is None or
            self.service_src is None or
            self.service_url is None or
            channel is None
        ):
            return False

        async with self.client.post(
            url=f'{self.service_url}/v1/message/random/create', 
            json={
                "channel_id": channel,
                "text": text,
            },
            headers={
                'Token': self.service_token,
                'Src': self.service_src,
            }
        ) as resp:
            print(f'Result for sending telegram bot status code {resp.status}')

            return resp.status == 200
                