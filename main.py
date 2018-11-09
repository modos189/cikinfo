"""CikInfo

Usage:
  main.py
  main.py <function> [--date=<date>] [--urovproved=<urovproved>] [--region=<region>] [-y] [--no-start-info]

Examples:
  main.py update                      Get all elections
  main.py update --date=2018          Get elections in 2018
  main.py update --date=2018-09 -y    Get elections in 2018 09, not interact
  main.py update --date=2018-09-09    Get elections in year-month-day (ISO 8601)

urovproved - default: all, 1-4

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
db = client.cikinfo5

IZBIRKOM_URL = 'http://www.vybory.izbirkom.ru/region/izbirkom'
ELECTION_NAME = "Выборы Президента Российской Федерации"
ELECTION_DATE = "18 марта 2018 года"
START_URL = 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&global=1&vrn=100100084849062&region=0&prver=0&pronetvd=null'


# Производит рекурсивную загрузку страниц выборов, начиная областями и республиками, заканчивая сайтами ИК субъектов
async def parse_election_page(session, election_id, parent_pid, parent_num, parent_name, url,
                              level=0, debug=False, progressbar=False, _progressbar_lvl=0, _meta_exist=False, _pbar_inner=None):

    pbar = None
    sum_results = {}

    param = {'parent_id': parent_pid, 'num': parent_num, 'name': parent_name, 'level': level}
    if db.area.count(param):
        parent = db.area.find_one(param, {'results.' + election_id: True})
        if 'results' in parent and len(parent['results']) > 0:
            # Статистика уже сохранена, переход к следующей территории
            return parent['results'][election_id]
        parent_id = parent['_id']
    else:
        parent_id = db.area.insert_one(param).inserted_id

    html = await helpers.async_download_url(session, url)
    nodes = parse.selects(html)
    itog_url = parse.url_itog(html)
    # Если на странице существует ссылка на результаты выборов
    if itog_url:
        itog_html = await helpers.async_download_url(session, itog_url)

        # Если не указана мета-информация в документе выборов о полях, по которым возможна выборка, то добавление
        if not _meta_exist and not database.election_meta_exist(db, election_id):
            meta = parse.simple_table_meta(itog_html)
            database.add_election_meta(db, election_id, meta)
            _meta_exist = True

    # Перебор значений селектора под шапкой
    if nodes is not None:
        if progressbar and len(nodes) > 1 and _progressbar_lvl < 2:
            pbar = tqdm(total=len(nodes), desc=parent_name)
            _progressbar_lvl += 1

        if level < 1:
            for node in nodes:
                res = await parse_election_page(
                    session, election_id, parent_id, node.num, node.name, node.url,
                    level=level + 1, debug=debug, progressbar=progressbar,
                    _progressbar_lvl=_progressbar_lvl, _meta_exist=_meta_exist,
                    _pbar_inner=pbar
                )
                sum_results = helpers.sum_results(sum_results, res)
                if pbar:
                    pbar.update(1)

        else:
            limit_nodes = 30
            for small_nodes in [nodes[d:d+limit_nodes] for d in range(0, len(nodes), limit_nodes)]:
                tasks = [
                    asyncio.ensure_future(
                        parse_election_page(
                            session, election_id, parent_id, node.num, node.name, node.url,
                            level=level + 1, debug=debug, progressbar=progressbar,
                            _progressbar_lvl=_progressbar_lvl, _meta_exist=_meta_exist,
                            _pbar_inner=pbar
                        )
                    ) for node in small_nodes
                ]

                completed = await asyncio.gather(*tasks)
                for item in completed:
                    if len(item) > 0:
                        sum_results = helpers.sum_results(sum_results, item)
                    else:
                        print('\nнеполные данные\n')

    # Если на странице отсутствует селектор
    else:
        local_ik_url = parse.local_ik_url(html)
        # При этом есть ссылка на сайт избирательной комиссии субъекта РФ
        if local_ik_url is not None:
            html = await helpers.async_download_url(session, local_ik_url)

            itog_url = parse.url_local_itog(html)
            if itog_url:
                region = parse.get_region_from_subdomain_url(itog_url)
                itog_html = await helpers.async_download_url(session, itog_url)
                uiks = parse.two_dimensional_table(itog_html)

                for uik in uiks:
                    sum_results = helpers.sum_results(sum_results, uik.results)

                database.add_uik_results(db, election_id, region, parent_id, level+1, uiks)

    if pbar:
        pbar.close()

    db.area.update_one(param, {
        '$set': {'results.' + election_id: sum_results},
        '$addToSet': {'results_tags': election_id}
    })
    if _pbar_inner is not None:
        _pbar_inner.update(1)

    return sum_results


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

                # Обработка ключа --urovproved
                # По-умолчанию значение all
                if arguments['--urovproved'] is not None:
                    params['urovproved'] = arguments['--urovproved']

                # Обработка ключа --region
                # Скрипт получает все регионы, а затем фильтрует, удаляя все, кроме указанного региона.
                # Если не указано, то не фильтрует
                if arguments['--region'] is not None:
                    params['region_name'] = arguments['--region']

                # Загрузка списка выборов
                elections = await spider.get_elections(_session, IZBIRKOM_URL, params)
                print("Будет загружено", len(elections), "событий.")

                # Отключение интерактивного режима, если указан ключ --y
                if not arguments['-y']:
                    val = input("Хотите продолжить? [Д/н] ")
                    print(val)

                print("loading")

                # Перебор всех выборов
                for i, el in enumerate(elections, start=1):
                    print(i, '/', len(elections))
                    html = await helpers.async_download_url(_session, el['url'])
                    q = parse.get_elections_type(html)

                    if q[0] == 0 and q[1] == 0:
                        nodes = parse.selects(html)
                        if nodes is not None and len(nodes) > 0:
                            htq = await helpers.async_download_url(_session, nodes[-1].url)
                            q = parse.get_elections_type(htq)

                    if q[0] == 0 or q[0] != q[1]:
                        print(el['title'], el['url'], el['date'])
                        print(q)
                        return

                    # election_id = database.add_election(db, el['title'], el['url'], el['date'])
                    #
                    # if database.election_is_loaded(db, election_id):
                    #     continue
                    #
                    # await spider.download_election(
                    #     db, _session, election_id, None, None, 'Российская Федерация', el['url'],
                    #     debug=False, progressbar=True
                    # )

        else:
            print(__doc__)

        # elections = await spider.get_elections(session, IZBIRKOM_URL)
        # print(elections)
        # parse_election_page(
        #     session, helpers.hash_item(START_URL), None, None, 'Российская Федерация', START_URL,
        #     debug=False, progressbar=True
        # )


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        main()
    )

    # Первый этап - создание записи о выборах с названием и датой их проведения
    # database.add_election(
    #     db,
    #     ELECTION_NAME,
    #     START_URL,
    #     helpers.get_datetime(ELECTION_DATE)
    # )

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(
    #     # Второй этап - загрузка данных с сайта избиркома
    #     #download_data()
    #
    # )
    # Третий этап - соотнесение УИКов с из адресами в реальном мире
    # Готовый файл cik.sqlite можно взять по адресу: http://gis-lab.info/qa/cik-data.html
    # parse_address('cik.sqlite')
