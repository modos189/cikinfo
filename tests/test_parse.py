import unittest
import datetime

from modules import parse


class Test(unittest.TestCase):
    izbirkom_html = open('izbirkom_utf8.html', 'r').read()
    simple_table_html = open('4352508c363e0f0371bc1e44b9c6f8046c6c37c9_utf8.html', 'r').read()

    def test_split_name(self):
        self.assertEqual(parse.split_name(" Республика Алтай"), [None, "Республика Алтай"])
        self.assertEqual(parse.split_name("75 Белгородская область – Белгородский"), [75, "Белгородский"])
        self.assertEqual(parse.split_name("2 Белгородская районная"), [2, "Белгородская районная"])
        self.assertEqual(parse.split_name("УИК №1110"), [1110, "УИК №1110"])

    def test_simple_name(self):
        self.assertEqual(parse.simple_name('ВСЕРОССИЙСКАЯ ПОЛИТИЧЕСКАЯ ПАРТИЯ "РОДИНА"'), '"РОДИНА"')
        self.assertEqual(parse.simple_name('Политическая партия "Российская партия пенсионеров за справедливость"'), '"Российская партия пенсионеров за справедливость"')
        self.assertEqual(parse.simple_name('Всероссийская политическая партия "ЕДИНАЯ РОССИЯ"'), '"ЕДИНАЯ РОССИЯ"')
        self.assertEqual(parse.simple_name('Политическая партия "Российская экологическая партия "Зеленые"'), '"Российская экологическая партия "Зеленые"')
        self.assertEqual(parse.simple_name('Политическая партия "Партия народной свободы" (ПАРНАС)'), '"Партия народной свободы" (ПАРНАС)')

    def test_simple_table_meta(self):
        self.assertEqual(parse.simple_table_meta(self.simple_table_html),
        [
            {'name': 'Число избирателей, внесенных в список избирателей на момент окончания голосования', 'is_meta': True},
            {'name': 'Число избирательных бюллетеней, полученных участковой избирательной комиссией', 'is_meta': True},
            {'name': 'Число избирательных бюллетеней, выданных избирателям, проголосовавшим досрочно', 'is_meta': True},
            {'name': 'Число избирательных бюллетеней, выданных в помещении для голосования в день голосования', 'is_meta': True},
            {'name': 'Число избирательных бюллетеней, выданных вне помещения для голосования в день голосования', 'is_meta': True},
            {'name': 'Число погашенных избирательных бюллетеней', 'is_meta': True},
            {'name': 'Число избирательных бюллетеней, содержащихся в переносных ящиках для голосования', 'is_meta': True},
            {'name': 'Число избирательных бюллетеней, содержащихся в стационарных ящиках для голосования', 'is_meta': True},
            {'name': 'Число недействительных избирательных бюллетеней', 'is_meta': True},
            {'name': 'Число действительных избирательных бюллетеней', 'is_meta': True},
            {'name': 'Число открепительных удостоверений, полученных участковой избирательной комиссией', 'is_meta': True},
            {'name': 'Число открепительных удостоверений, выданных на избирательном участке до дня голосования', 'is_meta': True},
            {'name': 'Число избирателей, проголосовавших по открепительным удостоверениям на избирательном участке', 'is_meta': True},
            {'name': 'Число погашенных неиспользованных открепительных удостоверений', 'is_meta': True},
            {'name': 'Число открепительных удостоверений, выданных избирателям территориальной избирательной комиссией', 'is_meta': True},
            {'name': 'Число утраченных открепительных удостоверений', 'is_meta': True},
            {'name': 'Число утраченных избирательных бюллетеней', 'is_meta': True},
            {'name': 'Число избирательных бюллетеней, не учтенных при получении', 'is_meta': True},
            {'name': 'ВСЕРОССИЙСКАЯ ПОЛИТИЧЕСКАЯ ПАРТИЯ "РОДИНА"', 'name_simple': '"РОДИНА"', 'is_meta': False},
            {'name': 'Политическая партия КОММУНИСТИЧЕСКАЯ ПАРТИЯ КОММУНИСТЫ РОССИИ', 'name_simple': 'КОММУНИСТИЧЕСКАЯ ПАРТИЯ КОММУНИСТЫ РОССИИ', 'is_meta': False},
            {'name': 'Политическая партия "Российская партия пенсионеров за справедливость"', 'name_simple': '"Российская партия пенсионеров за справедливость"', 'is_meta': False},
            {'name': 'Всероссийская политическая партия "ЕДИНАЯ РОССИЯ"', 'name_simple': '"ЕДИНАЯ РОССИЯ"', 'is_meta': False},
            {'name': 'Политическая партия "Российская экологическая партия "Зеленые"', 'name_simple': '"Российская экологическая партия "Зеленые"', 'is_meta': False},
            {'name': 'Политическая партия "Гражданская Платформа"', 'name_simple': '"Гражданская Платформа"', 'is_meta': False},
            {'name': 'Политическая партия ЛДПР - Либерально-демократическая партия России', 'name_simple': 'ЛДПР - Либерально-демократическая партия России', 'is_meta': False},
            {'name': 'Политическая партия "Партия народной свободы" (ПАРНАС)', 'name_simple': '"Партия народной свободы" (ПАРНАС)', 'is_meta': False},
            {'name': 'Всероссийская политическая партия "ПАРТИЯ РОСТА"', 'name_simple': '"ПАРТИЯ РОСТА"', 'is_meta': False},
            {'name': 'Общественная организация Всероссийская политическая партия "Гражданская Сила"', 'name_simple': '"Гражданская Сила"', 'is_meta': False},
            {'name': 'Политическая партия "Российская объединенная демократическая партия "ЯБЛОКО"', 'name_simple': '"Российская объединенная демократическая партия "ЯБЛОКО"', 'is_meta': False},
            {'name': 'Политическая партия "КОММУНИСТИЧЕСКАЯ ПАРТИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ"', 'name_simple': '"КОММУНИСТИЧЕСКАЯ ПАРТИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ"', 'is_meta': False},
            {'name': 'Политическая партия "ПАТРИОТЫ РОССИИ"', 'name_simple': '"ПАТРИОТЫ РОССИИ"', 'is_meta': False},
            {'name': 'Политическая партия СПРАВЕДЛИВАЯ РОССИЯ', 'name_simple': 'СПРАВЕДЛИВАЯ РОССИЯ', 'is_meta': False}
        ])

    def test_get_region_from_subdomain_url(self):
        self.assertEqual(parse.get_region_from_subdomain_url("http://www.adygei.vybory.izbirkom.ru/region/region/adygei?action=show&root=12000001&tvd=2012000133849&vrn=100100022176412&region=1&global=true&sub_region=1&prver=0&pronetvd=null&vibid=2012000133849&type=227"), 'adygei')

    def test_get_region_from_getparams_url(self):
        self.assertEqual(parse.get_region_from_getparams_url("http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=431401998981&region=31&prver=0&pronetvd=null"), 31)

    def test_vidvibref_from_title(self):
        self.assertEqual(parse.vidvibref_from_title('Местный референдум муниципального образования - Касимовский район'), 0)
        self.assertEqual(parse.vidvibref_from_title('Опрос граждан (местный опрос) на территории МО "Эжвинский район г.Сыктывкара"'), 0)
        self.assertEqual(parse.vidvibref_from_title('Голосование по вопросу преобразования Губахинского муниципального района'), 0)

        self.assertEqual(parse.vidvibref_from_title('Выборы главы муниципального образования "Угранский район" Смоленской области'), 1)
        self.assertEqual(parse.vidvibref_from_title('Досрочные выборы Главы муниципального образования "Ахвахский район"'), 1)
        self.assertEqual(parse.vidvibref_from_title('Выборы Мэра города Хабаровска'), 1)
        self.assertEqual(parse.vidvibref_from_title('Выборы главы муниципального образования "Угранский район" Смоленской области'), 1)

        self.assertEqual(parse.vidvibref_from_title('Выборы депутатов Совета муниципального района Бакалинский район Республики Башкортостан второго созыва'), 2)
        self.assertEqual(parse.vidvibref_from_title('Повторные выборы депутата представительного органа местного самоуправления муниципального образования "Усть-Канский район" '), 2)
        self.assertEqual(parse.vidvibref_from_title('Повторные выборы (вторые) депутата Земского Собрания Чайковского муниципального района первого созыва по одномандатному избирательному округу № 2'), 2)

        self.assertEqual(parse.vidvibref_from_title('Гипотетическое голосование по отзыву депутата'), 3)

        self.assertEqual(parse.vidvibref_from_title('Голосование по отзыву главы городского поселения Малиновский Апатова Максима Андреевича'), 4)

    def test_parse_list_elections(self):
        self.assertEqual(parse.parse_list_elections(self.izbirkom_html, '1'), [
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация', None, None],
  'region_id': 0,
  'title': 'Дополнительные выборы депутатов Государственной Думы Федерального '
           'Собрания Российской Федерации седьмого созыва по одномандатным '
           'избирательным округам',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&global=1&vrn=100100136845944&region=0&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация',
             'Кабардино-Балкарская Республика',
             'Урванский муниципальный район'],
  'region_id': 7,
  'title': 'Дополнительные выборы  депутатов Совета местного самоуправления '
           'сельского поселения Кахун  Урванского муниципального района '
           'Кабардино-Балкарской Республики шестого созыва',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4074008168587&region=7&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация',
             'Приморский край',
             'Партизанский муниципальный район'],
  'region_id': 25,
  'title': 'Дополнительные выборы депутатов муниципального комитета '
           'Сергеевского сельского поселения Партизанского муниципального '
           'района по многомандатному (десятимандатному) избирательному округу',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4254023205893&region=25&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация',
             'Хабаровский край',
             'Тугуро-Чумиканский муниципальный район'],
  'region_id': 27,
  'title': 'Дополнительные выборы  депутатов Собрания депутатов '
           'Тугуро-Чумиканского муниципального района',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4274017127466&region=27&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация',
             'Астраханская область',
             'Наримановский район'],
  'region_id': 30,
  'title': 'Досрочные выборы депутатов Совета муниципального образования '
           '"Барановский сельсовет" шестого созыва',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4304013268247&region=30&prver=0&pronetvd=null',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация',
             'Волгоградская область',
             'Жирновский муниципальный район'],
  'region_id': 34,
  'title': 'Досрочные выборы главы Кленовского сельского поселения Жирновского '
           'муниципального района Волгоградской области',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4344016233706&region=34&prver=0&pronetvd=null',
  'urovproved': '1',
  'vidvibref': 1},
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация',
             'Ярославская область',
             'Ростовский муниципальный район'],
  'region_id': 76,
  'title': 'Досрочные выборы Главы сельского поселения Поречье-Рыбное '
           'Ростовского района Ярославской области',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4764013204807&region=76&prver=0&pronetvd=null',
  'urovproved': '1',
  'vidvibref': 1},
 {'date': datetime.datetime(2018, 12, 23, 0, 0),
  'region': ['Российская Федерация',
             'Ханты-Мансийский автономный округ',
             'Нефтеюганский район'],
  'region_id': 86,
  'title': 'Выборы Главы сельского поселения Куть-Ях',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4864019231484&region=86&prver=0&pronetvd=null',
  'urovproved': '1',
  'vidvibref': 1},
 {'date': datetime.datetime(2010, 3, 14, 0, 0),
  'region': ['Российская Федерация', 'Белгородская область', None],
  'region_id': 31,
  'title': 'Дополнительные выборы депутата Совета депутатов города Белгорода '
           'четвертого созыва по одномандатному избирательному округу №5',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=4314002107908&region=31&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2010, 3, 14, 0, 0),
  'region': ['Российская Федерация',
             'Белгородская область',
             'муниципальный район "Борисовский район"'],
  'region_id': 31,
  'title': 'Дополнительные выборы  депутата Земского собрания Стригуновского '
           'сельского поселения муниципального района "Борисовский район" '
           'второго созыва',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=431400482278&region=31&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2010, 3, 14, 0, 0),
  'region': ['Российская Федерация',
             'Белгородская область',
             'муниципальный район "Борисовский район"'],
  'region_id': 31,
  'title': 'Дополнительные выборы депутата Земского собрания Белянского '
           'сельского поселения муниципального района "Борисовский район" '
           'второго созыва',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=431400482243&region=31&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2010, 3, 14, 0, 0),
  'region': ['Российская Федерация',
             'Белгородская область',
             'муниципальный район "Борисовский район"'],
  'region_id': 31,
  'title': 'Дополнительные выборы депутата Земского собрания Грузсчанского '
           'сельского поселения муниципального района "Борисовский район"  '
           'второго созыва',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=431400482260&region=31&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2},
 {'date': datetime.datetime(2010, 3, 14, 0, 0),
  'region': ['Российская Федерация',
             'Белгородская область',
             'муниципальный район "Город Валуйки и Валуйский район"'],
  'region_id': 31,
  'title': 'Дополнительные выборы  депутатов поселкового собрания городского '
           'поселения "Поселок Уразово" второго созыва',
  'url': 'http://www.vybory.izbirkom.ru/region/izbirkom?action=show&vrn=431400587458&region=31&prver=0&pronetvd=0',
  'urovproved': '1',
  'vidvibref': 2}])

    def test_get_start_end_date(self):
        self.assertEqual(parse.get_start_end_date("2018"), {'start_date': '01.01.2018', 'end_date': '31.12.2018'})
        self.assertEqual(parse.get_start_end_date("2018-10"), {'start_date': '01.10.2018', 'end_date': '31.10.2018'})
        self.assertEqual(parse.get_start_end_date("2018-10-10"), {'start_date': '10.10.2018', 'end_date': '10.10.2018'})
        self.assertEqual(parse.get_start_end_date("2018-77"), None)
        self.assertEqual(parse.get_start_end_date("2005"), None)


if __name__ == '__main__':
    unittest.main()
