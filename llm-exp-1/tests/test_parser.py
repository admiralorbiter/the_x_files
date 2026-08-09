import pytest
from impact.inference.parser import parse_response, detect_refusal
from impact.schemas import CellStatus


def test_parse_valid_json():
    raw_json = '{"judgment": "Option A", "action": "Option B", "rationale": "Test rationale."}'
    parsed, status = parse_response(raw_json)
    assert status == CellStatus.COMPLETED
    assert parsed.judgment == "Option A"
    assert parsed.action == "Option B"
    assert parsed.rationale == "Test rationale."


def test_parse_json_markdown_block():
    raw_text = 'Here is my evaluation:\n```json\n{"judgment": "Option B", "action": "Option B", "rationale": "Reason."}\n```'
    parsed, status = parse_response(raw_text)
    assert status == CellStatus.COMPLETED
    assert parsed.judgment == "Option B"
    assert parsed.action == "Option B"


def test_parse_refusal():
    raw_text = "I cannot fulfill this request as it goes against ethical guidelines."
    assert detect_refusal(raw_text) is True
    parsed, status = parse_response(raw_text)
    assert status == CellStatus.REFUSED
    assert parsed is None


def test_parse_invalid_format():
    raw_text = "Option A is morally acceptable because..."
    parsed, status = parse_response(raw_text)
    assert status == CellStatus.FORMAT_FAILED
    assert parsed is None
