from . import helpers


# Возвращает идентификатор УИКа, при необходимости создаёт
def uik_id(db, param):
    collection = db.area

    if collection.count(param):
        _id = collection.find_one(param, {})['_id']
    else:
        _id = collection.insert_one(param).inserted_id

    return _id


# Добавляет информацию о выборах в БД
def add_election(db, name, url, date, sub_elections):
    _hash = helpers.hash_item(url)
    if db.election.count({'_id': _hash}):
        return _hash
    else:
        doc = {'_id': _hash, 'name': name, 'url': url, 'date': date, 'sub_elections': sub_elections, 'is_loaded': False}
        return db.election.insert_one(doc).inserted_id


def election_is_loaded(db, _id):
    return db.election.find({'_id': _id})['is_loaded']


# Сохраняет идентификатор стартовой территории, с которой начинается приближение до УИКов
# Может быть корневым "Российская Федерация", неким округом или городом
def set_election_start_area(db, election_id, area_id):
    db.election.update_one({'_id': election_id}, {
        '$set': {"start_area": area_id}
    })


# Сохраняет результаты выборов в БД
def add_uik_results(db, election_id, election_type, region, parent_id, level, uiks):
    for uik in uiks:
        aid = uik_id(db, {
            'region': region, 'num': uik['num'], 'name': uik['name'], 'level': level, 'parent_id': parent_id
        })

        db.area.update_one({'_id': aid}, {
            '$set': {'results.' + election_id + '.' + election_type: uik['results'], "max_depth": True},
            '$addToSet': {'results_tags': election_id}
        })


# Возвращает значение, указана ли мета-информация для документа выборов
def election_meta_exist(db, election_id):
    return bool(db.election.count({'_id': election_id, 'meta.0': {'$exists': True}}))
