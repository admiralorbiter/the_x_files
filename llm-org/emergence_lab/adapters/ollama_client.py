import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from emergence_lab.domain.events import AgentTurnProposal, AgentAction
from emergence_lab.config import default_config
from emergence_lab.engine.text_cleanup import clean_stutters, fix_name_references, is_generic_response
from emergence_lab.engine.dialogue_scaffolds import assemble_speech

def extract_json_payload(text: str) -> Dict[str, Any]:
    """Extracts JSON object from response text, handling markdown codeblocks or raw text."""
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting markdown ```json ... ``` block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding outer braces { ... }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse valid JSON from text: {text[:100]}...")

class OllamaClient:
    def __init__(
        self,
        base_url: str = default_config.ollama_base_url,
        model: str = default_config.default_model,
        fallback_model: str = default_config.fallback_model,
        temperature: float = default_config.temperature
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback_model = fallback_model
        self.temperature = temperature

    def _call_api(self, model_name: str, system_prompt: str, user_prompt: str, use_json_format: bool = True, temperature: Optional[float] = None) -> str:
        temp = temperature if temperature is not None else self.temperature
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temp
            }
        }
        if use_json_format:
            payload["format"] = "json"

        url = f"{self.base_url}/api/chat"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=default_config.request_timeout) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("message", {}).get("content", "{}")

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Calls Ollama API with fallback strategies to prevent HTTP 500 errors."""
        # Strategy 1: Primary model with format=json
        try:
            content_str = self._call_api(self.model, system_prompt, user_prompt, use_json_format=True, temperature=temperature)
            return extract_json_payload(content_str)
        except Exception:
            pass

        # Strategy 2: Primary model WITHOUT format=json (bypasses Ollama grammar 500 bugs)
        try:
            content_str = self._call_api(self.model, system_prompt, user_prompt, use_json_format=False, temperature=temperature)
            return extract_json_payload(content_str)
        except Exception:
            pass

        # Strategy 3: Fallback model (mistral:latest) with format=json
        if self.model != self.fallback_model:
            try:
                content_str = self._call_api(self.fallback_model, system_prompt, user_prompt, use_json_format=True, temperature=temperature)
                return extract_json_payload(content_str)
            except Exception:
                pass

            # Strategy 4: Fallback model WITHOUT format=json
            try:
                content_str = self._call_api(self.fallback_model, system_prompt, user_prompt, use_json_format=False, temperature=temperature)
                return extract_json_payload(content_str)
            except Exception as fb_err:
                raise RuntimeError(f"Ollama call failed across primary ({self.model}) and fallback ({self.fallback_model}): {fb_err}") from fb_err

        raise RuntimeError(f"Ollama call failed for {self.model}")

    def get_agent_proposal(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        canonical_names: Optional[List[str]] = None
    ) -> AgentTurnProposal:
        """Query model and parse into AgentTurnProposal Pydantic model with quality post-processing."""
        raw_json = self.chat_json(system_prompt, user_prompt, temperature=temperature)
        
        try:
            proposal = AgentTurnProposal.model_validate(raw_json)
        except Exception:
            action_data = raw_json.get("action", {}) if isinstance(raw_json.get("action"), dict) else {}
            if isinstance(raw_json.get("action"), str):
                action_data = {"action_type": "speak", "message": raw_json.get("action"), "rationale": raw_json.get("rationale", "Engaging in dialogue")}
            
            action_type = action_data.get("action_type", "speak")
            if action_type not in ["observe", "move", "gather", "trade", "create_institution", "spawn_agent", "record_artifact", "speak", "synthesize"]:
                action_type = "speak"

            action = AgentAction(
                action_type=action_type,
                target_location=action_data.get("target_location"),
                target_agent=action_data.get("target_agent"),
                resource_type=action_data.get("resource_type"),
                resource_amount=int(action_data.get("resource_amount", 0)),
                institution_name=action_data.get("institution_name"),
                institution_charter=action_data.get("institution_charter"),
                sub_agent_name=action_data.get("sub_agent_name"),
                sub_agent_motive=action_data.get("sub_agent_motive"),
                artifact_title=action_data.get("artifact_title"),
                artifact_content=action_data.get("artifact_content"),
                message=action_data.get("message"),
                claim=action_data.get("claim"),
                evidence=action_data.get("evidence"),
                challenge=action_data.get("challenge"),
                question=action_data.get("question"),
                rationale=str(action_data.get("rationale", "Engaging in Socratic debate"))
            )
            proposal = AgentTurnProposal(
                thoughts=str(raw_json.get("thoughts", "Reflecting on current dialogue.")),
                action=action
            )

        # Assemble speech from structured sub-fields if message is empty or generic
        action_dict = raw_json.get("action", {}) if isinstance(raw_json.get("action"), dict) else {}
        assembled = assemble_speech(action_dict)
        if assembled and (not proposal.action.message or is_generic_response(proposal.action.message)):
            proposal.action.message = assembled

        # Fix small model quirks (e.g. qwen2.5:3b putting speech in thoughts or writing literal "None")
        msg = proposal.action.message
        if not msg or str(msg).strip().lower() in ["none", "null", "..."]:
            if proposal.thoughts and len(proposal.thoughts.strip()) > 15 and not proposal.thoughts.startswith("Reflecting on"):
                proposal.action.message = proposal.thoughts.strip()
                proposal.thoughts = "Delivering response to panel."
            else:
                proposal.action.message = "We must confront the fundamental trade-offs in this scenario rather than settling for superficial agreement."

        # Apply text cleanup (stutters & name corrections)
        if proposal.action.message:
            proposal.action.message = clean_stutters(proposal.action.message)
            if canonical_names:
                proposal.action.message = fix_name_references(proposal.action.message, canonical_names)

        return proposal
