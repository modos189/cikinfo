"""CikInfo

Usage:
  main.py
  main.py <function> [--date=<date>] [--urovproved=<urovproved>] [--vidvibref=<vidvibref>] [--region=<region>] [-y] [--no-start-info]

Examples:
  main.py update                      Get elections in current year
  main.py update --date=2018          Get elections in 2018
  main.py update --date=2018-09 -y    Get elections in 2018 09, not interact
  main.py update --date=2018-09-09    Get elections in year-month-day (ISO 8601)

--urovproved - 1,2,3,4. Default: 1,2

--vidvibref - 0,1,2,3,4. Default: all

Options:
  -h --help
  -q       quiet mode
"""
from datetime import datetime
from docopt import docopt
import asyncio
import aiohttp
from git import Repo
import time
from pymongo import MongoClient
from tqdm import tqdm
from modules import helpers, parse, database
from pathlib import Path
import spider

client = MongoClient()
db = client.cikinfo

IZBIRKOM_URL = 'http://www.vybory.izbirkom.ru/region/izbirkom'


def parse_address(filename):
    address_file = Path(filename)

    if address_file.is_file():
        import sqlite3

        conn = sqlite3.connect(filename)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT region FROM cik_uik")
        regions_raw = cursor.fetchall()

        for reg in [region[0] for region in regions_raw]:

            nodes = list(db.area.find({'region': reg, 'max_depth': True, 'address': {'$exists': False}}, {'num': True}))
            pbar = tqdm(total=len(nodes))
            for area in nodes:

                sql = "SELECT name, address FROM cik_uik WHERE region='"+reg+"' and `name` LIKE (?)"
                cursor.execute(sql, ['%№'+str(area['num'])])
                data = cursor.fetchone()
                if data is not None:
                    db.area.update_one({'_id': area['_id']}, {'$set': {'address': data[1]}})

                pbar.update(1)


async def main():
    async with aiohttp.ClientSession() as _session:
        arguments = docopt(__doc__)

        if not arguments['--no-start-info']:
            repo = Repo(search_parent_directories=True)
            head_commit = repo.head.commit
            print("CikInfoServer --- commit hash", head_commit.hexsha,
                  "(", time.strftime("%d %b %Y %H:%M", time.gmtime(head_commit.committed_date)), ")")

        if arguments['<function>'] is not None and arguments['<function>'] in ['update']:
            # Пока только одна функция, обновление базы выборов
            if arguments['<function>'] == 'update':
                params = {}

                # Обработка ключа --date
                # Если не указано, то получаем выборы за текущий год
                if arguments['--date'] is None:
                    year = str(datetime.today().year)
                    date_range = {'start_date': '01.01.'+year, 'end_date': '31.12.'+year}
                else:
                    date_range = parse.get_start_end_date(arguments['--date'])
                if date_range is None:
                    print("Неверно указан ключ --data")
                    return
                params.update(date_range)

                # Обработка числовых ключей
                for key in ['urovproved', 'vidvibref']:
                    if arguments['--'+key] is not None:
                        params[key] = arguments['--'+key].split(",")

                # Обработка ключа --region
                # Скрипт получает все регионы, а затем фильтрует, удаляя все, кроме указанного региона.
                # Если не указано, то не фильтрует
                if arguments['--region'] is not None:
                    params['region_name'] = arguments['--region']

                # Загрузка списка выборов
                elections = await spider.get_elections(_session, IZBIRKOM_URL, params)

                print()
                for i, el in enumerate(elections, start=1):
                    print("%i [%s] %s" % (i, el['date'].date(), el['title']))

                print("Будет загружено", len(elections), "событий.")

                # Отключение интерактивного режима, если указан ключ --y
                if not arguments['-y']:
                    val = input("0 - Отмена; A (по-умолчанию) - Скачать все; Либо номер выборов: ")
                    if val.isdigit() is False and val.lower() not in ['', 'a', 'а'] or val == '0':
                        return
                    elif val.isdigit() is True:
                        elections = [elections[int(val)-1]]

                # Перебор всех выборов
                for i, el in enumerate(elections, start=1):
                    print(i, '/', len(elections))
                    html = await helpers.async_download_url(_session, el['url'])
                    sub_elections = parse.get_elections_type(html)

                    if sub_elections['status'] and len(sub_elections['types']) == 0:
                        nodes = parse.selects(html)
                        if nodes is not None and len(nodes) > 0:
                            htq = await helpers.async_download_url(_session, nodes[-1].url)
                            sub_elections = parse.get_elections_type(htq)

                    if not sub_elections['status'] or len(sub_elections['types']) == 0:
                        print('ВНИМАНИЕ: Ошибка при определении типов выборов:')
                        print(el['title'], el['url'], el['date'])

                        if not arguments['-y']:
                            val = input("Всё равно продолжить? [Y/n] ")
                            if val != "" and val.lower() != "y":
                                return
                        print('Проигнорировано.')

                    # тут надо уже парсить результаты, чё

                    election_id = database.add_election(db, el['title'], el['url'], el['date'], list(sub_elections['types'].keys()))

                    for election_type, url in sub_elections['types'].items():
                        await spider.download_election(
                            db, _session, election_id, election_type, None, None, el['region'][-1], url,
                            debug=False, progressbar=True
                        )

        else:
            print(__doc__)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        main()
    )

    # Соотнесение УИКов с из адресами в реальном мире
    # Готовый файл cik.sqlite можно взять по адресу: http://gis-lab.info/qa/cik-data.html
    # parse_address('cik.sqlite')
