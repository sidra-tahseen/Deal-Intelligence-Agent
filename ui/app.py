"""Modern Streamlit UI for the Deal Intelligence Agent.

Run from the project root with:

    streamlit run ui/app.py
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make src/ importable
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.agent import ingest_call, prep_next_call
from src.memory import recall_deal_context, recall_similar_tactics
from src.deals_store import (
    load_deals,
    add_deal,
    get_call_count,
    increment_call,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Deal Intelligence Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

st.html(
    """
    <style>

    /* ---------- Global ---------- */

    .stApp {
        background: #f6f8fb;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* ---------- Sidebar ---------- */

    section[data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
    }

    section[data-testid="stSidebar"] * {
        color: #f9fafb;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background: #1f2937;
        border: 1px solid #374151;
        color: #f9fafb;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #60a5fa;
        color: #ffffff;
    }

    /* ---------- Hero ---------- */

    .hero {
        background: linear-gradient(135deg, #111827 0%, #1e3a5f 100%);
        border-radius: 20px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        margin: 8px 0 0 0;
        color: #dbeafe;
        font-size: 1rem;
    }

    .online-pill {
        display: inline-block;
        margin-top: 18px;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(134, 239, 172, 0.35);
        color: #bbf7d0;
        font-size: 0.82rem;
        font-weight: 700;
    }

    /* ---------- Cards ---------- */

    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px 20px;
        min-height: 105px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }

    .metric-label {
        color: #6b7280;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-value {
        color: #111827;
        font-size: 1.55rem;
        font-weight: 800;
        margin-top: 7px;
    }

    .metric-note {
        color: #6b7280;
        font-size: 0.78rem;
        margin-top: 3px;
    }

    .section-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.035);
    }

    .section-title {
        font-size: 1.05rem;
        font-weight: 750;
        color: #111827;
        margin-bottom: 4px;
    }

    .section-subtitle {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 14px;
    }

    /* ---------- Brief cards ---------- */

    .brief-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 22px 16px 22px;
        margin: 0 0 16px 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 5px 18px rgba(15, 23, 42, 0.045);
    }

    .brief-status {
        border-left: 5px solid #3b82f6;
    }

    .brief-watch {
        border-left: 5px solid #f59e0b;
    }

    .brief-tactics {
        border-left: 5px solid #8b5cf6;
    }

    .brief-card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 15px;
    }

    .brief-icon {
        font-size: 1.45rem;
        line-height: 1;
    }

    .brief-card-label {
        color: #111827;
        font-size: 0.92rem;
        font-weight: 800;
        letter-spacing: 0.06em;
    }

    .brief-card-description {
        color: #6b7280;
        font-size: 0.79rem;
        margin-top: 3px;
    }

    .brief-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        color: #374151;
        font-size: 0.91rem;
        line-height: 1.55;
        padding: 9px 0;
        border-top: 1px solid #f1f5f9;
    }

    .brief-marker {
        flex: 0 0 20px;
        font-weight: 800;
        color: #2563eb;
    }

    .brief-watch .brief-marker {
        color: #d97706;
    }

    .brief-tactics .brief-marker {
        color: #7c3aed;
    }

    /* ---------- Intelligence cards ---------- */

    .action-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 15px 17px;
        margin-bottom: 10px;
    }

    .action-number {
        color: #2563eb;
        font-weight: 850;
        font-size: 1.05rem;
    }

    .action-title {
        color: #111827;
        font-weight: 750;
    }

    .action-description {
        color: #64748b;
        font-size: 0.84rem;
        margin-top: 4px;
    }

    .stakeholder-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
    }

    .stakeholder-name {
        font-weight: 800;
        color: #111827;
    }

    .stakeholder-role {
        color: #2563eb;
        font-size: 0.82rem;
        font-weight: 650;
    }

    .stakeholder-context {
        color: #64748b;
        font-size: 0.84rem;
        margin-top: 5px;
    }

    .objection-card {
        background: #fff;
        border-left: 5px solid #f59e0b;
        border-top: 1px solid #e5e7eb;
        border-right: 1px solid #e5e7eb;
        border-bottom: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 15px 17px;
        margin-bottom: 10px;
    }

    .commitment-card {
        background: #f8fafc;
        border-left: 5px solid #22c55e;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 9px;
    }

    .contradiction-card {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 13px;
        padding: 15px;
        margin-bottom: 10px;
    }

    .evidence-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 13px 15px;
        margin-bottom: 8px;
    }

    .memory-banner {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 14px;
        padding: 15px 18px;
        margin-bottom: 18px;
    }

    .memory-banner-title {
        color: #166534;
        font-weight: 800;
        margin-bottom: 3px;
    }

    .memory-banner-text {
        color: #166534;
        font-size: 0.86rem;
    }

    .timeline-item {
        border-left: 3px solid #60a5fa;
        padding: 4px 0 14px 16px;
        margin-left: 5px;
    }

    .timeline-number {
        font-weight: 800;
        color: #1d4ed8;
    }

    .timeline-text {
        color: #4b5563;
        font-size: 0.88rem;
    }

    .empty-state {
        background: white;
        border: 1px dashed #cbd5e1;
        border-radius: 16px;
        padding: 35px;
        text-align: center;
        color: #64748b;
    }

    .info-chip {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 8px;
        background: #eff6ff;
        color: #1d4ed8;
        font-size: 0.78rem;
        font-weight: 650;
        margin: 3px 4px 3px 0;
        border: 1px solid #dbeafe;
    }

    /* ---------- Tabs ---------- */

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding-left: 15px;
        padding-right: 15px;
    }

    div.stButton > button[kind="primary"] {
        border-radius: 10px;
        font-weight: 700;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def clean_brief(text: str) -> str:
    """Clean common formatting issues and escape dollar signs."""
    if not text:
        return ""

    text = re.sub(
        r"\*{2,3}\s*(#{1,3})\s*(.+?)\s*\*{2,3}",
        r"\1 \2",
        text,
    )

    return text.replace("$", r"\$")


def render_metric(label: str, value: str, note: str = ""):
    st.html(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
    )


def extract_brief_sections(brief: str):
    sections = {}
    current = None

    for line in (brief or "").splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        heading = re.sub(r"^[#\*\s]+", "", stripped).strip()
        normalized = heading.lower().replace("**", "")

        if (
            "where this deal stands" in normalized
            or "deal stands" in normalized
        ):
            current = "Deal status"
            sections[current] = []
            continue

        if "watch for" in normalized or "risks" in normalized:
            current = "Watch for"
            sections[current] = []
            continue

        if "tactics that worked" in normalized or "tactics" in normalized:
            current = "Learned tactics"
            sections[current] = []
            continue

        if current:
            sections[current].append(stripped)

    return sections


def render_brief(brief: str):
    """Render generated brief as polished cards."""

    sections = extract_brief_sections(brief)

    if not sections:
        st.markdown(clean_brief(brief))
        return

    card_config = {
        "Deal status": {
            "icon": "",
            "class_name": "brief-status",
            "label": "DEAL STATUS",
            "description": "What the agent currently knows about this opportunity.",
        },
        "Watch for": {
            "icon": "⚠️",
            "class_name": "brief-watch",
            "label": "WATCH FOR",
            "description": "Risks and objections likely to resurface.",
        },
        "Learned tactics": {
            "icon": "",
            "class_name": "brief-tactics",
            "label": "PROVEN TACTICS",
            "description": "Reusable tactics recalled from the shared deal playbook.",
        },
    }

    for title, lines in sections.items():

        config = card_config.get(
            title,
            {
                "icon": "•",
                "class_name": "brief-status",
                "label": title.upper(),
                "description": "",
            },
        )

        st.html(
            f"""
            <div class="brief-card {config['class_name']}">
                <div class="brief-card-header">
                    <div class="brief-icon">{config['icon']}</div>
                    <div>
                        <div class="brief-card-label">{config['label']}</div>
                        <div class="brief-card-description">
                            {config['description']}
                        </div>
                    </div>
                </div>
            """,
        )

        for line in lines:

            cleaned = clean_brief(line).strip()

            if not cleaned:
                continue

            cleaned = re.sub(
                r"\*{2}(.+?)\*{2}",
                r"<strong>\1</strong>",
                cleaned,
            )

            cleaned = re.sub(r"^[-\*•]\s*", "", cleaned)

            is_tactic = "tactic" in cleaned.lower()
            marker = "✓" if is_tactic else "•"

            st.html(
                f"""
                <div class="brief-item">
                    <span class="brief-marker">{marker}</span>
                    <span>{cleaned}</span>
                </div>
                """,
            )

        st.html("</div>")


def unique_memories(memories):
    """Remove duplicate memory lines while preserving order."""

    result = []
    seen = set()

    for memory in memories:
        cleaned = str(memory).strip()

        if not cleaned:
            continue

        key = cleaned.lower()

        if key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def find_lines(memories, keywords):
    """Return memories containing any keyword."""

    results = []

    for memory in memories:
        lower = memory.lower()

        if any(keyword in lower for keyword in keywords):
            results.append(memory)

    return results


def extract_people(memories):
    """Extract only explicitly named stakeholders from memory text."""

    people = {}

    for memory in memories:
        text = memory.strip()

        # Pattern: "Stakeholder: Raj (CFO)"
        for match in re.finditer(
            r"Stakeholder:\s*([A-Z][a-z]{2,20})\s*\(([^)]+)\)",
            text,
            re.IGNORECASE,
        ):
            name = match.group(1).strip()
            role = match.group(2).strip()

            people.setdefault(name, [])
            people[name].append(f"{role}: {text}")

        # Pattern: "CFO Priya" / "CFO Raj"
        for match in re.finditer(
            r"\b(CFO|CEO|CTO|COO|VP|Director|Manager)\s+([A-Z][a-z]{2,20})\b",
            text,
        ):
            role = match.group(1)
            name = match.group(2)

            people.setdefault(name, [])
            people[name].append(f"{role}: {text}")

        # Pattern: "Raj is the CFO"
        for match in re.finditer(
            r"\b([A-Z][a-z]{2,20})\s+is\s+(?:the\s+)?"
            r"(CFO|CEO|CTO|COO|VP|Director|Manager)\b",
            text,
        ):
            name = match.group(1)
            role = match.group(2)

            people.setdefault(name, [])
            people[name].append(f"{role}: {text}")

        # Pattern: "Raj (CFO)"
        for match in re.finditer(
            r"\b([A-Z][a-z]{2,20})\s*\((CFO|CEO|CTO|COO|VP|Director|Manager)\)",
            text,
        ):
            name = match.group(1)
            role = match.group(2)

            people.setdefault(name, [])
            people[name].append(f"{role}: {text}")

    return people
    


def generate_next_actions(memories):
    """Generate explainable next actions from stored memory."""

    actions = []

    text = " ".join(memories).lower()

    if "cfo" in text or "approval" in text:
        actions.append(
            (
                "Confirm approval path",
                "Identify who must approve the commercial decision and what evidence they need.",
            )
        )

    if "price" in text or "pricing" in text:
        actions.append(
            (
                "Strengthen pricing justification",
                "Prepare the value, ROI, or cost-saving evidence before the next pricing discussion.",
            )
        )

    if "objection" in text:
        actions.append(
            (
                "Address the latest objection",
                "Turn the recurring objection into a specific response or proof point.",
            )
        )

    if "timeline" in text or "deadline" in text:
        actions.append(
            (
                "Lock the implementation timeline",
                "Confirm the required date and work backwards to identify remaining decisions.",
            )
        )

    if "follow-up" in text or "follow up" in text or "agreed" in text:
        actions.append(
            (
                "Close the agreed next step",
                "Verify that the previously discussed follow-up action has an owner and completion point.",
            )
        )

    if not actions:
        actions.append(
            (
                "Capture the next commitment",
                "Use the next conversation to establish a concrete action, owner, and expected follow-up.",
            )
        )

    return actions[:5]


def generate_followup(memories, deal_name):
    """Generate a deterministic follow-up draft from existing memory."""

    text = " ".join(memories)

    objections = find_lines(
        memories,
        ["objection", "price", "pricing", "concern"],
    )

    next_steps = find_lines(
        memories,
        ["next step", "follow-up", "follow up", "agreed"],
    )

    lines = [
        f"Subject: Follow-up — {deal_name}",
        "",
        "Hi,",
        "",
        "Thanks for the conversation. I wanted to follow up on the points we discussed.",
    ]

    if objections:
        lines.append(
            "We will make sure the key concerns raised in the conversation are addressed with the relevant details and supporting information."
        )

    if next_steps:
        lines.append(
            "I have captured the agreed next steps and will use those as the basis for our follow-up."
        )

    if not objections and not next_steps:
        lines.append(
            "I will follow up with the relevant information and proposed next steps."
        )

    lines.extend(
        [
            "",
            "Please let me know if there is anything else you would like us to clarify.",
            "",
            "Best,",
            "Deal Team",
        ]
    )

    return "\n".join(lines)


def detect_contradictions(memories):
    """
    Lightweight contradiction detector.

    It flags potentially conflicting statements rather than claiming
    that they are definitely contradictions.
    """

    findings = []

    price_values = []

    for memory in memories:
        matches = re.findall(
            r"\$?\s?(\d+(?:\.\d+)?)\s*(?:/month|per month|monthly)",
            memory.lower(),
        )

        for value in matches:
            price_values.append((value, memory))

    unique_prices = {}

    for value, memory in price_values:
        unique_prices.setdefault(value, []).append(memory)

    if len(unique_prices) > 1:
        findings.append(
            (
                "Pricing values differ across memory",
                "Different monthly price points were found. Verify which value is current.",
            )
        )

    deadline_lines = find_lines(
        memories,
        ["deadline", "expires", "expiration"],
    )

    timeline_lines = find_lines(
        memories,
        ["timeline", "week"],
    )

    if deadline_lines and timeline_lines:
        findings.append(
            (
                "Timeline information should be verified",
                "The memory contains both deadline and timeline statements. Confirm the current target date.",
            )
        )

    if not findings:
        findings.append(
            (
                "No obvious contradiction detected",
                "The current memory does not contain an obvious conflicting statement using the available checks.",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Load deals
# ---------------------------------------------------------------------------

deals = load_deals()
deal_ids = list(deals.keys())

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:

    st.markdown("##  Deal Intelligence")
    st.caption("Persistent memory for every sales conversation.")
    st.divider()

    st.markdown("### Your deals")

    if deal_ids:

        labels = [
            f"{deals[d]['name']} · {get_call_count(d)} call"
            f"{'s' if get_call_count(d) != 1 else ''}"
            for d in deal_ids
        ]

        selected_idx = st.radio(
            "Select a deal",
            range(len(deal_ids)),
            format_func=lambda i: labels[i],
            label_visibility="collapsed",
        )

    else:
        selected_idx = None

    st.divider()

    st.markdown("### ➕ New deal")

    new_name = st.text_input(
        "Deal name",
        placeholder="e.g. Initech",
        label_visibility="collapsed",
    )

    if st.button("Create deal", use_container_width=True) and new_name.strip():

        add_deal(new_name.strip())
        st.rerun()

    st.divider()

    st.caption("AI pipeline")

    st.markdown(" **Groq** · Extraction")
    st.markdown(" **Hindsight** · Memory")
    st.markdown(" **Playbook** · Cross-deal learning")


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------

if not deal_ids:

    st.html(
        """
        <div class="empty-state">
            <h3>Welcome to Deal Intelligence</h3>
            <p>Create your first deal from the sidebar to begin.</p>
        </div>
        """,
    )

    st.stop()


# ---------------------------------------------------------------------------
# Current deal
# ---------------------------------------------------------------------------

deal_id = deal_ids[selected_idx]
deal_name = deals[deal_id]["name"]

call_count = get_call_count(deal_id)

deal_memories = unique_memories(
    recall_deal_context(deal_id)
)



# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.html(
    f"""
    <div class="hero">
        <div class="hero-title"> Deal Intelligence Agent</div>

        <div class="hero-subtitle">
            Persistent memory across sales calls · AI-powered pre-call intelligence
        </div>

        <div class="online-pill">
            ● AI MEMORY SYSTEM ONLINE
        </div>
    </div>
    """,
)

st.markdown(f"## {deal_name}")


# ---------------------------------------------------------------------------
# Deal overview metrics
# ---------------------------------------------------------------------------

m1, m2, m3, m4 = st.columns(4)

with m1:
    render_metric(
        "Deal",
        deal_name,
        "Active workspace",
    )

with m2:
    render_metric(
        "Calls remembered",
        str(call_count),
        "Stored in deal memory",
    )

with m3:
    render_metric(
        "Memory layer",
        "Hindsight",
        f"{len(deal_memories)} memories",
    )

with m4:
    render_metric(
        "Learning",
        "Cross-deal",
        "Shared playbook",
    )

st.markdown("")


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab_brief, tab_actions, tab_people, tab_risks, tab_ingest, tab_memory = st.tabs(
    [
        " Pre-Call Brief",
        " Next Actions",
        " Stakeholders",
        " Deal Intelligence",
        " Add a Call",
        " Memory Explorer",
    ]
)


# ===========================================================================
# TAB 1 — PRE-CALL BRIEF
# ===========================================================================

with tab_brief:

    st.html(
        """
        <div class="memory-banner">
            <div class="memory-banner-title">
                 Memory-powered preparation
            </div>

            <div class="memory-banner-text">
                The agent combines this deal's history with tactics learned
                from other deals before preparing the next-call brief.
            </div>
        </div>
        """,
    )

    c1, c2 = st.columns([3, 1])

    with c1:

        st.markdown("### Prepare for the next call")

        st.caption(
            f"Generate an AI briefing using everything remembered about {deal_name}."
        )

    with c2:

        generate = st.button(
            "Generate Brief",
            type="primary",
            use_container_width=True,
        )

    if generate:

        with st.spinner(
            "Recalling memory and drafting the brief..."
        ):

            brief = prep_next_call(
                deal_id,
                deal_name,
            )

        st.session_state[f"brief_{deal_id}"] = brief

    brief = st.session_state.get(
        f"brief_{deal_id}"
    )

    if brief:

        render_brief(brief)

    else:

        st.html(
            """
            <div class="empty-state">
                <h3>Ready for your next call</h3>

                <p>
                    Click <b>Generate brief</b> to turn your accumulated
                    deal memory into an actionable pre-call plan.
                </p>
            </div>
            """,
        )

    # -----------------------------------------------------------------------
    # Deal activity
    # -----------------------------------------------------------------------

    st.markdown("###  Deal timeline")

    if call_count:

        for i in range(call_count, 0, -1):

            st.html(
                f"""
                <div class="timeline-item">

                    <div class="timeline-number">
                        Call #{i}
                    </div>

                    <div class="timeline-text">
                        Conversation retained in persistent deal memory.
                    </div>

                </div>
                """,
            )

    else:

        st.caption("No calls have been added yet.")


# ===========================================================================
# TAB 2 — NEXT BEST ACTIONS
# ===========================================================================

with tab_actions:

    st.markdown("###  Next Best Actions")

    st.caption(
        "Actions are generated from the current deal memory."
    )

    actions = generate_next_actions(
        deal_memories,
    )

    for index, (title, description) in enumerate(actions, start=1):

        st.html(
            f"""
            <div class="action-card">

                <span class="action-number">
                    {index:02d}
                </span>

                &nbsp;

                <span class="action-title">
                    {title}
                </span>

                <div class="action-description">
                    {description}
                </div>

            </div>
            """,
        )

    st.markdown("### ✉️ Follow-up draft")

    st.caption(
        "Draft generated from the information already retained for this deal."
    )

    followup = generate_followup(
        deal_memories,
        deal_name,
    )

    st.text_area(
        "Suggested follow-up",
        value=followup,
        height=260,
        label_visibility="collapsed",
    )


# ===========================================================================
# TAB 3 — STAKEHOLDER INTELLIGENCE
# ===========================================================================

with tab_people:

    st.markdown("###  Stakeholder Intelligence")

    st.caption(
        "People and roles detected from the persistent deal memory."
    )

    people = extract_people(
        deal_memories
    )

    if people:

        people_cols = st.columns(
            min(3, len(people))
        )

        for index, (name, evidence) in enumerate(
            people.items()
        ):

            with people_cols[index % len(people_cols)]:

                role_text = "Stakeholder"

                combined = " ".join(evidence).lower()

                if "cfo" in combined:
                    role_text = "CFO / Approval"
                elif "decision-maker" in combined or "decision maker" in combined:
                    role_text = "Decision-maker"
                elif "manager" in combined:
                    role_text = "Manager"
                elif "director" in combined:
                    role_text = "Director"

                st.html(
                    f"""
                    <div class="stakeholder-card">

                        <div class="stakeholder-name">
                            {name}
                        </div>

                        <div class="stakeholder-role">
                            {role_text}
                        </div>

                        <div class="stakeholder-context">
                            Appears in {len(evidence)} memory item(s).
                        </div>

                    </div>
                    """,
                )

    else:

        st.html(
            """
            <div class="empty-state">
                <h3>No stakeholder map yet</h3>
                <p>
                    Add a call containing stakeholder information to build
                    the relationship map.
                </p>
            </div>
            """,
        )

    st.markdown("###  Stakeholder evidence")

    stakeholder_memories = find_lines(
        deal_memories,
        [
            "stakeholder",
            "decision-maker",
            "decision maker",
            "cfo",
            "ceo",
            "manager",
            "director",
            "buyer",
            "approval",
        ],
    )

    if stakeholder_memories:

        for memory in stakeholder_memories[:10]:

            st.html(
                f"""
                <div class="evidence-card">
                    {memory}
                </div>
                """,
            )

    else:

        st.caption("No stakeholder-specific evidence found yet.")


# ===========================================================================
# TAB 4 — DEAL INTELLIGENCE
# ===========================================================================

with tab_risks:

    st.markdown("###  Deal Intelligence")

    intel1, intel2 = st.columns(2)

       # -----------------------------------------------------------------------
    # Objections
    # -----------------------------------------------------------------------

    with intel1:

        st.markdown("#### Objection Tracker")

        objections = []

        for memory in deal_memories:

            text = memory.strip()
            lower = text.lower()

            # Ignore memories that describe resolutions, tactics, or commitments.
            is_resolution = (
                lower.startswith("resolved ")
                or lower.startswith("resolved a ")
                or "tactic that worked" in lower
                or "was resolved by" in lower
                or "used to resolve" in lower
                or "user resolved" in lower
                or "user has resolved" in lower
                or "resolved the objection" in lower
                or "resolved a stakeholder objection" in lower
                or "resolved a price objection" in lower
                or "resolved a pricing objection" in lower
                or "resolved a timing objection" in lower
            )

            is_commitment = (
                lower.startswith("next step agreed:")
                or lower.startswith("next step for")
                or "will send" in lower
                or "will review" in lower
                or "agreed to send" in lower
                or "agreed to provide" in lower
                or "agreed to reconnect" in lower
            )

            # Recognize explicit objection language.
            is_objection = (
                lower.startswith("objection raised:")
                or "prospect objected" in lower
                or "prospect raised" in lower
                or "raised a pricing objection" in lower
                or "raised a price objection" in lower
                or "raised a competitor objection" in lower
                or "raised a timing objection" in lower
                or "raised a stakeholder objection" in lower
                or "price objection" in lower
                or "pricing objection" in lower
                or "competitor objection" in lower
                or "timing objection" in lower
                or "stakeholder objection" in lower
                or "budget objection" in lower
                or "prospect was concerned" in lower
                or "prospect expressed concern" in lower
            )

            if (
                is_objection
                and not is_resolution
                and not is_commitment
            ):
                objections.append(text)

        if objections:

            for objection in objections[:8]:

                st.html(
                    f"""
                    <div class="objection-card">
                        <b>Potential objection / friction</b>
                        <div style="margin-top:6px;">
                            {objection}
                        </div>
                    </div>
                    """,
                )

        else:

            st.info(
                "No explicit objection has been detected yet."
            )
    # -----------------------------------------------------------------------
    # Commitments
    # -----------------------------------------------------------------------

    with intel2:

        st.markdown("#### ✅ Commitment Tracker")

        commitments = find_lines(
            deal_memories,
            [
                "agreed",
                "commit",
                "next step",
                "follow-up",
                "follow up",
                "will send",
                "will review",
                "scheduled",
            ],
        )

        if commitments:

            for commitment in commitments[:8]:

                st.html(
                    f"""
                    <div class="commitment-card">
                        ✓ {commitment}
                    </div>
                    """,
                )

        else:

            st.info(
                "No explicit commitments have been detected yet."
            )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Contradictions
    # -----------------------------------------------------------------------

    st.markdown("###  Contradiction Detector")

    st.caption(
        "Potential inconsistencies are flagged for human verification; "
        "the system does not automatically assume that conflicting statements are errors."
    )

    contradictions = detect_contradictions(
        deal_memories
    )

    for title, description in contradictions:

        if "No obvious" in title:

            st.success(
                f"{title} — {description}"
            )

        else:

            st.html(
                f"""
                <div class="contradiction-card">

                    <b>⚠ {title}</b>

                    <div style="margin-top:6px;">
                        {description}
                    </div>

                </div>
                """,
            )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Cross-deal learning
    # -----------------------------------------------------------------------

    st.markdown("###  Cross-Deal Insights")

    st.caption(
        "Reusable tactics recalled from other deals facing similar situations."
    )

    objection_lines = find_lines(
        deal_memories,
        ["objection", "price", "pricing", "budget", "roi"],
    )

    tactic_query = (
        " ".join(objection_lines[-3:])
        if objection_lines
        else deal_name
    )

    try:

        cross_deal = recall_similar_tactics(
            tactic_query,
            deal_id,
            deal_name,
        )

    except Exception:

        cross_deal = []

    if cross_deal:

     cross_deal = [
        tactic for tactic in cross_deal
        if f"deal {deal_name.lower()}" not in tactic.lower()
    ]

    for tactic in cross_deal[:6]:

            st.html(
                f"""
                <div class="brief-card brief-tactics">

                    <div class="brief-card-header">

                        <div class="brief-icon">
                            
                        </div>

                        <div>

                            <div class="brief-card-label">
                                LEARNED FROM ANOTHER DEAL
                            </div>

                            <div class="brief-card-description">
                                Cross-deal memory
                            </div>

                        </div>

                    </div>

                    <div class="brief-item">

                        <span class="brief-marker">
                            ✓
                        </span>

                        <span>
                            {tactic}
                        </span>

                    </div>

                </div>
                """,
            )

    else:
        pass



# ===========================================================================
# TAB 5 — ADD A CALL
# ===========================================================================

with tab_ingest:

    st.markdown("###  Add a new sales call")

    st.caption(
        f"Paste a transcript for **{deal_name}**. "
        "The agent extracts structured facts and stores them in persistent memory."
    )

    samples = {
        "Acme call 1": "data/transcripts/acme_call1.txt",
        "Acme call 2": "data/transcripts/acme_call2.txt",
        "Globex call 1": "data/transcripts/globex_call1.txt",
    }

    st.markdown("**Try a bundled sample**")

    sample_cols = st.columns(3)

    for col, (label, path) in zip(
        sample_cols,
        samples.items(),
    ):

        if col.button(
            label,
            use_container_width=True,
        ):

            sample_path = PROJECT_ROOT / path

            if sample_path.exists():

                st.session_state["transcript_text"] = (
                    sample_path.read_text(
                        encoding="utf-8"
                    )
                )

            else:

                st.error(
                    f"Sample file not found: {path}"
                )

    with st.form(
        "add_call_form",
        clear_on_submit=True,
    ):

        transcript = st.text_area(
            "Call transcript",
            height=320,
            key="transcript_text",
            placeholder=(
                "Paste the raw call transcript here...\n\n"
                "The agent will identify objections, stakeholders, pricing signals, "
                "resolutions and next steps."
            ),
        )

        word_count = (
            len(transcript.split())
            if transcript.strip()
            else 0
        )

        st.caption(
            f"{word_count:,} words"
        )

        ingest = st.form_submit_button(
            " Analyze & remember call",
            type="primary",
            use_container_width=True,
        )

    # IMPORTANT: This is OUTSIDE the form.
    if ingest and transcript.strip():

        call_number = increment_call(
            deal_id
        )

        with st.spinner(
            f"AI is analyzing call #{call_number} and updating memory..."
        ):

            facts = ingest_call(
                deal_id,
                deal_name,
                call_number,
                transcript,
            )

        st.success(
            f"Call #{call_number} analyzed successfully and retained in memory."
        )

        st.markdown(
            "###  Extracted intelligence"
        )

        fcols = st.columns(3)

        with fcols[0]:

            st.metric(
                "Objections",
                len(facts.get("objections", [])),
            )

        with fcols[1]:

            st.metric(
                "Stakeholders",
                len(facts.get("stakeholders", [])),
            )

        with fcols[2]:

            st.metric(
                "Next steps",
                len(facts.get("next_steps", [])),
            )

# ===========================================================================
# TAB 6 — MEMORY EXPLORER
# ===========================================================================

with tab_memory:

    st.markdown("###  Memory Explorer")

    st.caption(
        "Inspect what Hindsight currently recalls for this deal. "
        "This makes the persistent-memory layer visible for demos and judging."
    )

    recall = st.button(
        " Recall deal memory",
        type="primary",
        use_container_width=True,
    )

    if recall:

        with st.spinner(
            "Recalling persistent memory..."
        ):

            memories = recall_deal_context(
                deal_id
            )

        st.session_state[
            f"memories_{deal_id}"
        ] = memories

    memories = st.session_state.get(
        f"memories_{deal_id}"
    )

    if memories is None:

        st.html(
            """
            <div class="empty-state">

                <h3>Memory explorer</h3>

                <p>
                    Click <b>Recall deal memory</b> to inspect what the AI
                    currently remembers.
                </p>

            </div>
            """,
        )

    elif not memories:

        st.info(
            "No memory yet for this deal."
        )

    else:

        st.success(
            f"{len(memories)} memory item(s) recalled."
        )

        for index, memory in enumerate(
            memories,
            start=1,
        ):

            with st.expander(
                f"Memory #{index}",
                expanded=index == 1,
            ):

                st.markdown(
                    clean_brief(memory)
                )

    # -----------------------------------------------------------------------
    # Why am I seeing this?
    # -----------------------------------------------------------------------

    st.markdown("###  Why am I seeing this?")

    st.caption(
        "Evidence behind the current intelligence is taken directly from memory."
    )

    evidence_keywords = [
        "objection",
        "stakeholder",
        "decision-maker",
        "decision maker",
        "pricing",
        "price",
        "cfo",
        "approval",
        "timeline",
        "deadline",
        "agreed",
        "follow-up",
        "follow up",
        "next step",
        "roi",
    ]

    evidence = find_lines(
        deal_memories,
        evidence_keywords,
    )

    if evidence:

        for memory in evidence[:12]:

            st.html(
                f"""
                <div class="evidence-card">
                    <b>Memory evidence</b>

                    <div style="margin-top:6px;">
                        {memory}
                    </div>
                </div>
                """,
            )

    else:

        st.caption(
            "No specific evidence signals have been found yet."
        )

    # -----------------------------------------------------------------------
    # Architecture flow
    # -----------------------------------------------------------------------

    st.markdown("###  How the memory system works")

    flow_cols = st.columns(5)

    flow = [
        ("", "Call", "Raw transcript"),
        ("", "Extract", "Structured facts"),
        ("", "Retain", "Hindsight memory"),
        ("", "Recall", "Relevant history"),
        ("", "Prepare", "Next-call brief"),
    ]

    for col, (icon, title, subtitle) in zip(
        flow_cols,
        flow,
    ):

        with col:

            st.html(
                f"""
                <div class="section-card" style="text-align:center;">

                    <div style="font-size:1.7rem;">
                        {icon}
                    </div>

                    <div style="font-weight:800;color:#111827;">
                        {title}
                    </div>

                    <div style="font-size:0.76rem;color:#6b7280;">
                        {subtitle}
                    </div>

                </div>
                """,
            )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")

st.caption(
    "Deal Intelligence Agent · Groq for reasoning · Hindsight for persistent "
    "memory · Cross-deal playbook learning · Explainable deal intelligence"
)