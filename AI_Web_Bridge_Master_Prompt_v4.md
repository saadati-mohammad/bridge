# AI WEB BRIDGE 7 — MASTER IMPLEMENTATION PROMPT (v7: BRAIN-DRIVEN LEARNING, group O24-O29, owner decision 7.33; v6: browser = the owner's own Chrome, NO Playwright; v5: v4 + group O onboarding/reverse-engineering/portability/autonomy + lean-work discipline §0A)

Attach `bridge.py` (AI Web Bridge 7, ~3,500 lines) together with this prompt. This prompt is self-contained. Everything the owner has asked for is listed here with a stable ID. Do not rely on any other message.

> **OWNER OVERRIDE (2026-10-25, updated for 7.64):** The owner's latest implementation request supersedes older workflow/scope instructions in this file and `HANDOFF_REPORT.md`. Keep web login independent from optional, owner-started per-account learning; login confirmation immediately saves the account/session and reuses an existing site recipe when present. A new unknown web account is immediately usable through its assigned personal Chrome tab for Claude Code; `needs_learning` means the optional optimized protocol is not learned, not that login cannot be used. Learning may add a faster direct protocol and only starts by owner choice. For generic UI serving, never inspect text inside the editable composer as a CAPTCHA/challenge signal; extract ChatGPT answers from assistant-message nodes rather than whole-page text diffs; preserve an already-open authenticated Chrome tab when starting requests. Do not switch accounts to Playwright. Use the owner's personal Chrome only: setup never opens a default profile automatically. Support independently paired Chrome profiles. Primary onboarding is: owner opens the desired AI site in the desired profile, then clicks “Add this site from current tab” in the Bridge extension; the selected tab is borrowed/consented, never Bridge-owned or closed. Confirmation is enabled only from that same tab. Keep login-only fast and skip request recording/analysis; learning starts only on the owner's explicit choice. Keep `needs_learning` visible after login-only success, but use success-green styling to indicate the web login/session was saved; never mislabel it as learned-protocol-ready. Integrate profile, account enablement, learning, delete/test-connection actions, and Claude Code account-pool strategy controls into the responsive, themeable dashboard. Let the owner choose accounts and selection strategy (fixed, automatic, rotation, failover, latency/best-fit, or manual approval); use only explicitly selected/enabled eligible accounts, preserve key pins and cooldowns, and never bypass provider challenges or account-wide restrictions. Claude Code commands use the recognized `sonnet` alias mapped through Bridge; do not set self-referential `ANTHROPIC_DEFAULT_*_MODEL` aliases. Expose full-access permission skipping as an explicit, off-by-default checkbox. The workspace picker, app selector, one-click open, copy command, and explicit Bridge API-key selector remain first-class controls. Commit and push implementation before tests. Update this prompt and handoff whenever they conflict with this override.
>
> **BOUNDARY:** Account pools only contain accounts the owner explicitly selected and enabled. Respect account-wide cooldowns, hard stops, challenges, and provider restrictions; never conceal a restriction or automate CAPTCHA/MFA. Rotation is an owner-selected workload strategy among eligible accounts, not permission to replay an ambiguous request or bypass a provider-wide restriction. Dashboard text may be localized; internal identifiers and evidence remain English.


> **BROWSER RULE (owner decision, overrides every Playwright mention below; v6, refined 7.61).** Playwright is NOT used by default: browser work runs in the owner's OWN Chrome through the bundled Manifest-V3 extension. Setup never launches Chrome; the owner chooses profiles and pairs the extension independently in each. The extension has a stable per-profile identity and token; commands, events, tabs, and login confirmations are isolated by that identity. An account is assigned to one paired profile; never imply that shared Chrome cookies are isolated when two accounts use the same profile. Primary flow registers the owner-selected active AI-site tab directly; the tab is consented/borrowed and must never be closed by Bridge. Confirmation is enabled only when that exact tab is active. A queued login/claim flow remains available for dashboard-created accounts. `BRIDGE_BROWSER=playwright` remains an explicit opt-in only, never a default or silent fallback. UI tests needing a real Chrome are reported as not run when none is available.
>
> **LEARNED-SITE RULE (owner).** Once a site is learned, answers must not use the browser. Before the browser steps aside the bridge must check that the learned recipe works without it (direct, then page); the browser tier stays only for what does not verify. Promotion to `stable_direct` happens only through the O8 battery, and the O8/O9 scheduler must run in the live program (not only in tests).
>
> **BRAIN RULE (owner decision 7.33, v7).** Learning a site is NOT a fixed, hard-coded procedure. When an account is connected to a web model, that model is a *reasoning brain*: the bridge uses it as the engineer that investigates the site (what the traffic and the front-end source mean, how a token is made, how a conversation continues) and writes the clean native modules (O18). The bridge supplies only the *tools* (bounded, read-only evidence views; deterministic replay experiments), the *gates* (secret guard, AST allow-list, sandbox, >= 3-capture cross-check, O8 battery, code-quality gate) and the *budget* (O6). The brain's opinion never promotes anything: only the deterministic gates do. No per-site knowledge and no site or provider name may be hard-coded (B7 applies to the learning procedure too). Continue O24-O29 work after the owner's 7.58 account/profile/workspace requirements are implemented and pushed; the owner's latest request has priority over the older dashboard order.

---

## 0. READ THIS FIRST — HOW YOU MUST WORK (anti-forgetting protocol)

The owner has had repeated problems with coding assistants forgetting requirements halfway through long jobs. This section exists to make that impossible. It is mandatory.

1. **Create a scratch folder outside the deliverable** (for example `./_work/`). It is for you only and is NOT part of the final product. In it keep:
   - `LEDGER.md` — copy of every requirement ID from Section 4 with a status column: `TODO | IN-PROGRESS | DONE | PARTIAL | BLOCKED`, a one-line evidence pointer (test name, line range, command output), and notes.
   - `BASELINE.md` — your findings from Phase 1.
   - `DECISIONS.md` — every non-trivial engineering decision and the reason.
   - `CHANGELOG.md` — what changed, in order.
2. **At the start of every phase, and again every time you have edited more than ~300 lines, re-read `LEDGER.md` and Section 4 of this prompt.** Say which IDs you are working on before you work on them.
3. **A requirement is only `DONE` when there is evidence** (a passing automated test, or a recorded manual check with exact command and output). "I wrote the code" is `IN-PROGRESS`, never `DONE`.
4. **Before finishing, run a full ledger audit**: walk every ID, re-open the code that implements it, and re-run its test. Fix anything that regressed. The final report must contain the full ledger table.
5. If your context is getting long, summarise into the scratch files first, then continue. Never silently drop a requirement because it is hard. Mark it `PARTIAL` or `BLOCKED` with the reason.
6. Never ask the owner to approve ordinary engineering choices. Decide, record the decision in `DECISIONS.md`, move on. Ask only if something is truly impossible without information only the owner has (e.g. a login).

---

## 0A. WORK DISCIPLINE — IMPLEMENT FIRST, TEST LEAN, QA AT THE END (owner's explicit instruction; overrides every "run the full suite" sentence elsewhere)

The owner has watched assistants burn most of their tokens and time on testing while little was built. Quality still matters, so testing is moved to where it is cheapest and most valuable.

1. **Implementation phases (everything before the QA campaign): at least ~80% of effort goes into writing the feature.** After an edit batch run only a *smoke check*: `python -m py_compile bridge.py`, then `python bridge.py --selftest --quick` (build this flag in your first phase: imports, starts the server on a free port, one request through the mock site, shuts down; target < 10 s). Add at most 2–4 small, focused tests *with* each feature (they are the feature's acceptance evidence), and run only those plus the tests of code you touched.
2. **Do not** in implementation phases: run mutation testing, repeated or parallel suite runs, fuzzing, exhaustive scenario matrices, or write a test that duplicates the risk another test already covers. One test per distinct risk.
3. **Time-box failures:** a failing test gets one real fix attempt and one re-run. If it still fails, record it in `LEDGER.md` as `PARTIAL` with the failing test name, move on, and settle it in the QA campaign.
4. The full suite runs at most: once when you change shared core (Router.handle, Store, protocol writers), once at the start of the QA campaign, once before delivery.
5. **QA campaign (Phase 10, near the end, once the implementation is essentially complete).** Create `_work/QA.md`: a numbered list of QA phases (Q1 startup/persistence/migration · Q2 onboarding + login on the mock · Q3 reverse-engineering pipeline and promotion to stable-direct · Q4 direct-tier stability and fallback/repair · Q5 routing, rotation and smooth failover · Q6 failure injection · Q7 context/continuity/budgeting · Q8 Claude Code transcript end-to-end on both protocols with a route change · Q9 security · Q10 resource/leak · Q11 dashboard render and controls · Q12 portability (copy the folder to a fresh directory/host)). For each: goal, exact commands, pass criteria, result `[x]` pass / `[ ]` fail, and the fix + re-check when it fails. Walk them in order, really run them, tick or reject honestly, and do not stop until every box is ticked or explicitly marked BLOCKED with a reason. Every test in the QA campaign must name the risk it covers; delete tests that cover none. This is where mutation checks (deliberately break the code, confirm a test fails) are allowed — only for critical paths (routing, state, persistence, security, protocol).
6. Keep the QA campaign sharp: no filler runs, no re-running green areas without a code change, no redundant matrices. Quality is guaranteed by *targeted* checks, not by volume.

---

## 1. YOUR ROLE AND THE MISSION

Act as a principal engineer with deep experience in: Python concurrency, HTTP/SSE servers, LLM API protocols (Anthropic Messages, OpenAI Chat Completions), browser automation (Playwright), reverse-engineering web-app network traffic, agent harness design (tool calling, context management), reliability engineering, security review, and test engineering.

You are not asked to review, advise, or produce a roadmap. **You are asked to modify the real code, run it, test it, and hand back a better working application.**

### What the product is

AI Web Bridge turns chat websites that the owner is logged into (DeepSeek, ChatGPT, LMArena, DesignArena, and any others added later) into a local standard API, so that **Claude Code** (Anthropic `/v1/messages`) and OpenAI-compatible tools (Cursor, VS Code agents) can use them as their model. Its history: it started as "DeepSeek Local Bridge V6.11" (browser-driven, one site) and is now a multi-site, recipe-learning, single-file bridge.

### What the owner wants (in the owner's own priorities)

1. **Output quality as close as possible to, or better than, dedicated coding agents (Codex, Antigravity)** when Claude Code runs on top of these web chats. Quality is dominated by: tool-call reliability, no information loss in context, correct streaming, choosing the right model, and low latency. Section 6 turns this into engineering work.
2. **The browser is used only to log in and to learn.** After that, requests go directly to the site's own services (the existing `direct` tier), with `page` and `ui` tiers only as verified fallbacks. Do not relaunch browsers per request.
3. **No wasted usage.** No resending huge message history, no new chat for every request, no unnecessary file uploads, no pointless probes/retries/health checks.
4. **Every account has its own dynamically discovered list of models/modes.** Nothing about model names is hard-coded. The dashboard builds its selectors from what was discovered. The user can pick a fixed model, an automatic policy, or a rotation pool, and can always see exactly what is being used.
5. **Rotation and failover that do not break work in progress**, including when a limit is reached mid-task.
6. **Easy to add other providers later** without touching routing code.
7. **Honest errors** that show what actually failed (not generic "upstream error").
8. **Light on system resources** and robust (not fragile).
9. **Deliverable stays ONE Python file.**

### 1.1 The owner's charter in plain words (source of truth — do not lose any of this)

1. **Use Claude Code on top of web-chat accounts and make it work at least as well as, and where possible better than, Claude Code with a paid API key** — in output quality of the whole agent loop, in speed, and in user experience.
2. **The goal is not more lines of code.** The goal is to remove the owner's real problems and raise quality dramatically. Think beyond what is written here: if you see a scenario, failure mode, or stronger idea the owner did not think of, **handle it and record it in `DECISIONS.md` as "ADDED BY AGENT"** (and put it in the ledger with an ID starting `X`).
3. **Use the chat's server-side memory where it can be trusted**, so history is not resent over and over. Where trust is not established, fall back to local reconstruction.
4. **Never do an action that makes the site restrict the account.** Example given by the owner: ChatGPT converts a long paste into a file attachment, and after a few messages the attachment quota is exhausted and the chat is dead. Prefer sending text as plain text whenever possible. That was described as a *very simple* example: find and handle all the other situations of the same family (Section 4-N).
5. **The bridge connects to any website**, each used differently (DeepSeek, ChatGPT, LMArena, DesignArena, and unknown future ones). Some sites offer many models. The bridge must rotate between models, **even in the middle of a task when a limit is reached, without breaking the work**.
6. **Everything is dynamic.** The dashboard lets the user choose, per account and according to what that account really offers, a specific model, a combination/pool, or automatic mode — and shows exactly what is being used when it is automatic. What the dashboard shows is produced dynamically per logged-in account (including with help from the AI connected to that account, validated against evidence). **Absolutely nothing about models is hard-coded.**
7. **Final deliverable: one single Python file.**

### 1.2 What "better than Claude Code with an API key" can honestly mean

The bridge cannot make a model smarter than it is. It **can**: waste none of the model's ability (no truncation, no lost history, no malformed tools, no stalled streams), remove round-trips (parallel tool calls, delta context, local dedupe), pick the best available model per request from many accounts/sites, survive limits and outages that would stop a single-key setup, and make everything visible. Success is measured, not claimed: the report must show before/after numbers on the same workloads and must not claim superiority over any product without a fair comparison you actually ran.

### 1.3 Engineering targets (measured on the offline mock, reported as measured values — targets, not promises)

- Tool-call validity on the corpus ≥ 99% after at most one bounded repair; zero invented tool results.
- Payload sent on turns 2..N with a trusted remote conversation: ≥ 80% smaller than full-history replay (report the real number).
- Zero requests that quota-consume while the bridge is idle.
- Bridge-added overhead p95 ≤ 50 ms (excluding upstream).
- 0 bridge-caused malformed streams across the protocol fuzz tests; 0 duplicated or spliced answers.


---

## 2. NON-NEGOTIABLE RULES

### 2.1 Deliverable
- The final product is **exactly one `.py` file** (keep the name `bridge.py` unless there is a strong reason; if renamed, say so). No new application modules, no helper scripts required at runtime, no ZIP, no patch-only output.
- Third-party packages are allowed only where already used (none required; Playwright only on explicit opt-in) or clearly justified; document them. Prefer the standard library. Do not vendor libraries.
- Runtime data stays in the existing data directory (`bridge_data`, overridable by `BRIDGE_HOME`). Never embed credentials, cookies, or user data in the source.
- A self-test suite may live **inside** the same file and be invoked with a CLI flag (e.g. `python bridge.py --selftest`). That is allowed and encouraged because it keeps the single-file rule. Keep it importable-safe: nothing executes on import except definitions.

### 2.2 Safety of existing work
- Before editing: copy the original to `bridge.orig.py` (scratch folder), and if Git exists, branch first. Never overwrite the owner's `bridge_data`. Run all tests against a **temporary** `BRIDGE_HOME`.
- Existing config, `accounts.json`, sessions, recipes, `docs/`, `tools/`, and browser profiles must keep working after the upgrade. Add schema versions and one-way migrations that **back up first**. Never silently reinterpret an existing account as "unrestricted auto-routing" — migrate it to an explicit policy that preserves current behaviour.
- Preserve every working feature (see inventory in 3.1). Do not remove features to simplify.

### 2.3 Honesty
- Never claim a test passed unless you ran it and saw it pass. Never claim a live provider, login, model, or quota behaviour was verified unless it really was. You probably have no logins: say so, and prove behaviour against the mock site (Section 7) instead.
- No fabricated metrics: no invented token usage, quota balances, latency, "intelligence scores", or benchmark wins. Label estimates as estimates.
- No placeholders, fake success paths, swallowed exceptions, decorative dashboard buttons, `TODO` for required behaviour.

### 2.4 Provider boundaries
- Work only inside the owner's own authorised sessions. Do not defeat CAPTCHAs, bot protection, paywalls, or explicit quota enforcement. A CAPTCHA/verification page is handed to the HUMAN in a visible browser (O7); the bridge never solves it, never installs stealth/fingerprint-spoofing tooling, and never hides automation from a site's protection. Replaying the owner's own session with the headers/cookies that browser itself sends is the direct tier and is allowed; some sites forbid automated access in their terms and may restrict accounts - show the owner a one-time per-site notice in the dashboard (O12). Do not impersonate other identities, replay requests to dodge limits, or manipulate cookies to bypass limits.
- Moving work to **another model that the owner has legitimately configured** (same account's other model, or another account the owner owns) is allowed *according to the owner's routing policy*, and must be visible. An account-wide restriction is respected (cooldown / wait / policy-approved alternative route), not disguised by cycling model names.

---

## 3. PHASE 1 — BASELINE (do this before changing anything)

Read **all** of `bridge.py`. Then write `BASELINE.md` and run baseline checks (`python -m py_compile bridge.py`, a launch against a temp `BRIDGE_HOME`, a `GET /v1/models`, and a simple mocked request if you can already build one).

### 3.1 Feature inventory to preserve (verify each; mark working / partial / broken / unverified)
- Local HTTP server (`ThreadingHTTPServer`), loopback binding, host check (`_host_ok`), admin key + client API keys (`Config`, `find_key`), per-key account pinning.
- Anthropic `/v1/messages` (stream + non-stream), `/v1/messages/count_tokens`, OpenAI `/v1/chat/completions`, `/v1/models`.
- Claude Code startup shortcuts in `Handler._chat` (the "quota" probe with `max_tokens<=1`, the title-generation shortcut). Keep working; make them robust and non-hijacking of real requests.
- Account lifecycle: add (browser login), relogin, relearn, remove, `add_api` (official API accounts via `ApiBackend`), job progress (`Job`), health loop, `auto_relearn`, cooldowns.
- Recipe learning: `Capture`, `run_probe`, `derive_recipe`, `validate_recipe`, `verify_recipe`, `_ai_repair`, `storage_source`/`resolve_source`, per-host `docs/<host>.md` and `tools/<host>_client.py` generation.
- Transports/tiers: `DirectTransport`, `PageTransport`, `UIBackend`, `TIER_CHAIN`, automatic downgrade in `Accounts.on_error`.
- Protocol layer: `normalize_anthropic`, `normalize_openai`, `build_prompt`, `tools_text`, `parse_tool_calls`, `TextGate`, `AnthropicWriter`, `OpenAIWriter`.
- Conversation continuity: `Router._take/_put`, `ConvEntry`, delta prompts, history summarisation, response cache.
- Dashboard API (`Handler._api`) and the dashboard HTML/JS.

### 3.2 Suspected defects and weaknesses already seen by static reading
These came from a read of the file. **Verify each one yourself, then fix or refute it.** Line numbers are approximate.

| # | Where | Suspicion |
|---|-------|-----------|
| D1 | `Accounts.choose` (~2307) | The request's `model` string is used as an *account selector* by substring-matching account id/label/host. There is no model entity at all. Two accounts of one site, or a model name that happens to be a substring of a host, resolve ambiguously. Unresolvable requests may silently fall back to any account. |
| D2 | `Handler._v1` `/v1/models` (~3064) | Lists `bridge-auto` plus account *labels*, not models. Ignores which API key may use which account. |
| D3 | `Router.handle` cache (~2799) | Cache key = system + message sigs + tool names + tool_choice + pinned account. It omits resolved model/route, `max_tokens`, temperature, stop sequences, tool schemas (only names), and API-key identity. It also caches responses that contain **tool calls**. Risk: wrong reuse, cross-key leakage, replayed side effects. |
| D4 | `msg_sig` (~2543) | Tool-result content is cut to 1500 chars before hashing, so two different long tool results with the same first 1500 chars collide; continuity may then wrongly treat history as unchanged. Tool signature uses `description[:200]`. |
| D5 | Truncation everywhere | `trim_middle` is applied to system prompt (`system_limit` 12000), tool results (`result_limit` 20000), history (`history_limit` 60000 chars), tool descriptions (`tool_desc_limit` 500), history-summary input (1500 per message / 30000 total), summary output (3000). Images become `[image omitted]`. Critical content (an error at the middle of a log, a schema detail) can be lost silently, and measured in characters not tokens. |
| D6 | `Router._take/_put` | Continuity is an in-memory exact-prefix match per account, max 40, lost on restart, keyed only on hashes that include the truncated sigs above. No notion of "how much do I trust the remote chat still contains this". |
| D7 | `Router._summary` | Spends an extra model request in a brand-new chat to summarise, silently returns `""` on failure, and the summary is injected as if authoritative. |
| D8 | `Router.handle` retry loop | Up to 4 attempts; error classification is coarse (`BridgeError.kind`). Rate-limit always puts the **whole account** in cooldown (`on_error`) even when it may be model-scoped. 3 consecutive non-auth failures trigger `auto_relearn`, which could be caused by a network blip. Retry after partial output is blocked (good) but there is no ambiguity handling for "request may have been accepted upstream". |
| D9 | Shared mutable state | `Router.stats`, `Accounts.inflight`, account dicts (`requests`, `streak_fail`, `cooldown_until`, `ema_ms`) are mutated from multiple request threads, many without a lock. `Router.cache`, `Router.summaries` are plain dicts. Check for races. |
| D10 | `Accounts.sem` (~2329) | Semaphore size is set from the tier at first creation and never updated when the tier changes. |
| D11 | Usage numbers | `est_tokens = len/3.6` is returned to clients as `usage` in both protocols as if it were real. Must be clearly estimated or omitted per protocol rules. |
| D12 | Request parameters | Check whether `max_tokens`, `temperature`, `top_p`, `stop`, `response_format`, `tool_choice`, `thinking`, `cache_control`, `metadata`, `parallel_tool_calls` are honoured, translated, or silently dropped on the text-backend path. |
| D13 | Streaming writers | Audit `AnthropicWriter` / `OpenAIWriter` / `TextGate` against the real event grammars (see 10.x). Check: `message_start`/`content_block_*`/`message_delta`/`message_stop` order, `input_json_delta` for tool args, `stop_reason` mapping (`end_turn`, `tool_use`, `max_tokens`, `stop_sequence`), OpenAI `finish_reason`, `[DONE]`, error mid-stream, double terminal events, UTF-8 split across chunks, CRLF. |
| D14 | `StreamDecoder` | Verify handling of chunk boundaries, multi-line `data:`, comments, partial JSON, EOF without terminator. |
| D15 | Dashboard / local security | Audit `_host_ok`, Origin/CSRF protection on state-changing `POST/DELETE`, admin-key handling, secrets in account serialisation (`Accounts.public`), `innerHTML` use with untrusted labels/errors (XSS), SSRF in `add_api`/recipe URLs/redirects, path handling for `docs/` and `tools/` generation, file permissions of session/cookie files (`Store.write(..., private=True)`). |
| D16 | Recipe model coupling | Recipes are per **host**, not per model. A learned recipe knows one chat endpoint; nothing records *how the site selects a model* (body field, URL, header, UI dropdown). That is the root reason dynamic models do not exist yet. |
| D17 | `ApiBackend.complete` | Check parameter mapping, tool-call streaming, error mapping, and whether a user-supplied base URL is validated. |
| D18 | Long text on UI tier | `ui_type_and_send` types/pastes text into the page. Sites commonly convert long pastes to attachments or reject them. No detection, no policy. |
| D19 | Error opacity | Errors reach the client as short messages without a stable category, evidence, or "which account/route/model". The owner explicitly complains they cannot see what failed. |

Record additional defects you find. Prioritise: (1) data/state corruption, (2) malformed protocol output, (3) lost context, (4) duplicated side effects, (5) secret/account leakage, (6) wrong model/account selection, (7) performance/resources, (8) UX.

---

## 4. REQUIREMENT LEDGER (every item is mandatory unless marked OPTIONAL; groups A–O plus any X-items you add)

Each requirement has an ID. Track them all in `LEDGER.md`. "Acceptance" is the minimum evidence for `DONE`.

### A. Foundation, data model, and migration

**A1 — Separate the concepts.** Introduce explicit, validated structures (dataclasses or equivalent, JSON-serialisable) for: `Provider/Site`, `Account`, `ModelVariant`, `Route`, `RoutingPolicy`, `RouteDecision`, `Capability`, `SiteProfile`, `TaskState`/`ConversationState`, `ToolCallState`, `RequestTrace`. A route = (account, model variant, adapter tier, execution config). Account ≠ model ≠ route ≠ policy.
*Acceptance:* unit tests for construction/validation/serialisation round-trip; no code path uses a display label as an identity.

**A2 — Stable identifiers.** Define and document a stable, unambiguous ID format, e.g. `acct:<id>/model:<variant-id>` and a public alias syntax for clients (see C4). IDs never depend on display labels.
*Acceptance:* test that renaming a label or a model display name does not change its ID; ambiguous input is rejected.

**A3 — Schema versioning and migration.** Version `config.json`, `accounts.json`, recipes, catalogs, routing policies, task states. Add a migration framework that backs up before migrating, preserves unknown fields, never resets to defaults on a missing field, and refuses to start with an actionable message if a critical file is corrupt (keeping a `.corrupt` copy).
*Acceptance:* tests migrating a fixture of the original 7.0 data layout; corrupt-file test; unknown-field preservation test.

**A4 — Atomic, safe persistence.** Atomic writes (temp + fsync + replace), restrictive permissions for secrets, file locking or a single writer for shared files, bounded retention for logs/history/traces.
*Acceptance:* crash-simulation test (write interrupted), concurrent-write test.

### B. Dynamic discovery of models, modes, and capabilities

**B1 — Per-account model catalog.** Each account owns an independent catalog of `ModelVariant`s with: stable ID, display name, provider-native model identifier **only if genuinely observed**, mode/variant (e.g. normal vs. deep-thinking vs. search toggle), capabilities, discovery source, discovered-at, last-verified-at, status (`unknown | discovering | available | degraded | unavailable | stale | requires_auth`), confidence (`verified | observed | inferred | unknown`), known constraints, failure history, observed latency stats.
*Acceptance:* two accounts on the same site can hold different catalogs; catalog persists across restart.

**B2 — Discovery sources, in order of preference.**
1. an official/documented model-list endpoint (for `api` accounts and any site that exposes one);
2. model/mode options that the site's own network responses expose (observed in traffic captured during login/learn, e.g. a "list models" or "user config" JSON call) — **extend the recipe format so such a call can be recorded and replayed at the `direct` tier without a browser**;
3. the model/mode selector as rendered in the site's UI (dropdown items, toggles) — read via the existing browser machinery, headless, only at discovery time;
4. a controlled, explicitly-disclosed probe only if nothing above works.
Never guess an endpoint, never invent a model name, never infer the hidden model from the answer text.
*Acceptance:* mock site (Section 7) exposes models via (a) a JSON endpoint, (b) only a UI dropdown, (c) neither; each yields a correct, honestly-labelled catalog; (c) yields `unknown` rather than made-up entries.

**B3 — LLM-assisted discovery with evidence validation.** The owner's idea: the AI behind the connected account can help interpret what the site offers. Reuse the existing `_ai_repair` pattern: when deterministic extraction fails, show the connected model the captured evidence (sanitised DOM snippets / network JSON, secrets masked via the existing `mask`/`build_evidence` approach) and ask for a catalog proposal as strict JSON. **The proposal is never trusted directly**: every proposed entry must be validated against the evidence (the label really appears in the DOM/network data; the selection mechanism really exists). Unvalidated entries are dropped or stored as `unknown`. "The model proposes, the evidence disposes."
*Acceptance:* test where the model proposes one real and one hallucinated model; only the real one survives.

**B4 — How a model gets selected on the wire (recipe extension).** Extend recipe learning (`derive_recipe`, `validate_recipe`, `verify_recipe`, `RecipeClient`, `UIBackend`) so that, per site, the recipe records the **model-selection mechanism**: a body field/path, URL segment, header, a prior "set model" call, or UI selector steps — each with a template variable the router can fill from the chosen `ModelVariant`. Learning should observe a model change (when the site offers one) the same way it already observes per-chat/per-turn state: two probes with different selections, diff the traffic.
*Acceptance:* mock site whose body has `"model":"x"` and one whose model is chosen via a separate call; both are learned and replayed with the selected variant; request actually sent contains the chosen variant (assert on the mock's received traffic).

**B5 — Capability registry.** Per variant (not per site), tri-state `supported | unsupported | unknown`, never collapsing unknown into supported: text in/out, streaming, system prompt, native tool calling vs. emulated tools, image input, file input, structured output, thinking/reasoning mode, server-side conversation continuity, max context/output (if known), stop sequences, usage reporting, cancellation.
*Acceptance:* routing excludes a route lacking a *required* capability and treats `unknown` according to policy (default: allowed but flagged, never reported as verified).

**B6 — Refresh lifecycle.** Discover on account add/login, on explicit refresh, on session change, when stale (configurable TTL), when an upstream error says a model/parameter is gone, and when the dashboard opens the account panel (only if stale). Dedupe concurrent refreshes per account. No uncontrolled polling. A failed refresh **never erases** the last good snapshot; it marks it `stale` with the reason and time.
*Acceptance:* tests for add/remove/rename/changed-capability fixtures, timeout keeps previous snapshot, concurrent refresh runs once.

**B7 — No hard-coded model catalogs.** No list of model names or model capabilities in source, HTML, or JS. Site **presets** (URL shortcuts for "add DeepSeek / ChatGPT / LMArena / DesignArena") may exist as convenience only and must not carry model data. A scan test must grep the file for known model-name patterns and fail the build if they appear in logic or UI.
*Acceptance:* the grep test exists and passes.

**B8 — Per-site behaviour profile.** One versioned `SiteProfile` per site (and per account where behaviour differs), data-driven, recording: auth/session behaviour and expiry signals, how to submit a message (direct request vs. page vs. UI), streaming format, how conversation continuity behaves, whether long pasted text is converted to an attachment / what the size limits are, rate-limit error shapes, model-selection mechanism, known failure modes and recovery steps, last verified time, confidence, recipe/profile version. Site-specific workarounds live in the profile or in a clearly isolated adapter section — never scattered through routing/protocol code.
*Acceptance:* profile persisted and used by router/submission logic; a stale or invalidated profile triggers revalidation instead of blind use.

**B9 — Change detection.** Detect and record: a previously good recipe now returns a non-answer (e.g. a login page with HTTP 200), a model disappeared/renamed, stream format changed, auth began failing, a new capability appeared. Mark affected profile/recipe `stale`/`degraded`, keep last-known-good, allow rollback to a previous validated recipe. A 200 status is never proof of a valid answer.
*Acceptance:* mock site changes its response shape; bridge flags `stale`, does not use the broken recipe for routing, and surfaces the reason.

### C. Routing

**C1 — Policies as validated data.** Implement and persist these policies (default scope: global; overridable per account, per pool, per API key, and per request via alias):
- `fixed` — one exact route. Never silently substitutes. If unavailable → clear error, or ask-for-approval if configured.
- `auto` — best eligible route by policy/profile.
- `rotation` — user-approved pool; strategies `round_robin`, `least_loaded`, `least_recently_used`, `health_weighted`. Rotation unit configurable: per request / per conversation / per task.
- `failover` — primary + ordered, explicitly permitted backups.
- `lowest_latency` — only among eligible routes with enough latency samples.
- `best_fit` — by required capabilities and measured outcomes, never by model name.
- `manual_approval` — pause and ask before switching route.
*Acceptance:* a policy validator rejects impossible configs (deleted account, unknown variant, pool with zero eligible members) with a precise message; one test per policy.

**C2 — Execution profiles.** `fast`, `balanced` (default), `quality_first` on top of the same engine. `fast`: minimise discovery/retries/context transfer. `quality_first`: prefer variants with measured tool-call validity and task success, thinking modes where supported, larger context. Profiles adjust ranking weights (bounded, configurable) — they never override fixed pins, account restrictions, capability requirements, or security policy. Without evidence, selection is labelled "capability-based", not "best quality".
*Acceptance:* ranking test with fabricated telemetry fixtures; unknown metrics stay neutral.

**C3 — Eligibility before ranking.** Exclude a route when: account disabled or not `ready`; session expired; variant absent from the usable catalog or `unavailable`; recipe not validated; required capability unsupported; estimated context does not fit; cooldown/circuit-breaker open; concurrency cap reached; policy/key forbids it; manually excluded; data-transfer policy forbids it. Each exclusion carries a reason code.
*Acceptance:* test table covering each exclusion; "no eligible route" returns an actionable explanation listing why each candidate was excluded.

**C4 — Exact model resolution.** Replace the substring matching in `Accounts.choose`. The request's `model` is resolved by this order: exact route ID → exact pool/alias name → exact variant ID with unique account → documented aliases (`bridge-auto`, `bridge-fast`, `bridge-balanced`, `bridge-quality`, and `bridge-pool/<name>`). Anything unresolved, ambiguous, or outside the API key's permitted accounts returns a clear 4xx/model-not-found error — never a random account. **Claude Code sends real-looking Claude model names** (e.g. names of Anthropic models, plus a small/fast model for background tasks): provide a configurable *client-model-name mapping* (e.g. "any `claude-*` name → policy X; names containing a small-model marker → fast profile") that is data, not code, so Claude Code works out of the box without hard-coding provider models.
*Acceptance:* tests for each resolution rule, ambiguity, key restrictions, and Claude Code-style model names.

**C5 — `/v1/models` as a real catalog.** Return selectable routes/aliases/pools the calling key may use, with Anthropic-style and OpenAI-style shapes appropriate to the endpoint, and an extension field (or separate dashboard endpoint) with capabilities, status, confidence, staleness. Never list accounts/models a key cannot use.
*Acceptance:* tests per key restriction; shape tests for both protocols.

**C6 — RouteDecision records.** For every request store (bounded, secret-free): request ID, requested model/alias, resolved policy and profile, selected account/variant/tier, reason, excluded candidates with reason codes, confidence of model identity, whether it is a fallback, timings. Expose via dashboard and, optionally, response headers (e.g. `x-bridge-route`, `x-bridge-account`, `x-bridge-model`, `x-bridge-fallback`, `x-bridge-request-id`) so Claude Code logs/curl show what happened.
*Acceptance:* decision present for success and failure paths; headers present on non-stream and stream responses.

**C7 — Honest model identity.** Three separate fields everywhere: *requested* (what the client asked), *selected route* (what the bridge chose), *observed identity* (what the site actually revealed, with confidence). Where a site does not reveal the model (or reveals it only after the reply, as arena-style sites may), show `identity unknown` / `revealed after response` — never infer from reply text.
*Acceptance:* test with a mock site that hides identity and one that reveals it post-reply.

**C8 — Safe concurrency in routing.** All counters, cooldown state, rotation indices, semaphores, in-flight counts and stats are protected (locks/atomics) and tested under concurrent load. Semaphore size follows the current tier (fix D10). Rotation under parallel requests is deterministic and race-free.
*Acceptance:* a 200-request threaded test: rotation distribution correct, no negative counters, no lost updates, no deadlock.

**C9 — Ensemble is not rotation.** If multi-route "ensemble"/review is offered, it must be an explicit separate mode with bounded fan-out, separate state per route, attribution, and no duplicate side effects. Default: not offered. (OPTIONAL feature; but rotation must never accidentally fan out.)

### D. Failure handling and mid-task continuity

**D1 — Typed errors.** Replace coarse kinds with a stable taxonomy carrying: category, safe message, evidence (redacted), `retryable`, `scope` (`model | account | provider | network | request`), `auth_implicated`, `limit_confirmed`, `may_have_been_accepted`, `partial_output_sent`. Categories at minimum: `network_error, dns_error, timeout, upstream_unavailable, rate_limited_model, rate_limited_account, usage_cap_account, auth_expired, permission_denied, model_not_found, unsupported_capability, unsupported_parameter, invalid_request, context_too_large, content_blocked, tool_call_invalid, malformed_response, empty_response, stream_interrupted, recipe_invalid, challenge_required, unknown`. Each site's error shapes map to these through its `SiteProfile`.
*Acceptance:* table-driven classification tests including ambiguous messages that must classify as `unknown`/low confidence rather than "quota".

**D2 — Scope-aware limits.** A model-scoped limit cools down only that route; an account-scoped limit cools the account; ambiguous → conservative, single-route, short, with recorded uncertainty; never loop through every model hoping one works. Honour `Retry-After` and site-provided reset times when present. No exact quota balances unless the site exposes them.
*Acceptance:* tests for each scope; test proving a model-limit does not mark sibling models unhealthy.

**D3 — Bounded retry with backoff, jitter, circuit breaker.** Global per-request retry budget and deadline; exponential backoff with jitter for transient errors only; no retry for invalid-request/permission/unsupported; per-route circuit breaker (closed → open → half-open with a single probe). Fix D8: transient network blips must not trigger `auto_relearn`; relearn only on evidence of recipe invalidity.
*Acceptance:* deterministic tests with a fake clock.

**D4 — Failover only at safe boundaries.**
- Before any byte reached the client and the failure is recoverable and policy permits → switch route, preserving request semantics.
- After streamed output/tool-call fragments reached the client → **do not** restart on another model and splice. Terminate honestly via the protocol's error mechanism (Anthropic `error` event; OpenAI error chunk then `[DONE]`), keep task state, and let the next request continue from checkpoint.
- If upstream acceptance is uncertain (request sent, response lost) → do not blindly resend; reconcile if the site allows (e.g. list the chat's messages), else return an explicit "outcome uncertain" error.
*Acceptance:* scenario tests E, F, G (Section 7).

**D5 — Canonical task state.** Maintain a local, authoritative, versioned state per task/conversation: objective, system/developer instructions (verbatim hash + stored copy), full message log with stable IDs and **full-content hashes** (fixing D4), tool definitions, tool-call lifecycle (`requested → delivered → result_received → validated → completed | failed | unknown`), files read/changed and test results *as reported by tool results*, decisions, failed attempts, route history, checkpoints. Task ID is independent of model/route ID. Stored on disk (bounded, atomic), survives restart; secrets never stored.
*Acceptance:* restart test: state reloaded; model switch test: task ID unchanged, route history grows.

**D6 — Handoff on route change.** When the route changes, rebuild context for the new route from canonical state: verbatim system/tool instructions, recent turns verbatim, tool calls/results with IDs, and a **structured, provenance-tagged summary** of older material (see E3). Never assume the new site remembers anything. Mark unfinished/uncertain actions explicitly. If the new route lacks a capability needed to continue (e.g. native tools, images), stop or ask — do not silently degrade.
*Acceptance:* scenario J; test that completed tool calls are not re-requested.

**D7 — No duplicated side effects.** The bridge never executes tools itself for Claude Code, but it must not cause the *client* to run a tool twice: never re-emit a tool_use the client already received; keep tool-call IDs stable across retries/handoffs; dedupe on idempotency of (task, call ID).
*Acceptance:* test that a retried request after a lost response does not produce a second tool_use with a new ID for the same logical call.

### E. Context, memory, and usage efficiency

**E1 — Remote continuity as a verified capability.** Per account+site, track: remote conversation ID, last acknowledged message, whether continuation was observed to work, last continuity check, and a **trust level** (`verified | observed | uncertain | broken`) with a defined meaning. Use native continuation (send only the delta) only when trust is `verified/observed` and the recorded conversation belongs to the same account, route, tools signature and system signature. On doubt, rebuild context locally. Stop creating a new chat per request: reuse the conversation for the same task (fixes the owner's core complaint). Persist the mapping across restarts (bounded).
*Acceptance:* test with a mock site that remembers messages, one that forgets after N turns, one that resets silently; bridge detects and recovers; request payload sizes shown to shrink with continuity on (assert on mock-received bytes).

**E2 — Robust delta detection.** Replace prefix/hash logic that truncates content. Use deterministic canonicalisation and full-content hashes per message/block type (text, tool_use, tool_result, image, thinking), plus hashes for the tools list (full schemas) and system prompt. Cover: repeated prefixes, long identical heads with different tails, reordered tools, changed system, edited earlier message, regenerated assistant message.
*Acceptance:* property/fuzz tests; D4 regression test.

**E3 — Context budgeting without silent loss.** Count in tokens where possible (a pluggable estimator; exact tokenizer only if available; otherwise conservative estimate flagged as estimate). Budget per route using known/learned limits. Strategy order when over budget: drop true duplicates → compress verbose tool outputs with *lossless references* (store full text locally, send preview + reference + the relevant slice) → structured summary of old turns → ask/error. **Never** truncate: the system prompt, tool schemas, the latest user message, JSON documents mid-structure, or tool-call arguments. Every reduction is recorded in the trace and (when the client can see it) in a compact note to the model: what was omitted and how to ask for it.
*Acceptance:* tests that an error line from the middle of a 200k log still reaches the model when it is the relevant part; that an over-limit request returns an explicit `context_too_large` explanation rather than being silently cut.

**E4 — Large tool results.** Type-aware handling (JSON, diffs, logs, code, search results, directory listings): keep first failure, last status, surrounding lines, path/line references, counts; retain full text locally for follow-up retrieval; do not resend unchanged large results already acknowledged by a trusted remote conversation.
*Acceptance:* tests per type; unchanged-result suppression test.

**E5 — Summaries are derived data.** Summaries are generated deterministically where possible (extractive from canonical state: goal, requirements, decisions, files touched, commands/results, failures, open items); model-written summaries are optional, flagged as generated, never replace originals, and must not drop requirements/paths/test results. Do not spend an extra upstream request on summarisation unless the profile says it is affordable (fixes D7).
*Acceptance:* "needle" test — place 15 specific facts in a long history, trigger summarisation, assert all 15 survive.

**E6 — Text-first submission.** Prefer ordinary text submission. Detect per site (and record in the `SiteProfile`) whether long pasted text is turned into an attachment, rejected, or truncated. If attachment conversion occurs, avoid it by (a) splitting at semantic boundaries into ordered text messages **only when** the profile shows that works and the content can be split without losing structure, or (b) reducing/deduplicating content first (E3/E4). If a file upload is unavoidable, make it explicit, configurable, counted, and never repeated for unchanged content. Never silently drop the overflow.
*Acceptance:* mock site that converts >N chars into an attachment and applies an upload quota: bridge detects it, avoids repeated uploads across multiple turns, and reports its policy decision in the trace (scenario K).

**E7 — Usage thrift.** No health-check/discovery/probe/test that consumes model quota unless configured and disclosed in the dashboard. Health checks default to non-consuming checks (session validity, catalog freshness). No duplicate user-message submissions. Count "requests saved" and "bytes saved" **as measurements with their method stated**.
*Acceptance:* test that idle bridge sends zero model requests; metrics labelled measured vs. estimated.

**E8 — Untrusted content boundary.** Web pages, tool outputs, files, recipes, imported JSON, and provider text are data. They must not be able to change routing policy, reveal secrets, or be treated as bridge instructions. Keep trusted instruction text structurally separate in prompt construction; escape/neutralise any text that imitates the bridge's own control tags (`<tool_call>`, `<system>`, etc.) inside untrusted content.
*Acceptance:* injection tests with tool results containing fake `<tool_call>` / fake system blocks; they must not become executed calls.

### F. Quality of agent behaviour (the Codex/Antigravity gap)

**F1 — Tool-calling reliability on text-only backends.** Treat this as the main quality lever. Improve the emulation layer (`tools_text`, `parse_tool_calls`, `loose_json`, `TextGate`): compact but complete schemas (never destructively minified; keep required/enums/nested types), a concise, unambiguous call grammar, strict validation of name and arguments against the real schema (type coercion only when lossless), tolerant parsing of common malformed outputs (code fences, trailing commas, smart quotes, truncated closers) with **a single bounded repair attempt** in the same conversation, parallel calls, `tool_choice` (`auto|any|tool|none`) honoured, call IDs generated deterministically and stable.
*Acceptance:* a corpus (≥60 cases) of valid/malformed/adversarial model outputs with expected parse results; repair-loop bound test.

**F2 — Native tools where the site/API supports them.** If a variant/route has verified native function-calling (official API accounts, or a recipe that exposes it), use it; otherwise emulate and label the route "emulated tools" in the capability registry and dashboard.
*Acceptance:* both paths exercised via mocks.

**F3 — Claude Code compatibility, exhaustively.** Handle what Claude Code actually sends: `/v1/messages?beta=true`, `anthropic-version`/`anthropic-beta` headers (accept, don't choke), `x-api-key` and `Authorization: Bearer`, `system` as string or array of blocks (with `cache_control`), `messages` with string or block content, `tool_use`/`tool_result` (including `is_error`, nested content blocks, images inside results), `thinking` config, `metadata`, `stop_sequences`, `temperature`, `top_p/top_k`, `tool_choice` variants, `/v1/messages/count_tokens` (labelled estimate), startup probes (`max_tokens` 1 / "quota"), title/summary side-requests for a small model, `HEAD`/`OPTIONS`, and streaming ping events. Unknown fields: ignore harmlessly only if they do not change semantics; otherwise report in diagnostics.
*Acceptance:* a recorded-style request corpus replayed against the bridge; protocol conformance assertions.

**F4 — Parameter fidelity.** Build a parameter-mapping table per protocol and per route capability: honour `max_tokens` (enforce `stop_reason: max_tokens` when the bridge itself must cut), `stop_sequences`/`stop` (enforce locally on the text stream if the site cannot), `temperature`/`top_p` (forward only if the recipe supports it, else report "ignored: unsupported" in diagnostics), structured output requests (validate result or error). Never silently ignore a parameter that changes meaning.
*Acceptance:* tests for local stop-sequence and max-token enforcement.

**F5 — Thinking/reasoning modes.** If a variant exposes a reasoning/"deep think" mode, treat it as part of the variant (discoverable, selectable, capability-tagged). For Anthropic `thinking` requests, map to a thinking-capable variant when policy allows; never fabricate thinking blocks; if reasoning text is available from the site, surface it only in a protocol-correct way (or drop it deliberately and say so).
*Acceptance:* mock with reasoning stream; correct block framing or documented drop.

**F6 — Images and non-text blocks.** Do not replace images with `[image omitted]` silently. If the route supports image input through its recipe/UI, send it; otherwise return an explicit, protocol-correct incompatibility error or route to a capable variant when policy allows.
*Acceptance:* routing test H.

**F7 — Latency work.** Reuse HTTP connections per account (bounded pools, no cross-account sharing), avoid per-request browser start, avoid redundant discovery/probes, stream first token as soon as safe (TextGate must hold back only what is necessary to detect a tool call — measure and minimise added latency), parallelise independent work. Report time-to-first-token and total latency per route.
*Acceptance:* benchmark on the mock site comparing baseline vs. new (same workload, same machine), numbers recorded in the report.

**F8 — Quality telemetry (no fake scores).** Per route and task-category record measured outcomes: completion rate, tool-call validity rate, repair rate, error rate, latency percentiles, context-rebuild count. Use them for `best_fit`/`quality_first` ranking only after a minimum sample size; display sample counts. Never present a model "intelligence" number.
*Acceptance:* ranking uses telemetry only above threshold; dashboard shows n.

### G. Protocol and streaming correctness

**G1 — Shared orchestration.** A single orchestration path (`Orchestrator`/`Router`) serves both protocols. Protocol parsers/serialisers are separate from routing and state.

**G2 — SSE parsing robustness (`StreamDecoder`).** Handle arbitrary chunk boundaries, UTF-8 split across chunks (incremental decoder), CRLF/LF/CR, multi-line `data:`, `event:` names, comments/heartbeats, partial JSON, upstream error events, EOF without terminator, huge lines (bounded), and cancellation.
*Acceptance:* fuzz test splitting a transcript at every byte offset yields identical output.

**G3 — Anthropic writer.** Exact event sequence: `message_start` → (`ping`) → `content_block_start` / `content_block_delta` (`text_delta`, `input_json_delta`) / `content_block_stop` per block → `message_delta` (with `stop_reason`, `stop_sequence`, usage) → `message_stop`. Tool-use blocks stream arguments as `input_json_delta`. Mid-stream errors use the `error` event. No double terminal events. Non-stream response shape correct.
*Acceptance:* a conformance parser asserts ordering/required fields on every test response; validate against the official event grammar from memory and document any uncertainty.

**G4 — OpenAI writer.** `chat.completion.chunk` objects with role delta first, content deltas, `tool_calls` deltas with `index`, `id`, `function.name`, incremental `arguments`, final chunk with `finish_reason` (`stop|tool_calls|length`), optional usage chunk only if requested and honest, then `data: [DONE]`. Error handling mid-stream defined and tested.
*Acceptance:* conformance parser as above.

**G5 — Usage honesty.** Use provider-reported usage if the site gives it; otherwise either omit or include clearly-flagged estimates (e.g. a response header `x-bridge-usage: estimated`), never presented as exact. `count_tokens` is marked estimated in docs and header.

**G6 — Cancellation and cleanup.** On client disconnect: set cancel event, abort upstream read, close responses, free semaphores, decrement in-flight in `finally`, stop UI-tier typing/waiting, and never let one cancelled request affect another. Timeouts everywhere (connect, first byte, stream-idle, overall). Bounded buffers.
*Acceptance:* disconnect-mid-stream test asserts resources released and upstream cancelled.

**G7 — Cache correctness (fix D3).** Default: caching disabled for any request with tools or with side-effect-sensitive context. If a response cache stays, its key must include: API key identity/security scope, resolved route, full tool schemas, tool_choice, all sampling/limit parameters, full system, full-content message hashes, profile; TTL and size bounded; entries never shared across keys/accounts. Capability/discovery caches are separate from response caches.
*Acceptance:* cross-key and cross-model contamination tests.

### H. Dashboard (functional, dynamic, safe)

**H1 — Account panel.** Per account: provider/site, state, tier, session health, catalog with each variant's name, identity confidence, capability chips (supported / unsupported / unknown shown differently, not by colour alone), staleness, last discovery, cooldowns with scope and reason, latency/success metrics with sample counts, recent safe errors, **Refresh models** button, enable/disable, test route (explicitly marked if it consumes quota).

**H2 — Routing panel.** Choose policy; fixed route picker; build/reorder/enable/disable rotation pools and failover chains; capability requirements; Fast/Balanced/Quality profile; approval rules; data-transfer rules; client-model-name mappings; per-key restrictions. All selectors are populated from the live catalog. Invalid combinations are blocked with inline messages. Persisted and validated server-side.

**H3 — Live view.** Active requests, queue/in-flight counts, last N route decisions with "requested vs. selected vs. observed identity", fallback/handoff events with reasons, context-reduction events, error timeline with typed categories. Every claim shows its confidence/staleness.

**H4 — Honest empty/loading/error states.** No-catalog state prompts discovery; unknown values shown as "unknown"; disabled features visibly disabled; no controls that do nothing.

**H5 — Safe rendering.** No untrusted string reaches `innerHTML`; use `textContent`/safe builders. Add a strict Content-Security-Policy and other security headers to dashboard responses where compatible. Accessible labels, keyboard operation, focus styles, responsive layout, copyable IDs.
*Acceptance:* XSS test using hostile model/account/error strings; manual DOM check or headless-render test if Playwright is available.

### I. Security

**I1 — Network exposure.** Loopback by default; binding elsewhere requires explicit flag plus warning; admin and client keys required; constant-time comparison; no secrets in URLs, logs, or HTML.
**I2 — Browser-origin attacks.** Validate `Host` (anti-DNS-rebinding) and `Origin`/`Sec-Fetch-Site` for all state-changing dashboard endpoints; CSRF protection for cookie-authenticated flows; CORS only where needed, never `*` on management endpoints.
**I3 — Secrets.** Never serialise cookies/tokens/API keys to the dashboard or logs; mask in errors; `private=True` files with 0600 (and best-effort on Windows); log redaction filter with tests; diagnostics export excludes secrets and prompt text by default.
**I4 — SSRF/URL validation.** Validate every outbound URL (API base URLs, recipe endpoints, redirects): schemes, host, port, resolved IP (block loopback/link-local/private/metadata) unless an explicit, documented opt-in is set for local model servers; re-validate every redirect hop; pin DNS result for the connection.
**I5 — Recipes and files.** Recipes/imported JSON are untrusted: schema-validate, forbid arbitrary code/paths, constrain template variables, prevent path traversal when writing `docs/<host>.md` and `tools/<host>_client.py` (slug hosts strictly). Generated tools must not embed secrets.
**I6 — Resource limits.** Request body cap, header cap, concurrent connection cap, bounded queues with explicit "overloaded" responses, bounded caches/histories, output buffer caps.
**I7 — Privacy.** Default metadata-only telemetry; prompt/content logging off by default and clearly labelled when on; retention limits; documented list of files containing sensitive data and how to delete them; account removal removes that account's sessions/catalog/state but never other accounts' or shared site recipes.
*Acceptance (I1–I7):* security test group listed in Section 7.

### J. Observability and operations

**J1 —** Request IDs end to end; structured, bounded, redacted event log; timing milestones with monotonic clocks (accepted → routed → upstream first byte → first client byte → done).
**J2 —** `/healthz` (local) separate from provider health; no quota-consuming health probes by default.
**J3 —** Graceful startup validation (port, data dir, dependencies, config) with actionable errors; graceful shutdown (stop accepting, drain with timeout, cancel, flush state, close browsers/sockets).
**J4 —** `--help` documents every flag/env var; `--selftest`, `--selftest --live` (opt-in, uses real accounts, low impact, clearly warns), `--export-diagnostics` (sanitised).
**J5 —** Browser resource control: reuse one headless context per account, idle shutdown (existing `AccountBrowser` idle timer — verify it works), cap concurrent browsers, make sure no browser or page leaks after errors/cancel.

### K. Extensibility

**K1 — Adding a provider** requires no change to routing/protocol code: a site is added via the dashboard (browser login → learn), or via a small declarative `SiteProfile`/recipe, or via an `api` account. Document the adapter interface inside the file's top docstring (what an adapter must report: capabilities, discover(), ask(), cancel(), classify_error(), verify()).
**K2 — Optional (only if it does not compromise anything else):** MCP-related passthrough fidelity (preserve tool names containing `mcp__…` and large tool lists), multi-agent/sub-agent request isolation (separate task state per concurrent Claude Code sub-agent, no shared conversation), Git-worktree friendliness (never assume one working directory). Do not fabricate support for what the bridge does not control.

### L. Documentation inside the single file
Top-of-file docstring: purpose, install, run, flags/env, endpoints, security model, data directory layout, upgrade/migration notes, how to add a provider, troubleshooting by error category, known limitations. Section banners and clear class boundaries; type hints on public structures.

### C (addendum)

**C10 — Model-change preview.** Before a fixed route is changed, or before a policy-approved switch to a different route, the dashboard (and, for `manual_approval`, the API error/pending state) shows what changes: capabilities gained/lost, identity confidence, remote-memory status (will context have to be rebuilt?), known limits, uncertain items. A switch that would lose a capability needed by the task (native tools, images, context size) is blocked or requires approval.
*Acceptance:* test where the backup route lacks image support and the task contains an image.

**C11 — Shadow evaluation of routing decisions.** A "shadow" mode logs what a *different* policy/version of the routing engine would have chosen for each real request, without sending anything extra upstream, so routing changes can be compared offline. Never silently double-send real requests.
*Acceptance:* test proving shadow mode makes zero extra upstream calls.

### M. Claude Code–specific quality and speed multipliers

These are the items most likely to make Claude Code feel as good as, or better than, using a paid API key. Treat them as first-class features, not polish.

**M1 — Session and sub-agent identity.** The Anthropic API has no session ID, so derive one robustly: use client-provided identifiers if present (inspect real captured requests, e.g. any `metadata.user_id`-style field — verify, do not assume), otherwise a stable fingerprint of (API key, system-prompt hash, tools signature, first user message). Claude Code runs sub-agents (separate system prompts/tool sets) and may run several windows at once: each gets its **own** canonical task state and its own remote conversation. Two parallel sessions on one account must never share a remote chat.
*Acceptance:* 3 interleaved sessions + 1 sub-agent on one mock account keep fully separate histories (assert on mock-received messages).

**M2 — Conversation state machine and divergence detection.** Model each session as a state machine (`new → active → awaiting_tool_result → generating → completed | errored | uncertain | rolled_over`) and classify every incoming request against stored history as exactly one of: `append` (normal), `truncate`/`rewind` (user rewound), `fork` (earlier message edited), `compacted` (client ran `/compact` and replaced history with a summary), `cleared` (new conversation), `interrupted` (user pressed Esc; the client's copy of the last assistant message may be partial while the remote copy is complete), `unknown`. Actions: `append` → delta only; `interrupted` → reconcile (treat remote full text as superseded by the client's version; do not resend what the client already has; verify trust level); `rewind/fork` → use the site's branch/edit feature only if the SiteProfile says it works, else start a new remote chat from canonical state; `compacted/cleared` → new remote chat seeded from the client's new history; `unknown` → rebuild context from canonical state (never continue blindly).
*Acceptance:* one test per class with the mock site, asserting both the classification and the payload sent.

**M3 — Request classification and turn-type routing.** Classify each request from protocol evidence (client model name, `max_tokens`, presence/absence and size of tools, system-prompt markers, `stream` flag) into: main-agent turn, sub-agent turn, small background task (title generation, topic/summary detection, command-prefix or permission classification, hook helpers), token-count call, startup probe. Route background tasks to the fastest adequate variant (capability-gated), main turns by the active policy. Local short-circuits (e.g. the existing "quota" probe and title shortcut) are allowed **only** when matching a strict, documented, tested signature, are logged in the trace, and can never swallow a real task request (fix the over-broad `max_tokens <= 1` condition). *Optional, default OFF:* `adaptive_turn_routing` — strongest model for planning/debugging turns, fast model for mechanical turns, switching only at turn boundaries through the canonical-state handoff, enabled only when telemetry shows it helps.
*Acceptance:* classification corpus test; test that a real request with `max_tokens=1` that is not the probe is not short-circuited.

**M4 — Pre-flight tool-call validation against what the transcript already shows.** The bridge sees every Read/Grep/Bash/Edit result in the conversation. Build a per-session *file knowledge* index (path → last known content hash/content, invalidated by later Write/Edit/Bash-that-mentions-the-path). Before delivering an edit-type tool call (identified by a configurable **tool-semantics map** keyed on schema field names such as old/new string and file path — data, defaulted for Claude Code, not hard-coded logic), check that: the path was seen, the old string occurs in the last known content, exactly once unless a replace-all flag is set, required fields exist. On a strong-evidence mismatch, perform **one** bounded repair turn in the same conversation with the exact error and the relevant snippet; if still invalid, deliver the call as-is only if evidence is weak (file may have changed), otherwise return an honest message. Never block on stale knowledge.
*Acceptance:* tests: correct edit passes untouched; wrong `old_string` triggers one repair; knowledge invalidated after a Bash that modified the file; repair never loops.

**M5 — Parallel tool calls.** Prompt the model (briefly) to batch independent tool calls in one turn, parse several calls per reply, preserve order and IDs, and emit them as multiple `tool_use` blocks / multiple OpenAI `tool_calls`. This cuts round-trips, which are the dominant latency in agent loops.
*Acceptance:* parser corpus with 1–5 calls per reply; protocol conformance for multiple blocks.

**M6 — Long-wait keep-alive and timeouts.** Reasoning-heavy sites can be silent for a long time. Emit protocol-valid keep-alive (`ping` events on Anthropic streams; SSE comments on OpenAI streams) so the client does not time out; define separate connect/first-byte/idle/overall timeouts; surface an honest error if the site is truly stuck. Keep-alives must not corrupt framing or be counted as content.
*Acceptance:* mock site that stalls 60 s; client stream stays valid.

**M7 — Thinking blocks.** If a variant exposes reasoning text, map it to protocol-correct thinking blocks **only if** the bridge can satisfy the protocol's requirements for them (including whatever signature field the client may require when it sends them back — verify in the spec); otherwise drop them deliberately and record that. Accept thinking blocks that clients send back in history without error and without leaking them to the model as fake user text.
*Acceptance:* round-trip test with a thinking block in history.

**M8 — Context-window and usage honesty so the client's auto-compaction works.** Claude Code decides when to compact from the usage numbers returned and the context window it assumes for the model *name*. If the bridge's real route has a smaller window, the client will overflow. Therefore: return best-effort `usage` flagged as estimated (header + dashboard), expose per-alias context windows, make `count_tokens` consistent with the same estimator, perform bridge-side safety compaction (E3) before the site's real limit, and when something genuinely cannot fit return the exact error shape the client treats as "prompt too long" (verify against the Anthropic error spec) so the client can recover. Research the official Claude Code settings/environment variables for custom gateways and for tuning auto-compaction; print recommended values at startup only for settings you could verify (otherwise label "unverified").
*Acceptance:* test where history crosses the route's real limit: client receives a recoverable error or the bridge compacts first; estimated-usage flag present.

**M9 — Seamless continuation of truncated outputs.** Sites cap per-message output and sometimes show "continue generating". Detect truncation (site signal, abrupt end, length-limit finish), continue **in the same conversation**, de-duplicate overlap, and present one continuous answer; map to `max_tokens` stop reason only when the *client's* limit was hit. Never splice across different models. Large `Write`-style outputs: prefer the continuation path; if impossible, return an honest incomplete-output error instead of a silently truncated file.
*Acceptance:* mock site that cuts at N chars; assembled output byte-identical to the source text.

**M10 — Character-exact output fidelity.** Code and tool arguments must survive unchanged: no smart-quote substitution, no whitespace/tab/CRLF/NFC-NFKC normalisation of code, correct Persian/RTL and other Unicode, no site "chrome" in the output (citation markers, "Searching…", "Copy code", auto-added fences, upsell banners, disclaimers) — extraction rules are per-site data in the SiteProfile. At learning time run a disclosed, low-cost fidelity probe (echo test with tricky characters) and record the result; mark sites whose output is altered.
*Acceptance:* golden-string tests through the mock site that deliberately mangles characters and injects banners.

**M11 — Minimal, measured prompt wrapper.** The instructions the bridge adds for text-only backends (tool grammar, parallel-call hint, output discipline) must be as short and unambiguous as possible and are *measured*: tool-call validity, repair rate and token overhead are compared across wrapper variants on the mock/benchmark corpus; keep the variant that wins, record the numbers.
*Acceptance:* benchmark table in the report.

**M12 — Local de-duplication of repeated tool output.** If the same file/command output appears again unchanged in later turns, reference it (stable local reference + hash) instead of resending, when the remote conversation is trusted to hold it; otherwise resend. Always hash-verified.
*Acceptance:* test with a file read three times, then changed once.

**M13 — Boilerplate/reminder de-duplication.** Clients inject repeated identical blocks each turn (reminders, environment info). When the remote conversation is trusted and the block's hash is unchanged, do not resend it; when it changed, send only the change. Strictly hash-verified, never applied to the system prompt, tools, the latest user message or the first turn after any trust drop.
*Acceptance:* payload-size test across 20 turns with unchanged and changed blocks.

**M14 — Refusals and moderation are not "routing problems".** Classify site-side content blocks/refusals as `content_blocked`, surface them honestly with the site's wording, and do **not** use failover to route around moderation decisions. Distinguish a hard policy refusal from a transient "something went wrong".
*Acceptance:* classifier corpus; test that `content_blocked` never triggers fallback.

**M15 — Silent model downgrade detection.** Some sites switch to a smaller model after a usage threshold or show a banner. Detect via response metadata/UI banner/profile signals, mark the observed identity as changed, flag the route `degraded`, show it in headers and dashboard, and apply policy (continue / switch / ask). Never keep labelling the route with the old identity.
*Acceptance:* mock site that downgrades after N messages.

**M16 — Measured limit awareness.** Track measured request counts per account/route per rolling window, parse reset hints from error text ("try again in…"), show countdowns, and pre-empt at a **request boundary** (before sending, never mid-stream) when a limit is near and policy allows another eligible route. Label all of it measured/parsed/estimated; never invent a quota.
*Acceptance:* tests with parsed reset times of several formats and languages (including Persian/English).

**M17 — Human-verification pause.** CAPTCHA/Cloudflare/"verify you are human"/login-challenge pages → `challenge_required`: stop sending, tell the user in the dashboard and in the API error exactly which account needs attention, resume after the user completes it in the browser. No bypass attempts.
*Acceptance:* mock challenge page; no further requests until cleared.

**M18 — Fairness across clients and sub-agents.** Several Claude Code windows/sub-agents may share an account: bounded per-account queue with priorities (main turn > sub-agent > background), per-chat serialisation (one generation per remote chat), maximum wait, and a clear overload error. Pacing between sends is configurable (courtesy and false-positive avoidance, not evasion).
*Acceptance:* concurrency test with 10 parallel sessions; no starvation of the main turn.

**M19 — Remote chat hygiene.** Reuse conversations per task; cap live remote chats per account; roll over a conversation before the site's own "conversation too long" limit using a canonical-state handoff; optional, **opt-in** archive/delete of bridge-created chats; never delete anything the bridge did not create.
*Acceptance:* rollover test at a mock length limit with no information loss (needle test).

**M20 — Streaming smoothness.** Stream text as soon as it is safe; hold back only the minimum needed to detect a tool call; emit tool-use blocks only after validation; coalesce tiny deltas without adding noticeable latency; honour backpressure; report added latency from the tool-detection gate.
*Acceptance:* time-to-first-byte measurement vs. baseline on the mock.

**M21 — Connection and session warmth.** Keep ready accounts warm: reuse HTTP connections, refresh tokens/cookies before expiry (capture rotation correctly), avoid browser relaunch, and never run quota-consuming keep-alives.
*Acceptance:* zero model requests while idle; token refresh before expiry on mock.

**M22 — Self-healing recipes with a safety net.** On recipe breakage: keep last-known-good, attempt a bounded background relearn (rate-limited, visible to the user), validate the candidate, then swap; if it fails, stay on last-known-good/degraded and notify. Network blips never trigger relearn.
*Acceptance:* mock site changes format; recovery or honest degradation.

**M23 — Onboarding and `--doctor`.** First run: a short guided flow (add account → learn → discovery → test). `--doctor` checks Python/dependencies, Playwright/browser presence, port, data dir permissions, clock skew, accounts/recipes/catalog freshness, config validity, and prints actionable fixes. At startup print ready-to-copy Claude Code connection settings, but only values verified from official documentation or the actual running configuration.
*Acceptance:* doctor test on a broken temp environment.

**M24 — Record/replay fixtures (opt-in).** A switch records sanitised request shapes and site traffic (secrets and content redacted by default) so real-world regressions can be turned into tests.
*Acceptance:* redaction test with canary secrets.

**M25 — Optional second-opinion pass (default OFF).** For high-stakes turns a configured reviewer route can critique a proposed destructive action or large rewrite as a *text-only* review (no tools, no side effects), with an explicit budget and visible attribution. Never a hidden double-send of the real request.
*Acceptance:* budget and attribution test; shows no tool execution path.

**M26 — Arena / side-by-side / battle-mode sites (LMArena- and DesignArena-style).** Handle sites where: the model is chosen from a dropdown or per-mode page; "battle" or "side-by-side" modes return two anonymous answers; identity is revealed only after voting or after the reply; sessions are ephemeral; outputs may be rendered designs/HTML rather than plain text. Prefer a direct single-model mode when discovery finds one; never vote, rate or alter site state automatically; identify when only anonymous output exists and mark the identity `unknown`; extract rendered/HTML output as text faithfully.
*Acceptance:* mock arena site with each mode; correct mode selected, identity labelling honest, no unintended state changes.

**M27 — Site-side tools and personalisation contamination.** Site features (web search, canvas/code interpreter, memory, custom instructions, projects) can inject text, consume separate quotas or alter answers. Per SiteProfile, prefer the plain-chat mode with such features off for coding traffic when a toggle is discoverable, and record when it is not. Where a "temporary/no-memory chat" mode exists, state the trade-off (isolation vs. continuity) and make it a per-account option.
*Acceptance:* profile flag respected; test with a mock that injects citations when search is on.

**M28 — Bridge overhead budget.** Measure routing + context preparation + serialization overhead excluding upstream time; engineering target p95 ≤ 50 ms on the mock for ordinary requests (a target to measure and report, not a claim). Optimise hot paths only after correctness.
*Acceptance:* reported numbers.

### N. Site-limit scenario catalogue (what must NOT happen, and what to do instead)

Each row is a real class of problem seen when driving consumer chat sites. Implement the behaviour, add a mock-site test per row, and add the site-specific facts only to the SiteProfile (discovered/observed, never hard-coded).

| ID | Scenario | Required behaviour |
|----|----------|--------------------|
| N1 | Long paste is auto-converted to an attachment, and attachment uploads have a small quota (the ChatGPT case) | Detect conversion; prefer ordinary text submission by every supported means; reduce/de-duplicate content first (E3/E4/M12/M13); split into ordered text messages only when the profile shows it works and no structure is lost; if an upload is unavoidable: configurable, counted, never repeated for unchanged content; stop and warn before the upload quota is exhausted instead of silently breaking the chat. |
| N2 | Per-window message caps (overall or per model) | Count measured sends; parse reset hints; pre-empt at request boundary (M16); respect, never evade. |
| N3 | Limit on creating new chats or very many chats | Reuse chats (E1/M19); cap live chats; roll over only when needed. |
| N4 | Site "conversation too long" or silently dropped early history | Detect via site signals or trust decay; roll over proactively with canonical-state handoff (M19, D6). |
| N5 | One generation at a time per chat/account | Per-chat serialisation and per-account queue (M18). |
| N6 | Edit/regenerate/“try again” consume quota | Never invoked automatically. |
| N7 | Image/file upload size or count caps | Capability + limit in registry; explicit incompatibility error rather than silent drop (F6). |
| N8 | Streaming connection cut after N minutes | Detect as `stream_interrupted`; continuation per M9 if safe; otherwise honest error. |
| N9 | Session/token expires mid-conversation | `auth_expired` → refresh (M21) → one bounded retry only if the request was provably not accepted (D4/G). |
| N10 | Risk-based challenge after rapid requests | Pacing (M18) and `challenge_required` pause (M17); no bypass. |
| N11 | Per-message output cap | Continuation (M9). |
| N12 | Upsell banners/ads/disclaimers inside the response | Per-site extraction rules; fidelity tests (M10). |
| N13 | Model changes inside a chat (silent downgrade or arena rotation) | Observed-identity tracking (C7, M15, M26). |
| N14 | Account flagged/suspended | Stop immediately, mark `account_restricted`, notify, never try to work around. |
| N15 | Site outage/maintenance | `site_unavailable`, circuit breaker, policy-approved alternative route only. |
| N16 | Many sub-agents flooding one account | Priority queue and bounded concurrency (M18). |
| N17 | Moderation false positive on benign code | `content_blocked` surfaced honestly; no routing around it (M14). |
| N18 | Site language/locale differences in error text (e.g. Persian/English) | Error classification must not depend on a single language; classify by status/structure first, text second, with unknown ≠ quota. |


---

### O. Onboarding, automatic reverse-engineering, portability, site directory, account cards, autonomy (owner's flow — added in v5)

**The flow the owner wants (confirmed and sharpened):** (1) the owner adds an account; a visible Playwright browser opens and the *owner logs in by hand* — this "classic" web path already gives a working chat. (2) When login is detected the browser hides and the bridge takes over the live browser session: it can see network traffic, storage, cookies and the page's scripts, and uses the connected site's own model (through that web session) to help read them. It reverse-engineers how the page talks to the server. (3) It builds a *direct* recipe (talk to the server without the browser) and **validates it with a battery of scenarios on that same account**. (4) Only after the validation passes does it promote the recipe to `stable`, store it, and from then on use the browser **only for login/session refresh and as a repair fallback**. (5) If the stable recipe later breaks, the account drops to the page/UI tier (the classic path) while a background repair re-learns the recipe, and returns to direct when it is stable again. (6) Everything lives in one folder next to `bridge.py`, so copying code + folder to another machine keeps the accounts alive when the stored sessions are still valid.

**IMPLEMENTATION ORDER FOR GROUP O (build in exactly this sequence; IDs are stable and are NOT in build order; later steps depend on earlier ones):**

| Step | ID | What | Depends on |
|---|---|---|---|
| 1 | O16 | Reverse-engineering must stay safe and honest | - |
| 2 | O20 | Extract, never guess | - |
| 3 | O6 | Bounded learning cost | - |
| 4 | O1 | Account lifecycle state machine | A (state/persistence) |
| 5 | O10 | Portable data folder | A, O1 |
| 6 | O2 | Add-account input that tells the owner what to type | O1 |
| 7 | O3 | Visible login, reliable login detection, then hide | O1, O2, O10 |
| 8 | O7 | Human-in-the-loop for verification | O1, O3 |
| 9 | O4 | Capture, with secrets kept out of the model | O3, O16 |
| 10 | O22 | Total network analysis | O3, O4, O6 |
| 11 | O21 | Per-site source analysis with a real toolchain | O22 |
| 12 | O23 | Every other surface that matters | O22, O21 |
| 13 | O5 | AI-assisted reverse-engineering with deterministic validation | O20, O21, O22, O23 |
| 14 | O17 | Challenge classes | O5 |
| 15 | O18 | Extracted site logic as native, readable project modules | O5, O17, O20 |
| 16 | O19 | Browser identity profile, replayed honestly | O3, O22 |
| 17 | O8 | Validation battery before promotion to `stable_direct` | O18, O19, O6 |
| 18 | O9 | Browser only for login, refresh and repair; zero browser RAM when stable | O8, O1 |
| 19 | O14 | Model choice after discovery | B, O8 |
| 20 | O13 | Rotation that the client never notices | C, D, O8, O9 |
| 21 | O12 | Account cards from what was actually discovered | O1, O8, O14 |
| 22 | O11 | Site directory | O2, O3, O12 |
| 23 | O15 | Autonomous mode | O1-O14 |
| 24 | O24 | Brain-driven learning: principles and boundaries | O5, O16, O20, O6 |
| 25 | O25 | Brain channel (ask the connected account's own model, safely, within budget) | O24, O4, O6, O3 |
| 26 | O26 | Investigation loop (plan, look, hypothesise, experiment, verify) | O25, O22, O21, O23 |
| 27 | O27 | Brain-authored native modules with a code-quality gate | O26, O18, O17, O19 |
| 28 | O28 | Independent engineer review pass (advisory only) | O27 |
| 29 | O29 | Live wiring and promotion: learn once, then direct, browser closed | O27, O8, O9 |

Steps 1-3 are *governing rules* (safety/honesty, extract-never-guess, learning budget): read them before building anything in this group and obey them throughout. Steps 4-8 are the base (state, storage, adding, login, human hand-off). Steps 9-12 are capture and analysis (capture safety, network, source, other surfaces). Steps 13-16 are the direct mechanism (extraction, challenge classes, native modules, identity). Steps 17-18 are validation and browser-off. Steps 19-22 are routing and experience (model choice, smooth rotation, cards, directory). Step 23 is autonomy.

**O16 — Reverse-engineering must stay safe and honest.** No fabricated success: a recipe is `stable` only through O8. Never log credentials; never send them to a model; recipes contain no secrets (secrets live in sessions, referenced by name). A tester without logins proves O1–O16 on the mock and states precisely that no real site was exercised.

**O20 — Extract, never guess (owner's explicit rule).** Every element of the direct mechanism - request URL/method/headers/body shape, token and signature algorithms, PoW routines, conversation/model identifiers, stream and error formats, refresh logic - must be **extracted from what actually exists**: the site's own script source (locate the function, follow its dependencies and constants, translate it faithfully) and the recorded network traffic. A model may *point to where* something is, but the content that enters a module is the **literal source or recorded data**, not a model's reconstruction or an assumption about "how such sites usually work". Each extracted element carries provenance in `manifest.json` (script URL + hash + offset/line range, or capture id). **Verification replaces trust:** replay the ported logic on recorded inputs and require byte-identical outputs on >= 3 captures (O17), and the validation battery (O8) on the live account. If any element cannot be extracted with provenance and verified, it is marked `unknown`, that site/feature stays on the page/UI tier, and nothing is filled in by inference. No heuristic "looks like a signature, so try HMAC with this key" - keys and constants must come from the source. Report per site: extracted / verified / unknown, with the evidence. *Acceptance:* a mock site whose token algorithm differs from every common pattern is reproduced exactly from its served script; a mock site with an unextractable element is left on the page tier with that element listed as `unknown`; grep of the modules shows no element without provenance.

**O6 — Bounded learning cost.** Reverse-engineering and validation spend the owner's quota: a visible budget (default ≤ 12 model requests per learn, ≤ 3 per repair attempt, configurable), cache everything reusable, never re-learn unless drift evidence exists (B9), and show "learning used N requests" on the card. No quota-consuming work while idle (E7).

**O1 — Account lifecycle state machine.** Per account: `adding → logging_in → capturing → learning → validating → stable_direct`, plus `degraded_fallback` (page/ui tier in use), `repairing`, `needs_login`, `needs_human` (CAPTCHA/verification), `disabled`. Explicit, persisted, shown on the card with a reason and a timestamp; transitions are logged in the account's event list. Routing (C3) uses it (`needs_human`/`needs_login` ⇒ not eligible, with a reason code). *Acceptance:* every transition covered on the mock; kill the process mid-state and restart → a sane state, never stuck in `learning` forever.

**O10 — Portable data folder.** On first run create `bridge_data/` next to `bridge.py` (override: `--home`/`BRIDGE_HOME`) and keep everything in it: sessions/cookies/storage, browser profiles, recipes, profiles, catalogs, task state, config, backups, a `MANIFEST.json` (schema, created, bridge version, folder id, per-account origin host fingerprint). Copy code + folder to another machine ⇒ at start (and via `--doctor`) the bridge *validates every stored session with a cheap non-consuming check*, and reports per account `valid | expired | looks IP/device-bound | needs_login`; only the invalid ones ask for a login. Browser profile directories are portable only when the OS/browser build matches — detect and say so; never crash on a foreign profile. The folder holds secrets: 0600/0700 permissions, never inside any API response, a clear warning on export/copy, `--export-bundle`/`--import-bundle` helpers (optional passphrase encryption only if a vetted library is present; otherwise document the risk rather than inventing crypto). *Acceptance:* copy a populated folder to a new path → accounts reported with correct validity on the mock, valid ones used without a login, an IP-bound session reported as such.

**O2 — Add-account input that tells the owner what to type.** The "add account" box accepts: the site's normal address (`https://site.example`, recommended default), a login/sign-in address, or a bare domain (`site.example`; `https://` added). Show a one-line hint and an example under the box and a "paste whatever you have" note: the bridge normalises (scheme, trailing path/query stripped for identity, original kept for opening), opens the *given* URL in the visible browser and lets the owner navigate to the real login page themselves — the bridge does not need to know the login URL. Also offer the site directory (O11) as one-click starting points. Validate with `url_guard` (I4); reject non-http(s). *Acceptance:* table test of ≥ 10 inputs (with/without scheme, www, path, query, port, uppercase, IDN, junk) → normalised identity host + open-URL.

**O3 — Visible login, reliable login detection, then hide.** Headed Playwright with a dedicated per-account profile directory; the owner logs in. Detect success from several signals and require **≥ 2** (or an explicit "I'm done" button): (a) auth-looking cookies/storage appeared or changed versus the pre-login snapshot, (b) login form/button gone and a chat input present, (c) an authenticated XHR returned 2xx with profile-like JSON, (d) the URL left the login/auth path. On success the account is created, the window hides only while capture/learning runs (O4-O5), and the lifecycle moves to `capturing`. Once the direct recipe is validated and promoted (O8) the browser process is **closed completely** (no hidden window, no idle Chromium), keeping only the profile/session files on disk. Timeouts and "closed the window early" are handled and reported, never a half-created account. *Acceptance:* mock login flows (cookie login, token-in-storage login, SSO redirect, login page returned with HTTP 200) → account created exactly once; early close → clean abort.

**O7 — Human-in-the-loop for verification.** A CAPTCHA/Cloudflare/"verify you are human"/MFA page (M17) sets `needs_human`: routing skips the account at once (smooth failover, see O13), the browser window for *that account* is shown with a dashboard notice (and optional OS notification), the owner solves it, and the bridge resumes (re-validates the session, returns to its previous state). The bridge never clicks through or solves challenges itself (2.4).

**O4 — Capture, with secrets kept out of the model.** While the owner chats a few times (or the bridge sends the probe messages, within the usage budget O6), record network exchanges, storage keys, and relevant script excerpts. **Credentials, cookies and tokens are never put into any prompt**: redact before building evidence for the site's model (reuse E8/I3 redaction; assert with a canary-secret test). Evidence from the site is untrusted data (prompt-injection safe, E8).

**O22 — Total network analysis ("swallow the network").** While the owner's browser session is live (login, a few real chats, a model switch, a regenerate, a stop, an upload if the site has one, a logout/expiry if safely reproducible) the bridge records **every** exchange at the CDP/HAR level: HTTP/1.1/2 requests and responses with full headers in order, redirects, preflights, cookies set/changed (with attributes: domain, path, SameSite, Secure, HttpOnly, expiry), request/response bodies (JSON, form, multipart, GraphQL, protobuf/gRPC-web, msgpack, base64/compressed bodies decoded when possible), streaming responses chunk by chunk (SSE, NDJSON, chunked, WebSocket frames both directions with opcodes, EventSource, long-poll), timing and ordering, initiator stacks (which script line triggered it), service-worker and worker traffic, iframes/`postMessage`, WebRTC signalling if any, and traffic from third-party hosts (telemetry/ads/anti-bot hosts are *classified and excluded from the mechanism*, never replayed). Then analyse it **from every direction**: (1) *per exchange* - purpose, schema inferred only from observed data (O20), required vs optional fields found by differential captures; (2) *causal/dependency graph across exchanges* - which response field feeds which later request (conversation id, parent/message ids, CSRF/bootstrap tokens, upload ids, signed URLs, pagination cursors, refresh tokens), with ordering and timing constraints; (3) *session state machine* - anonymous -> authenticated -> chat created -> message sent -> streaming -> done/stopped/error, token/cookie lifetimes and renewal paths, what each error status/body means (map to D1 categories); (4) *differential analysis* - change exactly one input (model, mode, message length, attachment, language, regenerate) within the O6 budget and diff the requests to learn which fields matter; (5) *stream grammar* - exact event/chunk format, delta vs cumulative text, tool/thinking/citation events, end-of-stream and error-in-stream markers (feeds G2); (6) *limits and headers* - rate-limit/quota headers, `Retry-After`, usage counters, upsell/limit payloads (feeds D2/N); (7) *versioning* - build ids, deploy hashes, feature-flag/config payloads and A/B flags that change behaviour (feed B9 drift detection). Everything is stored locally as a compressed, credential-redacted capture set with an index (`analysis/<host>/captures/`) so analysis is repeatable offline. *Acceptance:* a mock site with multi-step bootstrap (token fetched before use), a WebSocket variant, a multipart upload, a GraphQL variant and a cumulative-text stream is fully mapped: the dependency graph, state machine and stream grammar in the report match the mock's ground truth exactly; a third-party telemetry host is listed and excluded.

**O21 — Per-site source analysis with a real toolchain (every site is different; nothing is shared by assumption).** Treat each site as its own project. The bridge collects the site's complete front-end as served: HTML, all JS bundles/chunks (including lazily loaded ones), source maps when published, service workers, web workers, JSON config/bootstrap payloads, and WASM modules (listed; WASM is `unknown` unless it is pure and can be verified), together with the recorded traffic. It then analyses it **statically and completely** with proper tooling instead of regex guessing: beautify/unminify, parse to an AST, split bundler output (webpack/vite/rollup-style module maps), build a call/data-flow index from the network call sites (fetch/XHR/WebSocket/EventSource) back to where each URL, header, body field and token value is produced, and extract exactly those functions and constants with their dependencies (O20). Output per site: `analysis/<host>/report.md` + machine-readable index (which module builds the request, where the token comes from, what is static / session-derived / per-request-computed, what is unknown), tied to script hashes. **Tooling:** the implementing agent and, with the owner's consent shown once in the dashboard, the bridge may install what the analysis needs (a JS parser/AST toolkit, beautifier, source-map and bundle-unpacking tools, an optional JS sandbox engine) - **into a local folder** (`bridge_data/tools/`, never system-wide), from official package registries only, with pinned versions and recorded hashes, and the analysis itself runs offline on the captured files (no site content leaves the machine; credentials are never part of the analysed material). If a tool is unavailable the step degrades to a clearly labelled lower-confidence path or `unknown` - never to guessing (O20). Analysis is re-run only when a script hash changes (O6/B9 budgets apply). *Acceptance:* two mock sites with different bundler layouts, token schemes and stream formats are each analysed from their own served files and produce correct, different modules; a changed script triggers re-analysis and fallback; the report lists extracted/verified/unknown per element.

**O23 — Every other surface that matters (the owner said: "anywhere else that needs examining - complete it yourself").** The analysis of O21/O22 also covers, per site: `localStorage`/`sessionStorage`/IndexedDB/Cache API/cookies (which values are session identity, which are client state, which are secrets - and how they are refreshed); the model/feature catalogue endpoints and any client-side model lists embedded in scripts (feeds B); conversation lifecycle endpoints (create/list/rename/delete/regenerate/stop/share, needed for remote hygiene M19 and continuity E1); file/image upload flow and size/type caps (E6/N1/N7/F6); account/plan/usage endpoints and plan-gated features (what the card may show, O12); error and moderation response shapes (D1/M14); locale/region/timezone dependence and geo or IP gating; CSP/CORS/Origin/Referer requirements the native client must satisfy; cookie/consent/terms/onboarding interstitials that block the first request; keep-alive/heartbeat and idle-timeout behaviour (M6/M21); retry and idempotency behaviour of the site's own client (to mimic its patience, not hammer); client-side validation rules (max lengths, allowed characters) so the native client never sends what the site's own UI would refuse; deprecation/maintenance banners and status endpoints (N15). Each item is reported as extracted / verified / unknown with evidence (O20). The agent must add any further surface it discovers to this list and to the ledger as an X-item.

**O5 — AI-assisted reverse-engineering with deterministic validation.** The existing learner (probes + `derive_recipe`) is extended: the connected model may propose where the request body, the conversation id, the model selector, the stream format, the token/anti-CSRF refresh and the error shapes live (strict JSON schema; B3 evidence rule — every claim must literally appear in captured evidence). The bridge itself performs the derivation/replay; **model-written code is never executed raw** — recipes are data (I5); *amended by the owner in v7:* model-written Python may become a site module ONLY through the O27 gates (AST allow-list, restricted namespace, cross-check, O8 battery, quality gate) and never runs anywhere else. Dynamic request parts (CSRF tokens, proof-of-work/sentinel-style challenges, timestamps, signed headers) are detected by comparing ≥ 2 captures and are classified `static | derived-from-session | per-request-computed | unknown`; `unknown` ⇒ no direct tier for that site (honest, falls back to page/ui), not a guess. *Acceptance:* mock sites with (i) static headers, (ii) a rotating CSRF token fetched from a bootstrap call, (iii) a per-request signed header the bridge cannot derive → (i)/(ii) reach direct, (iii) stays on the page tier with the reason shown.

**O17 — Challenge classes: protocol tokens vs anti-bot defences.** Split every dynamic element found in O5 into two classes. (a) *Protocol tokens* that are part of the site's own API contract (CSRF/bootstrap tokens, timestamps, signed or HMAC headers, nonce, simple hash proof-of-work with a stated difficulty): reproduce them **in Python from a small set of audited, built-in primitives** (sha256/HMAC/base64/timestamp/uuid/PoW-loop with a difficulty parameter) declared as data in the recipe; the algorithm must be read from the site's own script (evidence-validated, B3) and cross-checked against ≥ 3 captured browser exchanges (same inputs → same output) before it is trusted. **Reuse the site's own pure client logic:** a function extracted from the site's script that is *pure and deterministic* (inputs -> output, no DOM/canvas/fingerprint/time-of-interaction dependence) may be run **inside a sandboxed JS engine** (an optional engine such as Node or QuickJS in a separate subprocess: no network, no filesystem, no environment variables, memory/time limits, data in/out as JSON only, never given cookies/tokens except the specific inputs the function needs) - far lighter than a browser. It is trusted only after the cross-check above passes, and re-checked when the script hash changes. If no engine is installed, fall back to the built-in primitives, then to the classic path. Code that touches browser state (canvas, WebGL, fonts, navigator/fingerprint, event timing) is class (b): never run with a faked environment. Never execute model-written code, and never execute site code outside that sandbox. (b) *Anti-bot defences* (CAPTCHA, Turnstile-style widgets, fingerprint/telemetry scripts, TLS/behavioural checks, heavily obfuscated rotating challenge code): **not reproduced** (2.4) - the account stays on the page/UI tier, or goes to `needs_human` (O7), with the reason shown. Anything not provably class (a) is class (b) or `unknown`. A recipe that depends on (a) is re-validated whenever the site's script hash changes (B9) and falls back to the classic path automatically if the cross-check fails. Do not promise that direct mode works for every site; say per site which class blocked it. *Acceptance:* mock sites: simple PoW + HMAC header → direct; rotating obfuscated challenge → stays on page tier with the reason; script changes → drift detected → fallback → re-learn.

**O18 — Extracted site logic as native, readable project modules (owner's wording: "as if it were part of our Python project").** What O5/O17 extract is not kept only as opaque recipe data: for each site the bridge writes **plain, readable Python modules** into `bridge_data/site_modules/<host>/` (e.g. `tokens.py` for token/signature/PoW logic ported from the site's script, `protocol.py` for how requests are built and how stream/error/model-list responses are parsed, `identity.py` for the stored browser identity) plus a `manifest.json` (source script hashes, module hashes, validated_at, scenarios passed). The request/response mechanism is **fully native** (the bridge's own HTTP client driven by these modules): zero dependence on the web interface at runtime, so the browser stays closed (O9). Rules: (1) modules are *pure functions + data*; before loading, a static check (AST allow-list) rejects anything but a small set of imports (`hashlib, hmac, base64, json, re, math, time, uuid, struct, urllib.parse`) and forbids `exec/eval/compile/open/__import__`, attribute tricks, sockets, subprocesses, file or env access; (2) they run in-process under a restricted namespace with a time limit; (3) they are hash-pinned: any edit or script-hash change forces re-validation (O8) and the last-known-good set is kept (B9); (4) generated by deterministic translation plus model assistance but **only trusted after the cross-check** of O17 (same inputs -> same outputs against >= 3 captured browser exchanges); anything that cannot be ported cleanly stays on the page tier; (5) the owner can open, read and edit them from the dashboard (O12 "show module"), and `--export-bundle` carries them. Hard-to-port logic may use the sandboxed JS option of O17, but ported Python is preferred.

**O19 — Browser identity profile, replayed honestly.** At login the bridge stores the identity of the browser the owner actually used: User-Agent, `sec-ch-ua*`, `Accept*`/language headers, platform/timezone/locale as the browser sent them, and the session cookies/storage. The native client replays exactly that identity (same header set and order as captured) wherever the recipe needs it, so requests are consistent with the session they belong to. **Boundaries:** it replays the owner's own real identity; it does not invent another one, rotate identities, impersonate TLS/JA3 fingerprints, simulate mouse/keyboard behaviour, or add stealth tooling (2.4). The assumption that sites do not check for automation is **not guaranteed**: if a site rejects the native client (blocked, challenge, changed behaviour) the account classifies it (D1, O17), falls back to the page/UI tier or `needs_human`, and the dashboard says why. Request pacing stays modest and bounded (no bursts that look like abuse); respect measured limits (M16).

**O8 — Validation battery before promotion to `stable_direct`.** On the real account (mock in tests) run, through the *direct* recipe: single turn; streaming; multi-turn with remote continuity (E1); a long message near the site's paste/attachment threshold (E6/N1); an error case (bad input → classified correctly, D1); cancellation (G6); a text tool-call round trip (F1); and the same battery again after a session refresh. Promotion rule: all pass in **≥ 2 independent sessions/runs separated in time** (configurable gap, default ≥ 5 minutes) with parity against the page-tier answers on the same prompts (same stream completeness, no truncation). Failure ⇒ stay on the lower tier, keep the evidence, retry later with backoff (no hot loop). The promoted recipe is versioned, keeps the last known good (B9) and records `validated_at`, the scenarios passed and their measured latencies (real numbers, F8).

**O9 — Browser only for login, refresh and repair; zero browser RAM when stable.** At runtime the stable direct path needs no browser, and **no browser process may exist** while every account is `stable_direct` and idle (the owner's RAM goal). Session renewal is first done *directly* (the refresh/token endpoint captured in O5) so the browser is not needed for it either. The browser launches (headless) only to: refresh an expiring session (M21/N9), recover from `needs_login`, or run a repair. Idle-close timers verified (J5). If a refresh needs the owner (login again), `needs_login` is raised with a card action. *Acceptance (RAM):* after promotion on the mock, no browser child process exists (checked in the process table) and the memory before/after is reported as measured numbers; relaunching for a refresh/repair and closing again leaves no leaked process (J5). Repair: on drift evidence (B9) the account moves to `degraded_fallback` (classic path, requests keep working) while a background re-learn runs (bounded, O6); success ⇒ re-validate (O8) ⇒ back to `stable_direct`.

**O14 — Model choice after discovery.** After O5/B-group discovery the owner can choose per account which discovered model/mode is used (when the site really offers a selector the bridge can drive), per policy (C1) or fixed; when a site offers only one model the selector is absent, not faked. Choices persist and survive recipe repair (re-resolved by native id, A2).

**O13 — Rotation that the client never notices.** (Builds on C, D.) Before an account is likely to fail, keep a *warm standby*: a validated, non-limited route whose session was checked cheaply. Switch only at safe boundaries (D4) and between turns when conversation affinity allows; with D6 handoff the next route continues the task. Soft-limit awareness (M16) lets the owner's policy rotate *before* a hard limit when it is measured, not guessed. Claude Code must not see an error unless every eligible route is exhausted. *Acceptance:* a multi-step Claude Code transcript on the mock with an injected model limit, an account limit, a `needs_human` event and a stable-recipe break in the middle → the client-visible stream stays protocol-valid and the task completes; rotation events are visible in the live view (H3).

**O12 — Account cards from what was actually discovered.** After reverse-engineering each card shows only what is true for *that* account: status (O1), tier in use and why, login/session health and expiry if known, discovered models/modes with tri-state capability chips (B5), features detected (streaming, native/emulated tools, images, file upload, remote memory, thinking modes, long-paste→attachment threshold), **measured** latency/reliability/limits (never invented, F8/M16), learning cost (O6), last events, and the one-time provider-terms notice (2.4). Everything is **owner-controllable**, applied immediately and recorded in the event list: enable/disable; priority/weight; allowed/forbidden models; per-feature switches (allow images, allow attachments/long-paste conversion, allow rotation into this account, max concurrency, soft daily cap); "use only for" task types (M3); alias/label; actions: test now, re-login, re-learn, rollback recipe, show browser, export recipe. Unknown stays `unknown`, never a fake toggle.

**O11 — Site directory (clean, editable, honest).** A tidy, searchable directory in the dashboard of sites that offer AI models: category `official_chat`, `model_arena_compare` (blind/side-by-side sites), `aggregator`, `api_compatible` (official APIs — use the API tier), `other`; each entry: name, home URL, notes, "how to add" hint, status (`not added | added | needs login`), and a `verified_at` date. The shipped list is *data* (URLs and names only, no model names, B7), clearly labelled "starter list — verify before relying on it", loaded from an editable file in the data folder, with "add custom site". One click starts O2/O3 for that entry. Arena-style sites follow M26.

**O15 — Autonomous mode (of the bridge).** `--autonomous` / `autonomous: true`: the bridge runs unattended — auto-discovery, auto-validation, auto-repair, auto-refresh, and rotation inside the owner's policy without prompts; `manual_approval` switches are auto-approved only if the owner wrote an explicit allow rule; events that truly need a human (login, CAPTCHA, MFA) are queued on the dashboard (and OS notification, optional) while work is routed around them; every autonomous action is bounded (budgets, backoff, kill switch `POST /api/autonomous/off`) and appears in the event log. **Explicit boundary:** the bridge never executes tools or commands for Claude Code, and it cannot grant Claude Code any permission. Claude Code's own unattended/permissive mode is configured *in Claude Code*; `--doctor` prints the recommended client settings for an unattended session and states plainly that loosening them removes the client's safety prompts and is the owner's decision.

**ORDER OF WORK (owner principle: respect prerequisites; otherwise make it real).** O24-O29 depend only on steps that already exist in the code (O4, O5, O6, O16-O23, O8, O9, all PARTIAL on mocks). Nothing else has development precedence over them, so they are the NEXT STEP, in this order: O25 -> O26 -> O27 -> O28 -> O29. The remaining dashboard work (O12 remainder, O13/O15 cards, O11 review) follows afterwards, unless a bug found while doing O25-O29 blocks them. The only external prerequisite is evidence from the real world: after O29 the owner runs ONE real site end to end and pastes the log; the next turn fixes what the log shows before anything new is built.

**O24 — Brain-driven learning: principles and boundaries.** (1) The investigation is *reasoned*, not scripted: the brain decides what to look at next from what it has seen; the bridge never contains a per-site recipe of how to learn. (2) The brain is the connected account's own model reached through the best tier that already works (classic UI/page tier through the owner's Chrome; an official API account if one is configured for this purpose). It is unreliable and small-context: every call is bounded, evidence is sliced, every claim is verified. (3) Safety is unchanged and non-negotiable: secrets never reach the brain (O4/O16 `guard_for_model` REFUSES, never masks), all quoted text is `neutralise`d, nothing the brain says is trusted without the deterministic gates, a model answer can only *point* or *propose*, never promote. (4) Cost is visible and bounded (O6, see O25). (5) Everything the brain concludes is stored as data with provenance (capture id or script sha256 + line range) so a human can audit it (O20). (6) If the brain is unavailable, wrong or exhausted, the site stays on the classic tier; learning failing must never break serving. *Acceptance:* a test that greps the source for site/provider names and per-site branches in the learning code finds none; a scripted fake brain that answers nonsense changes nothing.

**O25 — Brain channel.** One class (`Brain`) with `ask(task, evidence, schema) -> validated JSON` over the account's working tier. Rules: strict JSON schema in/out with repair-free parsing (one reformat request at most); evidence passes `evidence_for_model` (O4) and the budget is spent through O6 `spend` BEFORE the request; hard caps on prompt size per call (slices, never whole captures; reuse E4 vault refs); each call, its purpose and its cost are logged (J1) without any evidence text; a per-site cache keyed by evidence hash so an identical question is never asked twice; raise the default learning budget for the brain loop to a configurable ~40 requests per site (visible meter, owner can change it, 12 stays the limit for the old single-shot path); a deterministic *fake brain* (recorded answers) for tests. *Acceptance:* with the fake brain, a site is analysed with zero real requests; with the budget at 0 nothing is sent and the report says why; a canary secret placed in evidence makes the call refuse.

**O26 — Investigation loop.** The brain works like an engineer in rounds (bounded, e.g. <= 8): (a) it is given the site map (endpoints, roles, dependency graph from O22; extracted function list from O21; surfaces from O23) and the goal ("reproduce one chat turn without the browser, including conversation continuation and token refresh"); (b) it answers with the NEXT ACTION from a small closed set: `view_capture(id, field)`, `view_script(sha, line_range)`, `compare(capture_a, capture_b)`, `hypothesis(part, claim, evidence_quotes)`, `experiment(kind, params)` where experiments are executed by the bridge (omit one header, replay with a changed value, replay without a cookie) inside the O6 budget and only against requests the O16 rules allow (no side effects beyond a normal chat turn); (c) every `hypothesis` must quote evidence that literally exists (B3/O5 rule) and is then confirmed or refuted by an experiment or a replay across >= 3 captures; (d) refuted hypotheses and the reason are fed back; (e) the loop ends with `spec` (data for O17/O18) or `give_up(reason)` - giving up is a valid, honest outcome that keeps the site on the classic tier. *Acceptance (mock sites):* a site whose header is a custom hash of (timestamp, body) over a served script is solved from the script by the loop (fake brain replaying a correct run), a wrong hypothesis is refuted by an experiment and not used, a site with a CAPTCHA-style token ends in `give_up` / `needs_human`.

**O27 — Brain-authored native modules with a code-quality gate.** The brain writes the Python modules of O18 (`tokens.py`, `protocol.py`, optionally `identity.py` data) against a fixed interface (templates the bridge supplies: function names, inputs/outputs, no I/O). The bridge never runs them raw. Gates, ALL required, in this order: (1) AST allow-list and restricted namespace of O18 (unchanged); (2) provenance: every constant and algorithm step carries a comment `# source: <script sha256[:12]> lines a-b` or `# capture: <id>` that the bridge CHECKS literally against the source (O20: unverifiable = rejected); (3) cross-check: identical output on >= 3 captured exchanges (O17); (4) the O8 battery; (5) **engineering quality gate (measurable, enforced by AST, the owner's "senior engineer" bar):** small pure functions (<= 40 lines, <= 10 branches, <= 5 parameters), descriptive names, type hints and a one-line docstring on every public function, no magic numbers without a named constant that cites its source, no dead code or unused imports, no bare `except`, no global mutable state, explicit errors (typed) instead of silent defaults, deterministic output, and a generated minimal test file per module (`test_<module>.py`: the captured inputs/outputs as data) that the bridge runs. A failing gate sends the concrete failure (test diff, rule name, line) back to the brain for a fix: at most 3 rounds, inside the budget; then the site stays on the classic tier and the failed draft is stored for inspection, never promoted. *Acceptance:* a draft with a hidden `import os` is refused; a correct but messy draft (200-line function, magic numbers, no docstrings) is refused with the rule names and passes after the fix round; a draft whose constant is not in the cited lines is refused.

**O28 — Independent engineer review (advisory).** After the gates pass, a second, separate brain call receives the module, the cited source slices and the failing/passing test data and answers a fixed checklist (does the code match the source, is anything guessed, edge cases, readability). Findings are shown in the account card and the site report; they never promote and never block by themselves; a finding that names a concrete, checkable defect triggers one extra gate run. *Acceptance:* a draft with a subtle off-by-one that passes the 3 captures but contradicts the cited source is flagged by the fake reviewer and the flag appears in the report; the review costs at most one counted request.

**O29 — Live wiring and promotion.** The learner (`_learn_fresh` / `_finish_analysis`) calls the O26 loop for every NEW site after the classic recipe is verified (so the owner is never blocked), and again on drift (B9/O9 repair, within the repair budget). Success writes modules + `native.json` -> O8 battery -> `stable_direct` (only through `lc_transition` with a validation id) -> the browser closes (O9); failure leaves the site on the classic tier with the reason on the card. The dashboard shows the loop's progress (round, spent/budget, current hypothesis, gate results) and a plain-language verdict: "direct", "browser needed because <reason>", "needs you". *Acceptance:* end to end on the mock suite: login -> classic recipe -> brain loop (fake brain) -> modules -> battery -> `stable_direct` -> second request served with no browser process (O9 `o9_measure`); a drift on the mock site sends it back to the classic tier and repairs it. REAL-RUN GATE: the owner runs one real site, pastes `bridge.log` / the diagnostic report; the next turn fixes what it shows before any new feature.

## 5. TARGET ARCHITECTURE (inside one file)

Organise the file in clearly banner-separated sections, in dependency order:

1. Constants, version, config schema + migrations
2. Utilities (time, hashing, redaction, safe JSON, URL/SSRF guard, atomic store, locks)
3. Typed errors + classifier
4. Data model (Provider/Account/ModelVariant/Capability/Route/Policy/Decision/TaskState/SiteProfile)
5. Stream decoding / text extraction
6. Transports (direct / page / ui) and recipe client (**unchanged behaviour preserved, extended for model selection and discovery**)
7. Learning pipeline (capture, derive, validate, verify, AI-repair, discovery)
8. Account manager (lifecycle, sessions, health, catalogs)
9. Routing engine (resolver, eligibility, policies, scoring, circuit breakers, decision log)
10. Context engine (canonicalisation, hashing, budgeting, summaries, continuity/trust, submission strategy)
11. Tool layer (schema handling, call grammar, parser, validator, repair)
12. Orchestrator (one request lifecycle shared by both protocols)
13. Protocol normalisers and SSE writers (Anthropic, OpenAI)
14. HTTP server, auth, dashboard API
15. Dashboard HTML/JS (served from a string constant)
16. Self-test suite and mock site (guarded behind `--selftest`)
17. CLI / main

Keep functions small, avoid global mutable state (hold state in objects with locks), prefer pure functions for anything testable (resolver, eligibility, ranking, delta detection, budgeting, parsing, classification).

---

## 6. WHAT ACTUALLY RAISES OUTPUT QUALITY (engineering checklist)

Use this to decide trade-offs. When in doubt, prefer whatever increases the chance that Claude Code completes a multi-step coding task correctly.

1. **Never lose task-critical text** (E3/E4) — most "dumb model" failures here are caused by truncation or missing tool output.
2. **Make tool calls valid the first time** (F1) — one invalid call costs a whole turn and quota.
3. **Keep the same conversation alive** (E1) so the model keeps its own context and you pay for deltas only.
4. **Pick a capable variant for the job** (C2/C3/F8) and use reasoning modes where they exist (F5).
5. **Stream promptly and correctly** (F7/G2–G4); a hung or malformed stream breaks Claude Code worse than a slow model.
6. **Fail loudly and precisely** (D1/C6) so the owner can see which route and why.
7. **Do not over-engineer the prompt wrapper**: the instructions the bridge adds around the client's own system prompt should be as short and unambiguous as possible; measure the effect of changes on the tool-call-validity metric using the mock/benchmark harness.

---

## 7. TESTING (mandatory — but timing and volume are governed by §0A: lean during implementation, systematic QA campaign at the end)

### 7.1 Offline mock site (build it inside `--selftest`)
A local HTTP server that imitates chat websites, configurable per scenario:
- login/session cookie, expiry on demand, login-page-with-200 on expiry;
- chat endpoint with SSE (and a JSON-lines variant and a non-stream variant);
- model selection by body field **and** by separate call **and** by UI-only dropdown (UI tests are optional if Playwright is unavailable — report that);
- model list endpoint present/absent/changed/renamed/removed;
- server-side conversation memory (remembers / forgets after N / silently resets);
- hidden vs. revealed model identity (including revealed-after-reply);
- rate limits: model-scoped, account-scoped, ambiguous text, `Retry-After`;
- long paste → attachment conversion with upload quota;
- failures: connect refused, timeout, mid-stream disconnect, malformed event, empty answer, request accepted but response lost;
- native tool-calling variant and text-only variant.
Also a mock official-API (OpenAI-style) server for `ApiBackend`.

### 7.2 Required scenarios (all must exist as automated tests)
A normal auto routing · B exact selection of unavailable model (no silent substitute) · C model-level limit → permitted sibling · D account-level limit respected (wait/approved alternative only) · E failure before first output → allowed fallback, protocol-valid · F failure after partial output → honest termination, no splice · G ambiguous acceptance → no blind resend · H capability mismatch (image/tool) · I stale discovery/recipe · J memory continuity across route change (tool results and checkpoints preserved) · K text-first submission vs. attachment conversion across several turns · L concurrent requests (no state leakage, race-free counters) · M restart persistence of task state/catalog/continuity map · N migration from a 7.0 data directory fixture · O Claude Code multi-step transcript (request → tool_use → tool_result → follow-up tool_use → failing test → fix → final) via both protocols, with a route change in the middle · P client disconnect mid-stream · Q prompt-injection in tool results · R hostile dashboard strings · S session/sub-agent isolation and divergence classes (append, rewind, fork, compact, clear, interrupt) · T arena-style site (battle/side-by-side/identity revealed later) · U silent model downgrade · V truncated-output continuation byte-identical · W pre-flight edit validation with one bounded repair · X rollover before the site's conversation-length limit · one test per row of the N table.

### 7.3 Other groups
- **Unit/property:** resolver, eligibility reasons, rotation strategies, circuit breaker with fake clock, error classifier, delta detection fuzz (D4 regression), budget/compaction needle tests, parser corpus, SSE decoder split-at-every-offset, writer conformance, cache key isolation, redaction.
- **Protocol conformance:** parse every produced Anthropic/OpenAI stream with an independent strict parser inside the test code.
- **Security:** missing/invalid/revoked keys; admin endpoints without admin key; hostile `Origin`; wrong `Host`; oversized body; wrong methods; path traversal in slugs; SSRF targets (127.0.0.1, 169.254.169.254, private ranges, redirect to private); malicious recipe JSON; secret-leak scan of all API responses and logs for a canary secret; cross-key cache contamination; cross-account state contamination.
- **Resource:** thread/FD/browser leak check after many cancelled and failed requests; memory growth bounded under 1,000 requests.
- **Benchmark harness (offline, reproducible):** same workload on the original `bridge.orig.py` and the new file against the same mock site: payload bytes per turn (E1), time-to-first-token, total latency percentiles, tool-call validity rate, retry count, success rate through injected faults. Report real numbers, state the method, and report regressions honestly. No claims about Codex/Antigravity without an actual fair comparison you performed.
- **Live smoke (opt-in only):** `--selftest --live` against configured accounts with minimal requests. If no accounts exist, say "not run".

### 7.4 Gate rules
- Per phase: smoke check + the tests of what you touched (§0A). The full suite runs when shared core changes, at the start of the QA campaign, and once before delivery. Fix, rerun the affected tests, then rerun everything before the final report.
- The file you test must be byte-identical to the file you deliver (print its SHA-256 in the report).

---

## 8. PHASES (with exit gates)

1. **Baseline** — read everything, `BASELINE.md`, run baseline checks, build the mock site skeleton. *Gate:* defect table verified/refuted; migration fixture saved.
2. **Safety net** — data model, typed errors, persistence/migration, locks, redaction, cache fix (D3), signature fix (D4), writers/decoder conformance tests. *Gate:* A, G, I-basics green.
3. **Discovery** — recipe extension for model selection, catalogs, SiteProfile, refresh lifecycle, change detection, LLM-assisted discovery with validation. *Gate:* B1–B9 green.
4. **Routing** — resolver, eligibility, policies, profiles, scope-aware limits, retries/circuit breaker, decisions, `/v1/models`. *Gate:* C, D1–D4 green.
5. **Context & continuity** — canonical state, trust/continuity, delta, budgeting, tool-result handling, summaries, text-first, and the limit-scenario catalogue (group N). *Gate:* D5–D7, E, N green.
6. **Agent quality** — tool layer, Claude Code compatibility corpus, parameter fidelity, thinking, images, latency, and the whole of group M (session identity, divergence detection, request classification, pre-flight tool validation, parallel calls, keep-alive, continuation, fidelity). *Gate:* F, G, M green.
7. **Onboarding & reverse-engineering pipeline** — group O, built strictly in the *Implementation order* table at the start of group O (governing rules -> state/storage/add/login/human hand-off -> capture and analysis -> extraction and native modules -> validation and browser-off -> routing/experience -> autonomy). Work in sub-steps 7a-7f along those bands; smoke-check after each band (§0A). *Gate:* O green on the mock.
8. **Dashboard** — panels, site directory, account cards and controls, safe rendering, live view. *Gate:* H and O11–O12 green.
9. **Security & hardening pass** — I, J, K, resource tests, adversarial review.
10. **QA campaign** — the phased, tick-or-reject checklist of §0A item 5 (`_work/QA.md`); this is where the systematic testing and mutation checks happen.
11. **Ledger audit** — re-verify every ID against the QA results, benchmark vs. baseline.
12. **Delivery** — final file, report.

---

## 8A. TRACEABILITY APPENDIX (nothing proposed earlier is allowed to fall through)

Earlier brainstorming produced three numbered idea lists (items 1–29, items 1–51, items 52–72) plus the owner's own messages. Every item maps to ledger IDs below. During the final ledger audit, confirm each row has evidence.

**Idea list A (items 1–29):**
1 cache correctness → G7 · 2 continuity/session identity → E1, E2, M1, M2 · 3 model/route selection → C4, C1 · 4 history/summary → E3, E5 · 5 protocol layering → G1, §5 · 6 full Anthropic API coverage → F3, G3 · 7 native vs emulated tools → F1, F2 · 8 images → F6 · 9 `max_tokens`/probe shortcut → F3, M3 · 10 first-token latency → F7, M6, M20, M21 · 11 concurrency → C8, G6, M18 · 12 errors/retry → D1–D4 · 13 fast/balanced/quality → C2 · 14 context engine → E3–E5 · 15 multi-layer memory → D5, E1, E5 · 16 structured summaries → E5 · 17 reasoning/parameters → F4, F5, M7 · 18 quality by tasks not prompts → §7.3, M11 · 19 capability registry → B5 · 20 fallback classes → C1, D4, C10 · 21 backend by task type → C2, M3 · 22 secrets → I3 · 23 input/network hardening → I4, I6 · 24 safe failure → D4, A4, B9 · 25 structured final report → M-note below · 26 isolated worktrees → K2 · 27 validation loop → M4 · 28 sub-agents → M1, M18, K2 · 29 MCP → F3, K2.
*M-note (items 25–29):* the final report text and the choice to use worktrees/MCP belong to Claude Code and the model; the bridge's duty is to carry tool schemas, large tool lists, and results **faithfully** (F1, E4, D5), keep sub-agents isolated (M1, M18), help the model succeed (M4), and expose a per-task evidence trace in the dashboard (H3, J1).

**Idea list B (items 1–51):**
1 server-side memory → E1 · 2 hybrid local+server memory → D5, E1 · 3 trust score → E1 · 4 delta/duplicate suppression → E2, M12, M13 · 5 conversation state machine → M2, D5 · 6 per-site profile → B8 · 7 behaviour-change detection → B9 · 8 session isolation → M1, I-group · 9 text-first submission → E6, N1 · 10 text→file detection → E6, B8 · 11 attachment/quota awareness → E6, M16, N1, N2 · 12 efficient large-content transfer → E3, E4 · 13 limit-type classification → D1, D2 · 14 respect service limits → §2.4, D2 · 15 layer separation → G1, §5 · 16 real Claude Code API compatibility → F3, G3, G4 · 17 native vs emulated → F2 · 18 full tool validation → F1 · 19 SSE state machine → G2–G4 · 20 stop/end mapping → G3, G4, M9 · 21 images/blocks → F6 · 22 parameters → F4 · 23 token budget → E3 · 24 multilayer memory → D5, E1 · 25 structured summaries → E5 · 26 targeted retrieval → E3, E4 · 27 big tool results → E4, M12 · 28 protect system prompt/schemas → E3 · 29 data vs instruction → E8 · 30 latency measurement → J1, F7, M28 · 31 connection/resource management → J5, M21 · 32 capability registry → B5 · 33 predictable model → C4, C1 · 34 smart retry → D3 · 35 concurrency/cancel → C8, G6, M18 · 36 cache redesign → G7 · 37 account health → D3, J2 · 38 key/cookie protection → I3 · 39 dashboard/request protection → I1, I2 · 40 recipe validation/versioning → B9, I5 · 41 recovery → D4, D5 · 42–46 agent-style reporting, worktrees, validation loop, sub-agents, MCP → see M-note · 47 benchmark → §7.3 · 48 observability → J1, C6 · 49 failure tests → §7.2 · 50 compare three profiles → C2, §7.3 · 51 per-site regression → B8, §7.1, M24.

**Idea list C (items 52–72):**
52 dynamic discovery → B2, B3 · 53 capability registry → B1, B5 · 54 versioned discovery → B6, B9, A3 · 55 adaptive site profile → B8 · 56 fixed/rotation/failover → C1 · 57 limit scope → D2 · 58 mid-task model change → D4, D6 · 59 model-vs-account error → D1 · 60 dynamic dashboard → H1–H4 · 61 rotation policies → C1 · 62 pool vs ensemble → C9 · 63 show real route → C6, C7, H3 · 64 eligibility → C3 · 65 evidence-based quality → F8 · 66 explainable decisions → C6 · 67 canonical state → D5 · 68 checkpoints → D5, D6 · 69 task id ≠ model id → D5 · 70 model-change preview → C10 · 71 shadow evaluation → C11 · 72 route observability → J1, C6.

**Owner's own messages:**
better than API-key Claude Code → §1.1–1.3, all of M · use server memory, repeat less → E1, E2, M12, M13 · avoid actions that make the site restrict you (text→file) → E6, N · "find the other scenarios yourself" → N, M, and §1.1 item 2 (ADDED BY AGENT rule) · DeepSeek/GPT/LMArena/DesignArena, per-account models, rotation, mid-work limit handling → B, C, D, M26 · dynamic dashboard fed per account, shown real model, no hard-coding → B3, B7, H, C6, C7 · single Python file, English prompt, no omissions → §2.1, §0 · confusion about the AI forgetting → §0.

---

**v7 additions → brain-driven learning (the model of the connected account is the reasoning engineer; gates decide) → O24-O29.** **v5 additions →** total network analysis → O22 · all other surfaces → O23 ·  per-site full source analysis with a local toolchain → O21 ·  extract-not-guess → O20 ·  extracted site logic as readable native Python modules + stored browser identity → O18, O19 ·  login-then-reverse-engineer-then-direct flow → O1, O3–O9 · direct only after validation, browser only for login/refresh/repair → O8, O9 · portable folder, no re-login on another machine → O10 · what to type when adding a site → O2 · visible login, hide, CAPTCHA by the human → O3, O7 · site directory (official, arena/compare) → O11 · model choice after discovery → O14 · smooth rotation for Claude Code → O13 · per-account cards with owner controls → O12 · autonomous mode → O15 · implement-first / lean tests / final QA campaign → §0A.

## 9. FINAL ADVERSARIAL REVIEW (answer each, with evidence)

Fresh install starts? Upgrade from 7.0 data keeps accounts/sessions/recipes? Can a malformed request crash the server? Can a login page be mistaken for an answer? Can a stale recipe route to the wrong model? Can two parallel requests corrupt rotation/counters? Can a route change drop the original system prompt or tool schemas? Can a retry cause the client to run a tool twice? Can a partial stream be reported as success or spliced with another model? Can a tool result be cut in a way that changes meaning? Can account A's cookies/conversation reach account B? Can a failed discovery erase a good catalog? Can any loop retry forever? Can a secret appear in logs/responses/dashboard? Can a URL reach internal services? Can injected text in a tool result cause a tool call? Does any dashboard control do nothing? Are all latency/usage numbers measured or labelled estimated? Is every ledger ID either DONE with evidence or reported PARTIAL/BLOCKED honestly? Is the delivered file the tested file and the only application source file?

---

## 10. FINAL DELIVERABLE AND REPORT

Deliver: the single `bridge.py` (save it to a real path and give the exact path, size, SHA-256).

Report format (be precise, separate fact from opinion):
1. Executive summary
2. Baseline findings (D-table with verified/refuted)
3. Architecture changes
4. **Full ledger table** (ID · status · evidence), including every X-item you added and why
5. Bug fixes with before/after
6. Discovery, routing and recovery behaviour as implemented
7. Context/continuity/text-first behaviour as implemented
8. Protocol and Claude Code compatibility notes
9. Security: fixed, remaining risks
10. Tests executed: exact commands, counts, pass/fail, and anything not run (with reason)
11. Benchmarks: method, baseline vs. new, regressions
12. Live verification: what was truly tested on real sites (likely nothing) vs. mock-only
13. Known limitations and provider-specific unknowns
14. How to run / selftest / live-test / back up / roll back
15. Highest-value next steps

Do not call it production-ready or better than any commercial product without evidence you actually produced. If something could not be finished, deliver the highest-priority safe subset in a consistent, working state and document the gap — never a half-edited file.

Begin now: read the whole of `bridge.py`, create the scratch folder and ledger, and start Phase 1.
