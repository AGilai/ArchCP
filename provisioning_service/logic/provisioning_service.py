from typing import List, Dict
from ..core.entities import AgentStateEntity
from ..core.domain_models import UserContext
from ..adapters.repositories import AgentRepository, RuleRepository, SegmentStateRepository

class ProvisioningService:
    def __init__(self, agent_repo: AgentRepository, rule_repo: RuleRepository, seg_repo: SegmentStateRepository):
        self.agent_repo = agent_repo
        self.rule_repo = rule_repo
        self.seg_repo = seg_repo

    def onboard_agent(self, agent_id: str, tenant_id: str, context: UserContext) -> Dict:
        """
        Orchestrates the onboarding logic:
        1. Calculate Segments (Business Logic)
        2. Persist State (Repo Call)
        3. Fetch Versions (Repo Call)
        """
        # 1. Business Logic: Map Groups -> Segments
        assigned_segments = ["seg-global"] # Default policy
        
        for group in context.groups:
            rule = self.rule_repo.find_rule_for_group(group)
            if rule:
                assigned_segments.append(rule.target_segment)
        
        # Deduplicate
        assigned_segments = list(set(assigned_segments))

        # 2. Persistence Logic: Create Entity and Save
        agent_entity = AgentStateEntity(
            agent_id=agent_id,
            tenant_id=tenant_id,
            assigned_segments=assigned_segments,
            status="ONLINE"
        )
        self.agent_repo.upsert_agent(agent_entity)

        # 3. Enrichment Logic: Get current versions
        versions_map = self.seg_repo.get_versions_map(assigned_segments)
        
        # Ensure every segment has a version (default to 0)
        for seg in assigned_segments:
            if seg not in versions_map:
                versions_map[seg] = 0
                
        return {
            "segments": assigned_segments,
            "versions": versions_map
        }

    def pick_random_segment_update(self):
        """Simulator Logic: Pick a segment and bump version"""
        import random
        all_segments = self.rule_repo.get_all_target_segments()
        if not all_segments:
            return None, None
            
        target = random.choice(all_segments)
        new_ver = self.seg_repo.increment_version(target)
        return target, new_ver