import os
from pymongo import MongoClient
from logs.models import RequestLog

def get_mongo_client():
    """
    Establish and return a MongoDB client based on environment variable MONGO_URI.
    """
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
    return MongoClient(mongo_uri)

def insert_log_to_mongo(log: RequestLog):
    """
    Receives a RequestLog instance and inserts it into MongoDB 'logs_db.requests' collection.
    """
    client = get_mongo_client()
    db = client["logs_db"]
    collection = db["requests"]

    collection.insert_one(log.to_dict())

    client.close()