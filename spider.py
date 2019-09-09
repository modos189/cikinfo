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
        'urovproved': [1, 2],
        'urovproved_all': [1, 2, 3, 4],

        # Вид выборов/референдумов и иных форм прямого волеизъявления:
        #   all - все
        #     0 - Референдум                    3 - Отзыв депутата
        #     1 - Выборы на должность           4 - Отзыв должностного лица
        #     2 - Выборы депутата
        'vidvibref': [0, 1, 2, 3, 4],
        'vidvibref_all': [0, 1, 2, 3, 4],

        # Тип выборов:
        #   all - все
        #   1 - Основные                        6 - Дополнительные повторные
        #   2 - Основные повторные              7 - Довыборы
        #   3 - Основные отложенные             8 - Повторное голосование
        #   4 - Основные отдельные              9 - Основные выборы и повторное голосование
        #   5 - Дополнительные
        # 'vibtype': "all",

        # Система выборов:
        #   all - все
        #   1 - мажоритарная
        #   2 - пропорциональная
        #   3 - смешанная - пропорциональная и мажоритарная
        #   4 - мажоритарная по общерегиональному округу
        #   5 - мажоритарная - по общерегиональному округу и по отдельным избирательным округам
        #   6 - пропорциональная и мажоритарная по общерегиональному округу и отдельным избирательным округам
        # 'sxemavib': "all",

        # actual_regions_subjcode
        # old_regions_subjcode
    }
    data.update(params)

    for key in ['urovproved', 'vidvibref']:
        if data[key] == ['all']:
            data[key] = data[key+"_all"]

    elections = []
    for urovproved in tqdm(data['urovproved']):

        fetch_data = data.copy()
        fetch_data.update({'urovproved': str(urovproved)})
        page_html = await helpers.async_download_url(session, url, fetch_data)
        items = parse.parse_list_elections(page_html, str(urovproved))

        # Фильтр региона, если пользователь указал желаемый
        if 'region_name' in params:
            items[:] = [el for el in items if el['region'][1] == params['region_name']]

        # Фильтр вида выборов/референдумов
        items[:] = [el for el in items if el['vidvibref'] in data['vidvibref']]

        elections.extend(items)

    elections = sorted(elections, key=lambda x: x['date'])

    return elections


# Производит рекурсивную загрузку страниц выборов, начиная областями и республиками, заканчивая сайтами ИК субъектов
async def download_election(db, _session, election_id, election_type, parent_pid, parent_num, parent_name, url,
                            level=0, debug=False, progressbar=False, _progressbar_lvl=0, _candidates=[],
                            _pbar_inner=None):
    pbar = None
    sum_results = {}

    param = {'parent_id': parent_pid, 'num': parent_num, 'name': parent_name, 'level': level}
    if db.area.count(param):
        parent = db.area.find_one(param, {'results.' + election_id + '.' + election_type: True})
        if 'results' in parent and election_id in parent['results'] and election_type in parent['results'][election_id]:
            # Статистика уже сохранена, переход к следующей территории
            return parent['results'][election_id][election_type]
        parent_id = parent['_id']
    else:
        parent_id = db.area.insert_one(param).inserted_id

    html = await helpers.async_download_url(_session, url)
    nodes = parse.selects(html)

    # Перебор значений селектора под шапкой
    if nodes is not None:
        if progressbar and len(nodes) > 1 and _progressbar_lvl < 2:
            pbar = tqdm(total=len(nodes), desc="%s [%s]" % (parent_name, election_type))
            _progressbar_lvl += 1

        if level < 1:
            for node in nodes:
                res = await download_election(
                    db, _session, election_id, election_type, parent_id, node.num, node.name, node.url,
                    level=level + 1, debug=debug, progressbar=progressbar,
                    _progressbar_lvl=_progressbar_lvl, _candidates=_candidates,
                    _pbar_inner=pbar
                )
                sum_results = helpers.sum_results(sum_results, res)
                # if pbar:
                #     print('+1, lvl:', level)
                #     pbar.update(1)

        else:
            limit_nodes = 30
            for small_nodes in [nodes[d:d + limit_nodes] for d in range(0, len(nodes), limit_nodes)]:
                tasks = [
                    asyncio.ensure_future(
                        download_election(
                            db, _session, election_id, election_type, parent_id, node.num, node.name, node.url,
                            level=level + 1, debug=debug, progressbar=progressbar,
                            _progressbar_lvl=_progressbar_lvl, _candidates=_candidates,
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
            itog_html = await helpers.async_download_url(_session, local_ik_url)
            region = parse.get_region_from_subdomain_url(local_ik_url)

            # itog_url = parse.url_local_itog(html)
            # if itog_url:
            #     region = parse.get_region_from_subdomain_url(itog_url)
            #     print(itog_url)
            #     itog_html = await helpers.async_download_url(_session, itog_url)

            meta = parse.table_meta(itog_html)
            uiks = parse.table_results(itog_html, meta)

            for uik in uiks:
                sum_results = helpers.sum_results(sum_results, uik['results'])

            database.add_uik_results(db, election_id, election_type, region, parent_id, level + 1, uiks)

    if pbar:
        pbar.close()

    if level == 0:
        database.set_election_start_area(db, election_id, parent_id)

    db.area.update_one(param, {
        '$set': {'results.' + election_id + '.' + election_type: sum_results},
        '$addToSet': {'results_tags': election_id}
    })
    if _pbar_inner is not None:
        _pbar_inner.update(1)

    return sum_results
