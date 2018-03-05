# encoding: utf8

import sys
import re
import cjson
import json
import os
import os.path
from random import sample
from time import sleep
from hashlib import sha1
from collections import namedtuple, defaultdict, Counter
from datetime import datetime

import requests
requests.packages.urllib3.disable_warnings()

import pandas as pd

import seaborn as sns
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import rc
import matplotlib.ticker as mtick
# For cyrillic labels
rc('font', family='Verdana', weight='normal')

from bs4 import BeautifulSoup


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
}
DATA_DIR = 'data'
HTML_DIR = os.path.join(DATA_DIR, 'html')
HTML_LIST = os.path.join(HTML_DIR, 'list.txt')
JSON_DIR = os.path.join(DATA_DIR, 'json')
JSON_LIST = os.path.join(JSON_DIR, 'list.txt')

OPENED_ROOT_URL = 'http://www.vybory.izbirkom.ru/region/region/izbirkom?action=show&root=1&tvd=100100067795854&vrn=100100067795849&region=0&global=1&sub_region=0&prver=0&pronetvd=0&vibid=100100067795854&type=238'
ODNOMANDAT_RESULS_ROOT_URL = 'http://www.vybory.izbirkom.ru/region/region/izbirkom?action=show&root=1&tvd=100100067795854&vrn=100100067795849&region=0&global=true&sub_region=0&prver=0&pronetvd=0&vibid=100100067795854&type=464'
PARTY_RESULTS_ROOT_URL = 'http://www.vybory.izbirkom.ru/region/region/izbirkom?action=show&root=1&tvd=100100067795854&vrn=100100067795849&region=0&global=true&sub_region=0&prver=0&pronetvd=0&vibid=100100067795854&type=233'

DUMP_DIR = os.path.join(DATA_DIR, 'dump')
UIKS_DUMP = os.path.join(DUMP_DIR, 'uiks.tsv')
ODNOMANDATS_DUMP = os.path.join(DUMP_DIR, 'odnomandats.tsv')
PARTY_RESULTS_DUMP = os.path.join(DUMP_DIR, 'party_results.tsv')
ODNOMANDAT_RESULTS_DUMP = os.path.join(DUMP_DIR, 'odnomandat_results.tsv')

ODNOMANDAT_SERPS_COUNT = 123

RESULT_ROWS = [
    u'Число избирателей, внесенных в список избирателей на момент окончания голосования',
    u'Число избирательных бюллетеней, полученных участковой избирательной комиссией',
    u'Число избирательных бюллетеней, выданных избирателям, проголосовавшим досрочно',
    u'Число избирательных бюллетеней, выданных в помещении для голосования в день голосования',
    u'Число избирательных бюллетеней, выданных вне помещения для голосования в день голосования',
    u'Число погашенных избирательных бюллетеней',
    u'Число избирательных бюллетеней, содержащихся в переносных ящиках для голосования',
    u'Число избирательных бюллетеней, содержащихся в стационарных ящиках для голосования',
    u'Число недействительных избирательных бюллетеней',
    u'Число действительных избирательных бюллетеней',
    u'Число открепительных удостоверений, полученных участковой избирательной комиссией',
    u'Число открепительных удостоверений, выданных на избирательном участке до дня голосования',
    u'Число избирателей, проголосовавших по открепительным удостоверениям на избирательном участке',
    u'Число погашенных неиспользованных открепительных удостоверений',
    u'Число открепительных удостоверений, выданных избирателям территориальной избирательной комиссией',
    u'Число утраченных открепительных удостоверений',
    u'Число утраченных избирательных бюллетеней',
    u'Число избирательных бюллетеней, не учтенных при получении'
]

PARTY_IDS = {
    u'ВСЕРОССИЙСКАЯ ПОЛИТИЧЕСКАЯ ПАРТИЯ "РОДИНА"': 'rodina',
    u'Всероссийская политическая партия "ЕДИНАЯ РОССИЯ"': 'er',
    u'Всероссийская политическая партия "ПАРТИЯ ВЕЛИКОЕ ОТЕЧЕСТВО"': 'vo',
    u'Всероссийская политическая партия "ПАРТИЯ РОСТА"': 'rost',
    u'Всероссийская политическая партия "Партия Возрождения Села"': 'selo',
    u'Всероссийская политическая партия "Союз Труда"': 'trud',
    u'Общественная организация - Политическая партия "ПАРТИЯ РОДИТЕЛЕЙ БУДУЩЕГО"': 'parent',
    u'Общественная организация Всероссийская политическая партия "Гражданская Сила"': 'gs',
    u'Политическая партия "Гражданская Платформа"': 'gp',
    u'Политическая партия "КОММУНИСТИЧЕСКАЯ ПАРТИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ"': 'kprf',
    u'Политическая партия "ПАТРИОТЫ РОССИИ"': 'partiot',
    u'Политическая партия "Партия народной свободы" (ПАРНАС)': 'parnas',
    u'Политическая партия "Российская объединенная демократическая партия "ЯБЛОКО"': 'apple',
    u'Политическая партия "Российская экологическая партия "Зеленые"': 'green',
    u'Политическая партия "Российская партия пенсионеров за справедливость"': 'pens',
    u'Политическая партия КОММУНИСТИЧЕСКАЯ ПАРТИЯ КОММУНИСТЫ РОССИИ': 'kommumist',
    u'Политическая партия ЛДПР - Либерально-демократическая партия России': 'ldpr',
    u'Политическая партия СПРАВЕДЛИВАЯ РОССИЯ': 'sr',
    u'Самовыдвижение': 'self'
}


RawOpenedRecord = namedtuple(
    'RawOpenedRecord',
    ['source', 'name', 'url', 'people', 'uiks', 'opened', 'ik']
)
OpenedRecord = namedtuple(
    'OpenedRecord',
    ['level', 'parent', 'id', 'name', 'people', 'uiks', 'opened', 'ik']
)
IkTreeRecord = namedtuple(
    'IkTreeRecord',
    ['region', 'parent', 'id', 'name']
)
RawIkRecord = namedtuple(
    'RawIkRecord',
    ['id', 'name', 'address']
)
Coordinates = namedtuple(
    'Coordinates',
    ['latitude', 'longitude']
)
OdnomandatSerpRecord = namedtuple(
    'OdnomandatSerpRecord',
    ['id', 'fio', 'date', 'party_id', 'party_name', 'oik', 'nominated']
)
ResultsTreeRecord = namedtuple(
    'ResultsTreeRecord',
    ['source', 'name', 'url']
)
RawResultsCell = namedtuple(
    'ResultsCell',
    ['source', 'row', 'column', 'value']
)
ResultsCell = namedtuple(
    'ResultsCell',
    ['uik_id', 'row_id', 'value']
)
Uik = namedtuple(
    'Uik',
    ['id', 'name', 'region_id', 'region_name', 'oik',
     'tik_id', 'tik_name', 'address', 'coordinates']
)


def log_progress(sequence, every=None, size=None):
    from ipywidgets import IntProgress, HTML, VBox
    from IPython.display import display

    is_iterator = False
    if size is None:
        try:
            size = len(sequence)
        except TypeError:
            is_iterator = True
    if size is not None:
        if every is None:
            if size <= 200:
                every = 1
            else:
                every = size / 200     # every 0.5%
    else:
        assert every is not None, 'sequence is iterator, set every'

    if is_iterator:
        progress = IntProgress(min=0, max=1, value=1)
        progress.bar_style = 'info'
    else:
        progress = IntProgress(min=0, max=size, value=0)
    label = HTML()
    box = VBox(children=[label, progress])
    display(box)

    index = 0
    try:
        for index, record in enumerate(sequence, 1):
            if index == 1 or index % every == 0:
                if is_iterator:
                    label.value = '{index} / ?'.format(index=index)
                else:
                    progress.value = index
                    label.value = u'{index} / {size}'.format(
                        index=index,
                        size=size
                    )
            yield record
    except:
        progress.bar_style = 'danger'
        raise
    else:
        progress.bar_style = 'success'
        progress.value = index
        label.value = str(index or '?')


def jobs_manager():
    from IPython.lib.backgroundjobs import BackgroundJobManager
    from IPython.core.magic import register_line_magic
    from IPython import get_ipython
    
    jobs = BackgroundJobManager()

    @register_line_magic
    def job(line):
        ip = get_ipython()
        jobs.new(line, ip.user_global_ns)

    return jobs


def kill_thread(thread):
    import ctypes
    
    id = thread.ident
    code = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(id),
        ctypes.py_object(SystemError)
    )
    if code == 0:
        raise ValueError('invalid thread id')
    elif code != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(id),
            ctypes.c_long(0)
        )
        raise SystemError('PyThreadState_SetAsyncExc failed')


def get_chunks(sequence, count):
    count = min(count, len(sequence))
    chunks = [[] for _ in range(count)]
    for index, item in enumerate(sequence):
        chunks[index % count].append(item) 
    return chunks


def hash_item(item):
    return sha1(item.encode('utf8')).hexdigest()


hash_url = hash_item


def load_items_cache(path):
    with open(path) as file:
        for line in file:
            line = line.decode('utf8').strip()
            # In case cache is broken with unstripped item
            if '\t' in line:
                hash, item = line.split('\t', 1)
                yield item


def update_items_cache(item, path):
    with open(path, 'a') as file:
        hash = hash_item(item)
        file.write('{hash}\t{item}\n'.format(
            hash=hash,
            item=item.encode('utf8')
        ))


def get_html_filename(url):
    return '{hash}.html'.format(
        hash=hash_url(url)
    )


def get_html_path(url):
    return os.path.join(
        HTML_DIR,
        get_html_filename(url)
    )


def list_html_cache():
    return load_items_cache(HTML_LIST)


def update_html_cache(url):
    update_items_cache(url, HTML_LIST)


def dump_html(url, html):
    path = get_html_path(url)
    if html is None:
        html = ''
    with open(path, 'w') as file:
        file.write(html)
    update_html_cache(url)


def load_content(path):
    with open(path) as file:
        return file.read()


def load_html(url):
    path = get_html_path(url)
    return load_content(path)


def decode_html(html):
    try:
        return html.decode('utf8')
    except UnicodeDecodeError:
        try:
            return html.decode('cp1251')
        except UnicodeDecodeError:
            return html.decode('utf8', 'ignore')
    

def load_decoded_html(url):
    html = load_html(url)
    return decode_html(html)


def download_url(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )
        return response.content
    except requests.RequestException:
        return None


def fetch_url(url):
    html = download_url(url)
    dump_html(url, html)
    return html


def fetch_urls(urls):
    for url in urls:
        fetch_url(url)


def get_soup(html):
    return BeautifulSoup(html, 'lxml')


def maybe_int(value):
    try:
        return int(value)
    except ValueError:
        return None

    
def parse_opened_table(html, source):
    soup = get_soup(html)
    ik = soup.find(
        'a',
        text=u'сайт избирательной комиссии субъекта Российской Федерации'
    )
    if ik:
        ik = ik['href']
    # last on page
    table = soup.find_all('table')[-1]
    # skip first 3 rows
    rows = table.find_all('tr')[3:]
    for row in rows:
        id, name, people, uiks, opened, share = row.find_all('td')
        url = name.find('a')
        if url:
            url = url['href']
        name = name.text
        people = maybe_int(people.text)
        uiks = maybe_int(uiks.text)
        opened = maybe_int(opened.text)
        yield RawOpenedRecord(source, name, url, people, uiks, opened, ik)


def parse_selects(html, source):
    soup = get_soup(html)
    ik = soup.find(
        'a',
        text=u'сайт избирательной комиссии субъекта Российской Федерации'
    )
    if ik:
        ik = ik['href']
    # select
    select = soup.find('select')
    # all options
    options = select.find_all('option')
    for option in options:
        if (option.text == '---'):
            continue
        url = option['value']
        # if url:
        #     url = url['href']
        name = option.text
        people = maybe_int(0)
        uiks = maybe_int(0)
        opened = maybe_int(0)
        yield RawOpenedRecord(source, name, url, people, uiks, opened, ik)

def parse_url_itog(html, source):
    soup = get_soup(html)
    url = soup.find(
        'a',
        text=u'Итоги голосования по федеральному избирательному округу'
    )
    if url:
        url = url['href']
    return url

def load_opened_table(url):
    html = load_decoded_html(url)
    return parse_opened_table(html, url)


def load_selects(url):
    html = load_decoded_html(url)
    return parse_selects(html, url)

def load_url_itog(url):
    html = load_decoded_html(url)
    return parse_url_itog(html, url)


def load_regional_ik_url(url):
    html = load_decoded_html(url)
    soup = get_soup(html)
    link = soup.find('a', text=u'Избирательные комиссии')
    return link['href']


def get_json_filename(url):
    return '{hash}.json'.format(
        hash=hash_url(url)
    )


def get_json_path(url):
    return os.path.join(
        JSON_DIR,
        get_json_filename(url)
    )


def list_json_cache():
    return load_items_cache(JSON_LIST)


def update_json_cache(url):
    update_items_cache(url, JSON_LIST)


def dump_raw_json(path, data):
    with open(path, 'w') as file:
        file.write(cjson.encode(data))


def load_raw_json(path):
    with open(path) as file:
        return cjson.decode(file.read())


def download_json(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )
    try:
        return response.json()
    except ValueError:
        return


def fetch_json(url):
    data = download_json(url)
    dump_json(data, url)
    update_json_cache(url)


def fetch_jsons(urls):
    for url in urls:
        fetch_json(url)


def load_json(url):
    path = get_json_path(url)
    return load_raw_json(path)


def dump_json(data, url):
    path = get_json_path(url)
    return dump_raw_json(path, data)


def get_geocode_url(address):
    return u'http://geocode-maps.yandex.ru/1.x/?format=json&geocode={address}'.format(
        address=address
    )


def parse_geocode_data(data):
    if not 'response' in data:
        return None
    response = data['response']['GeoObjectCollection']
    data = response['featureMember']
    if data:
        item = data[0]['GeoObject']
        longitude, latitude = item['Point']['pos'].split(' ')
        longitude = float(longitude)
        latitude = float(latitude)
        return Coordinates(
            latitude,
            longitude
        )


def load_coordinates(address):
    url = get_geocode_url(address)
    data = load_json(url)
    return parse_geocode_data(data)


def get_url_vibid(url):
    if url:
        match = re.search(r'vibid=(\d+)', url)
        if match:
            return int(match.group(1))
    

def get_regional_ik_url_region(url):
    if url:
        match = re.search(r'/([^/]+)/ik$', url)
        if match:
            return match.group(1)


def make_opened(chunks, mapping):
    for level, records in enumerate(chunks):
        for record in records:
            parent = get_url_vibid(record.source)
            id = record.url
            if id:
                id = get_url_vibid(id)
            ik = record.ik
            if ik:
                ik = get_regional_ik_url_region(mapping[ik])
            yield OpenedRecord(
                level, parent, id, record.name,
                record.people, record.uiks,
                record.opened, ik
            )


def get_ik_tree_url(region, id=None):
    url = 'http://www.{region}.vybory.izbirkom.ru/{region}/ik_tree/'.format(
        region=region
    )
    if id is not None:
        url += '?id={id}'.format(id=id)
    return url


def parse_ik_tree(data, region, parent=None):
    for item in data:
        name = item['text']
        id = int(item['id'])
        yield IkTreeRecord(region, parent, id, name)
        children = item.get('children')
        if children and isinstance(children, list):
            for record in parse_ik_tree(children, region, id):
                yield record

                
def load_ik_tree(region, id=None):
    url = get_ik_tree_url(region, id=id)
    data = load_json(url)
    return parse_ik_tree(data, region, parent=id)


def get_ik_url(region, id):
    return 'http://www.{region}.vybory.izbirkom.ru/{region}/ik/{id}'.format(
        region=region,
        id=id
    )


def parse_ik_html(html, id):
    soup = get_soup(html)
    main = soup.find('div', class_='center-colm')
    name = main.find('h2').text
    address = main.find('span', class_='view_in_map')['rel']
    return RawIkRecord(id, name, address)
    

def load_raw_ik(region, id):
    url = get_ik_url(region, id)
    html = load_decoded_html(url)
    return parse_ik_html(html, id)
    

def dump_ik(data, region, id):
    url = get_ik_url(region, id)
    dump_json(data, url)
    
    
def load_ik(region, id):
    url = get_ik_url(region, id)
    id, name, address = load_json(url)
    return RawIkRecord(id, name, address)


def convert_ik(region, id):
    data = load_raw_ik(region, id)
    dump_ik(data, region, id)


def get_odnomandat_serp_url(page):
    return 'http://www.vybory.izbirkom.ru/region/region/izbirkom?action=show&root=1&tvd=100100067795849&vrn=100100067795849&region=0&global=true&sub_region=0&prver=0&pronetvd=0&type=220&number={page}'.format(
        page=page
    )


def parse_date(date):
    return datetime.strptime(date, '%d.%m.%Y')


def parse_odnomandat_serp(html):
    soup = get_soup(html)
    # trust me
    table = soup.find('tbody', id='test')
    for row in table.find_all('tr'):
        (id, fio, date, party, oik, state,
         registered, when, number1, number2) = row.find_all('td')
        fio = fio.find('a')
        id = get_url_vibid(fio['href'])
        fio = fio.text.strip()
        date = parse_date(date.text)
        party_name = party.text
        party_id = get_party_id(party_name)
        oik = int(oik.text)
        nominated = (state.text == u'выдвинут')
        yield OdnomandatSerpRecord(id, fio, date, party_id, party_name, oik, nominated)

        
def get_party_id(name):
    if name[0].isdigit():
        name = re.sub(r'^\d+\. ', '', name)
    return PARTY_IDS.get(name)


def load_odnomandat_serp(page):
    url = get_odnomandat_serp_url(page)
    html = load_decoded_html(url)
    return parse_odnomandat_serp(html)


def parse_results_tree_node(html, source):
    soup = get_soup(html)
    form = soup.find('form', attrs={'name': 'go_reg'})
    if form:
        options = form.find_all('option')
        for option in options[1:]:
            name = option.text.strip()
            url = option['value']
            yield ResultsTreeRecord(source, name, url)
    else:
        # terminal node?
        link = soup.find(
            'a',
            text=u'сайт избирательной комиссии субъекта Российской Федерации'
        )
        url = link['href']
        yield ResultsTreeRecord(source, None, url)
    

def load_results_tree_node(url):
    html = load_decoded_html(url)
    return parse_results_tree_node(html, url)


def parse_results_table(html, source):
    # kaliningrad header has </body>, </html>
    html = html.replace('</body>', '').replace('</html>', '')

    soup = get_soup(html)
    tables = soup.find_all('table')

    rows = []
    # rows table before body
    items = tables[-2].find_all('tr')
    # skip header
    for row in items:
        cells = row.find_all('td')
        if len(cells) == 3:
            id, name, total = cells
            name = name.text
        else:
            # otherwise it is empty row
            name = None
        rows.append(name)

    # last table is body
    items = tables[-2].find_all('tr')
    columns = []
    for cell in items[0].find_all('td'):
        name = cell.text
        print(name)
        columns.append(name)
    
    for row, item in enumerate(items[1:]):
        cells = item.find_all('td')
        for column, cell in enumerate(cells):
            cell = cell.find('b')
            if cell:
                value = int(cell.text)
                yield RawResultsCell(source, rows[row], columns[column], value)


def load_results_table(url):
    html = load_decoded_html(url)
    return parse_results_table(html, url)


def get_ik_uik_id(name):
    match = re.search(ur'(№[\s\d/-]+)', name, re.U)
    if match:
        id = match.group(1)
        id = re.sub(ur'[№\s/-]', '', id)
        return int(id)


def get_results_uik_id(name):
    match = re.match(ur'^УИК №(\d+)$', name)
    if match:
        return int(match.group(1))


def get_oik_id(name):
    match = re.match(ur'^ОИК №(\d+)$', name)
    if match:
        return int(match.group(1))


def make_uiks(opened, ik_tree, ik_pages, address_coordinates):
    ik_pages_mapping = {_.id: _ for _ in ik_pages}
    # assume region, uik_id pair is unique
    # build mapping[region, uik_id]
    ik_region_uik = defaultdict(list)
    for record in ik_tree:
        id = get_ik_uik_id(record.name)
        if id is None:
            print >>sys.stderr, 'Bad ik UIK name:', record.name
        else:
            ik_region_uik[record.region, id].append(record)
    for key in ik_region_uik:
        records = ik_region_uik[key]
        size = len(records)
        assert size in (1, 2), (key, size)
        if size == 2:
            # some id may have two different parents but usually they
            # have same address
            a, b = records
            # seems to be broken since ik_pages have not parents
            a = ik_pages_mapping.get(a.parent)
            b = ik_pages_mapping.get(b.parent)
            if a and b and a.address != b.address:
                print >>sys.stderr, 'Same name diff UIKs:', (a.region, a.id, b.id)
                pass
        ik_region_uik[key] = records[0].id
    
    opened_region_uik = defaultdict(list)
    for record in opened:
        if record.level == 3:
            id = get_results_uik_id(record.name)
            assert id is not None and record.ik is not None
            opened_region_uik[record.ik, id].append(record)
    for key in opened_region_uik:
        records = opened_region_uik[key]
        assert len(records) == 1
        opened_region_uik[key] = records[0]
        
    print 'Opened UIKs:', len(opened_region_uik)
    print 'Ik UIKs:', len(ik_region_uik)
    print 'opened & ik:', len(set(opened_region_uik) & set(ik_region_uik))
       
    opened_id_names = {_.id: _.name for _ in opened}
    opened_id_parents = {_.id: _.parent for _ in opened}
    for region, uik_id in opened_region_uik:
        key = (region, uik_id)
        if key in ik_region_uik:
            id = ik_region_uik[key]
            address = ik_pages_mapping[id].address
            coordinates = address_coordinates[address]
        else:
            id = '{region}_{uik_id}'.format(
                region=region,
                uik_id=uik_id
            )
            address = None
            coordinates = None
        record = opened_region_uik[key]
        name = record.name
        tik_id = record.parent
        tik_name = opened_id_names[tik_id]
        oik_id = opened_id_parents[tik_id]
        oik = get_oik_id(opened_id_names[oik_id])
        region_id = opened_id_parents[oik_id]
        region_name = opened_id_names[region_id]

        yield Uik(
            id, name, region, region_name, oik,
            tik_id, tik_name, address, coordinates
        )


def parse_nikolaev_oleg(row):
    # for cases like "Николаев Олег Алексеевич  10/12/69"
    match = re.match(ur'^([\s\w]+)  ([\d/]+)$', row, re.U)
    if match:
        fio = match.group(1)
        day, month, year = match.group(2).split('/', 2)
        day = int(day)
        month = int(month)
        year = 1900 + int(year)
        date = datetime(year, month, day)
        return fio, date
    return None, None
        

def make_odnomandat_cells(uiks, odnomandats, raw_odnomandat_cells):
    uik_ids = {(_.tik_id, get_ik_uik_id(_.name)): _.id for _ in uiks}
    row_ids = {_: index for index, _ in enumerate(RESULT_ROWS, 1)}
    tik_oiks = {_.tik_id: _.oik for _ in uiks}
    # since fios collide
    odnomandat_ids = {(_.oik, _.fio): _.id for _ in odnomandats}
    # specialy for Николаев Олег Алексеевич
    odnomandat_ids2 = {(_.oik, _.fio, _.date): _.id for _ in odnomandats}
    
    for record in raw_odnomandat_cells:
        tik_id = get_url_vibid(record.source)
        id = get_results_uik_id(record.column)
        uik_id = uik_ids[tik_id, id]

        row = record.row.strip()
        if row in row_ids:
            row_id = row_ids[row]
        else:
            # row is fio
            oik = tik_oiks[tik_id]
            fio, date = parse_nikolaev_oleg(row)
            if fio:
                row_id = odnomandat_ids2[oik, fio, date]
            else:
                fio = row
                row_id = odnomandat_ids[oik, fio]

        yield ResultsCell(uik_id, row_id, record.value)


def dump_uiks(uiks):
    table = pd.DataFrame(
        [(_.id, _.name, _.region_id, _.region_name, _.oik,
          _.tik_id, _.tik_name, _.address,
          _.coordinates.latitude if _.coordinates else None,
          _.coordinates.longitude if _.coordinates else None)
        for _ in uiks],
        columns=['id', 'name', 'region_id', 'region_name', 'oik',
             'tik_id', 'tik_name', 'address', 'latitude', 'longitude']
    )
    # to check easier uiks == load_uiks()
    # table = table.sort_values('id')
    table.to_csv(UIKS_DUMP, encoding='utf8', index=False, sep='\t')


def load_uiks():
    table = pd.read_csv(UIKS_DUMP, encoding='utf8', sep='\t')
    table = table.where(pd.notnull(table), None)
    for _, row in table.iterrows():
        (id, name, region_id, region_name, oik,
         tik_id, tik_name, address, latitude, longitude) = row
        if id.isdigit():
            id = int(id)
        coordinates = None
        if latitude and longitude:
            coordinates = Coordinates(latitude, longitude)
        yield Uik(
            id, name, region_id, region_name, oik,
            tik_id, tik_name, address, coordinates
        )


def dump_odnomandats(odnomandats):
    table = pd.DataFrame(
        [(_.id, _.fio, _.date, _.party_id, _.party_name, _.oik, int(_.nominated))
         for _ in odnomandats],
        columns=['id', 'fio', 'date', 'party_id', 'party_name', 'oik', 'nominated']
    )
    table.to_csv(ODNOMANDATS_DUMP, encoding='utf8', index=False, sep='\t')


def load_odnomandats():
    table = pd.read_csv(ODNOMANDATS_DUMP, encoding='utf8', sep='\t')
    table = table.where(pd.notnull(table), None)
    for _, row in table.iterrows():
        id, fio, date, party_id, party_name, oik, nominated = row
        date = datetime.strptime(date, '%Y-%m-%d')
        nominated = bool(nominated)
        yield OdnomandatSerpRecord(id, fio, date, party_id, party_name, oik, nominated)


def dump_party_cells(cells):
    columns = sorted({_.row_id for _ in cells})
    data = defaultdict(dict)
    for record in cells:
        data[record.uik_id][record.row_id] = record.value
    with open(PARTY_RESULTS_DUMP, 'w') as file:
        write_row(['uik_id'] + columns, file)
        for uik_id in sorted(data):
            chunk = data[uik_id]
            row = [uik_id] + [chunk.get(_) for _ in columns]
            write_row(row, file)


def load_party_cells():
    with open(PARTY_RESULTS_DUMP) as file:
        columns = next(file)
        columns = columns.rstrip('\n').split('\t')
        columns = [(int(_) if _.isdigit() else _) for _ in columns[1:]]
        for line in file:
            line = line.rstrip()
            row = line.split('\t')
            uik_id = row[0]
            if uik_id.isdigit():
                uik_id = int(uik_id)
            
            row = [int(_) for _ in row[1:]]
            assert len(row) == len(columns)
            for row_id, value in zip(columns, row):
                yield ResultsCell(uik_id, row_id, value)


def make_party_cells(uiks, raw_party_cells):
    uik_ids = {(_.tik_id, get_ik_uik_id(_.name)): _.id for _ in uiks}
    row_ids = {_: index for index, _ in enumerate(RESULT_ROWS, 1)}
    tik_oiks = {_.tik_id: _.oik for _ in uiks}
    
    for record in raw_party_cells:
        tik_id = get_url_vibid(record.source)
        id = get_results_uik_id(record.column)
        uik_id = uik_ids[tik_id, id]

        row = record.row.strip()
        if row in row_ids:
            row_id = row_ids[row]
        else:
            # row is party
            row_id = get_party_id(row)
            assert row_id is not None, row
        yield ResultsCell(uik_id, row_id, record.value)


def write_row(row, file):
    line = '\t'.join(
        str(_) if _ is not None else ''
        for _ in row
    )
    file.write(line + '\n')

       
def dump_odnomandat_cells(cells):
    with open(ODNOMANDAT_RESULTS_DUMP, 'w') as file:
        write_row(['uik_id', 'row_id', 'value'], file)
        for record in cells:
            write_row(record, file)


def load_odnomandat_cells():
    with open(ODNOMANDAT_RESULTS_DUMP) as file:
        next(file)
        for line in file:
            line = line.rstrip()
            uik_id, row_id, value = line.split('\t', 2)
            if uik_id.isdigit():
                uik_id = int(uik_id)
            row_id = int(row_id)
            value = int(value)
            yield ResultsCell(uik_id, row_id, value)
