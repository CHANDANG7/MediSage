from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'medisage_db')

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGODB_URI)
async_db = async_client[DATABASE_NAME]

# Collections
users_collection = async_db['users']
patients_collection = async_db['patients']
chat_sessions_collection = async_db['chat_sessions']

def get_database():
    """Get database instance"""
    return async_db
