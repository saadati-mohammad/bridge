# AI Web Bridge

Single-file local bridge that presents web-model and compatible API accounts through Anthropic- and OpenAI-compatible endpoints. The implementation, full requirement ledger, and working handoff are in `bridge.py`, `AI_Web_Bridge_Master_Prompt_v4.md`, and `HANDOFF_REPORT.md`.

## Current verification status

Version 7.58 adds independent Chrome-profile identities and extension pairings, profile-bound login requests that the owner confirms in the extension, and per-account Chrome-profile assignment. Login stays separate from optional learning. The integrated dashboard manages enabled accounts and an explicit Claude Code account pool with fixed, automatic, rotation, failover, measured-latency, best-fit, and manual-approval strategies. The workspace picker, API-key selector, selected pool model, direct app launch, and copyable command are included. Implementation has been pushed before tests; the 7.58 suite is pending. No live Chrome profile, real site, or model request has yet been verified.

See `HANDOFF_REPORT.md` for the evidence ledger, known gaps, and verification status.
