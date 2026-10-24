# AI Web Bridge

Single-file local bridge that presents web-model and compatible API accounts through Anthropic- and OpenAI-compatible endpoints. The implementation, full requirement ledger, and working handoff are in `bridge.py`, `AI_Web_Bridge_Master_Prompt_v4.md`, and `HANDOFF_REPORT.md`.

## Current verification status

The project is version 7.36. The code compiles and the quick self-test passes. The latest full offline self-test ran 421 tests with 3 failures and 5 skips, so this revision is not release-ready. No end-to-end run against a real site, the owner's Chrome, or a real model has been recorded.

See `HANDOFF_REPORT.md` for the evidence ledger, known gaps, and the next required step: make the full suite deterministic and green before wiring O29 live promotion.
