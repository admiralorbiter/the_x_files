"""Deterministic State Compiler for Emergence Lab.

Compiles WorldState and event history into compact, token-dense packets for LLMs,
using deterministic IDs (p1, p2, p3) rather than full transcript dumps.
"""

from typing import Dict, Any, List, Optional
from emergence_lab.domain.events import WorldState, AgentState, Event

class StateCompiler:
    def __init__(self, world_state: WorldState):
        self.state = world_state
        self.agent_to_pid: Dict[str, str] = {}
        self.pid_to_agent: Dict[str, AgentState] = {}
        self.pid_to_name: Dict[str, str] = {}
        
        for idx, (agent_id, agent) in enumerate(self.state.agents.items(), start=1):
            pid = f"p{idx}"
            self.agent_to_pid[agent.name] = pid
            self.agent_to_pid[agent.agent_id] = pid
            self.pid_to_agent[pid] = agent
            self.pid_to_name[pid] = agent.name

    def get_pid(self, agent_name_or_id: str) -> str:
        return self.agent_to_pid.get(agent_name_or_id, agent_name_or_id)

    def resolve_pid(self, pid: str) -> Optional[AgentState]:
        clean_pid = pid.strip().lower()
        if clean_pid in self.pid_to_agent:
            return self.pid_to_agent[clean_pid]
        # Fallback search by name
        for agent_name, agent_pid in self.agent_to_pid.items():
            if clean_pid in agent_name.lower():
                return self.pid_to_agent.get(agent_pid)
        return None

    def compile_for_agent(self, agent_id: str, events: List[Event], max_ticks: int) -> str:
        agent = self.state.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        self_pid = self.get_pid(agent.name)
        
        # Other panelists info
        other_panelists = []
        valid_targets = []
        for pid, other in self.pid_to_agent.items():
            if pid != self_pid:
                valid_targets.append(pid)
                other_panelists.append(
                    f"  {pid}: role={other.dialectical_role or 'PANELIST'}, stance=\"{other.stance or other.motive}\""
                )

        # Extract recent claims by PID
        recent_claims = []
        for ev in reversed(events):
            if ev.event_type == "action:speak":
                actor_pid = self.get_pid(ev.actor_id)
                payload = ev.payload
                speech = payload.get("speech", {}) if isinstance(payload, dict) else {}
                claim = speech.get("claim") or speech.get("message", "")
                if claim:
                    recent_claims.append(f"  {actor_pid} claimed: \"{claim}\"")
                if len(recent_claims) >= len(self.state.agents):
                    break
        recent_claims.reverse()

        claims_block = "\n".join(recent_claims) if recent_claims else "  (No previous claims made)"
        panel_block = "\n".join(other_panelists) if other_panelists else "  None"
        curr_tick = self.state.tick + 1

        return f"""YOU
id: {self_pid} ({agent.name})
role: {agent.dialectical_role or 'PANELIST'}
stance: "{agent.stance or agent.motive}"

SCENARIO
"{self.state.scenario_text or 'No scenario defined'}"

OTHER PANELISTS
{panel_block}

VALID TARGET IDs: {', '.join(valid_targets)}

RECENT DEBATE CLAIMS
{claims_block}

ROUND {curr_tick} OF {max_ticks} MANDATE
Respond primarily to one of the target IDs ({', '.join(valid_targets)}).
State your claim, evidence, direct challenge to target_id, and a probing question."""
