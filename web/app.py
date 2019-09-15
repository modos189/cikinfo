import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import plotly.graph_objs as go
import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import urllib.parse
import textwrap
import database
import math

SITE = 'https://cikinfo.modos189.ru'

metas = [{'property': 'og:image', 'content': SITE + "/data/logo.png"}]
app = dash.Dash(__name__, meta_tags=metas)
app.title = 'ЦИК Инфо | Удобный просмотр статистики избиркома'

client = MongoClient()
db = client.cikinfo
#country_id = db.area.find_one({'name': 'Российская Федерация'}, {'_id': True})['_id']


colors = ['#f44336', '#9C27B0', '#3F51B5', '#03A9F4',
          '#009688', '#8BC34A', '#FF9800', '#E64A19',
          '#5D4037', '#9E9E9E', '#607D8B', '#212121',
          '#F50057', '#651FFF', '#2979FF', '#00E5FF',
          '#00E676', '#AEEA00', '#FFC400', '#FF3D00',
          '#000']

election_type_localization = {
    'edin': "по единому округу",
    'edmj': "по единому мажоритарному округу",
    'edmn': "по единому многомандатному округу",
    'mngm': "по одномандатному (многомандатному) округу"
}

# Возвращает массив маркеров, состоящий из дат начала каждого года и дат выборов
def get_marks():
    marks = {}
    for year in range(2004, datetime.date.today().year + 1):
        marks[datetime.date(year, 1, 1).toordinal()] = {'label': str(year)}

    for election in db.election.find({}, {'date': True}):
        marks[election['date'].toordinal()] = {'label': '|', 'style': {
            'fontSize': '24px',
            'lineHeight': '1px',
            'zIndex': '1',
            'bottom': '26px'
        }}
    print(marks)
    return marks


# Возвращает список процедур выборов, входящих в указанный временной интерва
def get_elections_options(start_date, end_date):
    # from
    start_date = datetime.datetime.combine(start_date, datetime.time.min)
    end_date = datetime.datetime.combine(end_date, datetime.time.min)

    opt = []
    for el in db.election.find({'date': {'$lt': end_date, '$gte': start_date}}):
        opt.append({'label': str(el['date'].year) + ' — ' + el['name'], 'value': el['_id']})
    return opt


# Возвращает список доступных территорий указанного уровня приближения
def get_area_options(level, p, election):
    where = {'results_tags': election, 'level': level, 'max_depth': {'$ne': True}}
    if len(p) > 0 and 'all' not in p:
        parent = [ObjectId(el) for el in p]
        where['parent_id'] = {"$in": parent}

    if level == 0:
        opt = []
    else:
        opt = [{'label': '-= выбрать всё =-', 'value': 'all'}]

    opt.extend([{
                    'label': el['name'] if el['num'] is None else str(el['num']) + ' — ' + el['name'],
                    'value': str(el['_id'])
                } for el in db.area.find(where)])

    return opt


app.layout = html.Div([

    html.Div([
        dcc.RangeSlider(
            id='date-slider',
            min=datetime.date(2003, 9, 28).toordinal(),
            max=(datetime.date.today()+datetime.timedelta(days=1)).toordinal(),
            value=[datetime.date(2016, 1, 1).toordinal(), datetime.date.today().toordinal()],
            marks=get_marks()
        ),
    ], className="date-slider-wrapper"),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='election-type',
                className='election-type',
                placeholder='Выберите тип выборов',
                options=[]
            ),
            dcc.Dropdown(
                id='area-level-0',
                className='area',
                placeholder='Нет данных',
                options=[],
                disabled=True
            ),
            dcc.Dropdown(
                id='area-level-1',
                className='area',
                placeholder='Выберите территорию...',
                options=[],
                multi=True
            ),
            dcc.Dropdown(
                id='area-level-2',
                className='area',
                placeholder='Выберите территорию...',
                options=[],
                multi=True,
                disabled=True
            ),
            dcc.Dropdown(
                id='area-level-3',
                className='area',
                placeholder='Выберите территорию...',
                options=[],
                multi=True,
                disabled=True
            ),
        ], className="left-bar"),
        html.Div([
            html.A([
                html.Img(
                    src="/assets/icon-twitter.svg")
            ],
                href="http://twitter.com/share?text=Найди аномалии на избирательных участках своего города&hashtags=Выборы,ЗаЧестныеВыборы&url=" + SITE,
                target="_blank", id="left-button-twitter"),
            html.A([
                html.Img(
                    src="/assets/icon-vk.svg")
            ], href="https://vk.com/share.php?url=" + SITE, target="_blank", id="left-button-vk"),
            html.A([
                html.Img(
                    src="/assets/icon-help.svg"),
                html.Span(['Помощь'])
            ], href="#", id="left-button-help"),
            html.A([
                html.Img(
                    src="/assets/icon-gitlab.svg"),
                html.Span(['Sources'])
            ], href="https://gitlab.com/modos189/cikinfo", target="_blank", id="left-button-sources"),
        ], id="left-button"),
        html.A([
            html.Div([
                html.I([], id="left-button-donate-icon")
            ], id="left-button-donate-icon-holder"),
            html.Span(['Пожертвовать'], id="left-button-donate-text")
        ], href="https://money.yandex.ru/to/410011752911192/500", id="left-button-donate"),
        html.Div([
        ], id="left-info"),
    ], className="left-bar-wrapper"),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='elections',
                options=[],
                placeholder="Для получения возможности просмотра статистики необходимо выбрать событие",
            )
        ], className="election-bar"),
        dcc.Tabs(
            children=[
                dcc.Tab(label='Доля голосов', value='0'),
                dcc.Tab(label='Поиск перекладок', value='1'),
                dcc.Tab(label='Число участков', value='2'),
                dcc.Tab(label='Кол-во избирателей', value='3'),
                dcc.Tab(label='Номер участка', value='4')
            ],
            value='0',
            id='tabs'
        ),
        html.Div([
            dcc.Graph(id='graph'),
            html.Span('https://cikinfo.modos189.ru', id="watermark")
        ]),
        html.Div(id='selected-data')
    ], className="main-bar"),
    html.Div([
        html.Ul([
            html.Li([
                html.Div([
                    html.H1('Добро пожаловать на сайт ЦИК Инфо'),
                    html.H1('Этот сервис использует официальные данные с сайта '
                            'izbirkom.ru и представляет их в визуальном виде'),
                    html.H1('Если вы здесь в первый раз, нажмите на кнопку справа, чтобы увидеть краткий гайд по '
                            'использованию сервиса')
                ]),
            ], className="help-slide help-slide__showing"),
            html.Li([
                html.Img(src=SITE + "/data/help-img-1.png"),
                html.H1('Первым делом необходимо указать, какие выборы будем анализировать'),
            ], className="help-slide"),
            html.Li([
                html.Img(src=SITE + "/data/help-img-2.png"),
                html.H1('Есть возможность указать временной промежуток, чтобы отфильтровать список выборов'),
            ], className="help-slide"),
            html.Li([
                html.Img(src=SITE + "/data/help-img-3.png"),
                html.H1('Слева можно указать территорию, для которой будет сформирована статистика'),
            ], className="help-slide"),
            html.Li([
                html.Img(src=SITE + "/data/help-img-4.png"),
                html.H1('Статистика формируется в виде четырёх интерактивных графиков'),
            ], className="help-slide"),
            html.Li([
                html.Img(src=SITE + "/data/help-img-5.png"),
                html.H1(['С помощью Box Select или Lasso Select можно выбрать точки на графике, чтобы под графиком '
                         'получить подробную информацию о них, в т.ч. адреса УИКов']),
            ], className="help-slide"),
            html.Li([
                html.Img(src=SITE + "/data/help-img-6.png"),
                html.H1(['Не забудьте поделиться ссылкой с друзьями или пожертвовать на более мощный сервер, если вам '
                         'нравится этот сервис']),
            ], className="help-slide"),
            html.Li([
                html.Div([
                    html.H1('В случае вопросов и предложений, или если нашли ошибку — обращайтесь:'),
                    html.Span('modos189 (собачка) protonmail.com'),
                    html.Span('(telegram): @modos189')
                ]),
            ], className="help-slide"),
        ], id='help'),
        html.Div('❌', className="help-controls help-controls-close", id="help-previous"),
        html.Div('>', className="help-controls", id="help-next"),
        html.Div([], id="help-shadow"),
    ], id="help-wrapper", className="help-wrapper"),
    html.Div([
        dcc.Location(id='test-location', refresh=False),
        html.Div(id='page-url-content'),
        html.Div('', id='page-hack'),
        html.Div('', id='page-hack-2'),
        html.Div('lock', id='graph-lock'),
    ], style={'display': 'none'})
])


@app.callback(
    Output('elections', 'options'),
    [Input('date-slider', 'value')])
def dates_selected(val):
    return get_elections_options(datetime.date.fromordinal(val[0]), datetime.date.fromordinal(val[1]))


########################################################################################################################
# < Синхронизация выбранных значений с URL >
########################################################################################################################
@app.callback(
    [Output('elections', 'value'),
     Output('date-slider', 'value'),
     Output('election-type', 'value'),
     Output('area-level-1', 'value'),
     Output('area-level-2', 'value'),
     Output('area-level-3', 'value'),
     Output('tabs', 'value')],
    [Input('page-url-content', 'children')],
    [State('elections', 'value')]
)
def get_data_from_url_elections(json_data, old_content):
    try:
        data = json.loads(json_data)
    except (TypeError, json.decoder.JSONDecodeError) as err:
        raise PreventUpdate

    if 'elections' in data and\
            'date-slider' in data and \
            'election-type' in data and \
            'area-level-1' in data and\
            'area-level-2' in data and\
            'area-level-3' in data and\
            'tabs' in data:

        return data['elections'],\
               data['date-slider'], \
               data['election-type'],\
               data['area-level-1'],\
               data['area-level-2'],\
               data['area-level-3'],\
               data['tabs']
    else:
        raise PreventUpdate


@app.callback(
    Output('page-url-content', 'children'),
    [Input('page-hack-2', 'children')],
    [State('test-location', 'pathname'), State('page-url-content', 'children')]
)
def get_data_from_url(_, pathname, old_content):
    if pathname is not None:
        json_data = urllib.parse.unquote(pathname)[6:]
        return json_data
    else:
        return '{}'


@app.callback(
    Output('left-button-twitter', 'href'),
    [Input('test-location', 'pathname')])
def update_url_twitter(pathname):
    return "http://twitter.com/share?text=Найди аномалии на избирательных участках своего города&hashtags=Выборы,ЗаЧестныеВыборы&url=" + SITE + pathname


@app.callback(
    Output('left-button-vk', 'href'),
    [Input('test-location', 'pathname')])
def update_url_twitter(pathname):
    return "https://vk.com/share.php?url=" + SITE + pathname


@app.callback(
    output=Output('test-location', 'pathname'),
    inputs=[
        Input('elections', 'value'),
        Input('date-slider', 'value'),
        Input('election-type', 'value'),
        Input('area-level-1', 'value'),
        Input('area-level-2', 'value'),
        Input('area-level-3', 'value'),
        Input('tabs', 'value')
    ],
    state=[State('test-location', 'pathname')])
def update_url_data(election, dateSlider, election_type, areaLevel1, areaLevel2, areaLevel3, tabs, current_pathname):
    if election is None:
        raise PreventUpdate

    json_data = json.dumps({
        'elections': election,
        'date-slider': dateSlider,
        'election-type': election_type,
        'area-level-1': areaLevel1,
        'area-level-2': areaLevel2,
        'area-level-3': areaLevel3,
        'tabs': tabs
    })

    return '/data=' + urllib.parse.quote(json_data, safe='')


@app.callback(
    Output('page-hack-2', 'children'),
    [Input('page-hack', 'children')])
def update_url_data_hack(val):
    return val


########################################################################################################################
# </ Синхронизация выбранных значений с URL >
########################################################################################################################


########################################################################################################################
# < Скрытие и показ полей выбора территории >
########################################################################################################################
@app.callback(
    Output('area-level-3', 'disabled'),
    [Input('area-level-2', 'value'),
     Input('area-level-2', 'options'),
     Input('elections', 'value')])
def area_level_3_disabled(val_raw, opt, election_id):
    if val_raw is None or len(val_raw) == 0 or not any(d['value'] == val_raw[0] for d in opt):
        return True

    val = []
    for i, a in enumerate(val_raw):
        if a != 'all' and type(a) is str:
            val.append(ObjectId(a))

    return db.area.find({
        'results_tags': election_id,
        'parent_id': {'$in': val},
        'max_depth': {'$ne': True}
    }).count() == 0


@app.callback(
    Output('area-level-2', 'disabled'),
    [Input('area-level-1', 'value'),
     Input('area-level-1', 'options')])
def area_level_2_disabled(val, opt):
    return val is None or len(val) == 0 or not any(d['value'] == val[0] for d in opt)


########################################################################################################################
# </ Скрытие и показ полей выбора территории >
########################################################################################################################


########################################################################################################################
# < Вывод статистики по выбранной территории в левом блоке >
########################################################################################################################
@app.callback(
    Output('left-info', 'children'),
    [Input('election-type', 'value'),
     Input('area-level-0', 'value'),
     Input('area-level-1', 'value'),
     Input('area-level-2', 'value'),
     Input('area-level-3', 'value'),
     Input('elections', 'value')],
    [State('area-level-1', 'options'),
     State('area-level-2', 'options'),
     State('area-level-3', 'options')]
)
def left_info_all(election_type, level0_val,
                  level1_val, level2_val, level3_val, election_id,
                  level1_opt, level2_opt, level3_opt):

    if election_type is None or election_id is None:
        return []

    data = database.get_area_by_levels(db, election_id, level0_val,
                                       level1_val, level2_val, level3_val,
                                       level1_opt, level2_opt, level3_opt, statistic_mode=True)
    if data.count() == 0:
        return []

    results = data[0]['results'][election_id][election_type]

    if 'all' not in results:
        return []

    # Суммирование результатов, если выбрано более одной территории
    if data.count() > 1:
        for i, area in enumerate(data):
            # Пропуск первого массива результатов
            if i == 0:
                continue
            res = area['results'][election_id]
            for k in res:
                if str(k).isdigit():
                    results[k] = results[k] + res[k]

    html_candidates = []
    for candidate in results['candidates']:
        percent = round(results['candidates'][candidate] / (results['calculated_number_bulletin']) * 100, 2)
        html_candidates.append(
            html.Div([
                html.P(candidate,
                        title=candidate,
                        className="left-info-name"),
                html.Div([
                    html.Span(html.B(str(percent) + '%')),
                    html.Span('(' + str(results['candidates'][candidate]) + ')')
                ], className="left-info-num", id='left-info-candidates'),
            ], style={'order': int(results['candidates'][candidate])}),
        )
    results['calculated_share'] = round(float(results['calculated_number_bulletin']) / results['all'] * 100, 2)

    return [
        html.Div([
            html.Div([
                html.Div([
                    html.P('Всего избирателей:', className="left-info-name"),
                    html.P(results['all'], className="left-info-num", id='left-info-all'),
                ], title="Число избирателей, внесенных в список избирателей на момент окончания голосования"),
                html.Div([
                    html.P('Голосов в помещении:', className="left-info-name"),
                    html.P(results['in_room'], className="left-info-num", id='left-info-indoors'),
                ], title="Число избирательных бюллетеней, выданных в помещении для голосования в день голосования"),
                html.Div([
                    html.P('Голосов вне помещения:', className="left-info-name"),
                    html.P(results['out_room'], className="left-info-num", id='left-info-outdoors'),
                ], title="Число избирательных бюллетеней, выданных вне помещения для голосования в день голосования"),
            ], className="left-info-block left-info-block-stat"),
            html.Div([
                html.Div([html.B([str(results['calculated_share']) + '%']), ' явка']),
            ], className="left-info-block left-info-block-share"),
        ], className="left-info-head"),
        html.Div(html_candidates, className="left-info-block left-info-block-candidates"),
    ]


########################################################################################################################
# </ Вывод статистики по выбранной территории в левом блоке >
########################################################################################################################


@app.callback(
    Output('area-level-3', 'options'),
    [Input('area-level-2', 'value'),
     Input('elections', 'value')])
def area_level_3_options(level_2, election):
    if level_2 is None or len(level_2) == 0:
        return []
    level = 3
    r = get_area_options(level, level_2, election)
    return r


@app.callback(
    [Output('graph-lock', 'children'),
     Output('area-level-2', 'options')],
    [Input('area-level-1', 'value'),
     Input('elections', 'value')])
def area_level_2_options(parent, election):
    if parent is None or len(parent) == 0:
        return "lock", []
    level = 2
    return "unlock", get_area_options(level, parent, election)


@app.callback(
    Output('area-level-1', 'options'),
    [Input('elections', 'value')])
def area_level_1_options(election):
    if election is None:
        return []
    level = 1
    return get_area_options(level, [], election)


@app.callback(
    [Output('area-level-0', 'options'), Output('area-level-0', 'value')],
    [Input('elections', 'value')])
def area_level_0_options(election):
    if election is None:
        raise PreventUpdate

    level = 0
    options = get_area_options(level, [], election)

    if len(options) == 0:
        return [], None

    return options, options[0]['value']


@app.callback(
    Output('election-type', 'options'),
    [Input('elections', 'value')])
def election_types_options(election):
    if election is None:
        raise PreventUpdate

    options = []
    for sub in db.election.find_one({'_id': election}, {'sub_elections': True})['sub_elections']:
        options.append({'label': election_type_localization.get(sub, sub), 'value': sub})

    return options


@app.callback(
    Output('graph', 'figure'),
    [Input('graph-lock', 'children'),
     Input('election-type', 'value'),
     Input('area-level-0', 'value'),
     Input('area-level-1', 'value'),
     Input('area-level-2', 'value'),
     Input('area-level-3', 'value'),
     Input('tabs', 'value')],
    [State('area-level-1', 'options'),
     State('area-level-2', 'options'),
     State('area-level-3', 'options'),
     State('elections', 'value')]
)
def update_graph(graph_lock, election_type, level0_val,
                 level1_val, level2_val, level3_val, tab,
                 level1_opt, level2_opt, level3_opt, election_id):

    if graph_lock == 'lock':
        return {}

    if election_type is None or election_id is None:
        return {}

    data = database.get_area_by_levels(db, election_id, level0_val,
                                       level1_val, level2_val, level3_val,
                                       level1_opt, level2_opt, level3_opt)
    uiks = list(data)

    l = data.count()
    if l < 500:
        point_size = 8
        point_opacity = 0.5
    elif l <= 5000:
        point_size = 6
        point_opacity = 0.4
    elif l > 5000:
        point_size = 4
        point_opacity = 0.3

    k = 0
    markers = []

    xaxis_title = "Явка"
    xaxis_range = [0, 105]
    yaxis_title = ""
    autorange = False
    if tab == '0':
        yaxis_title = "Доля голосов"
        autorange = False
        hovermode = 'closest'

        if len(uiks) < 2 or \
                uiks[0]['results'][election_id][election_type]['candidates'].keys() != uiks[-1]['results'][election_id][election_type]['candidates'].keys():
            return {}

        for candidate in uiks[0]['results'][election_id][election_type]['candidates']:

            share_votes = [(int(item['results'][election_id][election_type]['candidates'][candidate]) /
                            item['results'][election_id][election_type]['calculated_number_bulletin'] * 100)
                           if item['results'][election_id][election_type]['calculated_number_bulletin'] > 0 else 0
                           for item in uiks]

            markers.append(
                go.Scattergl(
                    x=[item['results'][election_id][election_type]['calculated_share'] for item in uiks],
                    y=share_votes,
                    text=[
                        item['name'] + '</br>'
                        + 'Всего избирателей: ' + str(item['results'][election_id][election_type]['all']) + '</br>'
                        + 'Голос в помещении: ' + str(item['results'][election_id][election_type]['in_room']) + '</br>'
                        + 'Голос вне помещения: ' + str(item['results'][election_id][election_type]['out_room']) for item in uiks],
                    customdata=[{
                                    'name': item['name'],
                                    'address': (item['address'] if 'address' in item else ''),
                                    'total': item['results'][election_id][election_type]['all'],
                                    'votes_inroom': item['results'][election_id][election_type]['in_room'],
                                    'votes_outroom': item['results'][election_id][election_type]['out_room'],
                                    'calculated_share': item['results'][election_id][election_type]['calculated_share']
                                } for item in uiks],
                    name=textwrap.fill(candidate, 32).replace("\n", "<br>"),
                    mode='markers',
                    marker={
                        'sizemode': 'area',
                        'color': colors[k],
                        'size': point_size,
                        'opacity': point_opacity,
                        'line': {'width': 0.1, 'color': 'white'}
                    }
            )
            )
            k += 1

    if tab == '1':
        xaxis_title = "Доля голосов за победителя"
        yaxis_title = "Процент кандидата от пула голосов за оппозицию"
        autorange = False
        hovermode = 'closest'

        if len(uiks) < 2 or \
                uiks[0]['results'][election_id][election_type]['candidates'].keys() != uiks[-1]['results'][election_id][election_type]['candidates'].keys():
            return {}

        parent_data = database.get_area_by_levels(db, election_id, level0_val,
                                           level1_val, level2_val, level3_val,
                                           level1_opt, level2_opt, level3_opt, statistic_mode=True)
        if parent_data.count() == 0:
            return []

        parent_results = parent_data[0]['results'][election_id][election_type]

        if 'all' not in parent_results or len(parent_results['candidates']) == 0:
            return []

        winners = {}
        for candidate in parent_results['candidates']:
            per = parent_results['candidates'][candidate] / (parent_results['calculated_number_bulletin']) * 100
            winners[candidate] = per

        winner = max(winners, key=winners.get)

        share_winner = [(int(item['results'][election_id][election_type]['candidates'][winner]) /
                        item['results'][election_id][election_type]['calculated_number_bulletin'] * 100)
                       if item['results'][election_id][election_type]['calculated_number_bulletin'] > 0 else 0
                       for item in uiks]

        for candidate in uiks[0]['results'][election_id][election_type]['candidates']:

            if candidate == winner:
                continue

            share_candidate = []
            for item in uiks:
                if item['results'][election_id][election_type]['calculated_number_bulletin'] > 0:

                    pool = 0
                    for c in item['results'][election_id][election_type]['candidates']:
                        if c != winner:
                            pool += item['results'][election_id][election_type]['candidates'][c]

                    share_from_pool = 0
                    if pool > 0:
                        share_from_pool = item['results'][election_id][election_type]['candidates'][
                                              candidate] / pool * 100
                    share_candidate.append(share_from_pool)
                else:
                    share_candidate.append(0)

            share_data = {}
            for i, item in enumerate(share_winner):
                round_x = round(share_winner[i])
                if round_x in share_data:
                    share_data[round_x].append(share_candidate[i])
                else:
                    share_data[round_x] = [share_candidate[i]]

            for sh_k in share_data:
                avg = sum(share_data[sh_k]) / len(share_data[sh_k])
                share_data[sh_k] = avg

            markers.append(
                go.Bar(
                    x=list(share_data.keys()),
                    y=list(share_data.values()),
                    name=textwrap.fill(candidate, 32).replace("\n", "<br>"),
                    marker={
                        'color': colors[k],
                        'opacity': point_opacity
                    }
                )
            )
            k += 1

        return {
            'data': markers,
            'layout': go.Layout(
                xaxis={
                    'title': xaxis_title,
                    'range': xaxis_range
                },
                yaxis={
                    'title': yaxis_title,
                    'range': [0, 105],
                    'autorange': autorange
                },
                margin=go.Margin(
                    l=80,
                    r=30,
                    b=55,
                    t=10
                ),
                legend=go.Legend(
                    x=0,
                    y=1
                ),
                barmode='stack',
                height=550,
                hovermode=hovermode
            )
        }

    elif tab == '2':
        autorange = True
        hovermode = 'x'

        if l < 1000000:
            yaxis_title = "Кол-во избирательных участков (в 1% интервале явки)"
            rou = 1
        else:
            yaxis_title = "Кол-во избирательных участков (в 0.1% интервале явки)"
            rou = 10

        data = [0 for _ in range(100 * rou + 1)]
        for uik in uiks:
            if uik['results'][election_id][election_type]['all'] > 500:
                share = uik['results'][election_id][election_type]['calculated_share']
                share = math.floor(share * rou)
                data[share] += 1

        markers.append(
            go.Scattergl(
                x=[i / rou for i, item in enumerate(data)],
                y=[item for item in data],
                mode='lines',
                marker={
                    'color': colors[4],
                    'opacity': point_opacity
                }
            )
        )

    elif tab == '3':
        yaxis_title = "Кол-во избирателей"
        autorange = True
        hovermode = 'closest'

        number_of_voters = [item['results'][election_id][election_type]['all'] for item in uiks]

        markers.append(
            go.Scattergl(
                x=[item['results'][election_id][election_type]['calculated_share'] for item in uiks],
                y=number_of_voters,
                text=[
                    item['name'] + '</br>'
                    + 'Всего избирателей: ' + str(item['results'][election_id][election_type]['all']) + '</br>'
                    + 'Голос в помещении: ' + str(item['results'][election_id][election_type]['in_room']) + '</br>'
                    + 'Голос вне помещения: ' + str(item['results'][election_id][election_type]['out_room']) for item in uiks],
                customdata=[{
                                'name': item['name'],
                                'address': (item['address'] if 'address' in item else ''),
                                'total': item['results'][election_id][election_type]['all'],
                                'votes_inroom': item['results'][election_id][election_type]['in_room'],
                                'votes_outroom': item['results'][election_id][election_type]['out_room'],
                                'calculated_share': item['results'][election_id][election_type]['calculated_share']
                            } for item in uiks],
                # name=textwrap.fill(m['name_simple'], 32).replace("\n", "<br>"),
                mode='markers',
                showlegend=False,
                marker={
                    'color': colors[0],
                    'size': point_size,
                    'opacity': point_opacity,
                    'line': {'width': 0.5, 'color': 'white'}
                }
            )
        )

    elif tab == '4':
        xaxis_title = "Номера участков"
        xaxis_range = None
        yaxis_title = "Явка"
        autorange = True
        hovermode = 'x'

        if len(uiks) > 0 and 'num' in uiks[0] and uiks[0]['num'] is not None:
            # Сортировка по номеру
            OrderCol = sorted(uiks, key=lambda k: k['num'])

            markers.append(
                go.Bar(
                    # добавлен невидимый символ к номеру, чтобы библиотека визуализации данных обрабатывала как текст
                    # и не делала пропуски, если участки идут не подряд
                    x=[str(item['num']) + ' ​' for item in OrderCol],
                    y=[item['results'][election_id][election_type]['calculated_share'] for item in OrderCol],
                    text=[
                        item['name'] + '</br>'
                        + 'Всего избирателей: ' + str(item['results'][election_id][election_type]['all']) + '</br>'
                        + 'Голос в помещении: ' + str(item['results'][election_id][election_type]['in_room']) + '</br>'
                        + 'Голос вне помещения: ' + str(item['results'][election_id][election_type]['out_room']) for item in OrderCol],
                    customdata=[{
                                    'name': item['name'],
                                    'address': (item['address'] if 'address' in item else ''),
                                    'total': item['results'][election_id][election_type]['all'],
                                    'votes_inroom': item['results'][election_id][election_type]['in_room'],
                                    'votes_outroom': item['results'][election_id][election_type]['out_room'],
                                    'calculated_share': item['results'][election_id][election_type]['calculated_share']
                                } for item in OrderCol],
                    marker={
                        'color': colors[8],
                        'opacity': 0.5,
                        'line': {'width': 0.5, 'color': 'white'}
                    }
                )
            )

    return {
        'data': markers,
        'layout': go.Layout(
            xaxis={
                'title': xaxis_title,
                'range': xaxis_range
            },
            yaxis={
                'title': yaxis_title,
                'range': [0, 105],
                'autorange': autorange
            },
            margin=go.Margin(
                l=80,
                r=30,
                b=55,
                t=10
            ),
            legend=go.Legend(
                x=0,
                y=1
            ),
            height=550,
            hovermode=hovermode
        )
    }


########################################################################################################################
# < Отображение подробной информации о выбранных на графике участках >
########################################################################################################################
@app.callback(
    Output('selected-data', 'children'),
    [Input('graph', 'selectedData')],
    [State('elections', 'value')]
)
def display_selected_data(selectedData, election_id):
    if selectedData is None or len(selectedData['points']) == 0:
        return ''

    points = set()
    data = []

    for el in selectedData['points']:
        if el['pointNumber'] not in points:
            points.add(el['pointNumber'])

            data.append(
                html.Div([
                    html.P(el['customdata']['name'] + ' | ' +
                           'Всего избирателей: ' + str(el['customdata']['total']) + ' | ' +
                           'Голосов в помещении: ' + str(el['customdata']['votes_inroom']) + ' | ' +
                           'Голосов вне помещения: ' + str(el['customdata']['votes_outroom']) + ' | ' +
                           'Явка: ' + str(el['customdata']['calculated_share']) + '%'),
                    html.P(el['customdata']['address']),
                ], className="selected-data-block")
            )

    data.insert(0, html.Div([
        html.P("Количество выбранных УИКов: "+str(len(points)))
    ], className="selected-data-block"))

    return data


########################################################################################################################
# </ Отображение подробной информации о выбранных на графике участках >
########################################################################################################################


if __name__ == '__main__':
    app.run_server(debug=True)
