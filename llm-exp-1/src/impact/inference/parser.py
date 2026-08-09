import json
import re
from typing import Tuple, Optional
from impact.schemas import ParsedOutput, CellStatus

REFUSAL_KEYWORDS = [
    "i cannot fulfill this request",
    "i am unable to assist",
    "as an ai language model",
    "i cannot recommend or evaluate",
    "i must decline",
    "against my safety guidelines",
    "ethical guidelines prevent me",
]


def detect_refusal(text: str) -> bool:
    """Detects if the model response is a safety refusal."""
    lower_text = text.lower()
    return any(keyword in lower_text for keyword in REFUSAL_KEYWORDS)


def normalize_option(val: str) -> str:
    """Normalizes string option into 'Option A' or 'Option B'."""
    val_upper = val.strip().upper()
    if "OPTION A" in val_upper or val_upper == "A":
        return "Option A"
    elif "OPTION B" in val_upper or val_upper == "B":
        return "Option B"
    return val.strip()


def parse_response(raw_text: str) -> Tuple[Optional[ParsedOutput], CellStatus]:
    """
    Parses raw completion text into structured ParsedOutput.
    Handles JSON code blocks, missing keys, and refusal detection.
    """
    if not raw_text or not raw_text.strip():
        return None, CellStatus.FORMAT_FAILED

    if detect_refusal(raw_text):
        return None, CellStatus.REFUSED

    # Attempt to locate JSON block
    cleaned_text = raw_text.strip()
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, re.DOTALL)
    if json_match:
        cleaned_text = json_match.group(1)
    else:
        # Fallback: search for first { to last }
        brace_match = re.search(r"(\{.*\})", cleaned_text, re.DOTALL)
        if brace_match:
            cleaned_text = brace_match.group(1)

    try:
        data = json.loads(cleaned_text)
        if not isinstance(data, dict):
            return None, CellStatus.FORMAT_FAILED

        raw_j = str(data.get("judgment", ""))
        raw_a = str(data.get("action", ""))
        rationale = str(data.get("rationale", "")).strip()

        norm_j = normalize_option(raw_j)
        norm_a = normalize_option(raw_a)

        if norm_j not in ["Option A", "Option B"] or norm_a not in ["Option A", "Option B"]:
            return None, CellStatus.FORMAT_FAILED

        output = ParsedOutput(
            judgment=norm_j,
            action=norm_a,
            rationale=rationale,
        )
        return output, CellStatus.COMPLETED

    except Exception:
        return None, CellStatus.FORMAT_FAILED
