from pymongo import MongoClient
from . import helpers

from tqdm import tqdm

client = MongoClient()
db = client.cikinfo_beta


# Возвращает идентификатор субъекта/региона/УИК, при необходимости создаёт документ
def area_id(data):
    collection = db.area
    parent_id = 0
    for i, area in enumerate(data):
        param = {'num': area[0], 'name': area[1], 'level': i, 'parent_id': parent_id}
        if collection.count(param):
            parent_id = collection.find_one(param, {})['_id']
        else:
            parent_id = collection.insert_one(param).inserted_id
    return parent_id


# Добавляет информацию о выборах в БД
def add_election(name, url, date):
    collection = db.election
    _hash = helpers.hash_item(url)
    if collection.count({'_id': _hash}):
        return False
    else:
        doc = {'_id': _hash, 'name': name, 'url': url, 'date': date}
        return collection.insert_one(doc).inserted_id


# Сохраняет результаты выборов в БД
def add_election_results(area, results, max_depth=False):
    collection = db.area
    aid = area_id(area)
    if results is not None:
        collection.update_one({'_id': aid}, {"$addToSet": {'results': results}})
    if max_depth is True:
        collection.update_one({'_id': aid}, {'$set': {"max_depth": True}})


# Добавление к документу выборов мета-информации о существующих полях, по которым возможна выборка
def add_election_meta(election_id, meta):
    db.election.update_one({'_id': election_id}, {"$set": {'meta': meta}})


# Возвращает значение, указана ли мета-информация для документа выборов
def election_meta_exist(election_id):
    return bool(db.election.count({'_id': election_id, 'meta': {'$exists': True}}))


# Возвращает уровень детализации уровней до УИКов
def get_depth_election_area(election_id):
    obj_area = db.area.find_one({'results.election_id': election_id}, {'level': 1}, sort=[("level", -1)])
    if obj_area is None:
        return None
    else:
        return obj_area['level']


def set_level_reverse(election_id, level, level_reverse):
    db.area.update_many({'results.election_id': election_id, 'level': level}, {'$set': {'level_reverse': level_reverse}})


def calc_stat(election_id):
    level = 5
    if level is not None:

        while level >= 0:

            a = list(db.area.find({'level': level, 'max_depth': {'$ne': True}}, {'_id': 1}))
            # Перебор родительского уровня приближения
            for item in tqdm(a):

                # Получение дочерних уровней приближения
                data = db.area.find(
                    {'parent_id': item['_id'], 'results.election_id': election_id},
                    {'results.$': True})

                if data.count() > 0:

                    # Получение каркаса массива результатов
                    results = data[0]['results'][0]
                    for k in results:
                        if str(k).isdigit():
                            results[k] = 0

                    for area in data:
                        res = area['results'][0]
                        for k in res:
                            if str(k).isdigit():
                                results[k] += int(res[k])

                    db.area.update_one({'_id': item['_id']}, {"$addToSet": {'results': results}})

            level -= 1
