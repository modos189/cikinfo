from bs4 import BeautifulSoup
from collections import namedtuple

RawSelectRecord = namedtuple(
    'RawSelectRecord',
    ['num', 'name', 'url']
)

RawUIKRecord = namedtuple(
    'RawUIKRecord',
    ['num', 'name', 'results']
)

RESULT_ROWS = [
    'Число избирателей, внесенных в список избирателей на момент окончания голосования',
    'Число избирательных бюллетеней, полученных участковой избирательной комиссией',
    'Число избирательных бюллетеней, выданных избирателям, проголосовавшим досрочно',
    'Число избирательных бюллетеней, выданных в помещении для голосования в день голосования',
    'Число избирательных бюллетеней, выданных вне помещения для голосования в день голосования',
    'Число погашенных избирательных бюллетеней',
    'Число избирательных бюллетеней, содержащихся в переносных ящиках для голосования',
    'Число избирательных бюллетеней, содержащихся в стационарных ящиках для голосования',
    'Число недействительных избирательных бюллетеней',
    'Число действительных избирательных бюллетеней',
    'Число открепительных удостоверений, полученных участковой избирательной комиссией',
    'Число открепительных удостоверений, выданных на избирательном участке до дня голосования',
    'Число избирателей, проголосовавших по открепительным удостоверениям на избирательном участке',
    'Число погашенных неиспользованных открепительных удостоверений',
    'Число открепительных удостоверений, выданных избирателям территориальной избирательной комиссией',
    'Число утраченных открепительных удостоверений',
    'Число утраченных избирательных бюллетеней',
    'Число избирательных бюллетеней, не учтенных при получении'
]


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

    num = ''.join(x for x in name if x.isdigit())
    if num == '':
        num = None
    else:
        num = int(num)

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


def _simple_table_meta(table):
    rows = table.find_all('tr')
    arr = []

    for row in rows:
        column = row.find_all('td')
        if len(column) == 3:
            _, title, _ = column

            title = title.text.split('.')[-1].strip()

            if title == '':
                continue
            else:
                if title.startswith('Число '):
                    arr.append({'name': title, 'is_meta': True})
                else:
                    arr.append({'name': title, 'name_simple': simple_name(title), 'is_meta': False})

    return arr


# Парсит простую одномерную таблицу с результатами выборов региона и возвращает список параметров и партий/кандидатов
def simple_table_meta(html):
    soup = __get_soup__(html)
    table = soup.find_all('table')[-3]
    return _simple_table_meta(table)


def two_dimensional_table(html):
    soup = __get_soup__(html)
    table = soup.find_all('table')[-3]

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
        data_tmp = {}
        n = 0
        # Перебор строк с данными
        for row in data_rows:
            data_column = row.find_all('td')

            # Пропуск пустой строки.
            # Читаем только если число колонок совпадает и в них есть данные
            if len(data_column) == len(uiks):
                tag_b = data_column[k].find('b')
                if tag_b:
                    num = tag_b.text
                    data_tmp[str(n)] = num
                    n += 1

        data.append(RawUIKRecord(spl[0], spl[1], data_tmp))
    return data
