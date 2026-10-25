# AI Web Bridge

Single-file local bridge that presents web-model and compatible API accounts through Anthropic- and OpenAI-compatible endpoints. The implementation, full requirement ledger, and working handoff are in `bridge.py`, `AI_Web_Bridge_Master_Prompt_v4.md`, and `HANDOFF_REPORT.md`.

## Current verification status

Version 7.56 keeps web login separate from optional learning. Newly added web accounts default to browser-backed serving; previously saved accounts keep their current transport setting. A fresh login for an unknown site is saved without probes, but Claude Code needs a site protocol recipe before it can send requests. The dashboard also includes native workspace selection and tool launch, account controls, route decisions, and selectable themes. No live-site, owner-Chrome, or model run is recorded.

See `HANDOFF_REPORT.md` for the evidence ledger, known gaps, and verification status.
