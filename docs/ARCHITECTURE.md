# AI Debate Coach — Technical Documentation

## 1. Problem (Week 1)
People preparing for debates, interviews or public speaking rarely have a sparring partner who will argue the opposite side, challenge weak points and give honest, structured feedback. The AI Debate Coach fills that gap.

## 2. Users and user stories
| User | Story |
|---|---|
| Student | As a student, I want the AI to argue the opposite side so I can practise defending my position. |
| Competition debater | As a debater, I want a harder opponent that demands evidence so I can prepare for strong teams. |
| Interview candidate | As a candidate, I want feedback on clarity and persuasiveness so I can answer questions better. |
| Returning user | As a regular user, I want to see my past scores so I know whether I'm improving. |

## 3. Features
| Core (v1) | Enhancements |
|---|---|
| Topic selection (starter motions + custom) | Difficulty levels (Beginner / Intermediate / Advanced) |
| Side selection — AI takes the opposite side | Hints that guide without writing the answer |
| Multi-round debate (Opening → Rebuttals → Closing) | Short coach's notes after selected rounds |
| Post-debate scorecard on 6 criteria | Debate history, statistics and progress summary |
| | Guardrails: prompt injection, abuse, off-topic, repeats, early quitting, unsafe motions |

## 4. User flow
```
Home → New Debate (motion, side, difficulty, rounds)
     → Debate Room: AI opening → [user argument → AI counter] × rounds → AI closing
                    (Hint any time · coach's note every 2nd round)
     → End Debate → Results (scores, strengths, weaknesses, recommendations) → saved
     → History & Progress (stats, charts, past transcripts)
```

## 5. Architecture
```
┌──────────────────────┐   HTTP/JSON   ┌──────────────────────────────────────────┐
│ Streamlit frontend   │ ────────────▶ │ FastAPI backend (main.py)                │
│ frontend/app.py      │ ◀──────────── │   └─ DebateCoach (engine.py)             │
└──────────────────────┘               │        ├─ guardrails.py  (input checks)  │
                                       │        ├─ llm.py ──▶ Ollama (optional)   │
                                       │        ├─ brain.py   (offline opponent)  │
                                       │        ├─ evaluator.py (scoring, JSON)   │
                                       │        └─ database.py ──▶ SQLite file    │
                                       └──────────────────────────────────────────┘
```

### Module responsibilities
| File | Responsibility |
|---|---|
| `main.py` | REST endpoints, request models, error → HTTP status mapping (400 / 404 / 409) |
| `engine.py` | Session state, side assignment, round management, choosing LLM vs offline brain, position-consistency check |
| `brain.py` | Offline opponent: opening, counterarguments, closing, hints, round feedback, progress summary |
| `evaluator.py` | Six-criterion rubric, Pydantic `Scorecard`, parsing/validating LLM JSON |
| `prompts.py` | System prompts for the debater and the separate evaluator role |
| `llm.py` | Talks to Ollama; health check is cached for 30 s to avoid unnecessary calls |
| `guardrails.py` | Empty/long input, control characters, unsafe motions, injection, abuse, off-topic, repeats |
| `database.py` | Users and completed debates; statistics |
| `topics.py` | Starter motions and argument banks |
| `analysis.py` | Text helpers: keywords, claim extraction, reasoning/evidence detection |

### Why two AI roles?
The **debater** argues; the **evaluator** judges. Mixing them would let the opponent "grade its own homework". The evaluator only scores the user's turns and gives no credit for agreeing with the AI.

### Why an offline brain?
API keys cost money, expire and need internet. The offline brain means the app always works — including in a defense hall with no Wi-Fi — and it is the automatic fallback whenever the local model fails or returns invalid JSON.

## 6. Database
**users**: `id`, `username` (unique), `created_at`

**debates**: `id`, `session_id`, `user_id → users.id`, `motion`, `category`, `user_side`, `difficulty`, `rounds_played`, `hints_used`, `overall_score`, `scores_json`, `feedback_json`, `summary`, `transcript_json`, `created_at`

Debates in progress are kept in memory; only completed, scored debates are stored. Each save is a single transaction.

## 7. Scoring rubric
| Criterion | Offline evaluator looks at |
|---|---|
| Logic | Reasoning connectors ("because", "therefore", "this means"), argument length, repetition |
| Relevance | Overlap with the motion's key words in each turn |
| Evidence | Examples, sources, data words; penalty for statistics with no source |
| Clarity | Average sentence length, very short answers |
| Rebuttal quality | Rebuttal phrases + how much each turn engages with the AI's previous message |
| Persuasiveness | Combination of the above + persuasive framing; penalty for conceding |

The overall score is always recomputed by the code (never trusted from the model).

## 8. Known limitations
- The offline brain is pattern-based, not true language understanding.
- Unfinished debates are lost if the backend restarts.
- No authentication — usernames only.
- Local LLM speed depends on the laptop's RAM/CPU.

## 9. Future improvements
Voice input, timed rounds, team debates, exporting the scorecard as PDF, comparing scores across difficulty levels, proper login.
