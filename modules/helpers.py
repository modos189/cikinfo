import requests
from time import sleep
from datetime import datetime
from hashlib import sha1

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
}


def hash_item(item):
    return sha1(item.encode('utf8')).hexdigest()


def _download_url(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )
        return response.content.decode('windows-1251')
    except requests.RequestException:
        return None


def download_url(url):
    html = None
    for i in range(5):
        html = _download_url(url)
        # в случае ошибки доступа к сайту повтор попытки
        if html is None:
            sleep(30)
        else:
            break
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
