import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient as AsyncMongoClient

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "linkedin_sdr")

client = AsyncMongoClient(MONGO_URI)
db = client[DB_NAME]

accounts_collection = db["accounts"]
batches_collection = db["batches"]
batch_values_collection = db["batch_values"]
leads_collection = db["leads"] 