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
def add_election(db, name, url, date):
    _hash = helpers.hash_item(url)
    if db.election.count({'_id': _hash}):
        return False
    else:
        doc = {'_id': _hash, 'name': name, 'url': url, 'date': date}
        return db.election.insert_one(doc).inserted_id


# Сохраняет результаты выборов в БД
def add_uik_results(db, election_id, region, parent_id, level, uiks):
    for uik in uiks:
        aid = uik_id(db, {
            'region': region, 'num': uik.num, 'name': uik.name, 'level': level, 'parent_id': parent_id
        })

        db.area.update_one({'_id': aid}, {
            '$set': {'results.' + election_id: uik.results, "max_depth": True},
            '$addToSet': {'results_tags': election_id}
        })


# Добавление к документу выборов мета-информации о существующих полях, по которым возможна выборка
def add_election_meta(db, election_id, meta):
    db.election.update_one({'_id': election_id}, {"$set": {'meta': meta}})


# Возвращает значение, указана ли мета-информация для документа выборов
def election_meta_exist(db, election_id):
    return bool(db.election.count({'_id': election_id, 'meta.0': {'$exists': True}}))
