import time
import logging
import re
from typing import Dict, Any, Tuple, Optional
import httpx
from impact.schemas import GenerationConfig

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    HTTP client for interacting with local Ollama instance.
    Includes model SHA digest fetching, stateless generation, and transport retries.
    """

    def __init__(self, base_url: str = "http://localhost:11434", timeout_seconds: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self._digest_cache: Dict[str, str] = {}

    def get_model_digest(self, model_name: str) -> str:
        """Fetches model SHA-256 digest via Ollama's /api/show endpoint."""
        if model_name in self._digest_cache:
            return self._digest_cache[model_name]

        url = f"{self.base_url}/api/show"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json={"name": model_name})
                resp.raise_for_status()
                data = resp.json()
                details = data.get("details", {})
                parent_model = details.get("parent_model", "")
                
                # Check for sha256 blob in modelfile
                modelfile = data.get("modelfile", "")
                sha_match = re.search(r"sha256-([a-f0-9]{64})", modelfile)
                if sha_match:
                    digest = f"sha256:{sha_match.group(1)[:16]}"
                elif parent_model:
                    digest = f"parent:{parent_model}"
                else:
                    digest = f"tag:{model_name}"

                self._digest_cache[model_name] = digest
                return digest
        except Exception as e:
            logger.warning(f"Could not fetch digest for model {model_name}: {e}")
            return f"unknown_digest:{model_name}"

    def generate(
        self,
        prompt: str,
        config: GenerationConfig,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ) -> Tuple[str, Dict[str, Any], float]:
        """
        Executes a stateless generation request to Ollama with transport retry logic.
        Returns: (raw_response_text, metadata_dict, latency_ms)
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
            },
        }

        if config.seed is not None:
            payload["options"]["seed"] = config.seed

        if system_prompt:
            payload["system"] = system_prompt

        last_exception = None
        for attempt in range(1, max_retries + 1):
            start_time = time.perf_counter()
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    raw_text = data.get("response", "")
                    meta = {
                        "prompt_eval_count": data.get("prompt_eval_count"),
                        "eval_count": data.get("eval_count"),
                        "done_reason": data.get("done_reason"),
                    }
                    return raw_text, meta, latency_ms
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exception = e
                logger.warning(f"Ollama transport error (attempt {attempt}/{max_retries}) for model {config.model_name}: {e}")
                time.sleep(2.0 ** attempt)

        raise RuntimeError(f"Ollama generation failed after {max_retries} attempts: {last_exception}")
