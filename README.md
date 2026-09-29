# Deal Intelligence Agent

An AI-powered Deal Intelligence Agent that turns sales call transcripts into persistent, actionable sales intelligence.

Instead of treating every sales call as an isolated conversation, the system extracts structured information, stores it as persistent memory using [Hindsight](https://hindsight.vectorize.io/), recalls relevant deal history before future calls, and surfaces useful tactics learned from other deals.

The result is a sales agent that can carry useful experience from one customer conversation into another while keeping deal-specific information isolated.

![Pre-call brief for a brand-new deal citing tactics learned from another deal](docs/screenshot-brief.png)

> A brand-new deal (Globex, one call in) can receive a brief containing concrete tactics learned from a different deal (Acme). The agent is reusing experience through persistent memory rather than relying only on the current conversation.

---

## What It Does

### 1. AI Call Analysis

The system processes sales call transcripts using an LLM and extracts structured information such as:

- Customer objections
- Objection resolutions
- Stakeholders and their roles
- Pricing signals
- Commitments
- Next steps
- Important deal information

The extraction pipeline focuses not only on **what happened**, but also on concrete actions that successfully addressed objections.

### 2. Persistent Deal Memory

Extracted information is stored using [Hindsight](https://hindsight.vectorize.io/).

Each deal has its own memory bank, identified by its `deal_id`.

```text
deal-acme
deal-globex
```

This keeps customer-specific information isolated while allowing useful, deal-agnostic experience to be stored in a shared playbook.

Instead of treating every transcript as a fresh input, the system can recall information from previous calls.

### 3. Cross-Deal Playbook

The system maintains a separate shared `playbook` memory bank.

The playbook stores reusable patterns such as:

- Successful objection resolutions
- Pricing approaches
- ROI framing
- Competitor positioning
- Timeline strategies

The important distinction is that **customer-specific details remain in the original deal memory**, while reusable tactics can be promoted into the shared playbook.

For example:

```text
Acme
  └── successful pricing approach
            │
            ▼
       Shared Playbook
            │
            ▼
        Globex Brief
```

This allows a new deal to benefit from experience gathered from previous deals without copying private deal details into it.

---

## Pre-Call Brief

Before a sales call, the agent recalls relevant information and generates a concise Pre-Call Brief.

The brief can include:

- Where the current deal stands
- Important objections
- Stakeholders and approval requirements
- Pricing context
- Previous commitments
- Timeline information
- Things to watch for
- Tactics that worked in other deals
- Suggested next actions

The current deal's memory and the shared playbook are recalled separately so that deal-specific facts and reusable tactics remain distinguishable.

---

## The Memory Architecture

The project uses two different Hindsight memory scopes.

| Memory | Hindsight Bank | What's Stored | Purpose |
|---|---|---|---|
| **Per-deal memory** | `deal-<deal_id>` | Objections, resolutions, stakeholders, pricing signals, next steps and deal history | Preserve the complete history of one customer |
| **Cross-deal playbook** | `playbook` | Deal-agnostic objections and reusable `TACTIC` entries | Surface proven approaches from other deals |

### Why resolutions matter

A useful sales memory is more than:

```text
Customer objected to pricing.
```

The system tries to capture the action that addressed the objection:

```text
Customer raised a pricing concern.
An annual-plan option was discussed to reduce the effective monthly rate.
```

That gives the shared playbook something concrete to retrieve later.

This distinction was important during development. Early cross-deal retrieval contained mostly objections, which produced generic advice. Adding concrete resolution information made the retrieved tactics substantially more useful.

---

## Architecture

```text
                    Sales Call Transcript
                              |
                              v
                     +----------------+
                     |   extract.py   |
                     |  LLM Extraction|
                     +-------+--------+
                             |
                             | structured facts
                             v
                     +----------------+
                     |   memory.py    |
                     |    Hindsight   |
                     +-------+--------+
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
        Deal-Specific Memory      Shared Playbook
        deal-<deal_id>               playbook
                 |                       |
                 |                       |
                 +-----------+-----------+
                             |
                             v
                     +----------------+
                     |    brief.py    |
                     | Hindsight Recall|
                     +-------+--------+
                             |
                             v
                     +----------------+
                     |    ui/app.py   |
                     |   Streamlit UI |
                     +----------------+
```

### End-to-end flow

```text
Transcript
    ↓
LLM extraction
    ↓
Structured facts
    ↓
Hindsight retain()
    ↓
┌───────────────────────┐
│ Deal memory           │
│ Shared playbook       │
└───────────────────────┘
    ↓
Focused Hindsight recall()
    ↓
Current deal context
+
Cross-deal tactics
    ↓
Pre-Call Brief
    ↓
Streamlit Dashboard
```

---

## Project Structure

```text
deal-intelligence-agent/
├── README.md
├── requirements.txt
├── .env.example
├── run_demo.py
│
├── src/
│   ├── config.py
│   ├── extract.py
│   ├── memory.py
│   ├── brief.py
│   ├── agent.py
│   └── deals_store.py
│
├── ui/
│   └── app.py
│
├── data/
│   ├── deals.json
│   └── transcripts/
│       ├── acme_call1.txt
│       ├── acme_call2.txt
│       └── globex_call1.txt
│
└── docs/
    └── screenshot-brief.png
```

### Core files

| File | Responsibility |
|---|---|
| `src/extract.py` | Extract structured sales intelligence from transcripts |
| `src/memory.py` | Hindsight retain/recall and memory-bank management |
| `src/brief.py` | Retrieve relevant memory and construct the Pre-Call Brief |
| `src/agent.py` | High-level call ingestion and briefing workflow |
| `src/deals_store.py` | Local deal registry used by the UI |
| `ui/app.py` | Streamlit dashboard |
| `run_demo.py` | End-to-end terminal demonstration |

---

## Dashboard

The Streamlit application provides multiple views for exploring deal intelligence:

- **Pre-Call Brief**
- **Next Best Actions**
- **Stakeholder Intelligence**
- **Deal Intelligence**
- **Add a Call**
- **Memory Explorer**

The Memory Explorer is particularly useful during development because it makes it possible to inspect what was actually retrieved from Hindsight separately from the final LLM-generated brief.

---

## Example: Acme → Globex

The bundled sample data contains:

- Two Acme calls
- One Globex call

Acme provides multiple pieces of sales experience that can be retained in its deal memory and promoted into the shared playbook.

When preparing a brief for Globex, the system can recall relevant playbook tactics learned from Acme, such as:

- Annual-plan pricing approaches
- Comparison material
- ROI and hours-saved framing

At the same time, Globex-specific information remains in:

```text
deal-globex
```

rather than being mixed with Acme's private deal history.

This is the core behavior the project is designed to demonstrate:

```text
Experience from Deal A
          ↓
    Shared Playbook
          ↓
    Deal B's Brief
```

---

## Hindsight Integration

Hindsight is used as the persistent memory layer.

The application uses:

```text
retain()
```

after processing calls and:

```text
recall()
```

when preparing future briefs.

The memory layer is deliberately separated from the application logic:

```text
extract.py
    ↓
memory.py
    ↓
Hindsight
    ↓
brief.py
```

This allows the application to decide:

- What should be retained
- Which memory bank it belongs to
- Which memories should be recalled
- How current-deal and cross-deal memories should be separated
- Which recalled tactics should be treated as proven experience

The project therefore uses Hindsight as more than a storage layer. Persistent memory directly changes what the agent can retrieve and use during later interactions.

---

## Grounding the Generated Brief

The LLM is used to generate and organize the natural-language brief, but the cross-deal tactic section is built from retrieved playbook memories.

This distinction helps prevent generic sales advice from being presented as something that actually happened in another deal.

The system prefers recalled `TACTIC` entries and treats unsupported recommendations as suggestions rather than proven historical tactics.

---

## Technical Design Notes

### One memory bank per deal

Each deal gets its own Hindsight bank:

```text
deal-acme
deal-globex
...
```

This makes deal isolation explicit.

### Shared playbook

Reusable experience is stored separately:

```text
playbook
```

Only deal-agnostic patterns are promoted into this bank.

### Focused recall queries

Hindsight recall queries are kept focused because the memory system has a query-size constraint.

Instead of continuously sending the entire accumulated deal history into a single query, the application builds focused queries around areas such as:

- Overall deal history
- Objections
- Pricing and approval
- Stakeholders
- Timelines
- Resolutions
- Cross-deal tactics

This keeps retrieval targeted as the amount of deal history grows.

### Metadata

Hindsight metadata values are normalized to strings before being retained.

This keeps metadata compatible with the client's expected format while still allowing memories to carry information such as:

```text
deal_id
call_number
category
source
```

### App bookkeeping vs memory

The local deal registry and Hindsight serve different purposes.

```text
data/deals.json
        ↓
Which deals exist?
How many calls are associated with them?

Hindsight
        ↓
What was actually said?
What happened?
What worked?
What should be remembered?
```

The local JSON file is therefore not treated as the source of truth for sales intelligence.

---

## Running the Project

### Prerequisites

- Python 3.10+
- Hindsight Cloud API key
- Groq API key

Create your Hindsight API key through:

[Hindsight](https://ui.hindsight.vectorize.io/)

Create your Groq API key through:

[Groq Console](https://console.groq.com/)

### 1. Clone the repository

```bash
git clone https://github.com/sidra-tahseen/Deal-Intelligence-Agent.git
cd Deal-Intelligence-Agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

**Windows PowerShell:**

```powershell
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Then configure:

```env
HINDSIGHT_API_KEY=your-hindsight-api-key
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
```

Never commit your real `.env` file or API keys to GitHub.

---

## Running the Demo

The terminal demo runs the sample pipeline end to end:

```bash
python run_demo.py
```

It processes the bundled sample calls, stores memories in Hindsight, recalls them, and prints the resulting briefs.

---

## Running the Streamlit UI

Start the dashboard with:

```bash
streamlit run ui/app.py
```

If `streamlit` is not available directly, use:

```bash
python -m streamlit run ui/app.py
```

Then open the local Streamlit URL shown in the terminal.

---

## Demo Walkthrough

### Step 1 — Populate memory

Run:

```bash
python run_demo.py
```

This processes the bundled sample calls and populates Hindsight.

Alternatively, calls can be ingested through the **Add a Call** tab.

### Step 2 — Open Acme

Generate an Acme brief.

The system can recall information from both Acme calls, including:

- Pricing context
- CFO approval requirements
- Competitor information
- Timeline
- Previous objections and resolutions

### Step 3 — Open Globex

Globex has only one bundled call.

Generate its brief and inspect the:

```text
Tactics that worked elsewhere
```

section.

The system can surface relevant tactics originating from Acme's experience through the shared Hindsight playbook.

### Step 4 — Inspect Memory

Open **Memory Explorer** to inspect the recalled Hindsight memories directly.

This makes it possible to distinguish:

```text
What Hindsight retrieved
        ↓
What the LLM generated
```

---

## Limitations

- **Sample data is synthetic.** The pipeline accepts transcript text, but the bundled demonstration does not represent production sales recordings.
- **Brief wording is LLM-generated.** Retrieved memories provide grounding, but the model can occasionally embellish or introduce framing that was not explicitly present in the source memory.
- **Resolution extraction is selective.** A vague future commitment such as "I'll follow up" should not automatically become a successful playbook tactic.
- **Deal registry is local.** `data/deals.json` is local application bookkeeping and is not shared across users or machines.
- **Memory quality depends on extraction quality.** If important information is not correctly extracted from a transcript, it cannot be reliably recalled later.

---

## Tech Stack

- [Hindsight](https://hindsight.vectorize.io/) — persistent agent memory
- [Hindsight GitHub](https://github.com/vectorize-io/hindsight) — memory infrastructure
- [Groq](https://groq.com/) — LLM inference
- `openai/gpt-oss-120b` — extraction and brief generation
- [Streamlit](https://streamlit.io/) — interactive dashboard
- Python

---

## Why Memory Matters

A conventional transcript summarizer answers:

> "What happened in this call?"

This project is designed to answer a different question:

> "What should this agent remember from this call, and what previous experience should it bring into the next one?"

That difference is what makes persistent agent memory useful for sales workflows.

The goal is not to make the model permanently retrain itself after every conversation.

The goal is to give the agent **persistent, retrievable experience** that can influence what it knows when the next conversation begins.

---

## Links

- [Hindsight Documentation](https://hindsight.vectorize.io/)
- [Hindsight GitHub](https://github.com/vectorize-io/hindsight)
- [What is Agent Memory?](https://vectorize.io/what-is-agent-memory)
- [Groq](https://groq.com/)
- [Streamlit](https://streamlit.io/)
