import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import datetime
from datetime import datetime as dt
from pymongo import MongoClient
from bson.objectid import ObjectId

import textwrap
#import database

app = dash.Dash()

app.css.append_css({
    "external_url": "http://modos189.lh/style.css"
})
#app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

client = MongoClient()
db = client.cikinfo_beta

colors = ['#f44336', '#9C27B0', '#3F51B5', '#03A9F4',
          '#009688', '#8BC34A', '#FF9800', '#E64A19',
          '#5D4037', '#9E9E9E', '#607D8B', '#212121',
          '#F50057', '#651FFF', '#2979FF', '#00E5FF',
          '#00E676', '#AEEA00', '#FFC400', '#FF3D00']


def get_marks():
    marks = {}
    for year in range(2004, datetime.date.today().year+1):
        marks[datetime.date(year, 1, 1).toordinal()] = {'label': year}

    for election in db.election.find({}, {'date': True}):
        marks[election['date'].toordinal()] = {'label': '|', 'style': {'color': '#f50'}}

    return marks


def get_elections_options(start_date, end_date):
    # from
    start_date = datetime.datetime.combine(start_date, datetime.time.min)
    end_date = datetime.datetime.combine(end_date, datetime.time.min)

    opt = []
    for el in db.election.find({'date': {'$lt': end_date, '$gte': start_date}}):
        opt.append({'label': el['name'], 'value': el['_id']})
    return opt


def get_area_options(level, p, election):
    where = {'results.election_id': election, 'level': level}
    if len(p) > 0:
        parent = []
        for el in p:
            parent.append(ObjectId(el))
        where['parent_id'] = {"$in": parent}

    opt = []

    for el in db.area.find(where):
        opt.append({'label': el['name'], 'value': str(el['_id'])})
    return opt


app.layout = html.Div([

    html.Div([
        dcc.RangeSlider(
            id='date-slider',
            min=datetime.date(2003, 9, 28).toordinal(),
            max=datetime.date.today().toordinal(),
            value=[datetime.date(2016, 1, 1).toordinal(), datetime.date.today().toordinal()],
            marks=get_marks()
        ),
    ], className="date-slider-wrapper"),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id='area-level-0',
                className='area',
                options=[{'label': "Российская Федерация", 'value': "Российская Федерация"}],
                value='Российская Федерация',
                clearable=False
            ),
            dcc.Dropdown(
                id='area-level-1',
                className='area',
                options=[],
                multi=True
            ),
            dcc.Dropdown(
                id='area-level-2',
                className='area',
                options=[],
                multi=True,
                disabled=True
            ),
            dcc.Dropdown(
                id='area-level-3',
                className='area',
                options=[],
                multi=True,
                disabled=True
            ),
        ], className="left-bar"),
        html.Div([
        ], id="left-info"),
    ], className="left-bar-wrapper"),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='elections',
                options=[],
                placeholder="Выберите выборы",
            )
        ], className="election-bar"),
        dcc.Tabs(
            tabs=[
                {'label': 'Явка / % от списочного состава', 'value': 0},
                {'label': 'Явка / Число участков', 'value': 1},
                {'label': 'Явка / Кол-во избирателей', 'value': 2}
                ],
            value=0,
            id='tabs'
        ),
        html.Div(id='tab-output'),
    ], className="main-bar")
])


@app.callback(
    Output('elections', 'options'),
    [Input('date-slider', 'value')])
def dates_selected(val):
    return get_elections_options(datetime.date.fromordinal(val[0]), datetime.date.fromordinal(val[1]))


@app.callback(
    Output('area-level-1', 'options'),
    [Input('elections', 'value')])
def area_level_1_options(election):
    if election is None:
        return []

    level = 1
    return get_area_options(level, [], election)


@app.callback(
    Output('area-level-2', 'options'),
    [Input('area-level-1', 'value'),
     Input('elections', 'value')])
def area_level_2_options(parent, election):
    if parent is None or len(parent) == 0:
        return []
    level = 2
    return get_area_options(level, parent, election)


@app.callback(
    Output('area-level-3', 'options'),
    [Input('area-level-1', 'value'),
     Input('area-level-2', 'value'),
     Input('elections', 'value')])
def area_level_3_options(_, parent, election):
    if parent is None or len(parent) == 0:
        return []
    level = 3
    return get_area_options(level, parent, election)


@app.callback(
    Output('area-level-2', 'disabled'),
    [Input('area-level-1', 'value')])
def area_level_2_options(val):
    return val is None or len(val) == 0


@app.callback(
    Output('area-level-3', 'disabled'),
    [Input('area-level-2', 'value')])
def area_level_2_options(val):
    return val is None or len(val) == 0


@app.callback(
    Output('left-info', 'children'),
    [Input('area-level-1', 'value'),
     Input('area-level-2', 'value'),
     Input('area-level-3', 'value'),
     Input('elections', 'value')])
def left_info_all(level1, level2, level3, election):

    if level3 is not None and len(level3) > 0:
        area = level3
    elif level2 is not None and len(level2) > 0:
        area = level2
    elif level1 is not None and len(level1) > 0:
        area = level1
    else:
        area = [db.area.find_one({'name': 'Российская Федерация'}, {'_id': True})['_id']]

    for i, a in enumerate(area):
        if type(a) is str:
            print("in type(a)")
            area[i] = ObjectId(a)

    data = db.area.find({'results.election_id': election, '_id': {'$in': area}}, {'name': True, 'results.$': True})

    if data.count() == 0:
        return

    results = data[0]['results'][0]
    # Суммирование результатов, если выбрано более одной территории
    if data.count() > 1:
        for i, area in enumerate(data):
            # Пропуск первого массива результатов
            if i == 0:
                continue
            res = area['results'][0]
            for k in res:
                if str(k).isdigit():
                    results[k] = str(int(results[k]) + int(res[k]))

    html_candidates = []
    for i, cand in enumerate(db.election.find_one({'_id': election})['meta']):
        if cand['is_meta'] is False:
            percent = round(int(results[str(i)]) / int(results['1']) * 100, 2)
            html_candidates.append(
                html.Div([
                    html.P(cand['name_simple'],
                           title=cand['name'],
                           className="left-info-name"),
                    html.P(str(percent)+'% ('+str(results[str(i)])+')',
                           className="left-info-num", id='left-info-candidates'),
                ]),
            )

    return html.Div([
            html.Div([
                html.Div([
                    html.P('Всего избирателей:', className="left-info-name"),
                    html.P(results['0'], className="left-info-num", id='left-info-all'),
                ], title="Число избирателей, внесенных в список избирателей на момент окончания голосования"),
                html.Div([
                    html.P('Голосов в помещении:', className="left-info-name"),
                    html.P(results['3'], className="left-info-num", id='left-info-indoors'),
                ], title="Число избирательных бюллетеней, выданных в помещении для голосования в день голосования"),
                html.Div([
                    html.P('Голосов вне помещения:', className="left-info-name"),
                    html.P(results['4'], className="left-info-num", id='left-info-outdoors'),
                ], title="Число избирательных бюллетеней, выданных вне помещения для голосования в день голосования"),
            ]),
            html.Div(html_candidates),
        ])


@app.callback(Output('tab-output', 'children'), [
    Input('area-level-1', 'value'),
    Input('area-level-2', 'value'),
    Input('area-level-3', 'value'),
    Input('elections', 'value'),
    Input('tabs', 'value')
])
def update_graph(level1, level2, level3, election_id, tab):
    if election_id is None:
        return html.Div([])

    if level3 is not None and len(level3) > 0:
        area = level3
    elif level2 is not None and len(level2) > 0:
        area = level2
    elif level1 is not None and len(level1) > 0:
        area = level1
    else:
        area = [db.area.find_one({'name': 'Российская Федерация'}, {'_id': True})['_id']]

    for i, a in enumerate(area):
        if type(a) is str:
            area[i] = ObjectId(a)

    where = {'results.election_id': election_id, 'parent_id': {'$in': area}}
    col = list(db.area.find(where, {'name': True, 'results.$': True}).limit(1000)) # TODO

    k = 0
    markers = []

    yaxis_title = ""
    autorange = False
    if tab == 0:
        yaxis_title = "Доля голосов"
        autorange = False

        for i, m in enumerate(db.election.find_one({'_id': election_id})['meta']):
            if m is None:
                continue
            if not m['is_meta']:

                markers.append(
                    go.Scattergl(
                        x=[(int(item['results'][0]['6'])+int(item['results'][0]['7'])) /
                           int(item['results'][0]['0']) * 100
                           for item in col],
                        y=[int(item['results'][0][str(i)]) /
                           (int(item['results'][0]['8'])+int(item['results'][0]['9'])) * 100
                           for item in col],
                        text=[
                            item['name'] + '</br>'
                            + 'Всего избирателей: ' + str(item['results'][0]['0']) + '</br>'
                            + 'Голос в помещении: ' + str(item['results'][0]['3']) + '</br>'
                            + 'Голос вне помещения: ' + str(item['results'][0]['4']) for item in col],
                        customdata=[item['name'] for item in col],
                        name=textwrap.fill(m['name_simple'], 32).replace("\n", "<br>"),
                        mode='markers',
                        marker={
                            'color': colors[k],
                            'size': 8,
                            'opacity': 0.5,
                            'line': {'width': 0.5, 'color': 'white'}
                        }
                    )
                )
                k += 1

    elif tab == 1:
        yaxis_title = "Кол-во избирательных участков (в 1% интервале явки)"
        autorange = True

        data = [0 for _ in range(101)]
        for uik in col:
            share = (int(uik['results'][0]['6']) + int(uik['results'][0]['7'])) / int(uik['results'][0]['0']) * 100
            share = round(share)
            data[share] += 1

        markers.append(
            go.Scattergl(
                x=[i for i, item in enumerate(data)],
                y=[item for item in data],
                # text=[
                #     item['name'] + '</br>'
                #     + 'Всего избирателей: ' + str(item['results'][0]['1']) + '</br>'
                #     + 'Голос в помещении: ' + str(item['results'][0]['3']) + '</br>'
                #     + 'Голос вне помещения: ' + str(item['results'][0]['4']) for item in col],
                # customdata=[item['name'] for item in col],
                # name=textwrap.fill(m['name_simple'], 32).replace("\n", "<br>"),
                mode='lines',
                marker={
                    'color': colors[k],
                    'size': 8,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'}
                }
            )
        )

    elif tab == 2:
        yaxis_title = "Кол-во избирателей"
        autorange = True

        markers.append(
            go.Scattergl(
                x=[(int(item['results'][0]['6']) + int(item['results'][0]['7'])) /
                   int(item['results'][0]['0']) * 100
                   for item in col],
                y=[int(item['results'][0][str('0')]) for item in col],
                text=[
                    item['name'] + '</br>'
                    + 'Всего избирателей: ' + str(item['results'][0]['0']) + '</br>'
                    + 'Голос в помещении: ' + str(item['results'][0]['3']) + '</br>'
                    + 'Голос вне помещения: ' + str(item['results'][0]['4']) for item in col],
                customdata=[item['name'] for item in col],
                # name=textwrap.fill(m['name_simple'], 32).replace("\n", "<br>"),
                mode='markers',
                marker={
                    'color': colors[k],
                    'size': 8,
                    'opacity': 0.5,
                    'line': {'width': 0.5, 'color': 'white'}
                }
            )
        )




            #     ['connectgaps', 'customdata', 'customdatasrc', 'dx', 'dy', 'error_x',
#     'error_y', 'fill', 'fillcolor', 'hoverinfo', 'hoverinfosrc',
#     'hoverlabel', 'hoveron', 'ids', 'idssrc', 'legendgroup', 'line',
#     'marker', 'mode', 'name', 'opacity', 'selected', 'selectedpoints',
#     'showlegend', 'stream', 'text', 'textsrc', 'type', 'uid', 'unselected',
#     'visible', 'x', 'x0', 'xaxis', 'xcalendar', 'xsrc', 'y', 'y0', 'yaxis',
#     'ycalendar', 'ysrc']

    return html.Div([
        dcc.Graph(
            id='graph',
            figure={
                'data': markers,
                'layout': go.Layout(
                    xaxis={
                        'title': "Явка",
                        'type': 'linear',  # if xaxis_type == 'Linear' else 'log'
                        'range': [0, 105]
                    },
                    yaxis={
                        'title': yaxis_title,
                        'type': 'linear',  # if yaxis_type == 'Linear' else 'log'
                        'range': [0, 105],
                        'autorange': autorange
                    },
                    margin=go.Margin(
                        l=80,
                        r=30,
                        b=40,
                        t=10
                    ),
                    legend=go.Legend(
                        x=0,
                        y=1
                    ),
                    height=550
                )
            }
        ),
        html.Div(' ')
    ])

if __name__ == '__main__':
    app.run_server(debug=True)
