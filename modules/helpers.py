import requests
from time import sleep
from datetime import datetime
from hashlib import sha1

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
}


def print_area(_area):
    print([item[1] for item in _area])


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
