from pymongo import MongoClient
from typing import List
from ..core.domain_models import UserContext

class MongoRepository:
    def __init__(self):
        self.client = MongoClient("mongodb://admin:password@localhost:27017/")
        self.db = self.client["sase_db"]

    def get_segments_for_user(self, context: UserContext) -> List[str]:
        segments = ["seg-global-default"]
        rules_col = self.db["segment_rules"]
        
        # Check each group the user belongs to
        for group in context.groups:
            rule = rules_col.find_one({"required_group": group})
            if rule:
                segments.append(rule["target_segment"])
        
        return list(set(segments))