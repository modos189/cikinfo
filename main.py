from tqdm import tqdm
from modules import helpers, parse, database

START_URL = 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&global=1&vrn=100100067795849&region=0&prver=0&pronetvd=0'

database.add_election(
    "Выборы Президента Российской Федерации",
    START_URL,
    helpers.get_datetime("4 марта 2012 года")
)


# Производит рекурсивную загрузку страниц выборов, начиная областями и республиками, заканчивая сайтами ИК субъектов
def parse_election_page(election_id, area, url, debug=False, progressbar=False, _progressbar_lvl=0, _meta_exist=False):
    html = helpers.download_url(url)
    nodes = parse.selects(html)

    pbar = None
    itog_url = parse.url_itog(html)
    # Если на странице существует ссылка на результаты выборов
    if itog_url:
        itog_html = helpers.download_url(itog_url)

        # Если не указана мета-информация в документе выборов о полях, по которым возможна выборка, то добавление
        if not _meta_exist and not database.election_meta_exist(election_id):
            meta = parse.simple_table_meta(itog_html)
            database.add_election_meta(election_id, meta)
            _meta_exist = True

    database.add_election_results(area, None)

    # Россия - Результаты выборов по федеральному избирательному округу
    # Регионы - Итоги голосования по федеральному избирательному округу

    # Перебор значений селектора под шапкой
    if nodes is not None:
        if progressbar and len(nodes) > 1 and _progressbar_lvl < 2:
            pbar = tqdm(total=len(nodes), desc=area[-1][1])
            _progressbar_lvl += 1

        for node in nodes:
            if debug:
                helpers.print_area(area+[[node.num, node.name]])

            if len(area) == 1 and node.name not in ['Ненецкий автономный округ', 'Чукотский автономный округ', 'Ямало-Ненецкий автономный округ']:
                continue

            parse_election_page(election_id, area+[[node.num, node.name]], node.url,
                                debug=debug, progressbar=progressbar,
                                _progressbar_lvl=_progressbar_lvl, _meta_exist=_meta_exist)

            if pbar:
                pbar.update(1)

    # Если на странице отсутствует селектор
    else:
        local_ik_url = parse.local_ik_url(html)
        # При этом есть ссылка на сайт избирательной комиссии субъекта РФ
        if local_ik_url is not None:
            html = helpers.download_url(local_ik_url)

            itog_url = parse.url_local_itog(html)
            if itog_url:
                itog_html = helpers.download_url(itog_url)
                uiks = parse.two_dimensional_table(itog_html)

                for uik in uiks:
                    uik.results['election_id'] = election_id
                    database.add_election_results(area + [[uik.num, uik.name]], uik.results, True)

    if pbar:
        pbar.close()

# parse_election_page(
#    helpers.hash_item(START_URL), [[None, 'Российская Федерация']], START_URL,
#    debug=False, progressbar=True
# )
#print(START_URL)
#print(helpers.hash_item(START_URL))
database.calc_stat(helpers.hash_item(START_URL))


# db.area.update({'_id': ObjectId('5a74bcedc4806b609150af2d')}, {'$unset': {'results.2':1}})
# db.area.update({'_id': ObjectId('5a74bcedc4806b609150af2d')}, {'$pull': {'results': None}})
