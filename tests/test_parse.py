import unittest
import datetime

from modules import parse


class Test(unittest.TestCase):
    def test_split_name(self):
        self.assertEqual(parse.split_name(" Республика Алтай"), [None, "Республика Алтай"])
        self.assertEqual(parse.split_name("75 Белгородская область – Белгородский"), [75, "Белгородский"])
        self.assertEqual(parse.split_name("2 Белгородская районная"), [2, "Белгородская районная"])
        self.assertEqual(parse.split_name("УИК №1110"), [1110, "УИК №1110"])
        self.assertEqual(parse.split_name("2 Одномандатный №2"), [2, "Одномандатный №2"])

    def test_simple_name(self):
        self.assertEqual(parse.simple_name('ВСЕРОССИЙСКАЯ ПОЛИТИЧЕСКАЯ ПАРТИЯ "РОДИНА"'), '"РОДИНА"')
        self.assertEqual(parse.simple_name('Политическая партия "Российская партия пенсионеров за справедливость"'), '"Российская партия пенсионеров за справедливость"')
        self.assertEqual(parse.simple_name('Всероссийская политическая партия "ЕДИНАЯ РОССИЯ"'), '"ЕДИНАЯ РОССИЯ"')
        self.assertEqual(parse.simple_name('Политическая партия "Российская экологическая партия "Зеленые"'), '"Российская экологическая партия "Зеленые"')
        self.assertEqual(parse.simple_name('Политическая партия "Партия народной свободы" (ПАРНАС)'), '"Партия народной свободы" (ПАРНАС)')

    def test_table_meta_1(self):
        with open('a13d83d0272494f41494b5450675e07a_utf8.html', 'r') as f:
            self.assertEqual(parse.table_meta(f.read()),
                             {0: {'is_meta': True, 'name': 'all'},
                              2: {'is_meta': True, 'name': 'early'},
                              4: {'is_meta': True, 'name': 'in_room'},
                              5: {'is_meta': True, 'name': 'out_room'},
                              9: {'is_meta': True, 'name': 'invalid'},
                              10: {'is_meta': True, 'name': 'valid'},
                              14: {'name': 'Бикбаев Тахир Ришатович'},
                              15: {'name': 'Иванова Ирина Владимировна'},
                              16: {'name': 'Петров Андрей Николаевич'},
                              17: {'name': 'Полтавченко Георгий Сергеевич'},
                              18: {'name': 'Сухенко Константин Эдуардович'}})

    def test_table_meta_2(self):
        with open('dc193816b750bddb0d131af3a9b477e9_utf8.html', 'r') as f:
            self.assertEqual(parse.table_meta(f.read()),
                             {0: {'is_meta': True, 'name': 'all'},
                              2: {'is_meta': True, 'name': 'early'},
                              3: {'is_meta': True, 'name': 'in_room'},
                              5: {'is_meta': True, 'name': 'out_room'},
                              9: {'is_meta': True, 'name': 'invalid'},
                              10: {'is_meta': True, 'name': 'valid'},
                              14: {'name': 'Бабич Елена Вениаминовна'},
                              15: {'name': 'Бабушкин Сергей Сергеевич'},
                              16: {'name': 'Безносюк Алексей Вячеславович'},
                              17: {'name': 'Головач Александр Александрович'},
                              18: {'name': 'Голубь Николай Иванович'},
                              19: {'name': 'Гусев Дмитрий Германович'},
                              20: {'name': 'Денисова Юлия Юрьевна'},
                              21: {'name': 'Казачков Виктор Александрович'},
                              22: {'name': 'Левина Маргарита Игоревна'},
                              23: {'name': 'Морозова Оксана Викторовна'},
                              24: {'name': 'Равина Наталья Владимировна'},
                              25: {'name': 'Рыжкова Екатерина Александровна'},
                              26: {'name': 'Сафонова Валентина Александровна'},
                              27: {'name': 'Соловейчик Алексей Валерьевич'},
                              28: {'name': 'Чулохин Юрий Павлович'},
                              29: {'name': 'Якубович Евгений Владимирович'}})

    def test_table_results(self):
        from modules.parse import RawUIKRecord

        with open('dc193816b750bddb0d131af3a9b477e9_utf8.html', 'r') as f:
            html = f.read()
            meta = parse.table_meta(html)
            self.assertEqual(parse.table_results(html, meta), [{
  'name': 'УИК №15',
  'num': 15,
  'results': {'all': 1799,
              'calculated_number_bulletin': 392,
              'calculated_share': 21.79,
              'early': 159,
              'in_room': 127,
              'invalid': 16,
              'out_room': 4,
              'valid': 376,
              'candidates': {'Бабич Елена Вениаминовна': 285,
                             'Бабушкин Сергей Сергеевич': 32,
                             'Безносюк Алексей Вячеславович': 23,
                             'Головач Александр Александрович': 34,
                             'Голубь Николай Иванович': 10,
                             'Гусев Дмитрий Германович': 35,
                             'Денисова Юлия Юрьевна': 265,
                             'Казачков Виктор Александрович': 28,
                             'Левина Маргарита Игоревна': 37,
                             'Морозова Оксана Викторовна': 221,
                             'Равина Наталья Владимировна': 43,
                             'Рыжкова Екатерина Александровна': 34,
                             'Сафонова Валентина Александровна': 263,
                             'Соловейчик Алексей Валерьевич': 244,
                             'Чулохин Юрий Павлович': 28,
                             'Якубович Евгений Владимирович': 27}}},
 {'name': 'УИК №16',
  'num': 16,
  'results': {'all': 1982,
              'calculated_number_bulletin': 539,
              'calculated_share': 27.19,
              'early': 241,
              'in_room': 187,
              'invalid': 25,
              'out_room': 19,
              'valid': 514,
              'candidates': {'Бабич Елена Вениаминовна': 371,
                             'Бабушкин Сергей Сергеевич': 38,
                             'Безносюк Алексей Вячеславович': 29,
                             'Головач Александр Александрович': 65,
                             'Голубь Николай Иванович': 21,
                             'Гусев Дмитрий Германович': 53,
                             'Денисова Юлия Юрьевна': 368,
                             'Казачков Виктор Александрович': 29,
                             'Левина Маргарита Игоревна': 44,
                             'Морозова Оксана Викторовна': 320,
                             'Равина Наталья Владимировна': 51,
                             'Рыжкова Екатерина Александровна': 43,
                             'Сафонова Валентина Александровна': 390,
                             'Соловейчик Алексей Валерьевич': 357,
                             'Чулохин Юрий Павлович': 29,
                             'Якубович Евгений Владимирович': 34}}},
 {'name': 'УИК №17',
  'num': 17,
  'results': {'all': 1972,
              'calculated_number_bulletin': 473,
              'calculated_share': 23.99,
              'early': 154,
              'in_room': 133,
              'invalid': 25,
              'out_room': 10,
              'valid': 448,
              'candidates': {'Бабич Елена Вениаминовна': 285,
                             'Бабушкин Сергей Сергеевич': 44,
                             'Безносюк Алексей Вячеславович': 50,
                             'Головач Александр Александрович': 66,
                             'Голубь Николай Иванович': 30,
                             'Гусев Дмитрий Германович': 58,
                             'Денисова Юлия Юрьевна': 282,
                             'Казачков Виктор Александрович': 39,
                             'Левина Маргарита Игоревна': 57,
                             'Морозова Оксана Викторовна': 226,
                             'Равина Наталья Владимировна': 89,
                             'Рыжкова Екатерина Александровна': 57,
                             'Сафонова Валентина Александровна': 346,
                             'Соловейчик Алексей Валерьевич': 239,
                             'Чулохин Юрий Павлович': 61,
                             'Якубович Евгений Владимирович': 46}}},
 {'name': 'УИК №18',
  'num': 18,
  'results': {'all': 1767,
              'calculated_number_bulletin': 432,
              'calculated_share': 24.45,
              'early': 196,
              'in_room': 152,
              'invalid': 16,
              'out_room': 22,
              'valid': 416,
              'candidates': {'Бабич Елена Вениаминовна': 239,
                             'Бабушкин Сергей Сергеевич': 50,
                             'Безносюк Алексей Вячеславович': 40,
                             'Головач Александр Александрович': 53,
                             'Голубь Николай Иванович': 21,
                             'Гусев Дмитрий Германович': 66,
                             'Денисова Юлия Юрьевна': 249,
                             'Казачков Виктор Александрович': 31,
                             'Левина Маргарита Игоревна': 34,
                             'Морозова Оксана Викторовна': 188,
                             'Равина Наталья Владимировна': 59,
                             'Рыжкова Екатерина Александровна': 49,
                             'Сафонова Валентина Александровна': 234,
                             'Соловейчик Алексей Валерьевич': 250,
                             'Чулохин Юрий Павлович': 42,
                             'Якубович Евгений Владимирович': 49}}}])

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
        with open('izbirkom_utf8.html', 'r') as f:
            self.assertEqual(parse.parse_list_elections(f.read(), '1'), [
 {'date': datetime.datetime(2018, 12, 16, 0, 0),
  'region': ['Российская Федерация'],
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
  'region': ['Российская Федерация', 'Белгородская область'],
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
        self.assertEqual(parse.get_start_end_date("2018-09"), {'start_date': '01.09.2018', 'end_date': '30.09.2018'})
        self.assertEqual(parse.get_start_end_date("2018-10"), {'start_date': '01.10.2018', 'end_date': '31.10.2018'})
        self.assertEqual(parse.get_start_end_date("2018-10-10"), {'start_date': '10.10.2018', 'end_date': '10.10.2018'})
        self.assertEqual(parse.get_start_end_date("2018-77"), None)
        self.assertEqual(parse.get_start_end_date("2005"), None)

    def test_get_elections_type(self):
        with open('izbirkom_elections_types_variant1_utf8.html', 'r') as f:
            self.assertEqual(parse.get_elections_type(f.read()), {'status': True,
 'types': {'mngm': 'http://www.khantu-mansy.vybory.izbirkom.ru/region/region/khantu-mansy?action=show&root=1&tvd=2862000196494&vrn=2862000196490&region=86&global=&sub_region=0&prver=1&pronetvd=1&vibid=2862000196494&type=427',
           'edin': 'http://www.khantu-mansy.vybory.izbirkom.ru/region/region/khantu-mansy?action=show&root=1&tvd=2862000196494&vrn=2862000196490&region=86&global=&sub_region=0&prver=2&pronetvd=1&vibid=2862000196494&type=381',
           'edmn': 'http://www.khantu-mansy.vybory.izbirkom.ru/region/region/khantu-mansy?action=show&root=1&tvd=2862000196494&vrn=2862000196490&region=86&global=&sub_region=0&prver=2&pronetvd=1&vibid=2862000196494&type=462'}})


if __name__ == '__main__':
    unittest.main()
