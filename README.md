# AI Web Bridge

Single-file local bridge that presents web-model and compatible API accounts through Anthropic- and OpenAI-compatible endpoints. The implementation, full requirement ledger, and working handoff are in `bridge.py`, `AI_Web_Bridge_Master_Prompt_v4.md`, and `HANDOFF_REPORT.md`.

## Current verification status

Version 7.61 streamlines account onboarding from the active Chrome tab, keeps that owner tab borrowed (never closes it), skips heavy capture for login-only flows, and adds an account connection check. Claude Code snippets now use the recognized `sonnet` alias while routing to the selected Bridge model/pool; full-access permission skipping is explicit and off by default. The account dashboard shows a compact start guide and keeps successful login green with `needs_learning` until the owner chooses learning. Earlier releases add independent Chrome-profile identities, optional learning, account deletion and pool strategies, workspace folder selection, themes, and responsive controls. Version 7.61 tests are pending the required source push. No real Chrome profile, real site, or model request has yet been verified.

See `HANDOFF_REPORT.md` for the evidence ledger, known gaps, and verification status.
