import aiohttp
import asyncio
import async_timeout

import requests
from time import sleep
from datetime import datetime
from hashlib import sha1

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
}


def hash_item(item):
    return sha1(item.encode('utf8')).hexdigest()


async def fetch(session, url, retry=0):
    try:
        async with async_timeout.timeout(5):
            async with session.get(url, headers=HEADERS) as response:
                return await response.text(encoding='windows-1251')

    except asyncio.TimeoutError:
        retry += 1
        if retry > 30:
            raise TimeoutError()
        await asyncio.sleep(retry)
        return await fetch(session, url, retry=retry)

async def async_download_url(url):
        async with aiohttp.ClientSession() as session:
            html = await fetch(session, url)
            return html


# Преобразует локализованную запись в datetime
def get_datetime(s):
    s = s.split(' ')
    local_months = [
        "января", "февраля", "марта", "апреля",
        "мая", "июня", "июля", "августа",
        "сентября", "октября", "ноября", "декабря"
    ]
    month = local_months.index(s[1])
    return datetime(int(s[2]), month, int(s[0]))


# Суммирование результатов участков
# Первый параметр может быть пустым словарём, на случай, если каркас словаря ещё не сформирван
def sum_results(data1, data2):
    data_new = data2.copy()
    for k in data_new:
        if k in data1:
            data_new[k] += data1[k]

    if data_new['0'] == 0:
        data_new['share'] = 0
    else:
        data_new['share'] = round(float(data_new['6'] + data_new['7']) / data_new['0'] * 100, 2)

    return data_new
