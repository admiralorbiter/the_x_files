import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from emergence_lab.domain.events import AgentTurnProposal, AgentAction
from emergence_lab.config import default_config

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

    def chat_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Calls local Ollama API requesting JSON format response."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature
            }
        }

        url = f"{self.base_url}/api/chat"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=default_config.request_timeout) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content_str = res_data.get("message", {}).get("content", "{}")
                return json.loads(content_str)
        except (urllib.error.URLError, json.JSONDecodeError) as err:
            # Attempt fallback model if primary fails
            if self.model != self.fallback_model:
                payload["model"] = self.fallback_model
                try:
                    req_fb = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req_fb, timeout=default_config.request_timeout) as fb_res:
                        res_data = json.loads(fb_res.read().decode("utf-8"))
                        content_str = res_data.get("message", {}).get("content", "{}")
                        return json.loads(content_str)
                except Exception as fb_err:
                    raise RuntimeError(f"Ollama call failed for primary ({err}) and fallback ({fb_err})") from fb_err
            raise RuntimeError(f"Ollama API call failed: {err}") from err

    def get_agent_proposal(self, system_prompt: str, user_prompt: str) -> AgentTurnProposal:
        """Query model and parse into AgentTurnProposal Pydantic model."""
        raw_json = self.chat_json(system_prompt, user_prompt)
        
        # Robust parsing of response structure
        try:
            return AgentTurnProposal.model_validate(raw_json)
        except Exception:
            # Fallback construct if model format returned nested or partial fields
            action_data = raw_json.get("action", {})
            if isinstance(action_data, str):
                action_data = {"action_type": "observe", "rationale": raw_json.get("rationale", "Observing surroundings")}
            
            action_type = action_data.get("action_type", "observe")
            if action_type not in ["observe", "move", "gather", "trade", "create_institution", "spawn_agent", "record_artifact", "speak"]:
                action_type = "observe"

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
                rationale=str(action_data.get("rationale", "Routine observation"))
            )
            return AgentTurnProposal(
                thoughts=str(raw_json.get("thoughts", "Reflecting on current world state.")),
                action=action
            )
