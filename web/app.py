import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

import textwrap


class Dash_responsive(dash.Dash):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    #Overriding from https://github.com/plotly/dash/blob/master/dash/dash.py#L282
    def index(self, *args, **kwargs):
        scripts = self._generate_scripts_html()
        css = self._generate_css_dist_html()
        config = self._generate_config_html()
        title = getattr(self, 'title', 'Dash')
        return ('''
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8"/>
                <meta property="og:image" content="https://cikinfo.modos189.ru/data/logo.png">
                <title>{}</title>
                {}
            </head>
            <body>
                <div id="react-entry-point">
                    <div class="_dash-loading">
                        Loading...
                    </div>
                </div>
            </body>
            <footer>
                {}
                {}
            </footer>
        </html>
        '''.format(title, css, config, scripts))


app = Dash_responsive()
app.title = 'ЦИК Инфо | Удобный просмотр статистики избиркома'
app.css.append_css({
    "external_url": ["https://cikinfo.modos189.ru/data/user.css",
                     "https://cikinfo.modos189.ru/data/pace-theme-flash.css"]
})
app.scripts.append_script({
    "external_url": ["https://cikinfo.modos189.ru/data/user.js",
                     "https://cikinfo.modos189.ru/data/pace.min.js"]
})

client = MongoClient()
db = client.cikinfo_beta2

colors = ['#f44336', '#9C27B0', '#3F51B5', '#03A9F4',
          '#009688', '#8BC34A', '#FF9800', '#E64A19',
          '#5D4037', '#9E9E9E', '#607D8B', '#212121',
          '#F50057', '#651FFF', '#2979FF', '#00E5FF',
          '#00E676', '#AEEA00', '#FFC400', '#FF3D00']


# Возвращает массив маркеров, состоящий из дат начала каждого года и дат выборов
def get_marks():
    marks = {}
    for year in range(2004, datetime.date.today().year+1):
        marks[datetime.date(year, 1, 1).toordinal()] = {'label': year}

    for election in db.election.find({}, {'date': True}):
        marks[election['date'].toordinal()] = {'label': '|', 'style': {
            'fontSize': '20px',
            'lineHeight': '1px',
            'zIndex': '1'
        }}

    return marks


# Возвращает список процедур выборов, входящих в указанный временной интерва
def get_elections_options(start_date, end_date):
    # from
    start_date = datetime.datetime.combine(start_date, datetime.time.min)
    end_date = datetime.datetime.combine(end_date, datetime.time.min)

    opt = []
    for el in db.election.find({'date': {'$lt': end_date, '$gte': start_date}}):
        opt.append({'label': el['name'], 'value': el['_id']})
    return opt


# Возвращает список доступных территорий указанного уровня приближения
def get_area_options(level, p, election):
    where = {'results_tags': election, 'level': level, 'max_depth': {'$ne': True}}
    if len(p) > 0:
        parent = [ObjectId(el) for el in p]
        where['parent_id'] = {"$in": parent}

    opt = [{'label': el['name'], 'value': str(el['_id'])} for el in db.area.find(where)]
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
                html.Img(src="""data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiA/PjwhRE9DVFlQRSBzdmcgIFBVQkxJQy"""+
                """AnLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTE"""+
                """uZHRkJz48c3ZnIGVuYWJsZS1iYWNrZ3JvdW5kPSJuZXcgMCAwIDU2LjY5MyA1Ni42OTMiIGhlaWdodD0iNTYuNjkzcHgiIGlk"""+
                """PSJMYXllcl8xIiB2ZXJzaW9uPSIxLjEiIHZpZXdCb3g9IjAgMCA1Ni42OTMgNTYuNjkzIiB3aWR0aD0iNTYuNjkzcHgiIHhtb"""+
                """DpzcGFjZT0icHJlc2VydmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6eGxpbms9Imh0dHA6Ly"""+
                """93d3cudzMub3JnLzE5OTkveGxpbmsiPjxwYXRoIGZpbGw9IiM0NDQiIGQ9Ik01Mi44MzcsMTUuMDY1Yy0xLjgxMSwwLjgwNS0"""+
                """zLjc2LDEuMzQ4LTUuODA1LDEuNTkxYzIuMDg4LTEuMjUsMy42ODktMy4yMyw0LjQ0NC01LjU5MmMtMS45NTMsMS4xNTktNC4x"""+
                """MTUsMi02LjQxOCwyLjQ1NCAgYy0xLjg0My0xLjk2NC00LjQ3LTMuMTkyLTcuMzc3LTMuMTkyYy01LjU4MSwwLTEwLjEwNiw0L"""+
                """jUyNS0xMC4xMDYsMTAuMTA3YzAsMC43OTEsMC4wODksMS41NjIsMC4yNjIsMi4zMDMgIGMtOC40LTAuNDIyLTE1Ljg0OC00Lj"""+
                """Q0NS0yMC44MzMtMTAuNTZjLTAuODcsMS40OTItMS4zNjgsMy4yMjgtMS4zNjgsNS4wODJjMCwzLjUwNiwxLjc4NCw2LjYsNC4"""+
                """0OTYsOC40MTIgIGMtMS42NTYtMC4wNTMtMy4yMTUtMC41MDgtNC41NzgtMS4yNjVjLTAuMDAxLDAuMDQyLTAuMDAxLDAuMDg1"""+
                """LTAuMDAxLDAuMTI4YzAsNC44OTYsMy40ODQsOC45OCw4LjEwOCw5LjkxICBjLTAuODQ4LDAuMjMtMS43NDEsMC4zNTQtMi42N"""+
                """jMsMC4zNTRjLTAuNjUyLDAtMS4yODUtMC4wNjMtMS45MDItMC4xODJjMS4yODcsNC4wMTUsNS4wMTksNi45MzgsOS40NDEsNy"""+
                """4wMTkgIGMtMy40NTksMi43MTEtNy44MTYsNC4zMjctMTIuNTUyLDQuMzI3Yy0wLjgxNSwwLTEuNjItMC4wNDgtMi40MTEtMC4"""+
                """xNDJjNC40NzQsMi44NjksOS43ODYsNC41NDEsMTUuNDkzLDQuNTQxICBjMTguNTkxLDAsMjguNzU2LTE1LjQsMjguNzU2LTI4"""+
                """Ljc1NmMwLTAuNDM4LTAuMDA5LTAuODc1LTAuMDI4LTEuMzA5QzQ5Ljc2OSwxOC44NzMsNTEuNDgzLDE3LjA5Miw1Mi44MzcsM"""+
                """TUuMDY1eiIvPjwvc3ZnPg==""")
            ], href="http://twitter.com/share?text=Найди фальсификации на избирательных участках своего города&hashtags=Выборы,ЗаЧестныеВыборы&url=https://cikinfo.modos189.ru", target="_blank", id="left-button-twitter"),
            html.A([
                html.Img(src="""data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiA/PjwhRE9DVFlQRSBzdmcgIFBVQkxJQy"""+
                """AnLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTE"""+
                """uZHRkJz48c3ZnIGVuYWJsZS1iYWNrZ3JvdW5kPSJuZXcgMCAwIDEwMCAxMDAiIGhlaWdodD0iMTAwcHgiIHZlcnNpb249IjEu"""+
                """MSIgdmlld0JveD0iMCAwIDEwMCAxMDAiIHdpZHRoPSIxMDBweCIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSIgeG1sbnM9Imh0dHA6L"""+
                """y93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayI+PGcgaWQ9Im"""+
                """NvbG9yX3g1Rl9maWxsIj48cGF0aCBkPSJNODQuNDE4LDY5LjkyMWMtMi41MjcsMS41ODMtMTIuODA3LDIuMDU0LTE1LjI5NSw"""+
                """wLjI0NmMtMS4zNjUtMC45OTEtMi42MTMtMi4yMzItMy43OTktMy40MTIgICBjLTAuODI4LTAuODI2LTEuNzctMS4yMjctMi40"""+
                """ODItMi4xMjNjLTAuNTgtMC43MzQtMC45NzktMS41OTktMS41OTItMi4zMjFjLTEuMDMzLTEuMjE1LTIuNjI1LTIuMjQ4LTMuO"""+
                """Dg1LTAuNzY0ICAgYy0xLjg5NSwyLjIzMSwwLjI5OSw2LjYxNy0yLjIyOSw4LjI4NWMtMC44NDgsMC41Ni0xLjcwMywwLjcyMi"""+
                """0yLjc2MiwwLjY0MmwtMi4zNDYsMC4xMDdjLTEuMzc5LDAuMDI3LTMuNTYyLDAuMDM5LTUuMTI5LTAuMjQ0ICAgYy0xLjc1LTA"""+
                """uMzE1LTMuMTkzLTEuMjcxLTQuNzczLTEuOTczYy0zLjAwMi0xLjMzMS01Ljg2My0zLjE0NS04LjAzOS01LjY1OGMtNS45MjIt"""+
                """Ni44NDMtMTMuODc3LTE2LjI1NS0xNi45NjctMjQuODU5ICAgYy0wLjYzNy0xLjc2OC0yLjMxNC01LjI2Ny0wLjcyMy02Ljc4N"""+
                """GMyLjE2NC0xLjU3MiwxMi43ODktMi4wMTcsMTQuNDQ1LDAuNDE2YzAuNjc0LDAuOTg3LDEuMDk4LDIuNDM2LDEuNTc0LDMuNT"""+
                """U1ICAgYzAuNTkyLDEuMzk2LDAuOTE0LDIuNzEzLDEuODQsMy45NDljMC44MiwxLjA5NywxLjQyNiwyLjE5OSwyLjA2MSwzLjQ"""+
                """wMmMwLjcxMywxLjM0OSwxLjM4NSwyLjY0MywyLjI1MiwzLjg4NiAgIGMwLjU4OCwwLjg0NSwyLjE0MywyLjUyNCwzLjEyNSwy"""+
                """LjY1YzIuMzk4LDAuMzA3LDIuMjQ4LTUuNTIxLDIuMDctNi45NDVjLTAuMTctMS4zNzEtMC4yMTUtMi44MjUtMC4xNy00LjIxN"""+
                """iAgIGMwLjAzOS0xLjE4NiwwLjE0Ni0yLjg1Ny0wLjU1Ny0zLjgyNmMtMS4xNDUtMS41OC0zLjY5NS0wLjM5Ny0zLjg5NS0yLj"""+
                """UyYzAuNDIyLTAuNjAzLDAuMzMyLTEuMTM4LDMuMTQ2LTIuMDY0ICAgYzIuMjE1LTAuNzI5LDMuNjQ2LTAuNzA2LDUuMTA3LTA"""+
                """uNTg5YzIuOTgsMC4yMzksNi4xMzktMC41NjgsOS4wMTQsMC4zOThjMi43NDYsMC45MjUsMi4zMjIsNC44MjgsMi4yMyw3LjE2"""+
                """OCAgIGMtMC4xMjMsMy4xOTUsMC4wMDgsNi4zMTIsMCw5LjU1M2MtMC4wMDQsMS40NzctMC4wNjIsMi45MTIsMS43MzYsMi43O"""+
                """TNjMS42ODgtMC4xMTMsMS44NTktMS41MzIsMi42NjQtMi43MDQgICBjMS4xMjEtMS42MzMsMi4xNDgtMy4yODgsMy4yODktNC"""+
                """45MTZjMS41MzctMi4xOTksMi00LjY3LDMuNDQ3LTYuOTIzYzAuNTE4LTAuODA3LDAuOTYzLTIuNTY4LDEuNzYtMy4yMDUgICB"""+
                """jMC42MDQtMC40ODEsMS43NS0wLjI3NSwyLjQ4LTAuMjc1aDEuNzM2YzEuMzMsMC4wMTYsMi42ODYsMC4wMzUsNC4wNTEsMC4w"""+
                """ODNjMS45NjcsMC4wNjgsNC4xNy0wLjM1OSw2LjEyMS0wLjA4NCAgIGM4LjQxNiwxLjE4OC0xMC41NzgsMTkuMTkxLTkuNTksM"""+
                """jIuNDAzYzAuNjg0LDIuMjE4LDUuMDE2LDQuNzAzLDYuNTgsNi41MjFDODIuOTk4LDYxLjk5MSw4OS4zODksNjYuODEsODQuND"""+
                """E4LDY5LjkyMXoiIGZpbGw9IiM0NDQiLz48L2c+PGcgaWQ9Im9mZnNldF94NUZfcHJpbnRfeDVGX291dGxpbmUiLz48L3N2Zz4=""")
            ], href="https://vk.com/share.php?url=https%3A%2F%2Fcikinfo.modos189.ru", target="_blank", id="left-button-vk"),
            html.A([
                html.Img(src="""data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiA/PjwhRE9DVFlQRSBzdmcgIFBVQkxJQy"""+
                """AnLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTE"""+
                """uZHRkJz48c3ZnIGhlaWdodD0iNTEycHgiIGlkPSJMYXllcl8xIiBzdHlsZT0iZW5hYmxlLWJhY2tncm91bmQ6bmV3IDAgMCA1"""+
                """MTIgNTEyOyIgdmVyc2lvbj0iMS4xIiB2aWV3Qm94PSIwIDAgNTEyIDUxMiIgd2lkdGg9IjUxMnB4IiB4bWw6c3BhY2U9InByZ"""+
                """XNlcnZlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy"""+
                """8xOTk5L3hsaW5rIj48Zz48cGF0aCBmaWxsPSIjNDQ0IiBkPSJNMjU2LDMyQzEzMi4zLDMyLDMyLDEzMi4zLDMyLDI1NnMxMDA"""+
                """uMywyMjQsMjI0LDIyNGMxMjMuNywwLDIyNC0xMDAuMywyMjQtMjI0UzM3OS43LDMyLDI1NiwzMnogTTI3Ni4yLDM1OC43ICAg"""+
                """Yy0wLjUsMTcuOC0xMy43LDI4LjgtMzAuOCwyOC4zYy0xNi40LTAuNS0yOS4zLTEyLjItMjguOC0zMC4xYzAuNS0xNy44LDE0L"""+
                """jEtMjkuMSwzMC41LTI4LjZDMjY0LjMsMzI4LjgsMjc2LjgsMzQwLjksMjc2LjIsMzU4Ljd6ICAgIE0zMjQuOSwyMzEuNGMtNC"""+
                """4yLDUuOS0xMy42LDEzLjUtMjUuNCwyMi43bC0xMy4xLDljLTYuNCw0LjktMTAuNCwxMC43LTEyLjUsMTcuM2MtMS4xLDMuNS0"""+
                """xLjksMTIuNi0yLjEsMTguNyAgIGMtMC4xLDEuMi0wLjgsMy45LTQuNSwzLjljLTMuNywwLTM1LDAtMzkuMSwwYy00LjEsMC00"""+
                """LjYtMi40LTQuNS0zLjZjMC42LTE2LjYsMy0zMC4zLDkuOS00MS4zYzkuMy0xNC44LDM1LjUtMzAuNCwzNS41LTMwLjQgICBjN"""+
                """C0zLDcuMS02LjIsOS41LTkuN2M0LjQtNiw4LTEyLjcsOC0xOS45YzAtOC4zLTItMTYuMi03LjMtMjIuOGMtNi4yLTcuNy0xMi"""+
                """45LTExLjQtMjUuOC0xMS40Yy0xMi43LDAtMjAuMSw2LjQtMjUuNCwxNC44ICAgYy01LjMsOC40LTQuNCwxOC4zLTQuNCwyNy4"""+
                """zSDE3NWMwLTM0LDguOS01NS43LDI3LjctNjguNWMxMi43LTguNywyOC45LTEyLjUsNDcuOC0xMi41YzI0LjgsMCw0NC41LDQu"""+
                """Niw2MS45LDE3LjggICBjMTYuMSwxMi4yLDI0LjYsMjkuNCwyNC42LDUyLjZDMzM3LDIwOS43LDMzMiwyMjEuNywzMjQuOSwyM"""+
                """zEuNHoiLz48L2c+PC9zdmc+"""),
                html.Span(['Помощь'])
            ], href="#", id="left-button-help"),
            html.A([
                html.Img(src="""data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiA/PjxzdmcgaGVpZ2h0PSIyNCIgdmlld0"""+
                """JveD0iMCAwIDI0IDI0IiB3aWR0aD0iMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTI"""+
                """yLjY1LDE0LjM5LDEyLDIyLjEzLDEuMzUsMTQuMzlhLjg0Ljg0LDAsMCwxLS4zLS45NEwyLjI3LDkuNjcsNC43MSwyLjE2QS40"""+
                """Mi40MiwwLDAsMSw0LjgyLDIsLjQzLjQzLDAsMCwxLDUuNCwyYS40Mi40MiwwLDAsMSwuMTEuMThMNy45NSw5LjY3aDguMWwyL"""+
                """jQ0LTcuNTFBLjQyLjQyLDAsMCwxLDE4LjYsMmEuNDMuNDMsMCwwLDEsLjU4LDAsLjQyLjQyLDAsMCwxLC4xMS4xOGwyLjQ0LD"""+
                """cuNTFMMjMsMTMuNDVBLjg0Ljg0LDAsMCwxLDIyLjY1LDE0LjM5WiIgZmlsbD0iIzQ0NCIvPjwvc3ZnPg=="""),
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
            tabs=[
                {'label': 'Явка / Доля голосов', 'value': 0},
                {'label': 'Явка / Число участков', 'value': 1},
                {'label': 'Явка / Кол-во избирателей', 'value': 2}
                ],
            value=0,
            id='tabs'
        ),
        html.Div([
            dcc.Graph(id='graph'),
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
                html.Img(src="https://cikinfo.modos189.ru/data/help-img-1.png"),
                html.H1('Первым делом необходимо указать, какие выборы будем анализировать'),
            ], className="help-slide"),
            html.Li([
                html.Img(src="https://cikinfo.modos189.ru/data/help-img-2.png"),
                html.H1('Есть возможность указать временной промежуток, чтобы отфильтровать список выборов'),
            ], className="help-slide"),
            html.Li([
                html.Img(src="https://cikinfo.modos189.ru/data/help-img-3.png"),
                html.H1('Слева можно указать территорию, для которой будет сформирована статистика'),
            ], className="help-slide"),
            html.Li([
                html.Img(src="https://cikinfo.modos189.ru/data/help-img-4.png"),
                html.H1('Статистика формируется в виде трёх интерактивных графиков'),
            ], className="help-slide"),
            html.Li([
                html.Img(src="https://cikinfo.modos189.ru/data/help-img-5.png"),
                html.H1(['С помощью Box Select или Lasso Select можно выбрать точки на графике, чтобы под графиком '
                         'получить подробную информацию о них, в т.ч. адреса УИКов']),
            ], className="help-slide"),
            html.Li([
                html.Img(src="https://cikinfo.modos189.ru/data/help-img-6.png"),
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
    Output('area-level-3', 'disabled'),
    [Input('area-level-2', 'value'),
     Input('area-level-2', 'options'),
     Input('elections', 'value')])
def area_level_3_disabled(val, opt, election_id):
    if val is None or len(val) == 0 or not any(d['value'] == val[0] for d in opt):
        return True

    for i, a in enumerate(val):
        if type(a) is str:
            val[i] = ObjectId(a)

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




@app.callback(
    Output('left-info', 'children'),
    [Input('area-level-1', 'value'),
     Input('area-level-2', 'value'),
     Input('area-level-3', 'value'),
     Input('elections', 'value')])
def left_info_all(level1, level2, level3, election_id):
    if election_id is None:
        return

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

    data = db.area.find(
        {'results_tags': election_id, '_id': {'$in': area}},
        {'name': True, 'results.'+election_id: True}
    )

    if data.count() == 0:
        return

    results = data[0]['results'][election_id]
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
    for i, cand in enumerate(db.election.find_one({'_id': election_id})['meta']):
        if cand['is_meta'] is False:
            percent = round(results[str(i)] / results['1'] * 100, 2)
            html_candidates.append(
                html.Div([
                    html.P(cand['name_simple'],
                           title=cand['name'],
                           className="left-info-name"),
                    html.Div([
                        html.Span(str(percent)+'%'),
                        html.Span('('+str(results[str(i)])+')')
                    ], className="left-info-num", id='left-info-candidates'),
                ], style={'order': int(results[str(i)])}),
            )

    return [
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
            ], className="left-info-block"),
            html.Div(html_candidates, className="left-info-block left-info-block-candidates"),
        ]



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
    Output('area-level-2', 'options'),
    [Input('area-level-1', 'value'),
     Input('elections', 'value')])
def area_level_2_options(parent, election):
    if parent is None or len(parent) == 0:
        return []
    level = 2
    return get_area_options(level, parent, election)


@app.callback(
    Output('graph', 'figure'),
    [Input('area-level-1', 'value'),
     Input('area-level-1', 'options'),
     Input('area-level-2', 'value'),
     Input('area-level-2', 'options'),
     Input('area-level-3', 'value'),
     Input('area-level-3', 'options'),
     Input('elections', 'value'),
     Input('tabs', 'value')])
def update_graph(level1_val, level1_opt,
                 level2_val, level2_opt,
                 level3_val, level3_opt,
                 election_id, tab):
    if election_id is None:
        return html.Div([])

    if level3_val is not None and len(level3_val) > 0 and any(d['value'] == level3_val[0] for d in level3_opt):
        area = level3_val
    elif level2_val is not None and len(level2_val) > 0 and any(d['value'] == level2_val[0] for d in level2_opt):
        area = level2_val
    elif level1_val is not None and len(level1_val) > 0 and any(d['value'] == level1_val[0] for d in level1_opt):
        area = level1_val
    else:
        area = [db.area.find_one({'name': 'Российская Федерация'}, {'_id': True})['_id']]

    for i, a in enumerate(area):
        if type(a) is str:
            area[i] = ObjectId(a)

    uiks = db.area.find(
        {'results_tags': election_id, 'parent_id': {'$in': area}},
        {'name': True, 'address': True, 'results.' + election_id: True}
    ).limit(1000)  # TODO

    if uiks.count() == 0:
        uiks = db.area.find(
            {'results_tags': election_id, '_id': {'$in': area}},
            {'name': True, 'address': True, 'results.' + election_id: True}
        ).limit(1000)  # TODO

    col = list(uiks)

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
                        x=[item['results'][election_id]['share'] for item in col],
                        y=[int(item['results'][election_id][str(i)]) /
                           item['results'][election_id]['number_bulletin'] * 100
                           for item in col],
                        text=[
                            item['name'] + '</br>'
                            + 'Всего избирателей: ' + str(item['results'][election_id]['0']) + '</br>'
                            + 'Голос в помещении: ' + str(item['results'][election_id]['3']) + '</br>'
                            + 'Голос вне помещения: ' + str(item['results'][election_id]['4']) for item in col],
                        customdata=[{
                                'name': item['name'],
                                'address': (item['address'] if 'address' in item else ''),
                                'total': item['results'][election_id]['0'],
                                'votes_inroom': item['results'][election_id]['3'],
                                'votes_outroom': item['results'][election_id]['4'],
                                'share': item['results'][election_id]['share']
                            } for item in col],
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
            share = uik['results'][election_id]['share']
            share = round(share)
            data[share] += 1

        markers.append(
            go.Scattergl(
                x=[i for i, item in enumerate(data)],
                y=[item for item in data],
                # text=[
                #     item['name'] + '</br>'
                #     + 'Всего избирателей: ' + str(item['results'][election_id]['1']) + '</br>'
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
                x=[item['results'][election_id]['share'] for item in col],
                y=[item['results'][election_id]['0'] for item in col],
                text=[
                    item['name'] + '</br>'
                    + 'Всего избирателей: ' + str(item['results'][election_id]['0']) + '</br>'
                    + 'Голос в помещении: ' + str(item['results'][election_id]['3']) + '</br>'
                    + 'Голос вне помещения: ' + str(item['results'][election_id]['4']) for item in col],
                customdata=[{
                                'name': item['name'],
                                'address': (item['address'] if 'address' in item else ''),
                                'total': item['results'][election_id]['0'],
                                'votes_inroom': item['results'][election_id]['3'],
                                'votes_outroom': item['results'][election_id]['4'],
                                'share': item['results'][election_id]['share']
                            } for item in col],
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

    return {
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
            height=520
        )
    }




@app.callback(
    Output('selected-data', 'children'),
    [Input('graph', 'selectedData')])
def display_selected_data(selectedData):
    if selectedData is None or len(selectedData['points']) == 0:
        return ''

    points = set()
    data = []
    for el in selectedData['points']:
        if el['pointNumber'] not in points:
            points.add(el['pointNumber'])

            data.append(
                html.Div([
                    html.P(el['customdata']['name']+' | '+
                           'Всего избирателей: '+str(el['customdata']['total'])+' | '+
                           'Голосов в помещении: '+str(el['customdata']['votes_inroom'])+' | '+
                           'Голосов вне помещения: '+str(el['customdata']['votes_outroom'])+' | '+
                           'Явка: '+str(el['customdata']['share'])+'%'),
                    html.P(el['customdata']['address']),
                ], className="selected-data-block")
            )

    return html.Div(data)

if __name__ == '__main__':
    app.run_server(debug=True)
