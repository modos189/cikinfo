import asyncio
from pymongo import MongoClient
from tqdm import tqdm
from modules import helpers, parse, database

client = MongoClient()
db = client.cikinfo5

START_URL = 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&global=1&vrn=100100084849062&region=0&prver=0&pronetvd=null'

database.add_election(
    db,
    "Выборы Президента Российской Федерации",
    START_URL,
    helpers.get_datetime("18 марта 2018 года")
)


# Производит рекурсивную загрузку страниц выборов, начиная областями и республиками, заканчивая сайтами ИК субъектов
async def parse_election_page(election_id, parent_pid, parent_num, parent_name, url,
                        level=0, debug=False, progressbar=False, _progressbar_lvl=0, _meta_exist=False, _pbar_inner=None):

    # html = await helpers.async_download_url('http://www.krasnoyarsk.vybory.izbirkom.ru/region/region/krasnoyarsk?action=show&root=242000042&tvd=2242000195400&vrn=100100022176412&region=24&global=true&sub_region=24&prver=0&pronetvd=null&vibid=2242000195400&type=227')
    # uiks = parse.two_dimensional_table(html)
    # print(uiks)
    # return

    if level == 1 and parent_name != 'Белгородская область':
        return {'0': 0}

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

    html = await helpers.async_download_url(url)
    nodes = parse.selects(html)
    itog_url = parse.url_itog(html)
    # Если на странице существует ссылка на результаты выборов
    if itog_url:
        itog_html = await helpers.async_download_url(itog_url)

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
                    election_id, parent_id, node.num, node.name, node.url,
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
                            election_id, parent_id, node.num, node.name, node.url,
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
                        print('блэд')

    # Если на странице отсутствует селектор
    else:
        local_ik_url = parse.local_ik_url(html)
        # При этом есть ссылка на сайт избирательной комиссии субъекта РФ
        if local_ik_url is not None:
            html = await helpers.async_download_url(local_ik_url)

            itog_url = parse.url_local_itog(html)
            if itog_url:
                region = parse.get_region_from_url(itog_url)
                itog_html = await helpers.async_download_url(itog_url)
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
    import sqlite3

    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    for reg in ['pskov', 'rostov', 'ryazan', 'samara', 'saratov', 'sakhalin', 'sverdlovsk', 'smolensk', 'tambov', 'tver', 'tomsk', 'tula', 'tyumen', 'ulyanovsk', 'chelyabinsk', 'yaroslavl', 'moscow_city', 'st-petersburg', 'jewish_aut', 'nenetsk', 'khantu-mansy', 'chukot', 'yamal-nenetsk', 'crimea', 'sevastopol']:

        nodes = list(db.area.find({'region': reg, 'max_depth': True}, {'num': True}))
        pbar = tqdm(total=len(nodes))
        for area in nodes:

            sql = "SELECT name, address FROM cik_uik WHERE region='"+reg+"' and `name` LIKE (?)"
            cursor.execute(sql, ['%№'+str(area['num'])])
            data = cursor.fetchone()
            if data is not None:
                db.area.update_one({'_id': area['_id']}, {'$set': {'address': data[1]}})
            else:
                print(area)

            pbar.update(1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        parse_election_page(
            helpers.hash_item(START_URL), None, None, 'Российская Федерация', START_URL,
            debug=False, progressbar=True
        )
    )

    # parse_address('cik.sqlite')
