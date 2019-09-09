import asyncio
import async_timeout
import copy

from datetime import datetime
from hashlib import sha1

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'
}


def hash_item(item):
    return sha1(item.encode('utf8')).hexdigest()


async def fetch(session, url, params, retry=0):
    try:
        async with async_timeout.timeout(5):
            async with session.post(url, data=params, headers=HEADERS) as response:
                return await response.text(encoding='windows-1251')

    except (asyncio.TimeoutError, OSError) as err:
        retry += 1
        if retry > 30:
            raise TimeoutError()
        await asyncio.sleep(retry)
        return await fetch(session, url, params, retry=retry)


async def async_download_url(session, url, params={}):
    html = await fetch(session, url, params)
    return html


# Преобразует локализованную запись в datetime
def get_datetime(s):
    s = s.split(' ')
    local_months = [
        "января", "февраля", "марта", "апреля",
        "мая", "июня", "июля", "августа",
        "сентября", "октября", "ноября", "декабря"
    ]
    month = local_months.index(s[1])+1
    return datetime(int(s[2]), month, int(s[0]))


# Суммирование результатов участков
# Первый параметр может быть пустым словарём, на случай, если каркас словаря ещё не сформирван
def sum_results(data1, data2):
    if 'all' not in data2:
        return data2

    data_new = copy.deepcopy(data2)
    if 'candidates_lock' not in data_new:
        data_new['candidates_lock'] = False

    for k in data_new:
        if k == 'candidates_lock':
            continue

        if k in data1 and k != 'candidates':
            data_new[k] += data1[k]
        elif k == 'candidates' and 'candidates' in data1:
            # Если кандидаты одинаковые, то суммирование данных, иначе очистка на этом приближении территории
            # Если в data1 (куда суммируем) кандидатов ещё нет, то используем уже имеющееся в data_new
            if data1['candidates'].keys() == data2['candidates'].keys() and data1['candidates_lock'] is False:
                for candidate in data_new['candidates']:
                    data_new['candidates'][candidate] += data1['candidates'][candidate]
            else:
                data_new['candidates'] = {}
                data_new['candidates_lock'] = True

    if data_new['all'] == 0:
        data_new['calculated_share'] = 0
    else:
        data_new['calculated_share'] = round(float(data_new['invalid'] + data_new['valid']) / data_new['all'] * 100, 2)

    return data_new
