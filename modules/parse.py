# coding=utf-8
from bs4 import BeautifulSoup
from collections import namedtuple
import calendar
from . import helpers

RawSelectRecord = namedtuple(
    'RawSelectRecord',
    ['num', 'name', 'url']
)

RawUIKRecord = namedtuple(
    'RawUIKRecord',
    ['num', 'name', 'results']
)


def __get_soup__(html):
    # Удаление </html> тега, который может оказаться посреди страницы.
    # Для возможности использования быстрого парсера lxml, следующего стандартам,
    # вместо толерантного к ошибкам, но медленного html5lib
    html = html.replace("</html>", "")
    return BeautifulSoup(html, 'lxml')


# Очищает строку от пробелов на концах и отделяет число от названия
def split_name(name):
    name = name.strip()
    text = name
    if len(name) > 3 and name[0].isdigit():
        meta = name.split(" – ")
        if len(meta) > 1:
            text = name[(len(meta[0]) + 3):]
        else:
            meta = name.split(" ")
            text = name[(len(meta[0])+1):]

    num = None
    for n in name.split():
        tnum = ''.join(x for x in n if x.isdigit())
        if len(tnum):
            num = int(tnum)
            break

    return [num, text]


def simple_name(title):
    text = "политическая партия"
    lower_title = title.lower()
    start = lower_title.find(text)
    if start != -1:
        title = title[start+len(text)+1:]
    return title


# Находит тег SELECT под шапкой и возвращает его значения
def selects(html):
    soup = __get_soup__(html)
    select = soup.find('select')

    # Если select не найден
    if select is None:
        return None

    data = []
    options = select.find_all('option')
    for option in options:
        if option.text == '---':
            continue
        url = option['value']
        spl = split_name(option.text)
        data.append(RawSelectRecord(spl[0], spl[1], url))
    return data


# Ищет на странице ссылку на сайт избирательной комиссии субъекта РФ
def local_ik_url(html):
    soup = __get_soup__(html)
    ik = soup.find('a', text=u'сайт избирательной комиссии субъекта Российской Федерации')
    if ik:
        ik = ik['href']
    return ik


# Ищет на странице ссылку на итоги выборов
def url_itog(html):
    soup = __get_soup__(html)

    url = soup.find('a', text=u'Итоги голосования по федеральному избирательному округу')
    if url:
        url = url['href']
        return url

    url = soup.find('a', text=u'Результаты выборов по федеральному избирательному округу')
    if url:
        url = url['href']
        return url

    url = soup.find('a', text=u'Итоги голосования')
    if url:
        url = url['href']
        return url

    url = soup.find('a', text=u'Результаты выборов')
    if url:
        url = url['href']
        return url

    return None


# Ищет на странице ссылку на сводную таблицу итогов выборов на сайте избирательной комиссии субъекта РФ
def url_local_itog(html):
    soup = __get_soup__(html)

    url = soup.find('a', text=u'Сводная таблица итогов голосования по федеральному избирательному округу')
    if url:
        url = url['href']
        return url

    url = soup.find('a', text=u'Сводная таблица итогов голосования')
    if url:
        url = url['href']
        return url

    url = soup.find('a', text=u'Сводная таблица результатов выборов')
    if url:
        url = url['href']
        return url

    return None


def get_election_table(html):
    soup = __get_soup__(html)
    table = soup.find_all('table')[-3]
    # В итогах выборов президента 2008 на одну таблицу меньше, потому берем не 3 с конца, а 2
    if len(table.find_all('tr')) == 1:
        table = soup.find_all('table')[-2]
    return table


# Парсит таблицу с результатами выборов региона и возвращает словарь, содержащий индексы
# недействительных бюллетеней, действительных бюллетеней, а также кандидатов и их индексов.
def table_meta(html):
    table = get_election_table(html)

    table_uiks = table.find_all('table')[0]
    rows = table_uiks.find_all('tr')[1:]
    meta = {
        0: {'name': 'all', 'is_meta': True}
    }
    already = []

    for i, row in enumerate(rows):
        column = row.find_all('td')
        if len(column) == 3:
            _, title, _ = column

            title = title.text.split('.')[-1].strip()

            if title != '':

                if title.startswith('Число '):
                    if "early" not in already and "досрочно" in title:
                        meta[i] = {'name': "early", 'is_meta': True}
                        already.append("early")
                    elif "in_room" not in already and ("в помещен" in title or "выданных избирателям на избирательном" in title):
                        meta[i] = {'name': "in_room", 'is_meta': True}
                        already.append("in_room")
                    elif "out_room" not in already and "вне помещен" in title:
                        meta[i] = {'name': "out_room", 'is_meta': True}
                        already.append("out_room")
                    elif "invalid" not in already and " недействительных" in title:
                        meta[i] = {'name': "invalid", 'is_meta': True}
                        already.append("invalid")
                    elif "valid" not in already and " действительных" in title:
                        meta[i] = {'name': "valid", 'is_meta': True}
                        already.append("valid")

                elif title.startswith('В '):
                    continue

                else:
                    meta[i] = {'name': simple_name(title)}

    return meta


# Парсит таблицу с результатами выборов региона и возвращает список УИКов с результатами на них
def table_results(html, meta):
    table = get_election_table(html)

    # Получаем список УИКов
    table_uiks = table.find_all('table')[1]
    header_row = table_uiks.find('tr')
    uiks = header_row.find_all('td')

    data = []
    # Записываем данные из таблицы
    # Перебор колонок с УИКами
    for k, uik in enumerate(uiks):
        spl = split_name(uik.text)
        data_rows = table_uiks.find_all('tr')[1:]

        # Массив результатов выборов для конкретного УИКа
        res = {'candidates': {}}
        # Перебор строк с данными
        for i, row in enumerate(data_rows):

            if i in meta:
                data_column = row.find_all('td')

                tag_b = data_column[k].find('b')
                if tag_b:
                    num = tag_b.text
                    meta_item = meta[i]

                    key = meta_item['name']
                    if 'is_meta' in meta_item:
                        res[key] = int(num)
                    else:
                        res['candidates'][key] = int(num)

        res['calculated_number_bulletin'] = res['invalid'] + res['valid']

        if res['all'] == 0:
            res['calculated_share'] = 0
        else:
            res['calculated_share'] = round(float(res['calculated_number_bulletin']) / res['all'] * 100, 2)

        # Если данные отсутсвуют, то обнуление
        for el in ['early']:
            if el not in res:
                res[el] = 0

        data.append(
            {
                'num': spl[0],
                'name': spl[1],
                'results': {
                    'all': res['all'],
                    'early': res['early'],
                    'in_room': res['in_room'],
                    'out_room': res['out_room'],
                    'invalid': res['invalid'],
                    'valid': res['valid'],
                    'calculated_share': res['calculated_share'],
                    'calculated_number_bulletin': res['calculated_number_bulletin'],
                    'candidates': res['candidates']}
            })
    return data


# Возвращает название региона, который указан в поддомене
def get_region_from_subdomain_url(url):
    url = url.split('.')
    return url[1]


# Возвращает название региона, который указан в GET параметрах адреса
def get_region_from_getparams_url(url):
    num = dict(x.split('=', 1) for x in url.split('&')).get('region')
    if num is not None:
        num = int(num)
    return num


# Вид выборов/референдумов и иных форм прямого волеизъявления:
#   all - все
#     0 - Референдум                    3 - Отзыв депутата
#     1 - Выборы на должность           4 - Отзыв должностного лица
#     2 - Выборы депутата
def vidvibref_from_title(title):
    title = title.lower()
    if title.find("отзыв") != -1:
        if title.find("депутат") != -1:
            return 3
        else:
            return 4
    elif title.find("выбор") != -1:
        if title.find("депутат") != -1:
            return 2
        else:
            return 1
    else:
        return 0


def parse_list_elections(html, urovproved):
    soup = __get_soup__(html)

    data = soup.find_all('table')
    if len(data) >= 7:
        data = data[7].find_all('tr')
    else:
        return []

    elections = []
    election_date = ""
    election_region = ""
    election_subregion = ""
    for row in data:
        item = row.find_all('td')

        if len(item) == 1:
            # В строке указана дата
            election_date = item[0].text.strip()
        elif len(item) == 2:
            _region = item[0].find('b')
            if _region is not None:
                election_region = _region.text
                if len(item[0].contents) == 3:
                    _subregion = item[0].contents[2].strip()
                else:
                    _subregion = None
                election_subregion = _subregion
            else:
                _subregion = item[0].text.strip()
                if _subregion != '':
                    election_subregion = _subregion

            if election_region == "Российская Федерация":
                region = ["Российская Федерация"]
            else:
                if election_subregion is None:
                    region = ["Российская Федерация", election_region]
                else:
                    region = ["Российская Федерация", election_region, election_subregion]

            title = item[1].text.strip()
            elections.append({
                'date': helpers.get_datetime(election_date),
                'region_id': get_region_from_getparams_url(item[1].find('a')['href']),
                'region': region,
                'title': title,
                'vidvibref': vidvibref_from_title(title),
                'urovproved': urovproved,
                'url': item[1].find('a')['href'],
            })

    return elections


# 2018 -> [01.01.2018,31.12.2018]
# 2018-10 -> [01.10.2018,31.10.2018]
# 2018-10-10 -> [10.10.2018,10.10.2018]
def get_start_end_date(s, _min_year=2008, _max_year=2142, _min_month=1, _max_month=12):
    s = s.split("-")
    if len(s) > 3:
        return None

    # Указан год
    year = int(s[0])
    if not(_min_year <= year <= _max_year):
        return None

    # Указан ещё и месяц
    if len(s) == 1:
        start_month = 1
        end_month = 12
    else:
        start_month = int(s[1])
        if not(_min_month <= start_month <= _max_month):
            return None
        end_month = start_month

    # Указан год, месяц и день
    if len(s) < 3:
        start_day = 1
        end_day = calendar.monthrange(year, end_month)[1]
    else:
        start_day = int(s[2])
        if not(1 <= start_day <= calendar.monthrange(year, end_month)[1]):
            return None
        end_day = start_day

    return {
        'start_date': '.'.join([
            str(start_day).zfill(2),
            str(start_month).zfill(2),
            str(year)
        ]),
        'end_date': '.'.join([
            str(end_day).zfill(2),
            str(end_month).zfill(2),
            str(year)
        ]),
    }


# Возвращает массив со списком систем выборов, по которым они проходят
# Варианты:
# - edin - "по единому округу"
# - edmj - "по единому мажоритарному округу"
# - edmn - "по единому многомандатному округу"
# - mngm - "по одномандатному (многомандатному) округу"
def get_elections_type(html):
    soup = __get_soup__(html)

    td = soup.find_all('table')[-1].find_all('td')
    results = []
    for item in td:
        if item.get('class') is None or item.get('class')[0] != "tdReport":
            continue
        else:
            if item.find('a').text.startswith('Сводная таблица'):
                results.append(item)

    types = {}
    for item in results:
        text = item.find('a').text
        url = item.find('a')['href']

        if text in ["Сводная таблица результатов выборов по единому округу",
                    "Сводная таблица результатов выборов",
                    "Сводная таблица предварительных итогов голосования"]:
            if 'edin' in types:
                return [0, 0, []]
            types['edin'] = url

        elif text in ["Сводная таблица результатов выборов по единому мажоритарному округу",
                      "Сводная таблица предварительных итогов голосования по единому мажоритарному округу"]:
            if 'edmj' in types:
                return [0, 0, []]
            types['edmj'] = url

        elif text in ["Сводная таблица результатов выборов по единому многомандатному округу",
                      "Сводная таблица предварительных итогов голосования по единому многомандатному округу"]:
            if 'edmn' in types:
                return [0, 0, []]
            types['edmn'] = url

        elif text in ["Сводная таблица результатов выборов по одномандатному (многомандатному) округу",
                      "Сводная таблица результатов выборов по одномандатному избирательному округу",
                      "Сводная таблица предварительных итогов голосования по одномандатному избирательному округу",
                      "Сводная таблица предварительных итогов голосования по одномандатному (многомандатному) округу"]:
            if 'mngm' in types:
                return [0, 0, []]
            types['mngm'] = url

    return {'status': len(results) == len(types), 'types': types}

