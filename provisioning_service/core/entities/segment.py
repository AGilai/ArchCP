from .base import BaseEntity

class SegmentVersionEntity(BaseEntity):
    segment_id: str
    version_counter: int = 1