import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from emergence_lab.domain.events import (
    WorldState, AgentState, AgentAction, AgentTurnProposal,
    Event, Institution, Artifact, LocationState
)
from emergence_lab.domain.telemetry import InferenceResult
from emergence_lab.domain.dialogue_schemas import DialogueTurn, IntakeAnalysis
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.engine.topics import get_random_shock
from emergence_lab.engine.state_compiler import StateCompiler
from emergence_lab.engine.verifier import DeterministicVerifier, run_targeted_target_repair
from emergence_lab.engine.text_cleanup import clean_stutters
from emergence_lab.engine.dialogue_scaffolds import MODERATOR_PROVOKER_PROMPT

logger = logging.getLogger("governor")

class Governor:
    def __init__(
        self,
        repository: EventRepository,
        ollama_client: OllamaClient,
        world_state: WorldState,
        harness_mode: str = "compact"
    ):
        self.repo = repository
        self.ollama = ollama_client
        self.state = world_state
        
        mode = harness_mode.lower()
        if mode in ["full", "compact", "light"]:
            self.harness_mode = "compact"
        else:
            self.harness_mode = "raw"
            
        self.compiler = StateCompiler(self.state)

    def get_procedural_shock(self) -> Optional[str]:
        if self.state.tick > 0 and self.state.tick % 3 == 0:
            return get_random_shock()
        return None

    def run_moderator_pass(self) -> Optional[str]:
        """Runs a moderator evaluation to detect easy consensus and inject provocations."""
        if not self.state.scenario_text or self.harness_mode == "raw":
            return None

        all_events = self.repo.get_events(self.state.run_id)
        recent_speeches = []
        for ev in reversed(all_events):
            if ev.get("event_type") == "action:speak":
                payload = json.loads(ev["payload"]) if isinstance(ev["payload"], str) else ev.get("payload", {})
                actor = ev.get("actor_id", "")
                msg = payload.get("speech", {}).get("message", "") if isinstance(payload, dict) else ""
                if msg:
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

        all_events = [
            Event(
                run_id=ev["run_id"],
                tick=ev["tick"],
                event_type=ev["event_type"],
                actor_id=ev["actor_id"],
                payload=json.loads(ev["payload"]) if isinstance(ev["payload"], str) else ev["payload"]
            )
            for ev in self.repo.get_events(self.state.run_id)
        ]

        # Harness Mode: COMPACT (V2 Architecture - StateCompiler + JSON Schema + Verifier)
        if self.harness_mode == "compact" and self.state.scenario_text:
            compiled_prompt = self.compiler.compile_for_agent(agent_id, all_events, max_ticks=max_ticks)
            sys_prompt = f"You are panelist {self.compiler.get_pid(agent.name)} in a high-stakes dialectic."

            # Call LLM with strict DialogueTurn JSON Schema
            turn_json, telemetry = self.ollama.chat_structured(
                sys_prompt,
                compiled_prompt,
                response_schema=DialogueTurn
            )

            try:
                turn = DialogueTurn.model_validate(turn_json)
            except Exception:
                turn = DialogueTurn(
                    target_id="p1",
                    claim=turn_json.get("claim", "We must analyze the core assumptions."),
                    evidence=turn_json.get("evidence", "Reasoning is required."),
                    challenge=turn_json.get("challenge", "Direct challenge."),
                    question=turn_json.get("question", "What is the priority?")
                )

            # Deterministic Verifier Pass
            valid_target_pids = [
                pid for pid in self.compiler.pid_to_agent.keys()
                if pid != self.compiler.get_pid(agent.name)
            ]
            verifier = DeterministicVerifier(valid_target_pids)
            v_res = verifier.verify(turn)

            # If target_id invalid, run targeted micro-repair
            if not v_res.is_valid and any("invalid_target_id" in issue for issue in v_res.issues):
                repaired_pid, is_success = run_targeted_target_repair(
                    self.ollama,
                    turn.target_id,
                    valid_target_pids
                )
                turn.target_id = repaired_pid
                telemetry.validation_status = "repaired"
                telemetry.repairs_applied.append(f"targeted_repair_target_id_{repaired_pid}")

            # Resolve PID target back to canonical AgentState
            target_agent_state = self.compiler.resolve_pid(turn.target_id)
            target_name = target_agent_state.name if target_agent_state else turn.target_id

            # Assembled speech text (no harness prose inserted!)
            assembled_speech = f"{turn.claim} {turn.evidence} {turn.challenge} {turn.question}".strip()
            assembled_speech = clean_stutters(assembled_speech)

            action = AgentAction(
                action_type="speak",
                target_agent=target_name,
                claim=turn.claim,
                evidence=turn.evidence,
                challenge=turn.challenge,
                question=turn.question,
                message=assembled_speech,
                rationale=f"Debating stance against {target_name}"
            )

            proposal = AgentTurnProposal(
                thoughts=f"Analyzing debate trajectory against {target_name}.",
                action=action,
                telemetry=telemetry
            )

        # Harness Mode: RAW or Fallback
        else:
            sys_prompt = f"You are {agent.name}. Respond to the scenario: {self.state.scenario_text}"
            usr_prompt = f"State your argument on tick {self.state.tick + 1}."
            raw_json, telemetry = self.ollama.chat_structured(sys_prompt, usr_prompt)
            
            action = AgentAction(
                action_type="speak",
                target_agent="all",
                message=str(raw_json.get("message", raw_json.get("claim", "Engaging in dialogue"))),
                rationale="Standard turn"
            )
            proposal = AgentTurnProposal(
                thoughts=str(raw_json.get("thoughts", "Reflecting.")),
                action=action,
                telemetry=telemetry
            )

        # Apply state mutation and record event with telemetry
        result_payload = self.apply_action(agent, proposal.action)
        result_payload["thoughts"] = proposal.thoughts

        event = Event(
            run_id=self.state.run_id,
            tick=self.state.tick,
            event_type=f"action:{proposal.action.action_type}",
            actor_id=agent.name,
            payload=result_payload,
            telemetry=proposal.telemetry
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

        if act_type == "speak":
            payload["speech"] = {
                "target": action.target_agent or "all",
                "message": action.message or "",
                "claim": action.claim,
                "evidence": action.evidence,
                "challenge": action.challenge,
                "question": action.question
            }
        elif act_type == "synthesize":
            payload["synthesis"] = {
                "target": action.target_agent or "all",
                "message": action.message or "",
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
