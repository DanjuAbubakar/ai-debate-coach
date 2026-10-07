# Test Checklist (Week 10)

Automated tests: `python -m pytest -v` (see `tests/`). Manual checks are below.

## Normal use
| # | Test | Expected | Automated? | Pass? |
|---|---|---|---|---|
| 1 | Start a debate with a starter motion | AI gives an opening for the opposite side | ✅ | |
| 2 | Start with a custom motion | Works, uses generic argument bank | | |
| 3 | Choose For | AI argues Against (and vice versa) | ✅ | |
| 4 | Send an argument | AI quotes your main claim and counters it; round moves on | ✅ | |
| 5 | Reach the last round | AI gives a closing statement; input box disappears | ✅ | |
| 6 | End debate | Scorecard with 6 scores, strengths, weaknesses, recommendations | ✅ | |
| 7 | Name entered | Debate appears in History & Progress | ✅ | |
| 8 | Hint | Coach hint shown; round does NOT move on | ✅ | |
| 9 | Round 2 | Coach's note appears | ✅ | |
| 10 | Difficulty levels | Advanced replies are longer and demand evidence; Beginner is simpler | | |
| 11 | Stats | Average, strongest/weakest, charts, progress summary | ✅ | |

## Edge cases
| # | Test | Expected | Automated? | Pass? |
|---|---|---|---|---|
| 12 | Empty message | Rejected with a clear message | ✅ | |
| 13 | Message over 2000 characters | Rejected | ✅ | |
| 14 | "Ignore previous instructions…" | AI stays in role, round not counted | ✅ | |
| 15 | Insult | Warning, not counted | ✅ | |
| 16 | "I give up" | Encouragement to continue | ✅ | |
| 17 | "Write me a poem" | Steered back to the motion | ✅ | |
| 18 | Same argument twice | Asked to develop it, not counted | ✅ | |
| 19 | Statistic with no source | AI asks for the source | ✅ | |
| 20 | Unsafe motion | Rejected | ✅ | |
| 21 | End with zero arguments | Rejected | ✅ | |
| 22 | Backend stopped | Frontend shows "Backend offline" message, no crash | | |
| 23 | Ollama stopped mid-debate | App switches to Offline Brain automatically | | |

## AI quality checks
| # | Check | How | Pass? |
|---|---|---|---|
| 24 | Strong argument scores higher than weak | `test_strong_beats_weak` | |
| 25 | Same transcript → same scores (offline) | `test_scoring_is_deterministic` | |
| 26 | Invalid LLM JSON handled | `test_parse_llm_bad_json` | |
| 27 | AI never switches sides | Run 5 debates per category, read replies | |
| 28 | Replies stay on topic & reasonable length | Same as above | |

## User testing notes
| Tester | Confusing points | Fix planned |
|---|---|---|
| | | |
| | | |
