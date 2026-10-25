# AI Web Bridge

Single-file local bridge that presents web-model and compatible API accounts through Anthropic- and OpenAI-compatible endpoints. The implementation, full requirement ledger, and working handoff are in `bridge.py`, `AI_Web_Bridge_Master_Prompt_v4.md`, and `HANDOFF_REPORT.md`.

## Current verification status

Version 7.55 keeps web login separate from optional learning. Accounts with an existing site recipe use the browser-backed web path by default; verified direct serving is an explicit owner choice. A fresh login for an unknown site is saved without probes, but Claude Code needs a site protocol recipe before it can send requests. The dashboard also includes native workspace selection and tool launch, account controls, route decisions, and selectable themes. No live-site, owner-Chrome, or model run is recorded.

See `HANDOFF_REPORT.md` for the evidence ledger, known gaps, and verification status.
