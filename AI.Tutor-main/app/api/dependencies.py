from fastapi import Depends
from app.database.milvus_db import MilvusDB

milvus_db = MilvusDB()

def get_db():
    return milvus_db
    
