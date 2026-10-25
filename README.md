# AI Web Bridge

Single-file local bridge that presents web-model and compatible API accounts through Anthropic- and OpenAI-compatible endpoints. The implementation, full requirement ledger, and working handoff are in `bridge.py`, `AI_Web_Bridge_Master_Prompt_v4.md`, and `HANDOFF_REPORT.md`.

## Current verification status

The current base revision is 7.53. Its handoff record reports 440 offline tests passing with 5 environment skips. Version 7.54 is in progress: it adds optional per-account learning, native workspace selection and launch, merged account/advanced controls, recent routing decisions, and selectable themes. The 7.54 tests have not yet been run; no end-to-end run against a real site, the owner's Chrome, or a real model has been recorded.

See `HANDOFF_REPORT.md` for the evidence ledger, known gaps, and verification status.
