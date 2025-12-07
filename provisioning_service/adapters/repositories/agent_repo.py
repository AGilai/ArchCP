from typing import Optional
from ...core.entities import AgentStateEntity
from .base import BaseRepository

class AgentRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "agents_state")

    def upsert_agent(self, agent: AgentStateEntity):
        data = agent.model_dump(exclude={"id"})
        self.collection.update_one(
            {"agent_id": agent.agent_id},
            {"$set": data},
            upsert=True
        )

    def get_agent(self, agent_id: str) -> Optional[AgentStateEntity]:
        doc = self.collection.find_one({"agent_id": agent_id})
        return AgentStateEntity(**doc) if doc else None