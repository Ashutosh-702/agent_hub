import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient as AsyncMongoClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "linkedin_db")

client = AsyncMongoClient(MONGO_URL)
db = client[DB_NAME]

accounts_collection = db["accounts"]
batches_collection = db["batches"]
batch_values_collection = db["batch_values"]
leads_collection = db["leads"] 