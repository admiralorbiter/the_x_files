import json
import re
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Type, Tuple
from pydantic import BaseModel
from emergence_lab.domain.events import AgentTurnProposal, AgentAction
from emergence_lab.domain.telemetry import InferenceResult
from emergence_lab.config import default_config
from emergence_lab.engine.text_cleanup import clean_stutters, fix_name_references

def extract_json_payload(text: str) -> Dict[str, Any]:
    """Extracts JSON object from response text, handling markdown codeblocks or raw text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

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
        temperature: float = default_config.temperature
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature

    def chat_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None
    ) -> Tuple[Dict[str, Any], InferenceResult]:
        """Calls Ollama API with explicit Pydantic JSON Schema enforcement and returns (parsed_json, telemetry)."""
        temp = temperature if temperature is not None else self.temperature
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temp
            }
        }

        if response_schema:
            payload["format"] = response_schema.model_json_schema()
        else:
            payload["format"] = "json"

        url = f"{self.base_url}/api/chat"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        start_time = time.time()
        attempts = 1
        
        try:
            with urllib.request.urlopen(req, timeout=default_config.request_timeout) as response:
                duration_ms = (time.time() - start_time) * 1000.0
                res_data = json.loads(response.read().decode("utf-8"))
                
                content_str = res_data.get("message", {}).get("content", "{}")
                parsed_json = extract_json_payload(content_str)

                telemetry = InferenceResult(
                    requested_model=self.model,
                    actual_model=res_data.get("model", self.model),
                    attempts=attempts,
                    prompt_tokens=res_data.get("prompt_eval_count"),
                    eval_tokens=res_data.get("eval_count"),
                    duration_ms=duration_ms,
                    validation_status="valid",
                    fallback_used=False
                )
                return parsed_json, telemetry

        except Exception as e:
            # Re-try once without explicit JSON format if grammar engine fails
            duration_ms = (time.time() - start_time) * 1000.0
            attempts = 2
            try:
                payload["format"] = "json"
                req_retry = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req_retry, timeout=default_config.request_timeout) as resp_retry:
                    res_data = json.loads(resp_retry.read().decode("utf-8"))
                    content_str = res_data.get("message", {}).get("content", "{}")
                    parsed_json = extract_json_payload(content_str)
                    
                    telemetry = InferenceResult(
                        requested_model=self.model,
                        actual_model=res_data.get("model", self.model),
                        attempts=attempts,
                        prompt_tokens=res_data.get("prompt_eval_count"),
                        eval_tokens=res_data.get("eval_count"),
                        duration_ms=(time.time() - start_time) * 1000.0,
                        validation_status="repaired",
                        repairs_applied=["format_schema_fallback"],
                        fallback_used=False
                    )
                    return parsed_json, telemetry
            except Exception as retry_err:
                telemetry = InferenceResult(
                    requested_model=self.model,
                    actual_model=self.model,
                    attempts=attempts,
                    duration_ms=(time.time() - start_time) * 1000.0,
                    validation_status="failed",
                    error_message=str(retry_err)
                )
                raise RuntimeError(f"Ollama call failed for model {self.model}: {retry_err}") from retry_err

    def chat_json(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Backward-compatible helper that returns parsed JSON payload."""
        parsed, _ = self.chat_structured(system_prompt, user_prompt, temperature=temperature)
        return parsed

    def get_agent_proposal(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None, canonical_names: Optional[List[str]] = None) -> AgentTurnProposal:
        """Backward-compatible helper that parses raw JSON into AgentTurnProposal."""
        raw_json = self.chat_json(system_prompt, user_prompt, temperature=temperature)
        try:
            return AgentTurnProposal.model_validate(raw_json)
        except Exception:
            action_data = raw_json.get("action", {}) if isinstance(raw_json.get("action"), dict) else {}
            action = AgentAction(
                action_type=action_data.get("action_type", "speak"),
                target_agent=action_data.get("target_agent"),
                resource_type=action_data.get("resource_type"),
                resource_amount=int(action_data.get("resource_amount", 0)),
                message=action_data.get("message"),
                rationale=str(action_data.get("rationale", "Reasoning for action"))
            )
            return AgentTurnProposal(
                thoughts=str(raw_json.get("thoughts", "Reflecting.")),
                action=action
            )
