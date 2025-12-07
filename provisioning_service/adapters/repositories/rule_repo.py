from typing import List, Optional
from ...core.entities import SegmentRuleEntity
from .base import BaseRepository

class RuleRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "segment_rules")

    def find_rule_for_group(self, group: str) -> Optional[SegmentRuleEntity]:
        doc = self.collection.find_one({"required_group": group})
        return SegmentRuleEntity(**doc) if doc else None
        
    def get_all_target_segments(self) -> List[str]:
        return self.collection.distinct("target_segment")