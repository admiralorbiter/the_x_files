"""Deterministic Turn Verifier and Targeted Micro-Repair Engine."""

from typing import List, Tuple, Dict, Any, Optional
from emergence_lab.domain.dialogue_schemas import DialogueTurn
from emergence_lab.engine.text_cleanup import GENERIC_RESPONSE_PATTERNS
import re

class VerificationResult:
    def __init__(self, is_valid: bool, issues: List[str], repairs: List[str]):
        self.is_valid = is_valid
        self.issues = issues
        self.repairs = repairs

class DeterministicVerifier:
    def __init__(self, valid_target_ids: List[str]):
        self.valid_target_ids = [v.lower().strip() for v in valid_target_ids]

    def verify(self, turn: DialogueTurn) -> VerificationResult:
        issues = []
        repairs = []

        # 1. Target ID Validation
        raw_target = (turn.target_id or "").strip().lower()
        if raw_target not in self.valid_target_ids:
            # Try fuzzy match (e.g. "target: p2" -> "p2")
            matched = False
            for v in self.valid_target_ids:
                if v in raw_target:
                    turn.target_id = v
                    repairs.append(f"coerced_target_id_{raw_target}_to_{v}")
                    matched = True
                    break
            if not matched:
                issues.append(f"invalid_target_id:{turn.target_id}")

        # 2. Question Check
        if not turn.question or "?" not in turn.question:
            issues.append("missing_question_mark")

        # 3. Placeholder Prose Check
        combined = f"{turn.claim} {turn.evidence} {turn.challenge} {turn.question}".lower()
        for pattern in GENERIC_RESPONSE_PATTERNS:
            if re.search(pattern, combined):
                issues.append(f"generic_placeholder_prose:{pattern}")

        is_valid = len(issues) == 0
        return VerificationResult(is_valid=is_valid, issues=issues, repairs=repairs)

def run_targeted_target_repair(
    ollama_client: Any,
    invalid_target: str,
    valid_targets: List[str]
) -> Tuple[str, bool]:
    """Runs a 10-token micro-repair asking Ollama ONLY to fix an invalid target_id."""
    sys_prompt = "You are a precise data validator."
    usr_prompt = f"The target_id '{invalid_target}' is invalid. Choose EXACTLY ONE valid ID from this list: [{', '.join(valid_targets)}]. Output JSON: {{\"corrected_target_id\": \"p1\"}}"

    try:
        res = ollama_client.chat_json(sys_prompt, usr_prompt, temperature=0.1)
        corrected = str(res.get("corrected_target_id", "")).strip().lower()
        for v in valid_targets:
            if v.lower() in corrected:
                return v, True
    except Exception:
        pass

    # Deterministic fallback to first valid target if repair API call fails
    return valid_targets[0] if valid_targets else "p1", False
