"""Top-level orchestration: ingest a call, or prep a brief for the next one."""
from src.extract import extract_facts
from src.memory import retain_call_facts
from src.brief import generate_pre_call_brief


def ingest_call(deal_id: str, deal_name: str, call_number: int, transcript_text: str) -> dict:
    """Extract facts from a transcript and store them in memory. Returns the facts."""
    facts = extract_facts(transcript_text)
    retain_call_facts(deal_id, deal_name, call_number, facts)
    return facts


def prep_next_call(deal_id: str, deal_name: str) -> str:
    """Generate the pre-call brief for a rep about to call this deal."""
    return generate_pre_call_brief(deal_id, deal_name)
