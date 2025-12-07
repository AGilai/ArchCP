from typing import List, Dict
from pymongo import ReturnDocument
from .base import BaseRepository

class SegmentStateRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "segments_state")

    def increment_version(self, segment_id: str) -> int:
        doc = self.collection.find_one_and_update(
            {"segment_id": segment_id},
            {"$inc": {"version_counter": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return doc["version_counter"]
        
    def get_versions_map(self, segment_ids: List[str]) -> Dict[str, int]:
        cursor = self.collection.find({"segment_id": {"$in": segment_ids}})
        return {doc["segment_id"]: doc["version_counter"] for doc in cursor}