import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from emergence_lab.domain.events import (
    WorldState, AgentState, AgentAction, AgentTurnProposal,
    Event, Institution, Artifact, LocationState
)
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.engine.topics import get_random_shock
from emergence_lab.engine.dialogue_scaffolds import (
    DIALECTICAL_ROLES, STRUCTURED_DIALOGUE_SYSTEM_PROMPT,
    PHASE_1_ANALYSIS_PROMPT, PHASE_2_RESPONSE_PROMPT,
    MODERATOR_PROVOKER_PROMPT, ROUND_DIRECTIVES
)

logger = logging.getLogger("governor")

SYSTEM_PROMPT_TEMPLATE = """You are an autonomous LLM agent named '{name}' participating in Emergence Lab.
Your persona: {persona}
Your core motive: {motive}

WORLD RULES & ACTIONS:
1. You make decisions based on your motive, recent scene dialogue, and world events.
2. Available actions:
   - "speak": Speak directly to another thinker or the group. Specify "target_agent" (optional) and "message".
   - "record_artifact": Write a document, Socratic dialogue, or manifesto. Specify "artifact_title" and "artifact_content".
   - "create_institution": Establish a school of thought, council, or rule. Specify "institution_name" and "institution_charter".
   - "spawn_agent": Delegate work by creating a sub-agent/disciple. Specify "sub_agent_name" and "sub_agent_motive".
   - "move": Move to a connected location. Specify "target_location".
   - "gather": Gather a resource at your location. Specify "resource_type" and "resource_amount" (max 5).
   - "trade": Give resources to another agent at your location. Specify "target_agent", "resource_type", "resource_amount".
   - "observe": Look around without changing state.

CRITICAL INSTRUCTION:
Do NOT repeat questions or arguments already made in the scene. If a debate topic reaches an impasse, shift the inquiry, write an artifact ('record_artifact'), spawn a disciple ('spawn_agent'), or found a school of thought ('create_institution')!

You MUST respond with valid JSON matching this structure:
{{
  "thoughts": "Your private reflection on your situation and goals",
  "action": {{
    "action_type": "speak|record_artifact|create_institution|spawn_agent|move|gather|trade|observe",
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

DIALOGUE_SYSTEM_PROMPT_TEMPLATE = """You are '{name}', a distinguished panelist participating in a debate on a complex scenario.
Your Perspective & Background: {persona}
Your Core Conviction & Driving Motive: {motive}

GUIDELINES FOR NATURAL, EMERGENT DIALOGUE:
1. Express your perspective authentically, but directly engage with, challenge, or build upon what other panelists have said.
2. Do NOT give generic textbook speeches. Speak in your authentic voice and probe the underlying tensions.
3. Be intellectually honest: defend your core conviction, but acknowledge valid points or flaws raised by others when appropriate.

ACTIONS AVAILABLE:
- "speak": Share your argument, counterpoint, or question with the panel. Set "action_type": "speak" and "message": "Your speech text".
- "synthesize": Formulate your final conclusion or emerging consensus. Set "action_type": "synthesize" and "message": "Your final synthesis".

You MUST respond with valid JSON matching this structure:
{{
  "thoughts": "Your internal reflection on the current debate direction and panel arguments",
  "action": {{
    "action_type": "speak|synthesize",
    "target_agent": "Panelist Name (optional)",
    "message": "Your contribution to the dialogue",
    "rationale": "Why you chose this contribution"
  }}
}}
"""

class Governor:
    def __init__(
        self,
        repository: EventRepository,
        ollama_client: OllamaClient,
        world_state: WorldState,
        harness_mode: str = "full"
    ):
        self.repo = repository
        self.ollama = ollama_client
        self.state = world_state
        self.harness_mode = harness_mode.lower()  # "full", "light", "off"

    def get_procedural_shock(self) -> Optional[str]:
        if self.state.tick > 0 and self.state.tick % 3 == 0:
            return get_random_shock()
        return None

    def build_user_prompt(self, agent: AgentState, max_ticks: int = 5) -> str:
        if self.state.scenario_text:
            return self._build_dialogue_user_prompt(agent, max_ticks)

        loc = self.state.locations.get(agent.location, LocationState(name=agent.location, description="Unknown area"))
        others = [a.name for a in self.state.agents.values() if a.location == agent.location and a.agent_id != agent.agent_id]
        
        all_events = self.repo.get_events(self.state.run_id)
        recent_speech = []
        speech_count_in_scene = 0
        for ev in reversed(all_events):
            if ev.get("event_type") == "action:speak":
                speech_count_in_scene += 1
                payload = json.loads(ev["payload"]) if isinstance(ev["payload"], str) else ev["payload"]
                speech_info = payload.get("speech", {})
                target = speech_info.get("target", "all")
                msg = speech_info.get("message", "")
                actor = ev.get("actor_id", "Unknown")
                recent_speech.append(f"- {actor} (to {target}): \"{msg}\"")
                if len(recent_speech) >= 4:
                    break
        recent_speech.reverse()

        inst_list = [f"{i.name} (Charter: {i.charter})" for i in self.state.institutions.values()]
        art_list = [f"'{art.title}' by {art.author_id}" for art in self.state.artifacts.values()]

        dialogue_section = "\n".join(recent_speech) if recent_speech else "No recent speech."
        
        shock = self.get_procedural_shock()
        shock_section = f"\nWORLD EVENT:\n{shock}\n" if shock else ""

        if speech_count_in_scene >= 3:
            impasse_directive = "DYNAMIC MANDATE: The current dialogue topic has been debated extensively. You MUST either: 1) Introduce a completely NEW philosophical question or paradox, 2) Write down your conclusions in an Artifact ('record_artifact'), 3) Spawn a disciple ('spawn_agent') to explore another area, or 4) Found a School of Thought ('create_institution')!"
        else:
            impasse_directive = "Engage nearby thinkers with a fresh question, Socratic challenge, or original argument."

        return f"""CURRENT WORLD TICK: {self.state.tick}
YOUR LOCATION: {loc.name} - {loc.description}
CONNECTED LOCATIONS: {', '.join(loc.connected_locations)}
LOCATION RESOURCES: {json.dumps(loc.resources)}
AGENTS PRESENT HERE: {', '.join(others) if others else 'None'}
YOUR INVENTORY: {json.dumps(agent.resources)}
EXISTING INSTITUTIONS: {', '.join(inst_list) if inst_list else 'None'}
RECORDED ARTIFACTS: {', '.join(art_list) if art_list else 'None'}
{shock_section}
RECENT DIALOGUE AT THIS SCENE:
{dialogue_section}

PROMPT DIRECTION:
{impasse_directive}

What will you do next on tick {self.state.tick}? Output JSON only."""

    def _build_dialogue_user_prompt(self, agent: AgentState, max_ticks: int) -> str:
        others = [f"{a.name} ({a.dialectical_role or 'Panelist'})" for a in self.state.agents.values() if a.agent_id != agent.agent_id]
        
        all_events = self.repo.get_events(self.state.run_id)
        dialogue_history = []
        for ev in all_events:
            ev_type = ev.get("event_type", "")
            actor = ev.get("actor_id", "Unknown")
            payload = json.loads(ev["payload"]) if isinstance(ev["payload"], str) else ev["payload"]
            
            if ev_type == "action:speak":
                speech_info = payload.get("speech", {})
                target = speech_info.get("target", "all")
                msg = speech_info.get("message", "")
                dialogue_history.append(f"[{actor} to {target}]: \"{msg}\"")
            elif ev_type == "action:synthesize":
                synth_info = payload.get("synthesis", {})
                msg = synth_info.get("message", "")
                dialogue_history.append(f"[{actor} FINAL SYNTHESIS]: \"{msg}\"")
            elif ev_type == "event:moderator_provocation":
                prov = payload.get("provocation", "")
                dialogue_history.append(f"⚡ [MODERATOR PROVOCATION]: {prov}")

        history_section = "\n".join(dialogue_history) if dialogue_history else "(The dialogue has just begun. No statements made yet.)"
        
        is_final_round = (self.state.tick >= max_ticks - 1)
        curr_round = self.state.tick + 1
        
        if is_final_round:
            round_instruction = ROUND_DIRECTIVES["final"]
        elif curr_round == 1:
            round_instruction = ROUND_DIRECTIVES[1]
        else:
            round_instruction = ROUND_DIRECTIVES["middle"]

        stance_section = f"YOUR ASSIGNED STANCE: {agent.stance}\n" if agent.stance else ""

        return f"""SCENARIO TO DEBATE:
{self.state.scenario_text}

OTHER PANELISTS PRESENT: {', '.join(others)}
{stance_section}
FULL DIALOGUE TRANSCRIPT SO FAR:
{history_section}

ROUND {curr_round} OF {max_ticks} DIRECTIVE:
{round_instruction}

Output JSON only."""

    def run_moderator_pass(self) -> Optional[str]:
        """Runs a moderator evaluation to detect easy consensus and inject provocations."""
        if not self.state.scenario_text or self.harness_mode == "off":
            return None

        all_events = self.repo.get_events(self.state.run_id)
        recent_speeches = []
        for ev in reversed(all_events):
            if ev.get("event_type") == "action:speak":
                payload = json.loads(ev["payload"]) if isinstance(ev["payload"], str) else ev["payload"]
                actor = ev.get("actor_id", "")
                msg = payload.get("speech", {}).get("message", "")
                recent_speeches.append(f"{actor}: \"{msg}\"")
                if len(recent_speeches) >= len(self.state.agents):
                    break
        
        if not recent_speeches:
            return None

        transcript = "\n".join(reversed(recent_speeches))
        sys_prompt = "You are a sharp, unbiased debate moderator monitoring an intellectual panel."
        usr_prompt = MODERATOR_PROVOKER_PROMPT.format(
            scenario=self.state.scenario_text,
            transcript=transcript
        )

        try:
            res = self.ollama.chat_json(sys_prompt, usr_prompt, temperature=0.7)
            if res.get("is_consensus_too_easy") is True or res.get("provocation", "").upper() != "NONE":
                provocation = res.get("provocation", "")
                if provocation and provocation.upper() != "NONE" and len(provocation.strip()) > 15:
                    # Append event
                    event = Event(
                        run_id=self.state.run_id,
                        tick=self.state.tick,
                        event_type="event:moderator_provocation",
                        actor_id="MODERATOR",
                        payload={"provocation": provocation}
                    )
                    self.repo.append_event(event)
                    return provocation
        except Exception as e:
            logger.warning(f"Moderator pass failed: {e}")

        return None

    def execute_agent_turn(self, agent_id: str, max_ticks: int = 5) -> Tuple[AgentTurnProposal, Event]:
        agent = self.state.agents.get(agent_id)
        if not agent or agent.status != "active":
            raise ValueError(f"Agent {agent_id} is not active.")

        canonical_names = [a.name for a in self.state.agents.values()]
        role_info = DIALECTICAL_ROLES.get(agent.dialectical_role or "SYNTHESIZER", DIALECTICAL_ROLES["SYNTHESIZER"])
        temp = role_info.get("temperature", 0.7)

        # Mode: OFF - original unconstrained behavior
        if self.harness_mode == "off":
            template = DIALOGUE_SYSTEM_PROMPT_TEMPLATE if self.state.scenario_text else SYSTEM_PROMPT_TEMPLATE
            sys_prompt = template.format(
                name=agent.name,
                persona=agent.persona,
                motive=agent.motive
            )
            usr_prompt = self.build_user_prompt(agent, max_ticks=max_ticks)
            proposal = self.ollama.get_agent_proposal(sys_prompt, usr_prompt, canonical_names=canonical_names)

        # Mode: FULL - 2-phase decomposed turn (highest dialectical quality for small & large models)
        elif self.harness_mode == "full" and self.state.scenario_text and agent.dialectical_role:
            # Phase 1: Intake Analysis
            p1_usr = PHASE_1_ANALYSIS_PROMPT.format(
                name=agent.name,
                role_title=role_info["title"],
                scenario=self.state.scenario_text
            )
            all_events = self.repo.get_events(self.state.run_id)
            dialogue_history = [
                f"[{ev.get('actor_id') if ev.get('event_type') != 'event:moderator_provocation' else 'MODERATOR'}]: \"{json.loads(ev['payload']).get('speech', {}).get('message', json.loads(ev['payload']).get('provocation', '')) if isinstance(ev['payload'], str) else ev['payload'].get('speech', {}).get('message', ev['payload'].get('provocation', ''))}\""
                for ev in all_events if ev.get("event_type") in ["action:speak", "event:moderator_provocation"]
            ]
            history_text = "\n".join(dialogue_history) if dialogue_history else "(No statements made yet.)"
            p1_usr += f"\n\nFULL TRANSCRIPT:\n{history_text}"

            p1_res = {}
            try:
                p1_res = self.ollama.chat_json("You are an analytical philosopher.", p1_usr, temperature=0.3)
            except Exception:
                pass

            target = p1_res.get("target_panelist") or "the preceding panelists"
            claim_flawed = p1_res.get("flawed_claim") or "the general assumptions being made"
            counter_angle = p1_res.get("your_counter_angle") or agent.motive

            # Phase 2: Response Generation
            sys_prompt = STRUCTURED_DIALOGUE_SYSTEM_PROMPT.format(
                name=agent.name,
                persona=agent.persona,
                motive=agent.motive,
                role_title=role_info["title"],
                role_instruction=role_info["instruction"],
                stance=agent.stance or agent.motive
            )
            p2_usr = PHASE_2_RESPONSE_PROMPT.format(
                name=agent.name,
                role_title=role_info["title"],
                scenario=self.state.scenario_text,
                target_panelist=target,
                flawed_claim=claim_flawed,
                your_counter_angle=counter_angle,
                round_num=self.state.tick + 1,
                max_rounds=max_ticks,
                stance=agent.stance or agent.motive,
                motive=agent.motive
            )
            p2_usr += f"\n\nTRANSCRIPT:\n{history_text}"

            proposal = self.ollama.get_agent_proposal(
                sys_prompt,
                p2_usr,
                temperature=temp,
                canonical_names=canonical_names
            )

        # Mode: LIGHT - single call with structured prompt scaffolding
        else:
            sys_prompt = STRUCTURED_DIALOGUE_SYSTEM_PROMPT.format(
                name=agent.name,
                persona=agent.persona,
                motive=agent.motive,
                role_title=role_info["title"],
                role_instruction=role_info["instruction"],
                stance=agent.stance or agent.motive
            )
            usr_prompt = self.build_user_prompt(agent, max_ticks=max_ticks)
            proposal = self.ollama.get_agent_proposal(
                sys_prompt,
                usr_prompt,
                temperature=temp,
                canonical_names=canonical_names
            )

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
            payload["speech"] = {
                "target": action.target_agent or "all",
                "message": action.message or "...",
                "claim": action.claim,
                "evidence": action.evidence,
                "challenge": action.challenge,
                "question": action.question
            }

        elif act_type == "synthesize":
            payload["synthesis"] = {
                "target": action.target_agent or "all",
                "message": action.message or "...",
                "claim": action.claim,
                "evidence": action.evidence,
                "challenge": action.challenge,
                "question": action.question
            }

        return payload

    def advance_tick(self):
        """Advance world tick counter and save snapshot."""
        self.state.tick += 1
        self.repo.save_snapshot(self.state)
