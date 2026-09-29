"""Tiny local registry of known deals, for the UI dropdown and call counter.

This is deliberately NOT stored in Hindsight - it's app-level bookkeeping
(which deals exist, how many calls each has had), separate from the actual
call memory that Hindsight retains and recalls.
"""
import json
from pathlib import Path

_DEALS_PATH = Path(__file__).resolve().parent.parent / "data" / "deals.json"


def load_deals() -> dict:
    """Returns {deal_id: {"name": str, "calls": int}}"""
    if not _DEALS_PATH.exists():
        return {}
    return json.loads(_DEALS_PATH.read_text())


def _save_deals(deals: dict):
    _DEALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DEALS_PATH.write_text(json.dumps(deals, indent=2))


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def add_deal(deal_name: str) -> str:
    """Creates a deal if it doesn't already exist. Returns its deal_id."""
    deal_id = slugify(deal_name)
    deals = load_deals()
    if deal_id not in deals:
        deals[deal_id] = {"name": deal_name, "calls": 0}
        _save_deals(deals)
    return deal_id


def get_call_count(deal_id: str) -> int:
    return load_deals().get(deal_id, {}).get("calls", 0)


def increment_call(deal_id: str) -> int:
    """Bumps and returns the new call number for this deal."""
    deals = load_deals()
    deals[deal_id]["calls"] = deals[deal_id].get("calls", 0) + 1
    _save_deals(deals)
    return deals[deal_id]["calls"]