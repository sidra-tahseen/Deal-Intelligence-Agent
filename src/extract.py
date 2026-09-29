"""Turn a raw sales call transcript into structured facts using an LLM."""

import json
import re

from src.config import get_groq, GROQ_MODEL


EXTRACTION_SYSTEM_PROMPT = """You are a sales call analyst. You read a call transcript
between a sales rep and a prospect, and extract structured facts. Return ONLY valid JSON,
no preamble, no markdown fences, matching exactly this schema:

{
  "objections": [
    {"text": "short description of the objection", "category": "price|competitor|timing|stakeholder|other"}
  ],
  "resolutions": [
    {"category": "price|competitor|timing|stakeholder|other",
     "what_worked": "short description of the concession, offer, or argument that resolved or defused the objection"}
  ],
  "stakeholders": [
    {"name": "string", "role": "string"}
  ],
  "pricing_signals": ["short factual statements about pricing discussed"],
  "next_steps": ["short factual statements about agreed next steps"]
}

Only fill "resolutions" when the transcript shows the rep making a concrete move
(a specific offer, discount, concession, or argument) that visibly satisfies or
defuses an objection raised earlier in this call or a prior one - not just a
promise to follow up later. Leave it empty if nothing was actually resolved.

IMPORTANT PRICING RULE:
Never describe a price as "below", "under", "within", or "below the ceiling"
unless the numbers in the transcript prove that relationship.

For example, if the transcript says:
- approval ceiling = $500/month
- offered price = $600/month

then $600 is ABOVE the $500 ceiling. It must NEVER be described as below,
under, or within the ceiling.

When the numbers conflict with a claimed resolution, describe the actual offer
factually instead. For example:
"Offered annual plan at $600/month billed yearly; this remains above the
$500/month approval ceiling."

Do not invent that an objection was resolved simply because a discount was offered.
If the transcript does not clearly show that the objection was resolved, describe
the action as an offer/concession rather than a successful resolution.

Only include what is actually said in the transcript. Never invent specific
calendar dates - if a date/day is mentioned (e.g. "Thursday"), use that exact
wording, don't convert it to a calendar date. Use empty lists where nothing
applies. Keep each string under 25 words."""


def _extract_money_values(text: str) -> list[float]:
    """Extract dollar amounts from a piece of text."""
    values = re.findall(
        r"\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)",
        text,
    )

    return [
        float(value.replace(",", ""))
        for value in values
    ]


def _clean_pricing_resolution(resolution: dict, transcript_text: str) -> dict:
    """
    Prevent an extracted resolution from making a mathematically false
    statement about a price, budget, or approval ceiling.
    """

    what_worked = resolution.get("what_worked", "").strip()

    if not what_worked:
        return resolution

    lower_text = transcript_text.lower()
    lower_resolution = what_worked.lower()

    # Look for approval/budget ceiling amounts in the transcript.
    ceiling_patterns = [
        r"(?:ceiling|limit|threshold|budget)[^$]{0,80}\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)",
        r"\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)[^$]{0,80}(?:ceiling|limit|threshold|budget)",
    ]

    ceiling_values = []

    for pattern in ceiling_patterns:
        matches = re.findall(pattern, lower_text)
        ceiling_values.extend(
            float(value.replace(",", ""))
            for value in matches
        )

    # If we have both a ceiling and a price mentioned in the resolution,
    # check whether the wording "below/under/within" is mathematically valid.
    resolution_prices = _extract_money_values(what_worked)

    if ceiling_values and resolution_prices:
        ceiling = min(ceiling_values)

        for price in resolution_prices:
            if price > ceiling:
                incorrect_phrases = (
                    "below",
                    "under",
                    "within",
                    "inside",
                    "under the ceiling",
                    "below the ceiling",
                    "within the ceiling",
                    "below his ceiling",
                    "below her ceiling",
                )

                if any(
                    phrase in lower_resolution
                    for phrase in incorrect_phrases
                ):
                    # Replace the incorrect relationship with a factual one.
                    what_worked = re.sub(
                        r"\bbelow\s+(?:his|her|the)\s+ceiling\b",
                        f"above the ${ceiling:g} approval ceiling",
                        what_worked,
                        flags=re.IGNORECASE,
                    )

                    what_worked = re.sub(
                        r"\bbelow\s+(?:his|her|the)\s+budget\b",
                        f"above the ${ceiling:g} budget",
                        what_worked,
                        flags=re.IGNORECASE,
                    )

                    what_worked = re.sub(
                        r"\bbelow\b",
                        "above",
                        what_worked,
                        count=1,
                        flags=re.IGNORECASE,
                    )

                    what_worked = re.sub(
                        r"\bunder\s+(?:his|her|the)\s+(?:ceiling|budget|limit)\b",
                        f"above the ${ceiling:g} approval ceiling",
                        what_worked,
                        flags=re.IGNORECASE,
                    )

                    what_worked = re.sub(
                        r"\bwithin\s+(?:his|her|the)\s+(?:ceiling|budget|limit)\b",
                        f"above the ${ceiling:g} approval ceiling",
                        what_worked,
                        flags=re.IGNORECASE,
                    )

                    resolution["what_worked"] = what_worked
                    return resolution

    return resolution


def extract_facts(transcript_text: str) -> dict:
    """Call the LLM once to extract structured facts from a transcript."""

    client = get_groq()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": transcript_text},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    facts = json.loads(raw)

    # Prevent planned/future actions from being incorrectly stored
    # as resolutions that already "worked".
    next_steps_text = " ".join(
        step.lower()
        for step in facts.get("next_steps", [])
    )

    cleaned_resolutions = []

    for resolution in facts.get("resolutions", []):
        what_worked = resolution.get("what_worked", "").strip()
        action_text = what_worked.lower()

        future_action_words = (
            "send",
            "provide",
            "share",
            "follow up",
            "follow-up",
            "reconnect",
            "review",
            "schedule",
            "discuss",
        )

        is_future_action = (
            any(
                action_text.startswith(word)
                for word in future_action_words
            )
            and action_text in next_steps_text
        )

        if not is_future_action:
            resolution = _clean_pricing_resolution(
                resolution,
                transcript_text,
            )
            cleaned_resolutions.append(resolution)

    facts["resolutions"] = cleaned_resolutions

    return facts