from pymongo import MongoClient
from typing import Optional

class PromptStore:
    def __init__(self, mongo_uri: str, db_name: str = "GameOnAI", collection_name: str = "Prompts"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_prompt(self, name: str, content: str, metadata: Optional[dict] = None) -> str:
        existing = self.collection.find_one({"name": name})
        if existing:
            self.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"content": content, "metadata": metadata or {}}}
            )
            return str(existing["_id"])
        result = self.collection.insert_one({
            "name": name,
            "content": content,
            "metadata": metadata or {}
        })
        return str(result.inserted_id)

    def get_prompt(self, name: str) -> Optional[str]:
        result = self.collection.find_one({"name": name})
        return result["content"] if result else None

    def list_prompts(self):
        return [doc["name"] for doc in self.collection.find({}, {"name": 1})]
