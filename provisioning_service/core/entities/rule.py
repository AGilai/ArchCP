from .base import BaseEntity

class SegmentRuleEntity(BaseEntity):
    required_group: str
    target_segment: str