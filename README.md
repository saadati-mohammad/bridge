# AI Web Bridge

Single-file local bridge that presents web-model and compatible API accounts through Anthropic- and OpenAI-compatible endpoints. The implementation, full requirement ledger, and working handoff are in `bridge.py`, `AI_Web_Bridge_Master_Prompt_v4.md`, and `HANDOFF_REPORT.md`.

## Current verification status

Version 7.61 streamlines account onboarding from the active Chrome tab, keeps that owner tab borrowed (never closes it), skips heavy capture for login-only flows, and adds an account connection check. Claude Code snippets now use the recognized `sonnet` alias while routing to the selected Bridge model/pool; full-access permission skipping is explicit and off by default. The account dashboard shows a compact start guide and keeps successful login green with `needs_learning` until the owner chooses learning. Earlier releases add independent Chrome-profile identities, optional learning, account deletion and pool strategies, workspace folder selection, themes, and responsive controls. Verification: `py_compile` passed; full offline selftest passed 449 tests with 5 environment skips. An isolated local app smoke check returned `/health` OK and dashboard HTTP 200. Real Chrome profile/site/model operation remains unverified.

See `HANDOFF_REPORT.md` for the evidence ledger, known gaps, and verification status.
