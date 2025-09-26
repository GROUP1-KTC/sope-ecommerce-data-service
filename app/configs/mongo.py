from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from app.configs.settings import settings

# Mongo URI
MONGO_URI = settings.mongo_uri

# Database & Collection
DB_NAME = settings.db_name_mongo
COLLECTION_NAME = settings.collection_name

# Mongo client init
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
