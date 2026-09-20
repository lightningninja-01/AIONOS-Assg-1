# Executive Productivity Agent — AIONOS Assignment 1

**Student:** Ujjwal Prakash Singh | 2301010234

This is an autonomous Executive Productivity Agent built as a standalone project for AIONOS Assignment 1. It operates on a closed-world dataset (meeting transcripts, emails, voice notes, and calendars) for Arjun Malhotra, VP Sales at Veridian Corp.

## Features

- **Hybrid Architecture:** LLM-based commitment extraction combined with deterministic validation, cross-source deduplication, deadline resolution, and rule-based ownership ambiguity detection.
- **Configurable Simulation:** Simulate different days of the week (`SIMULATED_TODAY`) to observe how deadlines and completion states evolve over time.
- **Traceability:** Every commitment and answer is fully grounded in the source data. The UI presents an `AgentTrace` and `EvidenceTimeline` to prove provenance.
- **Q&A Graph:** LangGraph-based Q&A flow that forces the LLM to cite specific commitment IDs, preventing hallucination.
- **Single Model:** Configured to use a single Groq model (`openai/gpt-oss-20b`) for all LLM operations to reduce orchestration complexity.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Groq API Key

## One-Command Local Run

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your GROQ_API_KEY

# Run server
uvicorn app.main:app --port 8001 --reload
```

### 2. Frontend (in a new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5174](http://localhost:5174) in your browser.

## Demo Scenarios

Once the app is running, try the following queries in the Chat Panel:

1. **"What did I promise Raghav?"**
   - Agent will identify the Vendor List commitment, citing the original meeting, emails, and voice notes.
2. **"What needs action today?"**
   - Shows due/overdue items based on the selected "Simulated date".
3. **"Who owns the Mumbai office renewal?"**
   - **Crucial Demo:** The agent will correctly state that ownership is UNCLEAR and will not assume it is Facilities, referencing Arjun's explicit "flag it, don't assume" remark.
4. **"What am I waiting on?"**
   - Lists items owned by others (like Divya's expense report or Neha's campaign deck) depending on the simulated date.

## Architecture & Logic

- **Extraction:** Raw sources → `loader.py` → `extractor.py` (Groq tool-calling) → candidate commitments.
- **Deduplication:** Groups candidates by semantic key and uses LLM pair-scoring to merge them.
- **Deadline Resolution:** Deterministic timeline walk to track deadline shifts.
- **Ownership:** Rule-based override for ambiguous phrases (e.g. "don't assume").
- **Agent Q&A:** LangGraph pipeline (`context_loader` → `llm_reasoning` → `response_builder`).

## Data

The original raw dataset is in `backend/data/sources/`. The `expected_commitments.json` file in `reference/` is used **only** for automated testing and evaluating extraction quality—it does not power the application itself.
