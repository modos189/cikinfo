from pymongo import MongoClient

client = MongoClient()
db = client.cikinfo_beta


# Добавляет информацию о выборах в БД
def get_elections():
    collection = db.election
    return collection.find()

