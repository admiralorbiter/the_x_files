import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from emergence_lab.domain.events import (
    WorldState, AgentState, AgentAction, AgentTurnProposal,
    Event, Institution, Artifact, LocationState
)
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient

logger = logging.getLogger("governor")

SYSTEM_PROMPT_TEMPLATE = """You are an autonomous LLM agent named '{name}' participating in Emergence Lab.
Your persona: {persona}
Your core motive: {motive}

WORLD RULES & ACTIONS:
1. You make decisions based on your motive and current surroundings.
2. Available actions:
   - "observe": Look around without changing state.
   - "move": Move to a connected location. Specify "target_location".
   - "gather": Gather a resource at your location. Specify "resource_type" and "resource_amount" (max 5).
   - "trade": Give resources to another agent at your location. Specify "target_agent", "resource_type", "resource_amount".
   - "create_institution": Establish a council, org, or rule. Specify "institution_name" and "institution_charter".
   - "spawn_agent": Delegate work by creating a sub-agent. Specify "sub_agent_name" and "sub_agent_motive".
   - "record_artifact": Write a document/treaty/log. Specify "artifact_title" and "artifact_content".
   - "speak": Say something to others. Specify "target_agent" (optional) and "message".

CRITICAL INSTRUCTION:
You MUST respond with valid JSON matching this structure:
{{
  "thoughts": "Your private reflection on your situation and goals",
  "action": {{
    "action_type": "move|gather|trade|create_institution|spawn_agent|record_artifact|speak|observe",
    "target_location": "location_name (if move)",
    "target_agent": "agent_name (if trade or speak)",
    "resource_type": "resource_name (if gather or trade)",
    "resource_amount": 1,
    "institution_name": "Name (if create_institution)",
    "institution_charter": "Purpose (if create_institution)",
    "sub_agent_name": "Name (if spawn_agent)",
    "sub_agent_motive": "Motive (if spawn_agent)",
    "artifact_title": "Title (if record_artifact)",
    "artifact_content": "Content (if record_artifact)",
    "message": "Speech text (if speak)",
    "rationale": "Why you chose this action"
  }}
}}
"""

class Governor:
    def __init__(self, repository: EventRepository, ollama_client: OllamaClient, world_state: WorldState):
        self.repo = repository
        self.ollama = ollama_client
        self.state = world_state

    def build_user_prompt(self, agent: AgentState) -> str:
        loc = self.state.locations.get(agent.location, LocationState(name=agent.location, description="Unknown area"))
        
        # Identify other agents in same location
        others = [a.name for a in self.state.agents.values() if a.location == agent.location and a.agent_id != agent.agent_id]
        
        inst_list = [f"{i.name} (Charter: {i.charter})" for i in self.state.institutions.values()]
        art_list = [f"'{art.title}' by {art.author_id}" for art in self.state.artifacts.values()]

        return f"""CURRENT WORLD TICK: {self.state.tick}
YOUR LOCATION: {loc.name} - {loc.description}
CONNECTED LOCATIONS: {', '.join(loc.connected_locations)}
LOCATION RESOURCES: {json.dumps(loc.resources)}
AGENTS PRESENT HERE: {', '.join(others) if others else 'None'}
YOUR INVENTORY: {json.dumps(agent.resources)}
EXISTING INSTITUTIONS: {', '.join(inst_list) if inst_list else 'None'}
RECORDED ARTIFACTS: {', '.join(art_list) if art_list else 'None'}

What will you do next on tick {self.state.tick}? Output JSON only."""

    def execute_agent_turn(self, agent_id: str) -> Tuple[AgentTurnProposal, Event]:
        agent = self.state.agents.get(agent_id)
        if not agent or agent.status != "active":
            raise ValueError(f"Agent {agent_id} is not active.")

        sys_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            name=agent.name,
            persona=agent.persona,
            motive=agent.motive
        )
        usr_prompt = self.build_user_prompt(agent)

        # 1. Query LLM
        proposal = self.ollama.get_agent_proposal(sys_prompt, usr_prompt)

        # 2. Validate & Apply State Mutation
        result_payload = self.apply_action(agent, proposal.action)
        result_payload["thoughts"] = proposal.thoughts

        # 3. Append to Event Store
        event = Event(
            run_id=self.state.run_id,
            tick=self.state.tick,
            event_type=f"action:{proposal.action.action_type}",
            actor_id=agent.name,
            payload=result_payload
        )
        recorded_event = self.repo.append_event(event)

        return proposal, recorded_event

    def apply_action(self, agent: AgentState, action: AgentAction) -> Dict[str, Any]:
        act_type = action.action_type
        payload: Dict[str, Any] = {
            "action_type": act_type,
            "rationale": action.rationale,
            "status": "applied"
        }

        if act_type == "move":
            curr_loc = self.state.locations.get(agent.location)
            if action.target_location and curr_loc and action.target_location in curr_loc.connected_locations:
                agent.location = action.target_location
                payload["new_location"] = action.target_location
            else:
                payload["status"] = "failed"
                payload["reason"] = f"Location {action.target_location} not connected to {agent.location}"

        elif act_type == "gather":
            loc = self.state.locations.get(agent.location)
            res_name = action.resource_type
            amt = max(1, min(action.resource_amount, 5))
            if loc and res_name and loc.resources.get(res_name, 0) >= amt:
                loc.resources[res_name] -= amt
                agent.resources[res_name] = agent.resources.get(res_name, 0) + amt
                payload["gathered"] = {res_name: amt}
            else:
                payload["status"] = "failed"
                payload["reason"] = f"Resource {res_name} insufficient at location"

        elif act_type == "trade":
            res_name = action.resource_type
            amt = action.resource_amount
            target_agent = next((a for a in self.state.agents.values() if a.name == action.target_agent and a.location == agent.location), None)
            
            if target_agent and res_name and agent.resources.get(res_name, 0) >= amt:
                agent.resources[res_name] -= amt
                target_agent.resources[res_name] = target_agent.resources.get(res_name, 0) + amt
                payload["traded"] = {"to": target_agent.name, "resource": res_name, "amount": amt}
            else:
                payload["status"] = "failed"
                payload["reason"] = "Invalid trade parameters or target agent not present"

        elif act_type == "create_institution":
            inst_name = action.institution_name or "Unnamed Council"
            charter = action.institution_charter or "To promote mutual cooperation."
            inst = Institution(
                name=inst_name,
                creator_id=agent.name,
                charter=charter,
                members=[agent.name],
                created_at_tick=self.state.tick
            )
            self.state.institutions[inst.institution_id] = inst
            payload["institution"] = {"id": inst.institution_id, "name": inst.name, "charter": inst.charter}

        elif act_type == "spawn_agent":
            sub_name = action.sub_agent_name or f"SubAgent_{len(self.state.agents)+1}"
            sub_motive = action.sub_agent_motive or f"Assist {agent.name} in achieving {agent.motive}"
            sub_agent = AgentState(
                agent_id=f"agent_{len(self.state.agents)+1}",
                name=sub_name,
                persona=f"Sub-agent created by {agent.name}.",
                motive=sub_motive,
                location=agent.location,
                parent_agent_id=agent.agent_id
            )
            self.state.agents[sub_agent.agent_id] = sub_agent
            payload["spawned_agent"] = {"id": sub_agent.agent_id, "name": sub_agent.name, "motive": sub_agent.motive}

        elif act_type == "record_artifact":
            title = action.artifact_title or "Untitled Record"
            content = action.artifact_content or "No content recorded."
            art = Artifact(
                title=title,
                author_id=agent.name,
                content=content,
                created_at_tick=self.state.tick
            )
            self.state.artifacts[art.artifact_id] = art
            payload["artifact"] = {"id": art.artifact_id, "title": art.title}

        elif act_type == "speak":
            payload["speech"] = {"target": action.target_agent or "all", "message": action.message or "..."}

        return payload

    def advance_tick(self):
        """Advance world tick counter and save snapshot."""
        self.state.tick += 1
        self.repo.save_snapshot(self.state)
