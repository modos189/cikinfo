from tqdm import tqdm
import asyncio
from modules import helpers, parse, database


# Возвращает массив всех выборов. Опционально с передачей параметров
async def get_elections(session, url, params=None):
    if params is None:
        params = {}

    data = {
        'action': "search_by_calendar",
        'region': "0",
        'start_date': "01.09.2018",
        'end_date': "01.01.2019",

        # Уровень выборов:
        #   all - все
        #     1 - Федеральный                   3 - Административный центр
        #     2 - Региональный                  4 - Местное самоуправление
        'urovproved': "all",

        # Вид выборов/референдумов и иных форм прямого волеизъявления:
        #   all - все
        #     0 - Референдум                    3 - Отзыв депутата
        #     1 - Выборы на должность           4 - Отзыв должностного лица
        #     2 - Выборы депутата
        'vidvibref': "all",

        # Тип выборов:
        #   all - все
        #   1 - Основные                        6 - Дополнительные повторные
        #   2 - Основные повторные              7 - Довыборы
        #   3 - Основные отложенные             8 - Повторное голосование
        #   4 - Основные отдельные              9 - Основные выборы и повторное голосование
        #   5 - Дополнительные
        'vibtype': "all",

        # Система выборов:
        #   all - все
        #   1 - мажоритарная
        #   2 - пропорциональная
        #   3 - смешанная - пропорциональная и мажоритарная
        #   4 - мажоритарная по общерегиональному округу
        #   5 - мажоритарная - по общерегиональному округу и по отдельным избирательным округам
        #   6 - пропорциональная и мажоритарная по общерегиональному округу и отдельным избирательным округам
        'sxemavib': "all",

        # actual_regions_subjcode
        # old_regions_subjcode
    }
    data.update(params)

    if data['urovproved'] == 'all':
        list_urovproved = range(1, 5)
    elif type(data['urovproved']) == 'list':
        list_urovproved = data['urovproved']
    else:
        list_urovproved = [data['urovproved']]

    elections = []
    for urovproved in list_urovproved:
        data['urovproved'] = str(urovproved)
        page_html = await helpers.async_download_url(session, url, data)
        item = parse.parse_list_elections(page_html, data['urovproved'])

        # Пропуск, если указан
        # Там список. Надо другим образом фильровать
        if params['region_name'] is not None and item['region'][1] != params['region_name']:
            continue

        elections.extend(item)

    elections = sorted(elections, key=lambda x: x['date'])

    return elections


# Производит рекурсивную загрузку страниц выборов, начиная областями и республиками, заканчивая сайтами ИК субъектов
async def download_election(db, _session, election_id, parent_pid, parent_num, parent_name, url,
                            level=0, debug=False, progressbar=False, _progressbar_lvl=0, _meta_exist=False,
                            _pbar_inner=None):
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

    html = await helpers.async_download_url(_session, url)
    nodes = parse.selects(html)
    itog_url = parse.url_itog(html)
    # Если на странице существует ссылка на результаты выборов
    if itog_url:
        itog_html = await helpers.async_download_url(_session, itog_url)

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
                res = await download_election(
                    _session, election_id, parent_id, node.num, node.name, node.url,
                    level=level + 1, debug=debug, progressbar=progressbar,
                    _progressbar_lvl=_progressbar_lvl, _meta_exist=_meta_exist,
                    _pbar_inner=pbar
                )
                sum_results = helpers.sum_results(sum_results, res)
                if pbar:
                    pbar.update(1)

        else:
            limit_nodes = 30
            for small_nodes in [nodes[d:d + limit_nodes] for d in range(0, len(nodes), limit_nodes)]:
                tasks = [
                    asyncio.ensure_future(
                        download_election(
                            _session, election_id, parent_id, node.num, node.name, node.url,
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
            html = await helpers.async_download_url(_session, local_ik_url)

            itog_url = parse.url_local_itog(html)
            if itog_url:
                region = parse.get_region_from_subdomain_url(itog_url)
                itog_html = await helpers.async_download_url(_session, itog_url)
                uiks = parse.two_dimensional_table(itog_html)

                for uik in uiks:
                    sum_results = helpers.sum_results(sum_results, uik.results)

                database.add_uik_results(db, election_id, region, parent_id, level + 1, uiks)

    if pbar:
        pbar.close()

    db.area.update_one(param, {
        '$set': {'results.' + election_id: sum_results},
        '$addToSet': {'results_tags': election_id}
    })
    if _pbar_inner is not None:
        _pbar_inner.update(1)

    return sum_results
