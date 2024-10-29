import asyncio
import os
import aiohttp
import json
from bs4 import BeautifulSoup

from notify.notify import Notify
from notify.print import Print
from notify.telegram import Telegram


PATH_CLOSES = './closes'
FILE_LOG = 'result.txt'
SOLDED_PRINT = True
DEBUG = False


def booler_rus(bool: bool) -> str:
    return 'Да' if bool else 'Нет'


def booler_rus_tag(bool: bool) -> str:
    return f'<i>{booler_rus(bool)}</i>'


async def send_message(notis: list[Notify], *args, **kwargs):
    for notify in notis:
        result = await notify.message(*args, **kwargs)

        if result:
            return
        else:
            print(f'Cant send data uses {notify.__class__.__name__}')


async def main():
    service_url = os.getenv('SERVICE_URL').strip('/') if os.getenv('SERVICE_URL') else None
    service_token = os.getenv('SERVICE_TOKEN') if os.getenv('SERVICE_TOKEN') else None
    service_src = os.getenv('SERVICE_SRC') if os.getenv('SERVICE_SRC') else None
    channel_id = int(os.getenv('CHANNEL_ID')) if os.getenv('CHANNEL_ID') else None
    private_id = int(os.getenv('PRIVATE_ID')) if os.getenv('PRIVATE_ID') else None

    closes_old = {}

    client = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(verify_ssl=False),
    )

    notis = [
        Telegram(
            client=client,
            service_url=service_url,
            service_src=service_src,
            service_token=service_token,
        ),
        Print(),
    ]

    for f in os.listdir(PATH_CLOSES):
        with open(f'{PATH_CLOSES}/{f}', 'r+') as f_:
            data = json.load(f_)

            if data.get('sold') and SOLDED_PRINT:
                print(data)
            
            if not data.get('sold', False):
                closes_old[f.split('.')[0]] = data

    await send_message(
        notis=notis,
        client=client,
        text="старт парсера кладовок",
        channel=private_id,
    )

    data = []

    page = 1

    while True:
        res = await client.post(
            'https://www.lsr.ru/ajax/search/msk/',
            data = {
                'premiseType': 4,
                'price[min]': 0,
                'price[max]': 10,
                'price_range[min]': 0,
                'price_range[max]': 10,
                'obj[]': 52,
                'ob[page]': page,
                'ob[sort]': 'price',
                'ob[order]': 'asc',
                'group[t]': 'false',
                'ob[id]': 52,
                'object': 52,
                'premiseType': 4,
                'a': 'flats',
            },
        )

        result = await res.json()

        soup = BeautifulSoup(result['html'], 'html.parser')

        closed = soup.select('div.listingCard')

        if len(closed) == 0:
            break

        for cls in closed:
            name_block = cls.select_one('div.listingCard__label')
            advisory_name = name_block.text.strip() if name_block else ''
            info_block = cls.select_one('div.listingCard__main')

            datt = [f'Страница {page}\n', f'{advisory_name}\n']

            info = []

            for inf in info_block:
                strip = inf.text.strip()

                if len(strip) > 0:
                    info.append(strip)
            
            name = info[0]
            size = info[1]
            price = int(info[2].replace(' ', '').replace('₽', ''))
            
            full_data = {
                'name': name,
                'advisory_name': advisory_name,
                'page': page,
                'size': size,
                'price': price,
            }

            file_name = f'{PATH_CLOSES}/{full_data["name"]}.json'

            if (
                closes_old.get(name) and (
                    name != closes_old[name]['name'] or
                    size != closes_old[name]['size'] or
                    price != closes_old[name]['price'] or
                    closes_old[name].get('sold', False) != False
                )
            ):
                await send_message(
                    notis=notis,
                    client=client,
                    text=(
                        f"Старые данные:\nв продаже:{booler_rus_tag(not closes_old[name].get('sold', False))}\nназвание: {closes_old[name]['name']}\nразмер: {closes_old[name]['size']}\nцена: {closes_old[name]['price']}\n\nНовые данные:\nв продаже:{booler_rus_tag(True)}\nназвание: {name}\nразмер: {size}\nцена: {price}"
                    ),
                    channel=channel_id,
                )

                datt.append("!!!ALARM!!! были изменения по кладовке\n")

            with open(
                file=file_name,
                mode='w+',
                encoding='utf-8'
            ) as f:
                json.dump(
                    full_data, 
                    f, 
                    ensure_ascii=False,
                )

            if closes_old.get(name):
                del closes_old[name]
            else:
                await send_message(
                    notis=notis,
                    client=client,
                    text=(
                        f"Новая кладовка с данными:\nв продаже: {booler_rus_tag(True)}\nназвание: {name}\nразмер: {size}\nцена: {price}"
                    ),
                    channel=channel_id,
                )

                datt.append('!!!NEW!!! была добавлена новая кладовка\n')

            datt.append(" ".join(info))
            dat = "".join(datt)

            print_data = f'{dat}\n{"-"*10}'
            
            data.append(print_data)

            print(print_data)

        if DEBUG:
            return

        page += 1

    with open(file=FILE_LOG, mode='+w') as file_:
        file_.write('\n'.join(data))

    for clos in closes_old:
        closes_old[clos]['sold'] = True

        with open(f'{PATH_CLOSES}/{clos}.json', 'w+') as f:
            print(f'Была продана кладовка {clos}')

            await send_message(
                notis=notis,
                client=client,
                text=(
                    f"Была продана кладовка с данными:\nназвание: {closes_old[clos]['name']}\nразмер: {closes_old[clos]['size']}\nцена: {closes_old[clos]['price']}"
                ),
                channel=channel_id,
            )

            json.dump(
                closes_old[clos],
                f,
                ensure_ascii=False,
            )

    await send_message(
        notis=notis,
        client=client,
        text="конец парсера кладовок",
        channel=private_id,
    )

    await client.close()


if __name__ == '__main__':
    asyncio.run(main())
