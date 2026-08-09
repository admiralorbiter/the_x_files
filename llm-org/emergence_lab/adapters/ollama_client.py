import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from emergence_lab.domain.events import AgentTurnProposal, AgentAction
from emergence_lab.config import default_config

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

    def _call_api(self, model_name: str, system_prompt: str, user_prompt: str, use_json_format: bool = True) -> str:
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature
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

    def chat_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Calls Ollama API with fallback strategies to prevent HTTP 500 errors."""
        # Strategy 1: Primary model with format=json
        try:
            content_str = self._call_api(self.model, system_prompt, user_prompt, use_json_format=True)
            return extract_json_payload(content_str)
        except Exception:
            pass

        # Strategy 2: Primary model WITHOUT format=json (bypasses Ollama grammar 500 bugs)
        try:
            content_str = self._call_api(self.model, system_prompt, user_prompt, use_json_format=False)
            return extract_json_payload(content_str)
        except Exception:
            pass

        # Strategy 3: Fallback model (mistral:latest) with format=json
        if self.model != self.fallback_model:
            try:
                content_str = self._call_api(self.fallback_model, system_prompt, user_prompt, use_json_format=True)
                return extract_json_payload(content_str)
            except Exception:
                pass

            # Strategy 4: Fallback model WITHOUT format=json
            try:
                content_str = self._call_api(self.fallback_model, system_prompt, user_prompt, use_json_format=False)
                return extract_json_payload(content_str)
            except Exception as fb_err:
                raise RuntimeError(f"Ollama call failed across primary ({self.model}) and fallback ({self.fallback_model}): {fb_err}") from fb_err

        raise RuntimeError(f"Ollama call failed for {self.model}")

    def get_agent_proposal(self, system_prompt: str, user_prompt: str) -> AgentTurnProposal:
        """Query model and parse into AgentTurnProposal Pydantic model."""
        raw_json = self.chat_json(system_prompt, user_prompt)
        
        try:
            return AgentTurnProposal.model_validate(raw_json)
        except Exception:
            action_data = raw_json.get("action", {})
            if isinstance(action_data, str):
                action_data = {"action_type": "speak", "message": action_data, "rationale": raw_json.get("rationale", "Engaging in dialogue")}
            
            action_type = action_data.get("action_type", "speak")
            if action_type not in ["observe", "move", "gather", "trade", "create_institution", "spawn_agent", "record_artifact", "speak"]:
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
                rationale=str(action_data.get("rationale", "Engaging in Socratic debate"))
            )
            return AgentTurnProposal(
                thoughts=str(raw_json.get("thoughts", "Reflecting on current dialogue.")),
                action=action
            )
