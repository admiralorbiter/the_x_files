from unittest.mock import MagicMock
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.domain.events import AgentTurnProposal

def test_ollama_client_fallback_parser():
    client = OllamaClient()
    client.chat_json = MagicMock(return_value={
        "thoughts": "I need to secure parchment.",
        "action": {
            "action_type": "gather",
            "resource_type": "Parchment",
            "resource_amount": 2,
            "rationale": "For writing books"
        }
    })
    
    proposal = client.get_agent_proposal("sys", "usr")
    assert isinstance(proposal, AgentTurnProposal)
    assert proposal.action.action_type == "gather"
    assert proposal.action.resource_type == "Parchment"

