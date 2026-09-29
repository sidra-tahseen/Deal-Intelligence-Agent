"""Hindsight retain/recall wrapper.

Two kinds of memory:
- deal bank (deal-<deal_id>): everything about ONE deal
- playbook bank (playbook): deal-agnostic objection/tactic patterns, shared
  across every deal, so a brand-new deal benefits from what happened elsewhere
"""

import asyncio
import threading
import time

from src.config import get_hindsight, deal_bank_id, PLAYBOOK_BANK_ID


_ensured_banks = set()

MAX_QUERY_CHARS = 1200


def _ensure_bank(bank_id: str, name: str, background: str = ""):
    """Create the bank if we haven't already this run."""

    if bank_id in _ensured_banks:
        return

    client = get_hindsight()

    try:
        client.create_bank(
            bank_id=bank_id,
            name=name,
            background=background,
        )
    except Exception:
        # Bank likely already exists from a previous run.
        pass

    _ensured_banks.add(bank_id)


def _meta(**kwargs) -> dict:
    """Hindsight metadata values must be strings."""
    return {k: str(v) for k, v in kwargs.items()}


def _cap_query(query: str) -> str:
    if len(query) <= MAX_QUERY_CHARS:
        return query

    truncated = query[:MAX_QUERY_CHARS]
    return truncated.rsplit(" ", 1)[0]


def _run_async_safely(async_operation):
    """Run a Hindsight async operation in its own thread/event loop."""

    result = []
    error = []

    def runner():
        async def operation():
            client = get_hindsight()

            try:
                return await async_operation(client)
            finally:
                await client.aclose()

        try:
            result.append(asyncio.run(operation()))
        except Exception as exc:
            error.append(exc)

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()

    if error:
        raise error[0]

    return result[0] if result else None


def _retain_batch(bank_id: str, items: list[dict]):
    """Store multiple memories using Hindsight's async API."""

    if not items:
        return

    async def retain(client):
        return await client.aretain_batch(
            bank_id=bank_id,
            items=items,
        )

    return _run_async_safely(retain)


def retain_call_facts(
    deal_id: str,
    deal_name: str,
    call_number: int,
    facts: dict,
):
    """Store extracted facts from one call into the deal's private bank,
    and generalized objection facts into the shared playbook bank.
    """

    bank_id = deal_bank_id(deal_id)

    _ensure_bank(
        bank_id,
        name=f"Deal: {deal_name}",
        background=f"Sales deal memory for {deal_name} ({deal_id})",
    )

    _ensure_bank(
        PLAYBOOK_BANK_ID,
        name="Sales Playbook",
        background=(
            "Cross-deal objections and outcomes, deal-agnostic, "
            "used to brief reps on tactics that worked before."
        ),
    )

    context = f"Call #{call_number} with {deal_name}"

    # ---------------------------------------------------------
    # Deal-specific memories
    # ---------------------------------------------------------

    deal_items = []

    for obj in facts.get("objections", []):
        deal_items.append(
            {
                "content": (
                    f"Objection raised: {obj['text']} "
                    f"(category: {obj['category']})"
                ),
                "context": context,
                "metadata": _meta(
                    call_number=call_number,
                    type="objection",
                    category=obj["category"],
                ),
            }
        )

    for res in facts.get("resolutions", []):
        deal_items.append(
            {
                "content": (
                    f"Resolved a {res['category']} objection: "
                    f"{res['what_worked']}"
                ),
                "context": context,
                "metadata": _meta(
                    call_number=call_number,
                    type="resolution",
                    category=res["category"],
                ),
            }
        )

    for sh in facts.get("stakeholders", []):
        deal_items.append(
            {
                "content": (
                    f"Stakeholder: {sh['name']} "
                    f"({sh['role']})"
                ),
                "context": context,
                "metadata": _meta(
                    call_number=call_number,
                    type="stakeholder",
                ),
            }
        )

    for sig in facts.get("pricing_signals", []):
        deal_items.append(
            {
                "content": f"Pricing signal: {sig}",
                "context": context,
                "metadata": _meta(
                    call_number=call_number,
                    type="pricing",
                ),
            }
        )

    for step in facts.get("next_steps", []):
        deal_items.append(
            {
                "content": f"Next step agreed: {step}",
                "context": context,
                "metadata": _meta(
                    call_number=call_number,
                    type="next_step",
                ),
            }
        )

    _retain_batch(bank_id, deal_items)

    # ---------------------------------------------------------
    # Cross-deal playbook memories
    # ---------------------------------------------------------

    playbook_items = []

    for obj in facts.get("objections", []):
        playbook_items.append(
            {
                "content": (
                    f"In a {obj['category']} objection situation, "
                    f"a prospect said: {obj['text']}"
                ),
                "context": f"Observed in deal {deal_name}",
                "metadata": _meta(
                    category=obj["category"],
                    source_deal=deal_id,
                    kind="objection",
                ),
            }
        )

    for res in facts.get("resolutions", []):
        playbook_items.append(
            {
                "content": (
                    f"TACTIC that worked on a "
                    f"{res['category']} objection "
                    f"(from deal {deal_name}): "
                    f"{res['what_worked']}"
                ),
                "context": f"Resolved in deal {deal_name}",
                "metadata": _meta(
                    category=res["category"],
                    source_deal=deal_id,
                    kind="tactic",
                ),
            }
        )

    _retain_batch(PLAYBOOK_BANK_ID, playbook_items)


# =============================================================
# CURRENT DEAL MEMORY
# =============================================================

def _recall_deal_query(
    client,
    bank_id: str,
    query: str,
):
    """Run one focused recall against the current deal bank."""

    try:
        result = client.recall(
            bank_id=bank_id,
            query=_cap_query(query),
            max_tokens=4096,
        )

        return result.results

    except Exception:
        return []


def _deduplicate_texts(memories: list[str]) -> list[str]:
    """Remove duplicate memories while preserving retrieval order."""

    unique = []
    seen = set()

    for memory in memories:
        cleaned = " ".join(memory.split()).strip()

        if not cleaned:
            continue

        normalized = cleaned.lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append(cleaned)

    return unique


def recall_deal_context(
    deal_id: str,
    query: str = (
        "complete deal history including objections, resolutions, "
        "stakeholders, decision makers, pricing, budgets, approval limits, "
        "timelines, next steps, commitments, risks and outcomes"
    ),
):
    """Recall a complete and stable view of the current deal.

    Multiple focused queries are used because a single Hindsight recall
    can return only a subset of the memories. The results are combined
    and deduplicated so the pre-call brief sees the full deal context.
    """

    client = get_hindsight()
    bank_id = deal_bank_id(deal_id)

    focused_queries = [
        (
            "complete deal history, all calls, latest updates, "
            "current status, commitments, outcomes, next steps"
        ),
        (
            "all objections, concerns, risks, unresolved issues, "
            "objection categories and how they were handled"
        ),
        (
            "all pricing information, prices offered, budgets, "
            "approval limits, discounts, annual plans and pricing signals"
        ),
        (
            "all stakeholders, decision makers, CFO, approvers, "
            "roles and people involved in this deal"
        ),
        (
            "all timelines, deadlines, implementation dates, "
            "contract expiry, follow-up dates and delivery commitments"
        ),
        (
            "all resolutions, agreements, comparison documents, "
            "ROI discussions, competitor comparisons and outcomes"
        ),
        (
            query
        ),
    ]

    all_memories = []

    # ---------------------------------------------------------
    # Try the complete set of focused queries.
    # ---------------------------------------------------------

    for focused_query in focused_queries:
        results = _recall_deal_query(
            client,
            bank_id,
            focused_query,
        )

        for memory in results:
            all_memories.append(memory.text)

    # ---------------------------------------------------------
    # If Hindsight temporarily returns nothing, retry once.
    # This handles eventual consistency after a call is retained.
    # ---------------------------------------------------------

    if not all_memories:
        time.sleep(0.8)

        for focused_query in focused_queries:
            results = _recall_deal_query(
                client,
                bank_id,
                focused_query,
            )

            for memory in results:
                all_memories.append(memory.text)

    # ---------------------------------------------------------
    # Final deduplication.
    # ---------------------------------------------------------

    return _deduplicate_texts(all_memories)


# =============================================================
# CROSS-DEAL PLAYBOOK
# =============================================================

def _normalize_memory(text: str) -> str:
    """Normalize text for duplicate detection."""

    normalized = text.lower()
    normalized = " ".join(normalized.split())

    return normalized


def _is_current_deal(
    text: str,
    current_deal_id: str | None,
    current_deal_name: str | None,
) -> bool:
    """Return True when a memory belongs to the current deal."""

    lower_text = text.lower()

    if (
        current_deal_name
        and current_deal_name.lower() in lower_text
    ):
        return True

    if (
        current_deal_id
        and f"deal-{current_deal_id.lower()}" in lower_text
    ):
        return True

    return False


def _is_tactic(text: str) -> bool:
    """Keep memories that describe an actual action/tactic."""

    lower_text = text.lower()

    action_indicators = (
        "tactic that worked",
        "offered ",
        "provided ",
        "promised ",
        "agreed to ",
        "included ",
        "presented ",
        "proposed ",
        "committed to ",
        "comparison",
        "annual plan",
        "discount",
        "showing ",
        "highlighting ",
        "demonstrated ",
        "shared ",
    )

    return any(
        indicator in lower_text
        for indicator in action_indicators
    )


def _tactic_theme(text: str) -> str:
    """Identify a broad tactic theme for diversity."""

    lower_text = text.lower()

    if any(
        word in lower_text
        for word in (
            "comparison",
            "compare",
            "flowstock",
            "competitor",
            "side-by-side",
        )
    ):
        return "comparison"

    if any(
        word in lower_text
        for word in (
            "price",
            "pricing",
            "annual plan",
            "monthly",
            "discount",
            "budget",
            "cost",
        )
    ):
        return "pricing"

    if any(
        word in lower_text
        for word in (
            "roi",
            "return on investment",
            "savings",
            "hours saved",
            "value",
        )
    ):
        return "roi"

    if any(
        word in lower_text
        for word in (
            "timeline",
            "6-week",
            "six-week",
            "implementation",
            "coverage gap",
            "deadline",
        )
    ):
        return "timeline"

    if any(
        word in lower_text
        for word in (
            "cfo",
            "approval",
            "decision-maker",
            "decision maker",
            "stakeholder",
        )
    ):
        return "approval"

    return "other"


def _select_diverse_tactics(
    tactics: list[str],
    limit: int = 3,
) -> list[str]:
    """Select tactics while avoiding repeated themes."""

    unique = []
    seen = set()

    for tactic in tactics:
        normalized = _normalize_memory(tactic)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        unique.append(tactic)

    selected = []
    used_themes = set()

    # First pass: one tactic per different theme.
    for tactic in unique:
        theme = _tactic_theme(tactic)

        if theme not in used_themes:
            selected.append(tactic)
            used_themes.add(theme)

        if len(selected) >= limit:
            return selected

    # Second pass: fill remaining slots if needed.
    for tactic in unique:
        if tactic not in selected:
            selected.append(tactic)

        if len(selected) >= limit:
            break

    return selected


def _recall_playbook_query(
    client,
    query: str,
):
    """Run one focused playbook recall."""

    try:
        result = client.recall(
            bank_id=PLAYBOOK_BANK_ID,
            query=_cap_query(query),
            max_tokens=4096,
        )

        return result.results

    except Exception:
        return []


def recall_similar_tactics(
    objection_summary: str,
    current_deal_id: str | None = None,
    current_deal_name: str | None = None,
):
    """Recall useful resolution tactics from OTHER deals.

    Multiple focused queries are used so one repeated tactic category
    does not dominate the entire result set.
    """

    client = get_hindsight()

    focused_queries = [
        (
            "successful pricing tactics, pricing objections, "
            "budget objections, discounts, annual plans, "
            "price justification and approval limits; "
            + objection_summary
        ),
        (
            "successful competitor comparison tactics, "
            "side-by-side comparisons, Flowstock comparisons, "
            "value justification and ROI tactics; "
            + objection_summary
        ),
        (
            "successful implementation timeline tactics, "
            "deadline objections, coverage gaps and "
            "implementation commitments; "
            + objection_summary
        ),
    ]

    all_results = []

    for query in focused_queries:
        all_results.extend(
            _recall_playbook_query(
                client,
                query,
            )
        )

    tactics = []

    for memory in all_results:
        text = memory.text

        # Exclude the current deal.
        if _is_current_deal(
            text,
            current_deal_id,
            current_deal_name,
        ):
            continue

        # Only keep actual tactics/actions.
        if not _is_tactic(text):
            continue

        tactics.append(text)

    return _select_diverse_tactics(
        tactics,
        limit=3,
    )