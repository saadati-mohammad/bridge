#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Local Bridge V6.4
==========================

Anthropic/OpenAI-compatible local gateway for Claude Code, backed by a real
chat.deepseek.com browser session (Playwright).

MULTI-INSTANCE MODEL
--------------------
One bridge process owns exactly one instance home, one config, one browser-profile set,
one log/attachment tree and one TCP port. The default instance home is the folder containing
this script. Use --instance DIR to choose another home. Run copies side by side with different
ports, for example: `python bridge.py --instance C:\bridge-B --port 8789 --ai deepseek --panel`.
An agent can launch another copy from another folder without sharing config, browser profiles,
logs or swarm attachments. A port is reused only when /health proves it is the exact same
script + instance home + config; a different instance on that port is a hard error.

PORT PRECEDENCE
---------------
CLI --port > DS_BRIDGE_PORT > saved config `port` > DEFAULT_PORT (8788). CLI --port is
process-local and is written only with --save-port. The env var likewise affects only the current run.
Mode precedence remains Claude Code's own permission flag > --mode/--safe/--ask/--auto >
DS_BRIDGE_MODE > saved mode > safe. `--panel` means foreground service/dashboard mode; combined
with --ai it starts that provider and keeps the process in panel mode. With no --ai in a non-TTY
launch, an enabled saved web account (prefer pinned) is used; otherwise the process exits non-zero
and explains how to start it explicitly.

INSTANCE CLI
------------
--instance/--instance-home, --instance-name, --list-instances [start-end], --save-port,
--print-paths, --force-claude-commands, --install-commands-into.

CURRENTLY HONORED DS_BRIDGE_* ENVIRONMENT VARIABLES
----------------------------------------------------
DS_BRIDGE_ACCOUNT_WAIT, DS_BRIDGE_ACCOUNTS_DIR, DS_BRIDGE_API_TIMEOUT, DS_BRIDGE_CHANNEL,
DS_BRIDGE_CHARS_PER_TOKEN, DS_BRIDGE_CHAT_URL, DS_BRIDGE_CLAUDE_HOOK_EVENTS, DS_BRIDGE_CONFIG,
DS_BRIDGE_COOLDOWN_BASE, DS_BRIDGE_COOLDOWN_MAX, DS_BRIDGE_DEBUG_DIR, DS_BRIDGE_DELETE_OLD_CHATS,
DS_BRIDGE_DELTA_BLOCK_LIMIT, DS_BRIDGE_HEADLESS, DS_BRIDGE_HISTORY_BUDGET_CHARS, DS_BRIDGE_HOOK_KEY,
DS_BRIDGE_HOOK_URL, DS_BRIDGE_KEEP_GOING, DS_BRIDGE_KEEP_GOING_MAX, DS_BRIDGE_KEEP_RECENT_MESSAGES,
DS_BRIDGE_LOGIN_WAIT, DS_BRIDGE_MAX_CONTINUES, DS_BRIDGE_MAX_FILES, DS_BRIDGE_MAX_FILE_BYTES,
DS_BRIDGE_MAX_HTTP_BODY_BYTES, DS_BRIDGE_MAX_KEPT_CONVS, DS_BRIDGE_MAX_PROMPT_CHARS, DS_BRIDGE_MAX_REPAIRS,
DS_BRIDGE_MAX_REPLY_SECONDS, DS_BRIDGE_MAX_RETRIES, DS_BRIDGE_MAX_TABS, DS_BRIDGE_MODE, DS_BRIDGE_OLD_BLOCK_LIMIT,
DS_BRIDGE_OPEN_DASH, DS_BRIDGE_PARALLEL_MODE, DS_BRIDGE_PARAM_DESC_LIMIT, DS_BRIDGE_POLL_SECONDS,
DS_BRIDGE_PORT, DS_BRIDGE_PROFILE_DIR, DS_BRIDGE_READY_TIMEOUT, DS_BRIDGE_REQUEST_GAP, DS_BRIDGE_RETRY_BACKOFF_MAX,
DS_BRIDGE_ROTATE_CHARS, DS_BRIDGE_STALL_TIMEOUT, DS_BRIDGE_SUBMIT_TIMEOUT, DS_BRIDGE_SWARM_AGENTS,
DS_BRIDGE_SWARM_AGENT_TIMEOUT, DS_BRIDGE_SWARM_ATTACH_DIR, DS_BRIDGE_SWARM_FIX_ROUNDS, DS_BRIDGE_SWARM_MAX_AGENTS,
DS_BRIDGE_SWARM_REVIEW, DS_BRIDGE_THINK_MODE, DS_BRIDGE_TOOL_DESC_LIMIT, DS_BRIDGE_UI_MODE,
DS_BRIDGE_UI_PERFORMANCE, DS_BRIDGE_UPLOAD_TIMEOUT. Explicit path env vars remain overrides; defaults are instance-local.

What is new in V6.2 (ACCOUNT TYPES, QUALITY TIERS, LIVE VIEW, PARALLEL AGENTS)
------------------------------------------------------------------------------
* MORE ACCOUNT TYPES: besides DeepSeek website logins you can add Grok (xAI API key), Claude (Anthropic API key),
  OpenAI, OpenRouter, DeepSeek API or ANY OpenAI-/Anthropic-compatible endpoint. Each account has a QUALITY TIER
  (1 Basic ... 5 Top, guessed from the model name, editable), a parallel-request limit, optional prices + a budget.
  API accounts report exact token counts and cost; keys are stored 0600 and never sent to the browser.
* SMART ROUTING BY QUALITY (automatic): Claude Code already tells the bridge how hard the job is through the model
  name - opus (planning / decisions) -> your strongest account, sonnet (normal coding) -> the cheapest account that
  is good enough, haiku (titles / small jobs) -> the cheapest. `/model opusplan` in Claude Code therefore uses
  your best account to plan and a cheaper one to implement. Swarm planners / reviewers use the strongest account.
* LIVE VIEW: a mirror of the Claude Code console in the panel (every request, reply, tool call, account, tier,
  tokens) - full page, or as a DOCK next to any panel page so you see both at once.
* /panel [live|swarm|...] opens the panel from inside Claude Code.
* SWARM (/swarm <goal> or the Swarm page): a planner splits the goal into tasks with disjoint file ownership; N agents
  (Claude Code processes) build them AT THE SAME TIME, each in its own git worktree + branch; each result is
  checked (tests auto-detected), fixed automatically when the check fails, optionally reviewed by a stronger account,
  merged (conflicts are resolved by an agent or reported) and applied to your branch only when you press Apply.
  The number of agents is adjustable live. With API accounts the parallelism is real; with DeepSeek website accounts it
  equals the number of accounts (one browser chat per account).
* /ds set <NAME> <value>, /ds settings, /ds tier <account> <1-5> from the Claude Code console.

What is new in V6.1 (FULL WEB PANEL, FILES, IMAGES)
---------------------------------------------------
* The panel (http://127.0.0.1:8788/dash) now does EVERYTHING the terminal does, for non-technical people:
  Dashboard (accounts), Chat (Claude-Code-style, streaming, markdown, slash commands, attachments),
  Launch (pick a folder + mode, then open Claude Code in a new terminal window with one click, copy the
  command, install Claude Code, run the self-test), Console (live log + every command), Connect (URL / key /
  model / ready-made snippets for Claude Code, Cline, Continue, Aider, Cursor, OpenAI + Anthropic SDKs, curl -
  per account) and Settings (every tuning knob that used to need an environment variable).
* Every account has its OWN endpoint:  http://127.0.0.1:8788/a/<account-id>  - point another agent at it and
  it always uses exactly that account.
* FILES + VISION: images, PDF, Word, Excel, text ... sent as Anthropic `image` / `document` blocks (or OpenAI
  `image_url` / `file` parts, or from the Chat page) are uploaded to DeepSeek through the site's own file input.
  This also makes pasted screenshots in Claude Code work.
* `--panel`: start only the bridge + panel (no terminal needed after that). Double-click friendly.

What is new in V6.0 (MULTI-ACCOUNT + DASHBOARD)
-----------------------------------------------
* ACCOUNT POOL: log in with as many DeepSeek accounts as you like. Every account has its own
  browser profile + its own worker thread, so one account being slow / busy / broken never blocks
  the others, and sub-agents can really run in parallel on different accounts.
* AUTOMATIC FAIL-OVER: when an account answers "server is busy", is rate limited, reports a full
  chat, loses its login or keeps failing, it is put on a cooldown and the SAME request is re-sent
  to another account (new chat + compacted history), invisibly to Claude Code.
* LOAD BALANCING: strategies `balanced` (default), `round_robin`, `failover` (priority list) and
  `pinned` (everything to one account). Long conversations rotate to another account every N
  messages / M minutes so no single account is hammered (0 = off).
* WEB DASHBOARD at http://127.0.0.1:8788/dash  (Persian / English): add / remove / rename /
  enable / disable accounts, re-login, show or hide an account's browser window (full hands-on
  access), test an account, reset or purge its chats, reorder priorities, switch the account that
  Claude Code uses - live, without closing Claude Code. Per account: estimated tokens in / out,
  today's tokens, messages, errors, rate limits, latency, total active time and the CURRENT
  CONTINUOUS USE time, a 60-minute activity graph, last error, live event log.
* INSIDE CLAUDE CODE:  /ds  (status)   /ds next   /ds prev   /ds use 2   /ds auto   /ds-next
  (answered locally by the bridge in milliseconds - no model call, no permission prompt).
* FROM ANOTHER TERMINAL:  python deepseek_bridge.py --ctl next   (status | use 2 | auto | ...)
  and  python deepseek_bridge.py --add-account "Work"  (adds + opens its login window).
* Zero overhead on the hot path: statistics are plain counters, the dashboard only reads memory.
* Your existing login (ds_profile) becomes "Account 1" automatically.

What is new in V5 (compared with V4)
------------------------------------
* PERSISTENT CONVERSATIONS: one DeepSeek chat (tab) per Claude Code conversation.
  Follow-up requests send only the *delta* (new user messages / tool results),
  so the model never "forgets" what it did. Conversations are matched by a
  tolerant message-signature prefix, several conversations (main agent,
  sub-agents) can live side by side (LRU tabs), and everything falls back to a
  fresh chat + full (compacted) history when a match is not possible.
* REAL RESPONSE CAPTURE: a fetch/XHR hook inside the page reads DeepSeek's raw
  SSE stream. Exact text (no innerText mangling), explicit end-of-generation,
  thinking separated from the answer, real streaming to the client,
  "Continue generating" handling, precise error reporting. The DOM scraper is
  only an automatic fallback.
* ROBUST DSML PARSER: fence-aware, survives closing tags inside parameter
  values, schema-aware coercion ("123" stays a string), tool-name / required
  parameter validation, truncated-call detection and an automatic in-chat
  "repair" round-trip.
* SAFE PROMPT COMPACTION: history is compacted per message / per block, never
  in the middle of a message; system + tool schema are budgeted separately;
  tool schemas are minified.
* SIDE REQUESTS: quota probes are answered locally, title-generation (haiku)
  requests use a scratch tab at lower priority.
* REAL CANCELLATION (Esc in Claude Code stops generation in the browser),
  early SSE headers + ping keep-alive, Anthropic-style errors (529 => retry).
* Correct headless handling, health checks / auto-recovery, debug dumps,
  chat cleanup, EOF-safe terminal, chunked bodies, bytes-safe key compare.

What is new in V5.1 (hardening release, same single file)
--------------------------------------------------------
* Streamed text now goes through the SAME sanitising rules as the final reply
  ([citation:N], [ASSISTANT], hallucinated [USER]/[TOOL_RESULT] turns), so the
  client never sees text that the final answer would have removed. A
  whitespace-tolerant reconciliation replaces the old strict prefix check.
* HTTP layer: a truncated chunked body can no longer spin a thread forever,
  socket read timeout, invalid Content-Length rejected, a dead worker thread or
  an overall deadline can no longer hang a request.
* Worker: catches BaseException per job, fails every queued job if it dies.
* Engine: cancelled / failed repair round-trips no longer leave a tab whose
  state disagrees with the client's history (the tab is dropped instead).
  A forced tool_choice {"type":"tool"} is now verified and repaired.
* Parser: integer schema no longer accepts 1.5, NaN/Infinity are rejected,
  fence detection follows Markdown fence-length rules (4-backtick outer fences
  may contain 3-backtick examples).
* Ops: friendly "port in use" error, --port validation, --version, bridge.log
  rotation, stderr restored, one-time warnings for unreadable env values / an
  unwritable config file / DOM-fallback mode, Linux/macOS lines in the banner,
  adaptive polling (fewer CDP round-trips while DeepSeek is thinking).
* Self-test now also spins up the real HTTP server against a fake worker
  (truncated chunked body, dead worker, streaming without citation leaks).

What is new in V5.9 (long-running / ERP-size projects)
------------------------------------------------------
* Chats are KEPT by default (DS_BRIDGE_DELETE_OLD_CHATS=0): errors, cancels, rotation and tab
  eviction no longer delete anything on chat.deepseek.com.  /purge still deletes on demand.
* Tab eviction now HIBERNATES: the tab closes, the chat stays, and it is re-opened by its session
  URL when that conversation continues (falls back to a fresh chat if that is not possible).
  Sub-agents can no longer push the main conversation out of existence.
* Much longer patience: stall 900s, max reply 3h, transient failures retried 6x with backoff.
* Claude Code is started with API_TIMEOUT_MS / BASH_*_TIMEOUT_MS raised, so long tasks are not
  aborted client-side (an abort used to cancel the request and throw the chat away).

What is new in V5.4 - V5.7 (safe mode proven against the real Claude Code)
--------------------------------------------------------------------------
* V5.4: `safe` allow list cut to what Claude Code does not already allow itself; `env` /
  `xargs` denied, `git log|show --output=` denied, `git init` exact-match only, a
  user-supplied --settings file is never overridden, --set-mode accepts the same aliases as --mode.
* V5.5: --verify-safe (see below).  V5.6: it runs in a clean room (own HOME / CLAUDE_CONFIG_DIR,
  no stray CLAUDE_* / ANTHROPIC_* variables), pairs results by tool_use id, needs an error
  result to count a stop.  V5.7: the stop detector matches only Claude Code's real wording
  (captured from the CLI), so an OS-level "Permission denied" or the word "redirection" can
  never be mistaken for a stop; if Claude Code rewords its messages the "asks" rows turn BAD
  (loud) instead of silently passing.  Temp folders are always cleaned up.

What is new in V5.3 (three permission modes, audit fixes)
--------------------------------------------------------
Claude Code now starts in one of three MODES (choose per run or save it):

  safe  (DEFAULT)  Claude works freely INSIDE the project folder: it creates /
                   edits files there and runs common dev commands (git, python,
                   node, npm, pytest, ...) without asking. Everything else - files
                   outside the folder, curl, rm, unknown programs - is asked
                   first, and a short list of destructive commands is blocked.
  ask              Claude Code's normal behaviour: it asks before acting.
  auto             Fully autonomous: --dangerously-skip-permissions, no prompts
                   at all (and its one-time warning screen is pre-accepted).

  python deepseek_bridge.py --mode auto         this run only
  python deepseek_bridge.py --set-mode auto     remember it (saved in the config file)
  DS_BRIDGE_MODE=auto                           environment variable
  Priority: your own Claude permission flag > --mode/--safe/--ask/--auto >
            DS_BRIDGE_MODE > saved mode > safe.

How `safe` is enforced (each point below was verified against the real Claude Code CLI):
  * File edits outside the project folder ask - Claude Code's own fence. No blanket
    Write/Edit/Read allow rule is used, because that would lift the fence.
  * Compound commands (a && b, a; b, a | b, a || b, newlines, $(...), `...`) are
    checked part by part: one unlisted part makes the whole command ask.
  * Read-only shell commands (cat, grep, ls, head, ...) and cp / mv / mkdir / touch are
    path-checked by Claude Code itself, so `cat ~/.ssh/id_rsa` or `mv` on a file
    outside the folder asks. They therefore need no allow rule.
  * The allow list only adds what Claude Code does not allow by itself: git
    write commands and the usual dev toolchain.
  * Honest limit: programs that run arbitrary code (python, node, npm scripts,
    pip/npm install, make, ...) run unrestricted - they are the point of a coding agent
    and no shell can be fenced in on Windows. Use a VM / container for real isolation.

Re-verify it yourself:  python deepseek_bridge.py --verify-safe
  runs the REAL `claude` (no DeepSeek, no network, no browser) against a scripted fake
  model and checks ~25 commands - inside the folder they run, everything that leaves
  it (or chains, pipes, wraps, redirects) asks. Run it again after updating Claude Code.

Also since V5.3: project folder --here (this .py file's folder); audit fixes: fence
handling, partial-valid tool calls merged with the repair, 408 on a stalled request
body, race-free submit(), no --start-minimized on Linux, delta prompts cap a giant
tool result, self-test no longer depends on user env variables.

Requirements:
    pip install playwright
    playwright install chrome

Run:
    python deepseek_bridge.py

Claude Code (PowerShell):
    $env:ANTHROPIC_BASE_URL="http://127.0.0.1:8788"
    $env:ANTHROPIC_API_KEY="<printed key>"
    claude
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import contextvars
import contextlib
import hashlib
import itertools
import json
import math
import os
import queue
import re
import secrets
import select
import shlex
import shutil
import signal
import socket
import string
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if os.name == "nt":
    os.system("")  # enables ANSI escape processing in the Windows console


# ============================================================================
# Configuration / per-instance runtime
# ============================================================================

VERSION = "6.4"
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = Path(__file__).resolve()
CHAT_URL = os.getenv("DS_BRIDGE_CHAT_URL", "https://chat.deepseek.com/")
DEFAULT_PORT = 8788
LOGIN_WAIT_DEFAULT = 600
HEADLESS_READY_TIMEOUT_DEFAULT = 20
CLIENT_API_TIMEOUT_MS = "7200000"
CLIENT_BASH_DEFAULT_TIMEOUT_MS = "1800000"
CLIENT_BASH_MAX_TIMEOUT_MS = "7200000"

PARALLEL_MODES = ("serial", "light", "full", "auto")
PRIORITY_MAIN = 0
PRIORITY_SIDE = 5
if os.getenv("DS_BRIDGE_PARALLEL_MODE", "auto").strip().lower() not in PARALLEL_MODES:
    _warn_bad = os.getenv("DS_BRIDGE_PARALLEL_MODE")
    if _warn_bad:
        print(f"[warning] DS_BRIDGE_PARALLEL_MODE={_warn_bad!r} is invalid; using auto", file=sys.stderr, flush=True)
MODES = ("safe", "ask", "auto")
DEFAULT_MODE = "safe"
SWARM_DIR_NAME = ".dsb-swarm"
BROWSER_STATES = ("CREATED", "STARTING", "LOGIN_REQUIRED", "READY", "BUSY",
                  "WAITING_RESPONSE", "RECOVERING", "FAILED", "CLOSED")
CLAUDE_HOOK_EVENT_UNION = (
    "PreToolUse", "PermissionRequest", "PermissionDenied", "PostToolUse", "PostToolUseFailure",
    "PostToolBatch", "Notification", "UserPromptSubmit", "UserPromptExpansion", "SessionStart",
    "SessionEnd", "Stop", "StopFailure", "SubagentStart", "SubagentStop", "PreCompact", "PostCompact",
    "TeammateIdle", "TaskCreated", "TaskCompleted", "Elicitation", "ElicitationResult", "ConfigChange",
    "CwdChanged", "DirectoryAdded", "FileChanged", "WorktreeCreate", "WorktreeRemove",
    "InstructionsLoaded", "Setup", "MessageDisplay", "PreModelSwitch", "PostModelSwitch",
)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except Exception:
        print(f"[warning] {name}={raw!r} is not an integer; using {default}", file=sys.stderr, flush=True)
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        print(f"[warning] {name}={raw!r} is not a number; using {default}", file=sys.stderr, flush=True)
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _resolve_env_path(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    return Path(raw).expanduser().resolve() if raw else default.expanduser().resolve()


@dataclass(frozen=True)
class InstancePaths:
    """Every persistent path owned by exactly one bridge instance."""
    script: Path
    home: Path
    config: Path
    usage: Path
    profile: Path
    accounts: Path
    log: Path
    swarm_attachments: Path

    def claude_settings(self, name: str) -> Path:
        return self.config.with_name(f".deepseek_bridge_claude_{name}.json")

    def keep_going_hook(self) -> Path:
        return self.claude_settings("keepgoing").with_suffix(".py")


def instance_paths(instance_home: Optional[Path] = None) -> InstancePaths:
    home = (Path(instance_home).expanduser() if instance_home is not None else SCRIPT_DIR).resolve()
    config = _resolve_env_path("DS_BRIDGE_CONFIG", home / ".deepseek_bridge.json")
    profile = _resolve_env_path("DS_BRIDGE_PROFILE_DIR", home / "ds_profile")
    accounts = _resolve_env_path("DS_BRIDGE_ACCOUNTS_DIR", home / "ds_profiles")
    swarm = _resolve_env_path("DS_BRIDGE_SWARM_ATTACH_DIR", home / ".deepseek_bridge" / "swarm_attachments")
    log_path = home / "bridge.log"
    return InstancePaths(SCRIPT_PATH, home, config, config.with_name(".deepseek_bridge_usage.json"),
                         profile, accounts, log_path, swarm)


@dataclass
class RuntimeState:
    """All mutable bridge state for one process/instance.

    No request or worker is allowed to mutate module-level runtime state. The HTTP
    handler, Pool, worker threads, dashboard and swarm all bind to this object.
    """
    paths: InstancePaths
    instance_name: str
    cfg: Dict[str, Any] = field(default_factory=dict)
    CONFIG_PATH: Path = field(init=False)
    PROFILE_DIR: Path = field(init=False)
    ACCOUNTS_DIR: Path = field(init=False)
    SWARM_ATTACH_DIR: Path = field(init=False)
    LOG_FILE: Any = None
    LOG_RING: Any = field(default_factory=lambda: deque(maxlen=3000))
    ACTIVITY: Any = field(default_factory=lambda: deque(maxlen=500))
    CLAUDE_MIRROR: Any = field(default_factory=lambda: deque(maxlen=1200))
    DASH_EVENT_SUBS: List[Any] = field(default_factory=list)
    _WARNED: set = field(default_factory=set, repr=False)
    _LOG_SEQ: Any = field(default_factory=lambda: itertools.count(1), repr=False)
    _ACT_SEQ: Any = field(default_factory=lambda: itertools.count(1), repr=False)
    DASH_EVENT_SEQ: Any = field(default_factory=lambda: itertools.count(1), repr=False)
    DASH_EVENT_LOCK: Any = field(default_factory=threading.RLock, repr=False)
    _dump_counter: Any = field(default_factory=lambda: itertools.count(1), repr=False)
    _TASKS: set = field(default_factory=set, repr=False)
    BRIDGE: Any = None
    SERVER: Any = None
    API_KEY: Optional[str] = None
    DEBUG_DIR: str = ""
    BROWSER_CHANNEL: str = "chrome"
    HEADLESS_MODE: str = "auto"
    LOGIN_WAIT_SECONDS: int = LOGIN_WAIT_DEFAULT
    HEADLESS_READY_TIMEOUT: int = HEADLESS_READY_TIMEOUT_DEFAULT
    THINK_MODE: bool = False
    MAX_PROMPT_CHARS: int = 800_000
    HISTORY_BUDGET_CHARS: int = 300_000
    ROTATE_CHARS: int = 700_000
    KEEP_RECENT_MESSAGES_FULL: int = 12
    BASE_BLOCK_LIMIT: int = 6000
    TOOL_DESC_LIMIT: int = 1800
    PARAM_DESC_LIMIT: int = 300
    DELTA_BLOCK_LIMIT: int = 150_000
    MAX_HTTP_BODY_BYTES: int = 32 * 1024 * 1024
    ATTACH_MAX_FILES: int = 6
    ATTACH_MAX_BYTES: int = 25 * 1024 * 1024
    UPLOAD_TIMEOUT: int = 240
    SWARM_AGENTS: int = 0
    SWARM_MAX_AGENTS: int = 6
    SWARM_AGENT_TIMEOUT: int = 3600
    SWARM_FIX_ROUNDS: int = 2
    SWARM_REVIEW: str = "auto"
    STALL_TIMEOUT: int = 900
    MAX_REPLY_SECONDS: int = 10800
    SUBMIT_TIMEOUT: int = 25
    POLL_SECONDS: float = 0.1
    MAX_CONTINUES: int = 8
    MAX_REPAIRS: int = 4
    REQUEST_GAP_SECONDS: float = 0.05
    MAX_TABS: int = 8
    MAX_KEPT_CONVS: int = 40
    DELETE_OLD_CHATS: bool = False
    MAX_RETRIES: int = 6
    RETRY_BACKOFF_MAX: int = 60
    CHARS_PER_TOKEN: float = 4.0
    PRIORITY_MAIN: int = 0
    PRIORITY_SIDE: int = 5
    COOLDOWN_BASE: int = 120
    COOLDOWN_MAX: int = 1800
    ACCOUNT_WAIT_SECONDS: int = 120
    STREAK_GAP: int = 300
    DASH_AUTOOPEN: bool = True
    UI_PERFORMANCE_MODE: str = "auto"
    UI_MODE: str = "beginner"
    PARALLEL_MODE: str = "auto"
    KEEP_GOING: bool = True
    KEEP_GOING_MAX: int = 400
    RUN_MODE: str = "claude"
    PANEL_ONLY: bool = False
    COLOR_ENABLED: bool = True
    RESOLVED_PORT: int = DEFAULT_PORT
    PORT_SOURCE: str = "config"
    PORT_PERSIST_ALLOWED: bool = False
    PERSISTED_PORT: int = DEFAULT_PORT
    CLAUDE_COMMANDS_DIR: Optional[Path] = None
    FORCE_CLAUDE_COMMANDS: bool = False
    SETTING_DEFAULTS: Dict[str, Any] = field(default_factory=dict)
    PID: int = field(default_factory=os.getpid, init=False)
    START_TIME: float = field(default_factory=time.time, init=False)

    def __post_init__(self) -> None:
        self.CONFIG_PATH = self.paths.config
        self.PROFILE_DIR = self.paths.profile
        self.ACCOUNTS_DIR = self.paths.accounts
        self.SWARM_ATTACH_DIR = self.paths.swarm_attachments
        self.DEBUG_DIR = os.getenv("DS_BRIDGE_DEBUG_DIR", "")
        self.BROWSER_CHANNEL = os.getenv("DS_BRIDGE_CHANNEL", "chrome")
        self.HEADLESS_MODE = os.getenv("DS_BRIDGE_HEADLESS", "auto").strip().lower()
        if self.HEADLESS_MODE not in {"auto", "0", "1"}:
            self.HEADLESS_MODE = "auto"
        self.LOGIN_WAIT_SECONDS = _env_int("DS_BRIDGE_LOGIN_WAIT", LOGIN_WAIT_DEFAULT)
        self.HEADLESS_READY_TIMEOUT = _env_int("DS_BRIDGE_READY_TIMEOUT", HEADLESS_READY_TIMEOUT_DEFAULT)
        self.THINK_MODE = _env_bool("DS_BRIDGE_THINK_MODE", False)
        self.MAX_PROMPT_CHARS = _env_int("DS_BRIDGE_MAX_PROMPT_CHARS", 800_000)
        self.HISTORY_BUDGET_CHARS = _env_int("DS_BRIDGE_HISTORY_BUDGET_CHARS", 300_000)
        self.ROTATE_CHARS = _env_int("DS_BRIDGE_ROTATE_CHARS", 700_000)
        self.KEEP_RECENT_MESSAGES_FULL = _env_int("DS_BRIDGE_KEEP_RECENT_MESSAGES", 12)
        self.BASE_BLOCK_LIMIT = _env_int("DS_BRIDGE_OLD_BLOCK_LIMIT", 6000)
        self.TOOL_DESC_LIMIT = _env_int("DS_BRIDGE_TOOL_DESC_LIMIT", 1800)
        self.PARAM_DESC_LIMIT = _env_int("DS_BRIDGE_PARAM_DESC_LIMIT", 300)
        self.DELTA_BLOCK_LIMIT = _env_int("DS_BRIDGE_DELTA_BLOCK_LIMIT", 150_000)
        self.MAX_HTTP_BODY_BYTES = _env_int("DS_BRIDGE_MAX_HTTP_BODY_BYTES", 32 * 1024 * 1024)
        self.ATTACH_MAX_FILES = _env_int("DS_BRIDGE_MAX_FILES", 6)
        self.ATTACH_MAX_BYTES = _env_int("DS_BRIDGE_MAX_FILE_BYTES", 25 * 1024 * 1024)
        self.UPLOAD_TIMEOUT = _env_int("DS_BRIDGE_UPLOAD_TIMEOUT", 240)
        self.SWARM_AGENTS = _env_int("DS_BRIDGE_SWARM_AGENTS", 0)
        self.SWARM_MAX_AGENTS = _env_int("DS_BRIDGE_SWARM_MAX_AGENTS", 6)
        self.SWARM_AGENT_TIMEOUT = _env_int("DS_BRIDGE_SWARM_AGENT_TIMEOUT", 3600)
        self.SWARM_FIX_ROUNDS = _env_int("DS_BRIDGE_SWARM_FIX_ROUNDS", 2)
        self.SWARM_REVIEW = os.getenv("DS_BRIDGE_SWARM_REVIEW", "auto")
        self.STALL_TIMEOUT = _env_int("DS_BRIDGE_STALL_TIMEOUT", 900)
        self.MAX_REPLY_SECONDS = _env_int("DS_BRIDGE_MAX_REPLY_SECONDS", 10800)
        self.SUBMIT_TIMEOUT = _env_int("DS_BRIDGE_SUBMIT_TIMEOUT", 25)
        self.POLL_SECONDS = _env_float("DS_BRIDGE_POLL_SECONDS", 0.1)
        self.MAX_CONTINUES = _env_int("DS_BRIDGE_MAX_CONTINUES", 8)
        self.MAX_REPAIRS = _env_int("DS_BRIDGE_MAX_REPAIRS", 4)
        self.REQUEST_GAP_SECONDS = _env_float("DS_BRIDGE_REQUEST_GAP", 0.05)
        self.MAX_TABS = _env_int("DS_BRIDGE_MAX_TABS", 8)
        self.MAX_KEPT_CONVS = _env_int("DS_BRIDGE_MAX_KEPT_CONVS", 40)
        self.DELETE_OLD_CHATS = _env_bool("DS_BRIDGE_DELETE_OLD_CHATS", False)
        self.MAX_RETRIES = _env_int("DS_BRIDGE_MAX_RETRIES", 6)
        self.RETRY_BACKOFF_MAX = _env_int("DS_BRIDGE_RETRY_BACKOFF_MAX", 60)
        self.CHARS_PER_TOKEN = _env_float("DS_BRIDGE_CHARS_PER_TOKEN", 4.0)
        self.PRIORITY_MAIN = 0
        self.PRIORITY_SIDE = 5
        self.COOLDOWN_BASE = _env_int("DS_BRIDGE_COOLDOWN_BASE", 120)
        self.COOLDOWN_MAX = _env_int("DS_BRIDGE_COOLDOWN_MAX", 1800)
        self.ACCOUNT_WAIT_SECONDS = _env_int("DS_BRIDGE_ACCOUNT_WAIT", 120)
        self.DASH_AUTOOPEN = _env_bool("DS_BRIDGE_OPEN_DASH", True)
        self.UI_PERFORMANCE_MODE = os.getenv("DS_BRIDGE_UI_PERFORMANCE", "auto").strip().lower()
        if self.UI_PERFORMANCE_MODE not in {"auto", "balanced", "light", "max"}:
            self.UI_PERFORMANCE_MODE = "auto"
        self.UI_MODE = os.getenv("DS_BRIDGE_UI_MODE", "beginner").strip().lower()
        if self.UI_MODE not in {"beginner", "pro"}:
            self.UI_MODE = "beginner"
        self.PARALLEL_MODE = os.getenv("DS_BRIDGE_PARALLEL_MODE", "auto").strip().lower()
        if self.PARALLEL_MODE not in PARALLEL_MODES:
            self.PARALLEL_MODE = "auto"
        self.KEEP_GOING = _env_bool("DS_BRIDGE_KEEP_GOING", True)
        self.KEEP_GOING_MAX = _env_int("DS_BRIDGE_KEEP_GOING_MAX", 400)


_CURRENT_STATE: contextvars.ContextVar[Optional[RuntimeState]] = contextvars.ContextVar("ds_bridge_runtime_state", default=None)


def _state() -> RuntimeState:
    state = _CURRENT_STATE.get()
    if state is None:
        raise RuntimeError("DeepSeek Bridge runtime state is not bound; call main() or bind_runtime() first")
    return state


@contextlib.contextmanager
def bind_runtime(state: RuntimeState):
    token = _CURRENT_STATE.set(state)
    try:
        yield state
    finally:
        _CURRENT_STATE.reset(token)


def _warn_once(key: str, msg: str) -> None:
    state = _CURRENT_STATE.get()
    if state is not None:
        if key in state._WARNED:
            return
        state._WARNED.add(key)
    try:
        print(f"[warning] {msg}", file=sys.stderr, flush=True)
    except Exception:
        pass


def _runtime_instance_name() -> str:
    return _state().instance_name


def _runtime_paths_for(home: Path) -> InstancePaths:
    return instance_paths(home)


def make_runtime_state(instance_home: Optional[Path] = None, instance_name: Optional[str] = None,
                       cfg: Optional[Dict[str, Any]] = None) -> RuntimeState:
    paths = instance_paths(instance_home)
    name = str(instance_name or paths.home.name or "bridge")
    return RuntimeState(paths, name, dict(cfg or {}))


def state_thread(*args: Any, **kwargs: Any) -> threading.Thread:
    """Create a thread that inherits the current RuntimeState context."""
    target = kwargs.get("target")
    if target is not None:
        ctx = contextvars.copy_context()
        def runner(*a: Any, **k: Any) -> Any:
            return ctx.run(target, *a, **k)
        kwargs["target"] = runner
    return threading.Thread(*args, **kwargs)


@contextlib.contextmanager
def config_file_lock(path: Path, timeout: float = 15.0):
    """Cross-platform advisory lock for config read/modify/write sequences."""
    lock_path = Path(path).with_suffix(Path(path).suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "a+b")
    started = time.monotonic()
    warned = False
    try:
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() - started >= timeout:
                        raise TimeoutError(f"timed out waiting for config lock: {lock_path}")
                    if not warned and time.monotonic() - started >= 3.0:
                        _warn_once("config_lock_slow", f"waiting for config lock {lock_path} (>3s)")
                        warned = True
                    time.sleep(0.1)
        else:
            import fcntl
            while True:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() - started >= timeout:
                        raise TimeoutError(f"timed out waiting for config lock: {lock_path}")
                    if not warned and time.monotonic() - started >= 3.0:
                        _warn_once("config_lock_slow", f"waiting for config lock {lock_path} (>3s)")
                        warned = True
                    time.sleep(0.1)
        yield f
    finally:
        try:
            if os.name == "nt":
                import msvcrt
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        f.close()


def _save_config_unlocked(cfg: Dict[str, Any]) -> None:
    path = _state().CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def _legacy_config_path() -> Path:
    return Path.home() / ".deepseek_bridge.json"


def maybe_migrate_legacy_config() -> bool:
    state = _state()
    local = state.CONFIG_PATH
    legacy = _legacy_config_path()
    if local.exists() or not legacy.exists():
        return False
    # Seamless one-time upgrade only for the historical ~/bridge/ installation.
    if state.paths.home != SCRIPT_DIR or SCRIPT_DIR.name.lower() != "bridge" or SCRIPT_DIR.parent.resolve() != Path.home().resolve():
        return False
    try:
        local.parent.mkdir(parents=True, exist_ok=True)
        with config_file_lock(local):
            if local.exists():
                return False
            shutil.copy2(legacy, local)
        print(f"[migration] copied legacy config {legacy} -> {local}; original left untouched", file=sys.stderr, flush=True)
        return True
    except Exception as exc:
        _warn_once("legacy_migration", f"could not migrate legacy config {legacy} -> {local}: {exc}")
        return False

# ============================================================================
# ANSI colours + logging
# ============================================================================

class C:
    @classmethod
    def enable(cls, value: bool) -> None:
        state = _CURRENT_STATE.get()
        if state is not None:
            state.COLOR_ENABLED = bool(value)

    @classmethod
    def _w(cls, code: str, text: Any) -> str:
        s = str(text)
        state = _CURRENT_STATE.get()
        enabled = state.COLOR_ENABLED if state is not None else True
        return f"\033[{code}m{s}\033[0m" if enabled else s

    @classmethod
    def cyan(cls, t): return cls._w("96", t)

    @classmethod
    def green(cls, t): return cls._w("92", t)

    @classmethod
    def yellow(cls, t): return cls._w("93", t)

    @classmethod
    def red(cls, t): return cls._w("91", t)

    @classmethod
    def bold(cls, t): return cls._w("1", t)

    @classmethod
    def dim(cls, t): return cls._w("2", t)


_LOG_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)(x-ds-bridge-hook-key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"sk-ds-local-[A-Za-z0-9_-]+"),
    re.compile(r"dsb-hook-[A-Za-z0-9_-]+"),
)

def _redact_log_text(text: Any) -> str:
    s = str(text)
    for pat in _LOG_SECRET_PATTERNS:
        s = pat.sub(lambda m: ((m.group(1) if m.lastindex else "") + "[REDACTED]"), s)
    return s[:2000]


def log(msg: str, color: Optional[Callable[[Any], str]] = None, *,
        provider: str = "", account: str = "", lane: str = "", project: str = "",
        request_id: str = "", event: str = "") -> None:
    lvl = {"red": "error", "yellow": "warn", "green": "ok"}.get(getattr(color, "__name__", ""), "info")
    safe_msg = _redact_log_text(msg)
    context: Dict[str, str] = {}
    for name, value in (("provider", provider), ("account", account), ("lane", lane),
                        ("project", project), ("request_id", request_id), ("event", event)):
        if value:
            context[name] = _redact_log_text(value)
    seq = next(_state()._LOG_SEQ)
    now = time.time()
    _state().LOG_RING.append((seq, now, lvl, safe_msg))
    try:
        item = {"n": seq, "t": now, "level": lvl, "message": safe_msg}
        if context:
            item["context"] = context
        emit_dash_event("console", item)
    except Exception:
        pass
    line = time.strftime("%H:%M:%S ") + f"[{_state().instance_name}] " + safe_msg
    if context:
        line += " " + " ".join(f"{k}={v!r}" for k, v in context.items())
    if _state().LOG_FILE is not None:
        try:
            _state().LOG_FILE.write(line + "\n")
            _state().LOG_FILE.flush()
        except Exception:
            pass
        return
    print(color(line) if color else line, flush=True)



def dump_debug(kind: str, text: str) -> None:
    if not _state().DEBUG_DIR:
        return
    try:
        d = Path(_state().DEBUG_DIR)
        d.mkdir(parents=True, exist_ok=True)
        name = f"{time.strftime('%H%M%S')}-{next(_state()._dump_counter):04d}-{kind}.txt"
        (d / name).write_text(text, encoding="utf-8", errors="replace")
    except Exception:
        pass


# ============================================================================
# Errors
# ============================================================================

class BridgeError(Exception):
    """kind: upstream | empty | timeout | login | bad_request"""

    def __init__(self, message: str, kind: str = "upstream"):
        super().__init__(message)
        self.kind = kind


class NotStarted(BridgeError):
    pass


class BridgeCancelled(Exception):
    pass


def error_status(exc: BaseException) -> Tuple[int, str]:
    if isinstance(exc, BridgeError):
        if exc.kind == "login":
            return 401, "authentication_error"
        if exc.kind == "bad_request":
            return 400, "invalid_request_error"
        # 529 makes Anthropic SDKs (Claude Code) retry automatically.
        return 529, "overloaded_error"
    return 500, "api_error"


# ---- V6: classify site errors / notices -------------------------------------

_RL_RE = re.compile(r"server (?:is )?busy|too many requests|rate[_ -]?limit|(?:too )?frequent(?:ly)?|"
                    r"try again later|HTTP 429|HTTP 5\d\d|overload|服务器繁忙|繁忙|请求过于频繁|访问过于频繁", re.I)
_FULL_RE = re.compile(r"context[_ -]?(?:window|length)|length[_ -]?limit|too long|token limit|"
                      r"conversation .{0,20}(?:full|limit)|reached .{0,30}limit|"
                      r"对话.{0,10}(?:上限|过长|长度)|开启新对话|start a new (?:chat|conversation)", re.I)


def classify_error(err: str) -> str:
    """login | chat_full | rate_limit | upstream"""
    s = err or ""
    if re.search(r"HTTP 40[13]", s):
        return "login"
    if _FULL_RE.search(s):
        return "chat_full"
    if _RL_RE.search(s):
        return "rate_limit"
    return "upstream"


_NOTICE_BUSY_RE = re.compile(r"server (?:is )?busy|服务器繁忙|系统繁忙|too many requests|"
                             r"messages? too frequent|请求过于频繁", re.I)
_NOTICE_FULL_RE = re.compile(r"conversation (?:has )?reached (?:its |the )?(?:length )?limit|"
                             r"(?:length|context) limit (?:has been )?reached|"
                             r"对话(?:已)?达到.{0,8}上限|超过.{0,6}长度限制|"
                             r"start a new (?:chat|conversation) to continue", re.I)


def site_notice_kind(text: str) -> Optional[str]:
    """DeepSeek sometimes answers with a short site notice instead of a real reply."""
    t = (text or "").strip()
    if not t or len(t) > 240 or ANY_DSML_RE.search(t):
        return None
    if _NOTICE_FULL_RE.search(t):
        return "chat_full"
    if _NOTICE_BUSY_RE.search(t):
        return "rate_limit"
    return None


_CMD_RE = re.compile(r"DS-BRIDGE-CMD[ \t]*([^\r\n]*)")


def extract_bridge_command(req: "NormReq") -> Optional[str]:
    """Text after DS-BRIDGE-CMD in the LAST plain user message (the /ds slash command), else None."""
    if not req.messages:
        return None
    last = req.messages[-1]
    if last.get("role") != "user":
        return None
    c = last.get("content")
    if isinstance(c, str):
        texts = [c]
    elif isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return None
        texts = [str(b.get("text", "")) for b in c if isinstance(b, dict) and b.get("type") == "text"]
    else:
        return None
    for t in texts:
        m = _CMD_RE.search(_REMINDER_RE.sub("", t))
        if m:
            return m.group(1).strip()
    return None


def fmt_tok(n: float) -> str:
    n = float(n)
    if n >= 1e6:
        return f"{n / 1e6:.2f}M"
    if n >= 1e3:
        return f"{n / 1e3:.1f}k"
    return str(int(n))


def fmt_dur(s: float) -> str:
    s = int(max(0, s))
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {sec:02d}s"
    return f"{sec}s"



# ============================================================================
# Config file
# ============================================================================

def save_config(cfg: Dict[str, Any]) -> None:
    """Atomically persist config while keeping a process-local port override transient."""
    state = _state()
    persist_cfg = dict(cfg)
    if state.RESOLVED_PORT != state.PERSISTED_PORT and not state.PORT_PERSIST_ALLOWED:
        persist_cfg["port"] = state.PERSISTED_PORT
    try:
        with config_file_lock(state.CONFIG_PATH):
            _save_config_unlocked(persist_cfg)
    except Exception as exc:
        _warn_once("save_config", f"could not write {state.CONFIG_PATH} ({exc}); a new API key will be generated on every start")


def load_config() -> Dict[str, Any]:
    state = _state()
    cfg: Dict[str, Any] = {"port": DEFAULT_PORT, "api_key": None, "hook_key": None}
    maybe_migrate_legacy_config()
    try:
        with config_file_lock(state.CONFIG_PATH):
            if state.CONFIG_PATH.exists():
                try:
                    with open(state.CONFIG_PATH, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, dict): cfg.update(loaded)
                except Exception as exc:
                    _warn_once("load_config", f"could not read {state.CONFIG_PATH} ({exc}); using defaults where needed")
            changed = False
            if not cfg.get("api_key"):
                cfg["api_key"] = "sk-ds-local-" + secrets.token_hex(24); changed = True
            if not cfg.get("hook_key"):
                cfg["hook_key"] = "dsb-hook-" + secrets.token_urlsafe(32); changed = True
            try: cfg["port"] = int(cfg.get("port", DEFAULT_PORT))
            except Exception: cfg["port"] = DEFAULT_PORT; changed = True
            if changed:
                _save_config_unlocked(cfg)
    except Exception as exc:
        _warn_once("load_config_lock", f"could not safely lock/read {state.CONFIG_PATH} ({exc}); using defaults where needed")
    return cfg


# ============================================================================
# Generic helpers
# ============================================================================

def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def h16(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:16]


def trim_text_boundary(text: str, limit: Optional[int]) -> str:
    """Head+tail trim of ONE text blob (never used across message borders)."""
    if not limit or len(text) <= limit:
        return text
    if limit < 100:
        return text[:limit]
    head = max(50, int(limit * 0.65))
    tail = max(50, limit - head)
    omitted = len(text) - head - tail
    return (
        text[:head]
        + f"\n\n[...{omitted:,} chars compacted by DeepSeek Local Bridge...]\n\n"
        + text[-tail:]
    )


def estimate_tokens(obj: Any) -> int:
    try:
        n = len(json.dumps(obj, ensure_ascii=False, default=str))
    except Exception:
        n = len(str(obj))
    return max(1, int(n / _state().CHARS_PER_TOKEN))


def make_id(prefix: str = "toolu_") -> str:
    return prefix + uuid.uuid4().hex[:24]


def content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        content = [content]
    if not isinstance(content, list):
        return str(content)
    out: List[str] = []
    for b in content:
        if isinstance(b, str):
            out.append(b)
        elif not isinstance(b, dict):
            out.append(str(b))
        else:
            t = b.get("type")
            if t == "text":
                out.append(str(b.get("text", "")))
            elif t == "image":
                out.append("[image attached]")
            elif t == "tool_result":
                out.append(content_to_text(b.get("content", "")))
            elif t == "tool_use":
                out.append(f"[tool_use:{b.get('name', '')}]")
            elif t in ("thinking", "redacted_thinking"):
                continue
            elif "text" in b:
                out.append(str(b["text"]))
    return "\n".join(x for x in out if x != "")


# ============================================================================
# DeepSeek V4 DSML parsing
# ============================================================================
#
# Native format:
#   <｜DSML｜tool_calls>
#   <｜DSML｜invoke name="Write">
#   <｜DSML｜parameter name="file_path" string="true">C:\x\y</｜DSML｜parameter>
#   </｜DSML｜invoke>
#   </｜DSML｜tool_calls>
#
# Tolerated variants: |DSML|, ｜DSML｜, ||DSML||, ｜｜DSML｜｜, extra spaces.

BAR = r"[|｜]+"
_OPEN = rf"<{BAR}\s*DSML\s*{BAR}\s*"
_CLOSE = rf"</{BAR}\s*DSML\s*{BAR}\s*"
_WRAP = r"(?:tool_calls|calls|function_calls|tool)"

INVOKE_OPEN_RE = re.compile(_OPEN + r"""invoke\s+name\s*=\s*["']([^"']+)["']\s*>""", re.I)
PARAM_OPEN_RE = re.compile(_OPEN + r"""parameter\s+name\s*=\s*["']([^"']+)["']([^>]*)>""", re.I)
PARAM_CLOSE_RE = re.compile(_CLOSE + r"parameter\s*>", re.I)
INVOKE_CLOSE_RE = re.compile(_CLOSE + r"invoke\s*>", re.I)
STRAY_RE = re.compile(rf"</?{BAR}\s*DSML\s*{BAR}\s*(?:parameter|invoke|{_WRAP})\b[^>]*>", re.I)
NEXT_OK_RE = re.compile(
    rf"\s*(?:{_OPEN}parameter\b|{_CLOSE}invoke\s*>|{_CLOSE}{_WRAP}\s*>|{_OPEN}invoke\b)", re.I
)
STRING_ATTR_RE = re.compile(r"""string\s*=\s*["']?(true|false)""", re.I)
ANY_DSML_RE = re.compile(rf"<{BAR}\s*DSML", re.I)
TOOL_CALL_START_RE = re.compile(r"<tool_call\b[^>]*>", re.I)


def dsml_param(key: str, value: Any, limit: Optional[int] = None) -> str:
    if isinstance(value, str):
        v = trim_text_boundary(value, limit) if limit else value
        return f'<｜DSML｜parameter name="{key}" string="true">{v}</｜DSML｜parameter>'
    v = compact_json(value)
    if limit and len(v) > limit * 4:
        v = trim_text_boundary(v, limit * 4)
        return f'<｜DSML｜parameter name="{key}" string="true">{v}</｜DSML｜parameter>'
    return f'<｜DSML｜parameter name="{key}" string="false">{v}</｜DSML｜parameter>'


def canonical_dsml_calls(calls: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
    if not calls:
        return ""
    out = ["<｜DSML｜tool_calls>"]
    for call in calls:
        args = call.get("arguments", {})
        if not isinstance(args, dict):
            args = {}
        out.append(f'<｜DSML｜invoke name="{call.get("name", "")}">')
        for k, v in args.items():
            out.append(dsml_param(str(k), v, limit))
        out.append("</｜DSML｜invoke>")
    out.append("</｜DSML｜tool_calls>")
    return "\n".join(out)


def canonical_dsml_tool_call(name: str, arguments: Dict[str, Any], limit: Optional[int] = None) -> str:
    return canonical_dsml_calls([{"name": name, "arguments": arguments}], limit)


# ---- code fence awareness ---------------------------------------------------

_FENCE_LINE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")


def _inside_fence(text: str, pos: int) -> bool:
    """
    Is `pos` inside an open fenced block? Uses the SAME Markdown rules as
    _whole_fenced: a fence closes only with a line made of the opener's
    character, at least as long as the opener, and nothing else on the line.
    (A 3-backtick example inside a 4-backtick fence therefore stays inside.)
    """
    ch: Optional[str] = None
    width = 0
    for line in text[:pos].splitlines():
        m = _FENCE_LINE_RE.match(line.lstrip())
        if not m:
            continue
        run, rest = m.group(1), m.group(2)
        if ch is None:
            if run[0] == "`" and "`" in rest:
                continue                      # ```code``` on one line is inline code, not a fence
            ch, width = run[0], len(run)
        elif run[0] == ch and len(run) >= width and not rest.strip():
            ch, width = None, 0
    return ch is not None


def _whole_fenced(text: str) -> bool:
    """
    True if the entire response is ONE fenced block. Follows Markdown fence
    rules: the closer is a line made only of the opener's character, at least
    as long as the opener. So a 4-backtick outer fence may contain 3-backtick
    examples, while an ambiguous same-length nesting stays "not whole" (safe:
    an example inside a fence must never be executed).
    """
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return False
    m = re.match(r"^\s*(`{3,}|~{3,})", lines[0])
    if not m:
        return False
    ch, width = m.group(1)[0], len(m.group(1))
    for k in range(1, len(lines)):
        s = lines[k].strip()
        if len(s) >= width and set(s) == {ch}:
            return k == len(lines) - 1
    return False


# ---- structured scanning ----------------------------------------------------

def _skip_ws(src: str, i: int) -> int:
    n = len(src)
    while i < n and src[i].isspace():
        i += 1
    return i


def _find_param_end(src: str, vstart: int) -> Optional[Tuple[int, int]]:
    """
    Return (value_end, tag_end). A closing tag only counts when it is followed
    by another parameter / the invoke close / the wrapper close / EOF. That way
    a literal '</｜DSML｜parameter>' inside file content does not cut the value.
    """
    for cm in PARAM_CLOSE_RE.finditer(src, vstart):
        end = cm.end()
        # DeepSeek often writes the closing tag TWICE ("</parameter></parameter>"). The value ends at
        # the first one; the duplicate is swallowed instead of being saved into the file.
        while True:
            d = PARAM_CLOSE_RE.match(src, _skip_ws(src, end))
            if d and (NEXT_OK_RE.match(src, d.end()) or not src[d.end():].strip()):
                end = d.end()
                continue
            break
        if NEXT_OK_RE.match(src, end) or not src[end:].strip():
            return cm.start(), end
    # The model forgot the closing tag: end at the next structural tag.
    nxt = None
    for rx in (PARAM_OPEN_RE, INVOKE_CLOSE_RE, INVOKE_OPEN_RE):
        m = rx.search(src, vstart)
        if m and (nxt is None or m.start() < nxt):
            nxt = m.start()
    if nxt is not None:
        return nxt, nxt
    return None


def _infer_tool_name(pnames: List[str], tools: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """Which tool takes exactly these parameters?  None when it is ambiguous."""
    ns = {p.lower() for p in pnames}
    fits: List[Tuple[int, str]] = []
    for tn, t in tools.items():
        schema = (t or {}).get("input_schema") or {}
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        pl = {k.lower() for k in props}
        req = {str(r).lower() for r in (schema.get("required") or [])}
        if ns <= pl and req <= ns:
            fits.append((len(pl - ns), tn))
    if not fits:
        return None
    fits.sort()
    if len(fits) > 1 and fits[0][0] == fits[1][0]:
        return None
    return fits[0][1]


def _repair_missing_invokes(src: str, tools: Optional[Dict[str, Dict[str, Any]]]) -> Tuple[str, int]:
    """
    DeepSeek sometimes forgets '<invoke name="X">' (parameters then float outside any invoke) or
    the '</invoke>'.  Re-insert them, naming the tool from its parameter names.
    Returns (repaired_text, number_of_parameter_groups_that_could_not_be_repaired).
    """
    if not tools or not ANY_DSML_RE.search(src):
        return src, 0
    whole = _whole_fenced(src)
    ins: List[Tuple[int, str]] = []
    unresolved = 0
    p, n, in_inv = 0, len(src), False
    while p < n:
        best = None
        for kind, rx in (("io", INVOKE_OPEN_RE), ("ic", INVOKE_CLOSE_RE), ("po", PARAM_OPEN_RE)):
            m = rx.search(src, p)
            if m and (best is None or m.start() < best[1].start()):
                best = (kind, m)
        if best is None:
            break
        kind, m = best
        if not whole and _inside_fence(src, m.start()):
            p = m.end()
            continue
        if kind == "io":
            in_inv, p = True, m.end()
            continue
        if kind == "ic":
            in_inv, p = False, m.end()
            continue
        got = _find_param_end(src, m.end())
        if in_inv:
            if got is None:
                break
            p = got[1]
            continue
        if got is None:                       # orphan parameter that never closes (cut off)
            unresolved += 1
            break
        names, p_end = [m.group(1)], got[1]
        while True:
            nm = PARAM_OPEN_RE.match(src, _skip_ws(src, p_end))
            if not nm:
                break
            g2 = _find_param_end(src, nm.end())
            if g2 is None:
                break
            names.append(nm.group(1))
            p_end = g2[1]
        tool = _infer_tool_name(names, tools)
        if tool is None:
            unresolved += 1
            p = p_end
            continue
        ins.append((m.start(), f'<｜DSML｜invoke name="{tool}">\n'))
        if not INVOKE_CLOSE_RE.match(src, _skip_ws(src, p_end)):
            ins.append((p_end, "\n</｜DSML｜invoke>"))
        p = p_end
    for pos, txt in sorted(ins, reverse=True):
        src = src[:pos] + txt + src[pos:]
    return src, unresolved


def _scan_invokes(src: str):
    whole = _whole_fenced(src)
    masked = src
    raws: List[Tuple[str, List[Tuple[str, Optional[str], str]]]] = []
    spans: List[Tuple[int, int]] = []
    truncated = False
    pos = 0
    while True:
        m = INVOKE_OPEN_RE.search(src, pos)
        if not m:
            break
        if not whole and _inside_fence(masked, m.start()):
            pos = m.end()
            continue
        name = m.group(1).strip()
        i = m.end()
        params: List[Tuple[str, Optional[str], str]] = []
        trunc = False
        while True:
            pm = PARAM_OPEN_RE.search(src, i)
            im = INVOKE_CLOSE_RE.search(src, i)
            nm = INVOKE_OPEN_RE.search(src, i)
            if nm and (pm is None or nm.start() < pm.start()) and (im is None or nm.start() < im.start()):
                break  # invoke without close, next invoke starts
            if pm and (im is None or pm.start() < im.start()):
                vs = pm.end()
                got = _find_param_end(src, vs)
                if got is None:
                    trunc = True
                    i = len(src)
                    break
                vend, tend = got
                fm = STRING_ATTR_RE.search(pm.group(2) or "")
                params.append((pm.group(1), fm.group(1).lower() if fm else None, src[vs:vend]))
                i = tend
                continue
            if im:
                i = im.end()
            break
        if trunc:
            truncated = True
            spans.append((m.start(), len(src)))
            break
        raws.append((name, params))
        spans.append((m.start(), i))
        masked = masked[:m.start()] + " " * (i - m.start()) + masked[i:]
        pos = max(i, m.end())
    return raws, spans, truncated


# ---- schema aware coercion --------------------------------------------------

_NO = object()


def _schema_types(prop: Any) -> set:
    if not isinstance(prop, dict):
        return set()
    t = prop.get("type")
    s: set = set()
    if isinstance(t, str):
        s.add(t)
    elif isinstance(t, list):
        s.update(x for x in t if isinstance(x, str))
    for key in ("anyOf", "oneOf"):
        for sub in prop.get(key) or []:
            s |= _schema_types(sub)
    return s


def _type_ok(v: Any, types: set) -> bool:
    if not types:
        return True
    if v is None:
        return "null" in types
    if isinstance(v, bool):
        return "boolean" in types
    if isinstance(v, int):
        return bool({"integer", "number"} & types)
    if isinstance(v, float):
        return "number" in types or ("integer" in types and v.is_integer())
    if isinstance(v, str):
        return "string" in types
    if isinstance(v, list):
        return "array" in types
    if isinstance(v, dict):
        return "object" in types
    return True


def _from_text(s: str, types: set) -> Tuple[Any, bool]:
    if types == {"string"}:
        return s, True
    try:
        v = json.loads(s)
    except Exception:
        v = _NO
    if isinstance(v, float) and not math.isfinite(v):
        v = _NO                                   # NaN / Infinity are never valid tool input
    if v is not _NO and _type_ok(v, types):
        if isinstance(v, float) and "integer" in types and "number" not in types:
            v = int(v)
        return v, True
    if "integer" in types or "number" in types:
        if re.fullmatch(r"-?\d+", s):
            return int(s), True
        if "number" in types:                     # "integer" alone must NOT accept 1.5
            try:
                f = float(s)
                if math.isfinite(f):
                    return f, True
            except Exception:
                pass
    if "boolean" in types and s.lower() in ("true", "false"):
        return s.lower() == "true", True
    if "string" in types:
        return s, True
    return None, False


def coerce_param(raw: str, flag: Optional[str], prop: Any) -> Tuple[Any, Optional[str]]:
    types = _schema_types(prop)
    if flag == "true":
        if not types or "string" in types:
            return raw, None
        v, ok = _from_text(raw.strip(), types)
        return (v, None) if ok else (raw, f"expected {'/'.join(sorted(types))}")
    s = raw.strip()
    if not types:
        try:
            return json.loads(s), None
        except Exception:
            return s, None
    if types == {"string"}:
        if flag == "false":
            try:
                v = json.loads(s)
                if isinstance(v, str):
                    return v, None
            except Exception:
                pass
            return s, None
        return raw.strip("\n"), None
    v, ok = _from_text(s, types)
    if ok:
        return v, None
    return s, f"expected {'/'.join(sorted(types))}"


def _norm_name(n: str) -> str:
    return re.sub(r"[_\-\s]", "", n.lower())


def build_call(name: str, params: List[Tuple[str, Optional[str], str]],
               tools: Optional[Dict[str, Dict[str, Any]]]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    problems: List[str] = []
    canon = name
    tool: Optional[Dict[str, Any]] = None
    if tools is not None:
        tool = tools.get(name)
        if tool is None:
            lowered = {_norm_name(k): k for k in tools}
            key = _norm_name(name)
            if key in lowered:
                canon = lowered[key]
                tool = tools[canon]
            else:
                avail = ", ".join(list(tools)[:40])
                return None, [f"unknown tool '{name}' (available tools: {avail})"]
    schema = (tool or {}).get("input_schema") or {}
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    args: Dict[str, Any] = {}
    for pname, flag, raw in params:
        if props and pname not in props:
            alt = next((k for k in props if k.lower() == pname.lower()), None)
            if alt is None:
                continue  # unknown parameter: dropped (schemas are strict)
            pname = alt
        v, prob = coerce_param(raw, flag, props.get(pname))
        if prob:
            problems.append(f"{canon}.{pname}: {prob}")
        args[pname] = v
    for req in schema.get("required") or []:
        if req not in args:
            problems.append(f"{canon}: missing required parameter '{req}'")
    if problems:
        return None, problems
    return {"name": canon, "arguments": args}, []


# ---- permissive JSON (recovery path for <tool_call>{...}) -------------------

class LooseJSONError(ValueError):
    pass


class LooseJSONParser:
    """Tolerates Windows backslashes, unescaped inner quotes, trailing commas."""

    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.n = len(text)

    def error(self, message: str) -> LooseJSONError:
        return LooseJSONError(f"{message} at position {self.i}")

    def skip_ws(self) -> None:
        while self.i < self.n and self.text[self.i].isspace():
            self.i += 1

    def parse(self) -> Any:
        v = self.parse_value()
        self.skip_ws()
        return v

    def parse_value(self) -> Any:
        self.skip_ws()
        if self.i >= self.n:
            raise self.error("unexpected end")
        ch = self.text[self.i]
        if ch in "\"'":
            return self.parse_string()
        if ch == "{":
            return self.parse_object()
        if ch == "[":
            return self.parse_array()
        for literal, value in (("true", True), ("false", False), ("null", None)):
            if self.text.startswith(literal, self.i):
                self.i += len(literal)
                return value
        m = re.match(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?", self.text[self.i:])
        if m:
            raw = m.group(0)
            self.i += len(raw)
            try:
                return float(raw) if any(c in raw for c in ".eE") else int(raw)
            except Exception:
                return raw
        start = self.i
        while self.i < self.n and self.text[self.i] not in ",}]":
            self.i += 1
        token = self.text[start:self.i].strip()
        if not token:
            raise self.error("invalid value")
        return token

    def parse_string(self) -> str:
        quote = self.text[self.i]
        self.i += 1
        out: List[str] = []
        simple = {'"': '"', "'": "'", "\\": "\\", "/": "/", "b": "\b",
                  "f": "\f", "n": "\n", "r": "\r", "t": "\t"}
        while self.i < self.n:
            ch = self.text[self.i]
            if ch == quote:
                j = self.i + 1
                while j < self.n and self.text[j].isspace():
                    j += 1
                if j >= self.n or self.text[j] in ",}]:":
                    self.i += 1
                    return "".join(out)
                out.append(ch)
                self.i += 1
                continue
            if ch == "\\":
                if self.i + 1 >= self.n:
                    out.append("\\")
                    self.i += 1
                    continue
                nxt = self.text[self.i + 1]
                if nxt == "u" and self.i + 5 < self.n:
                    hx = self.text[self.i + 2:self.i + 6]
                    if re.fullmatch(r"[0-9a-fA-F]{4}", hx):
                        out.append(chr(int(hx, 16)))
                        self.i += 6
                        continue
                if nxt in simple:
                    out.append(simple[nxt])
                    self.i += 2
                    continue
                out.append("\\")  # invalid escape (C:\Users...) => literal backslash
                self.i += 1
                continue
            out.append(ch)
            self.i += 1
        return "".join(out)

    def parse_object_key(self) -> str:
        self.skip_ws()
        if self.i >= self.n:
            raise self.error("missing object key")
        if self.text[self.i] in "\"'":
            return self.parse_string()
        start = self.i
        while self.i < self.n and self.text[self.i] not in ":,}":
            self.i += 1
        key = self.text[start:self.i].strip()
        if not key:
            raise self.error("empty object key")
        return key

    def parse_object(self) -> Dict[str, Any]:
        self.i += 1
        obj: Dict[str, Any] = {}
        while self.i < self.n:
            self.skip_ws()
            if self.i < self.n and self.text[self.i] == "}":
                self.i += 1
                return obj
            key = self.parse_object_key()
            self.skip_ws()
            if self.i >= self.n or self.text[self.i] != ":":
                raise self.error("expected :")
            self.i += 1
            obj[str(key)] = self.parse_value()
            self.skip_ws()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1
                self.skip_ws()
                if self.i < self.n and self.text[self.i] == "}":
                    self.i += 1
                    return obj
                continue
            if self.i < self.n and self.text[self.i] == "}":
                self.i += 1
            return obj
        return obj

    def parse_array(self) -> List[Any]:
        self.i += 1
        arr: List[Any] = []
        while self.i < self.n:
            self.skip_ws()
            if self.i < self.n and self.text[self.i] == "]":
                self.i += 1
                return arr
            arr.append(self.parse_value())
            self.skip_ws()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1
                continue
            if self.i < self.n and self.text[self.i] == "]":
                self.i += 1
            return arr
        return arr


def parse_loose_object(text: str) -> Optional[Dict[str, Any]]:
    try:
        v = LooseJSONParser(text).parse()
        return v if isinstance(v, dict) else None
    except Exception:
        return None


def extract_first_json_object(text: str) -> Optional[str]:
    start = text.find("{")
    if start < 0:
        return None
    i, depth, in_str = start, 0, False
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    return text[start:]


def parse_single_tool_call_payload(raw: str) -> Optional[Dict[str, Any]]:
    raw = raw.strip()
    try:
        v = json.loads(raw)
        if isinstance(v, dict):
            return v
    except Exception:
        pass
    obj_text = extract_first_json_object(raw)
    if obj_text:
        obj = parse_loose_object(obj_text)
        if isinstance(obj, dict):
            return obj
    nm = re.search(r'"name"\s*:\s*"([^"]+)"', raw)
    if not nm:
        return None
    name = nm.group(1)
    am = re.search(r'"(?:arguments|input)"\s*:\s*', raw[nm.end():])
    if not am:
        return {"name": name, "arguments": {}}
    arg_obj = extract_first_json_object(raw[nm.end() + am.end():])
    if arg_obj:
        args = parse_loose_object(arg_obj)
        if isinstance(args, dict):
            return {"name": name, "arguments": args}
    return {"name": name, "arguments": {}}


def parse_tool_call_tags(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    source = text or ""
    calls: List[Dict[str, Any]] = []

    def _extract(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        name = obj.get("name")
        args = obj.get("arguments", obj.get("input", {}))
        if isinstance(args, str):
            pa = parse_loose_object(args)
            args = pa if pa is not None else {}
        if name:
            return {"name": str(name), "arguments": args if isinstance(args, dict) else {}}
        return None

    for m in re.finditer(r"<tool_call\b[^>]*>(.*?)</tool_call\s*>", source, re.S | re.I):
        obj = parse_single_tool_call_payload(m.group(1))
        c = _extract(obj) if isinstance(obj, dict) else None
        if c:
            calls.append(c)

    if not calls:  # closing tag missing / mangled
        for sm in TOOL_CALL_START_RE.finditer(source):
            tail = source[sm.end():]
            obj = parse_single_tool_call_payload(tail)
            c = _extract(obj) if isinstance(obj, dict) else None
            if c:
                calls.append(c)
                if ANY_DSML_RE.search(tail) or STRAY_RE.search(tail):
                    return TOOL_CALL_START_RE.sub("", source[:sm.start()]).strip(), calls
                break

    if not calls:
        return source.strip(), []
    clean = re.sub(r"<tool_call\b[^>]*>.*?</tool_call\s*>", "", source, flags=re.S | re.I)
    clean = STRAY_RE.sub("", clean)
    return re.sub(r"\n{3,}", "\n\n", clean).strip(), calls


# ---- reply sanitising -------------------------------------------------------

_CITATION_RE = re.compile(r"\[citation:\d+\]")
_HALLUCINATED_TURN_RE = re.compile(r"\n\[(?:USER|TOOL_RESULT)\b[^\]\n]*\]")


def sanitize_reply(text: str) -> str:
    t = text or ""
    t = re.sub(r"^\s*\[ASSISTANT\][ \t]*\n?", "", t)
    t = _CITATION_RE.sub("", t)
    m = _HALLUCINATED_TURN_RE.search(t)
    if m:
        last_close = 0
        for cm in INVOKE_CLOSE_RE.finditer(t):
            last_close = cm.end()
        if m.start() >= last_close:  # never cut inside a tool call
            t = t[:m.start()]
    return t


def parse_tool_calls(text: str, tools: Optional[Dict[str, Dict[str, Any]]] = None
                     ) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    """
    Returns (clean_text, valid_calls, problems).
    DSML is authoritative; the <tool_call> JSON form is only tried when no
    DSML invoke exists (prevents double parsing of one response).
    """
    src = sanitize_reply(text)
    problems: List[str] = []
    calls: List[Dict[str, Any]] = []

    src, unresolved = _repair_missing_invokes(src, tools)
    raws, spans, truncated = _scan_invokes(src)
    if unresolved:
        problems.append(f"{unresolved} tool call(s) had broken markup (a missing "
                        "<｜DSML｜invoke name=...> line) and were not executed")
    if raws or truncated:
        for name, params in raws:
            call, probs = build_call(name, params, tools)
            if call:
                calls.append(call)
            else:
                problems.extend(probs)
        if truncated:
            problems.append("the last tool call was cut off before it was complete")
        clean = src
        for a, b in reversed(spans):
            clean = clean[:a] + clean[b:]
    else:
        clean, jcalls = parse_tool_call_tags(src)
        for jc in jcalls:
            plist = []
            for k, v in (jc.get("arguments") or {}).items():
                if isinstance(v, str):
                    plist.append((k, "true", v))
                else:
                    plist.append((k, "false", compact_json(v)))
            call, probs = build_call(jc["name"], plist, tools)
            if call:
                calls.append(call)
            else:
                problems.extend(probs)

    if tools and not calls and not problems:
        for am in ANY_DSML_RE.finditer(src):
            if not _inside_fence(src, am.start()):
                problems.append("your reply contained tool-call markup that could not be read")
                break

    clean = STRAY_RE.sub("", clean)
    clean = re.sub(r"(?:```|~~~)[a-zA-Z]*\s*(?:```|~~~)", "", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    return clean, calls, problems


def reconcile_stream(final: str, sent: str) -> Tuple[str, bool]:
    """
    What is still to be sent after `sent` was already streamed to the client.
    Returns (rest, diverged). Whitespace differences are ignored (the final
    text is stripped / newline-collapsed, the streamed text is not). If the
    streamed text is not a prefix of the final text even ignoring whitespace,
    nothing more is sent (a stream cannot be retracted) and diverged=True.
    """
    if not sent:
        return final, False
    if final.startswith(sent):
        return final[len(sent):], False
    i, j, n, m = 0, 0, len(final), len(sent)
    while j < m:
        if sent[j].isspace():
            j += 1
            continue
        while i < n and final[i].isspace():
            i += 1
        if i >= n or final[i] != sent[j]:
            return "", True
        i += 1
        j += 1
    return final[i:], False


class SafeTextStream:
    """
    Feeds only text that is safe to show to the client:
      * never any part of a tool call (blocks at the first DSML / <tool_call>),
      * applies the same removals as sanitize_reply() ([ASSISTANT] header,
        [citation:N], hallucinated [USER]/[TOOL_RESULT] turns) BEFORE sending,
      * holds back a trailing fragment that could still turn into one of those.
    The streamed text is therefore (up to whitespace) a prefix of the final reply.
    """
    MARK_RE = re.compile(r"<[|｜]+\s*DSML|<tool_call\b", re.I)
    _HEADER_RE = re.compile(r"^\s*\[ASSISTANT\][ \t]*\n?")
    _CITE_HOLD_RE = re.compile(r"\[(?:c(?:i(?:t(?:a(?:t(?:i(?:o(?:n(?::\d*)?)?)?)?)?)?)?)?)?$")
    _TURN_HOLD_RE = re.compile(r"\n\[([^\]\n]{0,40})$")
    _TURN_WORDS = ("USER", "TOOL_RESULT")

    def __init__(self, emit: Callable[[str], None]):
        self.emit = emit
        self.sent_text = ""
        self.blocked = False

    @classmethod
    def _turn_prefix(cls, rest: str) -> bool:
        return any(w.startswith(rest) or rest.startswith(w) for w in cls._TURN_WORDS)

    def update(self, full: str) -> None:
        if self.blocked:
            return
        s = self._HEADER_RE.sub("", full)
        st = s.lstrip()
        if st and len(st) < len("[ASSISTANT]") and "[ASSISTANT]".startswith(st):
            return                                   # might still become a role header
        limit = len(s)
        blocked = False
        m = self.MARK_RE.search(s)
        if m:
            limit, blocked = m.start(), True
        tm = _HALLUCINATED_TURN_RE.search(s, 0, limit)
        if tm:
            limit, blocked = tm.start(), True
        seg = s[:limit]
        if not blocked:
            lt = seg.rfind("<")
            if lt >= 0 and len(seg) - lt < 24 and ">" not in seg[lt:]:
                limit = lt
            cm = self._CITE_HOLD_RE.search(seg, 0, limit)
            if cm:
                limit = min(limit, cm.start())
            hm = self._TURN_HOLD_RE.search(seg, 0, limit)
            if hm and self._turn_prefix(hm.group(1)):
                limit = min(limit, hm.start())
            limit = len(seg[:limit].rstrip("\n"))      # a trailing newline may still precede a [USER] marker
        vis = _CITATION_RE.sub("", s[:limit])
        if blocked:
            self.blocked = True
        if not vis.startswith(self.sent_text):
            return                                   # cannot happen by construction; stay safe
        delta = vis[len(self.sent_text):]
        if delta:
            self.sent_text += delta
            self.emit(delta)


# ============================================================================
# Tools -> prompt text
# ============================================================================

def minify_schema(node: Any, desc_limit: Optional[int] = None, _depth: int = 0) -> Any:
    if desc_limit is None:
        desc_limit = _state().PARAM_DESC_LIMIT
    if isinstance(node, (list, dict)) and _depth > 32:
        return [] if isinstance(node, list) else {}      # pathological nesting: never recurse forever
    if isinstance(node, list):
        return [minify_schema(x, desc_limit, _depth + 1) for x in node]
    if not isinstance(node, dict):
        return node
    out: Dict[str, Any] = {}
    for k, v in node.items():
        if k in ("$schema", "additionalProperties", "title", "examples", "$id"):
            continue
        if k == "description" and isinstance(v, str):
            out[k] = trim_text_boundary(v, desc_limit)
        elif k == "properties" and isinstance(v, dict):
            out[k] = {pk: minify_schema(pv, desc_limit, _depth + 1) for pk, pv in v.items()}
        else:
            out[k] = minify_schema(v, desc_limit, _depth + 1)
    return out


TOOL_GRAMMAR = [
    "You have access to the following client-side tools.",
    "When you need a tool, end your reply with ONE DeepSeek DSML tool_calls block.",
    "Do NOT wrap DSML in Markdown code fences. Do NOT use <tool_call>{JSON}</tool_call>.",
    "",
    "Grammar:",
    "<｜DSML｜tool_calls>",
    '<｜DSML｜invoke name="TOOL_NAME">',
    '<｜DSML｜parameter name="PARAMETER_NAME" string="true">RAW_STRING</｜DSML｜parameter>',
    '<｜DSML｜parameter name="PARAMETER_NAME" string="false">JSON_VALUE</｜DSML｜parameter>',
    "</｜DSML｜invoke>",
    "</｜DSML｜tool_calls>",
    "",
    'String parameters MUST use string="true" and are written RAW (no JSON escaping, so',
    "Windows paths and source code are safe). Numbers, booleans, arrays and objects use",
    'string="false" with valid JSON. Several <｜DSML｜invoke> blocks are allowed in one',
    "tool_calls block. Only use tool names and parameters that exist below.",
    "",
    "Example:",
    "<｜DSML｜tool_calls>",
    '<｜DSML｜invoke name="Read">',
    '<｜DSML｜parameter name="file_path" string="true">C:\\Users\\Pc\\Desktop\\hello.txt</｜DSML｜parameter>',
    '<｜DSML｜parameter name="limit" string="false">50</｜DSML｜parameter>',
    "</｜DSML｜invoke>",
    "</｜DSML｜tool_calls>",
    "",
    "Available tools:",
]


def build_tools_text(tools: Dict[str, Dict[str, Any]], tool_choice: Optional[Dict[str, Any]] = None) -> str:
    if not tools:
        return ""
    lines = list(TOOL_GRAMMAR)
    for name, tool in tools.items():
        desc = trim_text_boundary(str(tool.get("description", "") or ""), _state().TOOL_DESC_LIMIT)
        schema = minify_schema(tool.get("input_schema") or tool.get("parameters") or {})
        lines.append(f"- {name}: {desc}")
        lines.append(f"  input schema: {compact_json(schema)}")
    tc = tool_choice or {}
    t = tc.get("type")
    if t == "any":
        lines += ["", "You MUST call at least one tool in this reply."]
    elif t == "tool" and tc.get("name"):
        lines += ["", f"You MUST call the tool '{tc['name']}' in this reply."]
    return "\n".join(lines)


# ============================================================================
# Anthropic messages -> text
# ============================================================================

def _result_text(block: Dict[str, Any]) -> str:
    v = block.get("content", "")
    if isinstance(v, list):
        parts = []
        for x in v:
            if isinstance(x, dict) and x.get("type") == "text":
                parts.append(str(x.get("text", "")))
            elif isinstance(x, dict) and x.get("type") == "image":
                parts.append("[image attached]")
            elif isinstance(x, str):
                parts.append(x)
        return "\n".join(parts)
    return str(v if v is not None else "")


def render_message(m: Dict[str, Any], limit: Optional[int] = None) -> str:
    """Render one message; limit trims each BLOCK (order is preserved)."""
    role = str(m.get("role", "user")).upper()
    content = m.get("content", "")
    text_l = limit * 2 if limit else None
    if isinstance(content, str):
        return f"[{role}]\n{trim_text_boundary(content, text_l)}"
    if not isinstance(content, list):
        return f"[{role}]\n{trim_text_boundary(content_to_text(content), text_l)}"
    pieces: List[str] = []
    for b in content:
        if isinstance(b, str):
            pieces.append(trim_text_boundary(b, text_l))
            continue
        if not isinstance(b, dict):
            pieces.append(trim_text_boundary(str(b), text_l))
            continue
        t = b.get("type")
        if t == "text":
            pieces.append(trim_text_boundary(str(b.get("text", "")), text_l))
        elif t == "tool_use":
            inp = b.get("input", {})
            pieces.append(f"[TOOL_USE id={b.get('id', '')}]\n" +
                          canonical_dsml_tool_call(str(b.get("name", "")), inp if isinstance(inp, dict) else {}, limit))
        elif t == "tool_result":
            err = " ERROR" if b.get("is_error") else ""
            pieces.append(f"[TOOL_RESULT id={b.get('tool_use_id', '')}{err}]\n" +
                          trim_text_boundary(_result_text(b), limit))
        elif t == "image":
            pieces.append("[image attached]")
        elif t == "document":
            pieces.append(f"[file attached: {b.get('title') or b.get('name') or 'document'}]")
        elif t in ("thinking", "redacted_thinking"):
            continue
        else:
            pieces.append(trim_text_boundary(compact_json(b), limit or 4000))
    body = "\n\n".join(p for p in pieces if p != "")
    return f"[{role}]\n{body}"


def render_messages(messages: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
    return "\n\n".join(render_message(m, limit) for m in messages)


def compact_history(messages: List[Dict[str, Any]], budget: int) -> str:
    """
    Render the history within `budget` chars using only whole-message / whole-
    block operations. Order of escalation:
      1. everything full
      2. older messages get per-block limits (progressively smaller)
      3. oldest middle messages are dropped (first + recent tail are kept)
      4. recent tail gets per-block limits too
    """
    if not messages:
        return ""
    full = [render_message(m) for m in messages]
    joined = "\n\n".join(full)
    if len(joined) <= budget:
        return joined

    n = len(messages)
    tail_start = max(1, n - _state().KEEP_RECENT_MESSAGES_FULL)

    def build(scale: float, tail_scale: Optional[float], drop: int) -> str:
        parts: List[str] = []
        omitted = 0
        for idx, m in enumerate(messages):
            if 1 <= idx < 1 + drop and idx < tail_start:
                omitted += 1
                continue
            if idx == 0:
                parts.append(render_message(m, int(_state().BASE_BLOCK_LIMIT * 3 * scale)) if scale < 1 else full[0])
            elif idx >= tail_start:
                if tail_scale is None:
                    parts.append(full[idx])
                else:
                    parts.append(render_message(m, max(400, int(_state().BASE_BLOCK_LIMIT * tail_scale))))
            else:
                parts.append(render_message(m, max(300, int(_state().BASE_BLOCK_LIMIT * scale))))
        if omitted:
            parts.insert(1, f"[{omitted} older messages omitted by DeepSeek Local Bridge to save context]")
        return "\n\n".join(parts)

    for scale in (1.0, 0.5, 0.25, 0.1):
        cur = build(scale, None, 0)
        if len(cur) <= budget:
            return cur
    middle = max(0, tail_start - 1)
    lo, hi = 0, middle
    best = None
    while lo <= hi:  # smallest drop count that fits
        mid = (lo + hi) // 2
        cur = build(0.1, None, mid)
        if len(cur) <= budget:
            best, hi = cur, mid - 1
        else:
            lo = mid + 1
    if best is not None:
        return best
    for tail_scale in (0.5, 0.25, 0.1, 0.03):
        cur = build(0.05, tail_scale, middle)
        if len(cur) <= budget:
            return cur
    # Last resort: only the first and the last message, block-trimmed.
    keep = [messages[0]] + ([messages[-1]] if n > 1 else [])
    per = max(500, budget // (2 * max(1, len(keep))))
    return "[history heavily compacted by DeepSeek Local Bridge]\n\n" + render_messages(keep, per)


PREAMBLE = (
    "You are the ASSISTANT in a tool-using agent session. A local gateway forwards the agent's\n"
    "requests to you as plain text.\n"
    "Rules:\n"
    "1. Reply with ONLY the next assistant turn: optional text, then optionally one tool-call block\n"
    "   in the DSML format described under [TOOLS]. Never write role headers such as [ASSISTANT],\n"
    "   [USER] or [TOOL_RESULT], and never invent tool results.\n"
    "2. [TOOL_RESULT ...] entries are outputs of tools you called earlier; continue the task from them.\n"
    "3. Later messages in this chat contain only NEW items (new user messages / tool results).\n"
    "   Everything said earlier in this chat is still your context - remember it."
)
TAIL = "(Write only your next assistant turn now, without a role header. Use DSML for tool calls.)"


def build_full_prompt(req: "NormReq", history_budget: int) -> str:
    tools_text = req.tools_text
    parts = [PREAMBLE]
    if req.system_text:
        parts.append("[SYSTEM]\n" + req.system_text)
    if tools_text:
        parts.append("[TOOLS]\n" + tools_text)
    overhead = sum(len(p) for p in parts) + 400
    budget = max(20_000, min(history_budget, _state().MAX_PROMPT_CHARS - overhead))
    parts.append("[TRANSCRIPT]\n" + compact_history(req.messages, budget))
    parts.append(TAIL)
    return "\n\n".join(parts)


def build_delta_prompt(req: "NormReq", delta: List[Dict[str, Any]], tools_changed: bool) -> str:
    parts = ["[NEW ITEMS SINCE YOUR LAST TURN]\n" + render_messages(delta, limit=_state().DELTA_BLOCK_LIMIT or None)]
    if tools_changed and req.tools_text:
        parts.append("[TOOLS UPDATE - the available tools changed; this list replaces the old one]\n" + req.tools_text)
    parts.append(TAIL)
    return "\n\n".join(parts)


def build_repair_prompt(problems: List[str], accepted: Optional[List[str]] = None) -> str:
    plist = "\n".join(f"- {p}" for p in problems[:12])
    msg = "[GATEWAY NOTICE] Your previous reply could not be executed completely:\n" + plist
    if accepted:
        msg += ("\n\nThese calls were accepted and will run: " + ", ".join(accepted[:12]) +
                ". Do NOT repeat them.\nRe-send ONLY the corrected version of the call(s) that failed")
    else:
        msg += "\n\nRe-send ONLY the corrected, COMPLETE tool_calls block"
    return msg + (" in the exact DSML format (string=\"true\" for strings, raw values). "
                  "No apology, no extra text.")


def _call_key(c: Dict[str, Any]) -> str:
    return c.get("name", "") + "|" + compact_json(c.get("arguments", {}))


def merge_repaired(kept: List[Dict[str, Any]], repaired: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Valid calls from the first reply stay; the repaired ones follow (no duplicates)."""
    seen = {_call_key(c) for c in repaired}
    return [c for c in kept if _call_key(c) not in seen] + repaired


# ============================================================================
# Request normalisation
# ============================================================================

_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)


def msg_signature(m: Dict[str, Any]) -> str:
    """Stable identity of a message, tolerant to reminders / compacted results."""
    role = str(m.get("role", ""))
    content = m.get("content", "")
    blocks = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
    parts = [role]
    for b in blocks:
        if isinstance(b, str):
            b = {"type": "text", "text": b}
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text":
            if role == "user":
                txt = _REMINDER_RE.sub("", str(b.get("text", ""))).strip()
                if txt:
                    parts.append("t:" + h16(txt))
        elif t == "tool_use":
            parts.append("u:" + str(b.get("id", "")))
        elif t == "tool_result":
            parts.append("r:" + str(b.get("tool_use_id", "")))
        elif t in ("thinking", "redacted_thinking"):
            continue
        elif t:
            parts.append("x:" + str(t))
    return h16("|".join(parts))


def assistant_tool_ids(m: Dict[str, Any]) -> List[str]:
    c = m.get("content")
    if not isinstance(c, list):
        return []
    return [str(b.get("id", "")) for b in c if isinstance(b, dict) and b.get("type") == "tool_use"]


def match_continuation(prev_sigs: List[str], prev_n: int, reply_ids: List[str],
                       messages: List[Dict[str, Any]], sigs: List[str]) -> bool:
    """Is `messages` = (previous request) + (our reply) + new items?"""
    if prev_n <= 0 or len(messages) < prev_n + 2:
        return False
    if sigs[:prev_n] != prev_sigs:
        return False
    a = messages[prev_n]
    if a.get("role") != "assistant":
        return False
    return assistant_tool_ids(a) == list(reply_ids)


@dataclass
class NormReq:
    raw: Dict[str, Any]
    fmt: str
    model: str
    stream: bool
    max_tokens: Optional[int]
    messages: List[Dict[str, Any]]
    system_text: str
    tools: Dict[str, Dict[str, Any]]
    tool_choice: Dict[str, Any]
    sigs: List[str]
    tools_sig: str
    tools_text: str
    side: bool
    id_prefix: str = "toolu_"
    pin: Optional[str] = None            # set by /a/<account>/... endpoints
    tag: Optional[str] = None            # set by /s/<run>.<agent>/... (swarm agents)
    role: Optional[str] = None           # planner | reviewer | coder | fast ...

    @property
    def force_tool(self) -> bool:
        return bool(self.tools) and self.tool_choice.get("type") in ("any", "tool")


def normalize_anthropic(data: Dict[str, Any], fmt: str = "anthropic", id_prefix: str = "toolu_") -> NormReq:
    messages = [m for m in (data.get("messages") or []) if isinstance(m, dict)]
    system_text = content_to_text(data.get("system")) if data.get("system") else ""
    tc = data.get("tool_choice") if isinstance(data.get("tool_choice"), dict) else {}
    tools_list = [t for t in (data.get("tools") or []) if isinstance(t, dict) and t.get("name")]
    if tc.get("type") == "none":
        tools_list = []
    tools = {str(t["name"]): t for t in tools_list}
    model = str(data.get("model") or "")
    mt = data.get("max_tokens")
    try:
        mt = int(mt) if mt is not None else None
    except Exception:
        mt = None
    return NormReq(
        raw=data, fmt=fmt, model=model, stream=bool(data.get("stream")), max_tokens=mt,
        messages=messages, system_text=system_text, tools=tools, tool_choice=tc,
        sigs=[msg_signature(m) for m in messages],
        tools_sig=h16(",".join(sorted(tools))),
        tools_text=build_tools_text(tools, tc),
        side=("haiku" in model.lower() and not tools),
        id_prefix=id_prefix,
    )


def openai_to_anthropic(data: Dict[str, Any]) -> Dict[str, Any]:
    system_parts: List[str] = []
    messages: List[Dict[str, Any]] = []
    for m in data.get("messages") or []:
        role = m.get("role")
        content = m.get("content")
        if role in ("system", "developer"):
            system_parts.append(content_to_text(content))
        elif role == "user":
            if isinstance(content, list):
                blocks = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") in ("text", "input_text"):
                        blocks.append({"type": "text", "text": str(p.get("text", ""))})
                    elif isinstance(p, dict):
                        blk = None
                        if p.get("type") == "image_url":
                            u = p.get("image_url")
                            blk = _data_url_block(u.get("url") if isinstance(u, dict) else u)
                        elif p.get("type") == "file":
                            f = p.get("file") or {}
                            blk = _data_url_block(f.get("file_data", ""), str(f.get("filename", "")))
                        blocks.append(blk or {"type": "text", "text": "[image attached]"})
                messages.append({"role": "user", "content": blocks})
            else:
                messages.append({"role": "user", "content": content_to_text(content)})
        elif role == "assistant":
            blocks = []
            txt = content_to_text(content)
            if txt:
                blocks.append({"type": "text", "text": txt})
            for tc in m.get("tool_calls") or []:
                fn = tc.get("function", {}) if isinstance(tc, dict) else {}
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = parse_loose_object(args) or {}
                blocks.append({"type": "tool_use", "id": tc.get("id") or make_id("call_"),
                               "name": fn.get("name", ""), "input": args if isinstance(args, dict) else {}})
            messages.append({"role": "assistant", "content": blocks or ""})
        elif role == "tool":
            block = {"type": "tool_result", "tool_use_id": m.get("tool_call_id", ""),
                     "content": content_to_text(content)}
            if messages and messages[-1]["role"] == "user" and isinstance(messages[-1]["content"], list) \
                    and messages[-1]["content"] and messages[-1]["content"][-1].get("type") == "tool_result":
                messages[-1]["content"].append(block)
            else:
                messages.append({"role": "user", "content": [block]})
    tools = []
    for t in data.get("tools") or []:
        fn = t.get("function", {}) if t.get("type") == "function" else t
        if fn.get("name"):
            tools.append({"name": fn["name"], "description": fn.get("description", ""),
                          "input_schema": fn.get("parameters") or {}})
    tc = data.get("tool_choice")
    tool_choice: Dict[str, Any] = {}
    if tc == "none":
        tool_choice = {"type": "none"}
    elif tc == "required":
        tool_choice = {"type": "any"}
    elif isinstance(tc, dict) and tc.get("function", {}).get("name"):
        tool_choice = {"type": "tool", "name": tc["function"]["name"]}
    return {"model": data.get("model"), "stream": data.get("stream"),
            "max_tokens": data.get("max_tokens") or data.get("max_completion_tokens"),
            "system": "\n\n".join(system_parts) if system_parts else None,
            "messages": messages, "tools": tools, "tool_choice": tool_choice}


# ============================================================================
# Outcomes and response builders
# ============================================================================

@dataclass
class Outcome:
    text: str
    calls: List[Dict[str, Any]]           # each: id, name, arguments
    stop_reason: str = "end_turn"
    usage: Optional[Tuple[int, int]] = None     # exact (input, output) tokens when the provider reports them
    account: str = ""
    tier: int = 0


def anthropic_message(o: Outcome, model: str, in_tokens: int) -> Dict[str, Any]:
    blocks: List[Dict[str, Any]] = []
    if o.text:
        blocks.append({"type": "text", "text": o.text})
    for c in o.calls:
        blocks.append({"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["arguments"]})
    return {
        "id": "msg_" + uuid.uuid4().hex[:24], "type": "message", "role": "assistant",
        "model": model, "content": blocks or [{"type": "text", "text": ""}],
        "stop_reason": o.stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": o.usage[0] if o.usage else in_tokens,
                  "output_tokens": o.usage[1] if o.usage else estimate_tokens([o.text, o.calls]),
                  "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
    }


def openai_completion(o: Outcome, model: str, in_tokens: int) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"role": "assistant", "content": o.text or None}
    finish = "stop"
    if o.calls:
        msg["tool_calls"] = [{"id": c["id"], "type": "function",
                              "function": {"name": c["name"], "arguments": compact_json(c["arguments"])}}
                             for c in o.calls]
        finish = "tool_calls"
    out_t = o.usage[1] if o.usage else estimate_tokens([o.text, o.calls])
    in_tokens = o.usage[0] if o.usage else in_tokens
    return {"id": "chatcmpl-" + uuid.uuid4().hex[:24], "object": "chat.completion",
            "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": msg, "finish_reason": finish}],
            "usage": {"prompt_tokens": in_tokens, "completion_tokens": out_t,
                      "total_tokens": in_tokens + out_t}}


class AnthropicSSE:
    def __init__(self, write: Callable[[str], None], model: str, in_tokens: int):
        self.write, self.model, self.in_tokens = write, model, in_tokens
        self.idx = 0
        self.text_open = False
        self.out_chars = 0
        self.mid = "msg_" + uuid.uuid4().hex[:24]

    def _ev(self, name: str, obj: Dict[str, Any]) -> None:
        self.write(f"event: {name}\ndata: {json.dumps(obj, ensure_ascii=False, separators=(',', ':'))}\n\n")

    def start(self) -> None:
        self._ev("message_start", {"type": "message_start", "message": {
            "id": self.mid, "type": "message", "role": "assistant", "model": self.model,
            "content": [], "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": self.in_tokens, "output_tokens": 1,
                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}})
        self._ev("ping", {"type": "ping"})

    def ping(self) -> None:
        self._ev("ping", {"type": "ping"})

    def _close_text(self) -> None:
        if self.text_open:
            self._ev("content_block_stop", {"type": "content_block_stop", "index": self.idx})
            self.idx += 1
            self.text_open = False

    def text(self, s: str) -> None:
        if not s:
            return
        if not self.text_open:
            self._ev("content_block_start", {"type": "content_block_start", "index": self.idx,
                                              "content_block": {"type": "text", "text": ""}})
            self.text_open = True
        self.out_chars += len(s)
        self._ev("content_block_delta", {"type": "content_block_delta", "index": self.idx,
                                          "delta": {"type": "text_delta", "text": s}})

    def tool(self, call: Dict[str, Any]) -> None:
        self._close_text()
        self._ev("content_block_start", {"type": "content_block_start", "index": self.idx,
                                          "content_block": {"type": "tool_use", "id": call["id"],
                                                            "name": call["name"], "input": {}}})
        payload = compact_json(call["arguments"])
        self.out_chars += len(payload)
        for pos in range(0, max(1, len(payload)), 4000):
            self._ev("content_block_delta", {"type": "content_block_delta", "index": self.idx,
                                              "delta": {"type": "input_json_delta",
                                                        "partial_json": payload[pos:pos + 4000]}})
        self._ev("content_block_stop", {"type": "content_block_stop", "index": self.idx})
        self.idx += 1

    def finish(self, stop_reason: str) -> None:
        self._close_text()
        self._ev("message_delta", {"type": "message_delta",
                                    "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                                    "usage": {"output_tokens": max(1, int(self.out_chars / _state().CHARS_PER_TOKEN))}})
        self._ev("message_stop", {"type": "message_stop"})

    def error(self, etype: str, msg: str) -> None:
        self._ev("error", {"type": "error", "error": {"type": etype, "message": msg}})


class OpenAISSE:
    def __init__(self, write: Callable[[str], None], model: str, in_tokens: int):
        self.write, self.model = write, model
        self.rid = "chatcmpl-" + uuid.uuid4().hex[:24]
        self.created = int(time.time())
        self.tool_index = 0

    def _chunk(self, delta: Dict[str, Any], finish: Optional[str] = None) -> None:
        obj = {"id": self.rid, "object": "chat.completion.chunk", "created": self.created,
               "model": self.model, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
        self.write("data: " + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n\n")

    def start(self) -> None:
        self._chunk({"role": "assistant"})

    def ping(self) -> None:
        self.write(": ping\n\n")

    def text(self, s: str) -> None:
        if s:
            self._chunk({"content": s})

    def tool(self, call: Dict[str, Any]) -> None:
        self._chunk({"tool_calls": [{"index": self.tool_index, "id": call["id"], "type": "function",
                                     "function": {"name": call["name"],
                                                  "arguments": compact_json(call["arguments"])}}]})
        self.tool_index += 1

    def finish(self, stop_reason: str) -> None:
        self._chunk({}, "tool_calls" if stop_reason == "tool_use" else "stop")
        self.write("data: [DONE]\n\n")

    def error(self, etype: str, msg: str) -> None:
        self.write("data: " + json.dumps({"error": {"message": msg, "type": etype}}) + "\n\n")
        self.write("data: [DONE]\n\n")


# ============================================================================
# Browser-side JavaScript
# ============================================================================

# Injected into every page BEFORE the site scripts run. It records DeepSeek's
# raw SSE stream (fetch and XHR) into window.__dsb.
HOOK_JS = r"""
(() => {
  try { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); } catch (e) {}
  if (window.__dsb) return;
  const B = { seq: 0, cur: null, up: { open: 0, n: 0, err: null, parsing: false, seen: false } };
  const UP_RE = /\/api\/v\d+\/file\/upload/;
  const FF_RE = /\/api\/v\d+\/file\/fetch/;
  window.__dsb = B;
  const URL_RE = /\/api\/v\d+\/chat\/(completion|continue|regenerate|edit_message|resume_stream)(\?|$)/;

  function newCur(url) {
    const c = { id: ++B.seq, url: url, text: '', think: '', frags: [], path: null, event: '', buf: '',
      status: null, messageId: null, incomplete: false, error: null, done: false, http: null,
      sessionId: null, gotData: false, t0: Date.now() };
    B.cur = c;
    return c;
  }
  function appendFrag(c, fr, s) {
    fr.content += s;
    if (fr.type === 'RESPONSE') c.text += s; else if (fr.type === 'THINK') c.think += s;
  }
  function addFragment(c, f) {
    const fr = { type: (f && f.type) || 'RESPONSE', content: '' };
    c.frags.push(fr);
    if (f && typeof f.content === 'string' && f.content) appendFrag(c, fr, f.content);
  }
  function recompute(c) {
    c.text = ''; c.think = '';
    for (const fr of c.frags) {
      if (fr.type === 'RESPONSE') c.text += fr.content; else if (fr.type === 'THINK') c.think += fr.content;
    }
  }
  function applyOp(c, path, op, v) {
    if (path === 'response' && op === 'BATCH' && Array.isArray(v)) {
      for (const s of v) {
        if (!s || typeof s !== 'object' || !s.p) continue;
        applyOp(c, s.p.indexOf('response') === 0 ? s.p : 'response/' + s.p, s.o || null, s.v);
      }
      return;
    }
    if (path === 'response/status') { c.status = v; return; }
    if (path === 'response/incomplete_message') { if (v) c.incomplete = true; return; }
    if (path === 'response/message_id') { c.messageId = v; return; }
    if (path === 'response/fragments') {
      if (op === 'APPEND' && Array.isArray(v)) { for (const f of v) addFragment(c, f); }
      else if (op === 'SET' && Array.isArray(v)) { c.frags = []; for (const f of v) addFragment(c, f); recompute(c); }
      return;
    }
    const m = /^response\/fragments\/(-?\d+)\/content$/.exec(path || '');
    if (m && typeof v === 'string') {
      let i = parseInt(m[1], 10); if (i < 0) i = c.frags.length + i;
      const fr = c.frags[i];
      if (fr) { if (op === 'SET') { fr.content = v; recompute(c); } else appendFrag(c, fr, v); }
    }
  }
  function onData(c, ev, o) {
    if (ev === 'ready') { if (o && o.response_message_id != null) c.messageId = o.response_message_id; return; }
    if (ev === 'error' || (ev === 'hint' && o && (o.type === 'error' || o.clear_response))) {
      c.error = (ev + ': ' + JSON.stringify(o)).slice(0, 500); return;
    }
    if (ev && ev !== 'message') return;
    if (!o || typeof o !== 'object') return;
    c.gotData = true;
    if (o.v && typeof o.v === 'object' && !Array.isArray(o.v) && o.v.response) {
      const r = o.v.response;
      if (r.message_id != null) c.messageId = r.message_id;
      if (r.status) c.status = r.status;
      if (r.incomplete_message) c.incomplete = true;
      c.frags = [];
      if (Array.isArray(r.fragments)) for (const f of r.fragments) addFragment(c, f);
      recompute(c);
      return;
    }
    if (o.p !== undefined && o.p !== null) c.path = o.p;
    applyOp(c, c.path, o.o === undefined ? null : o.o, o.v);
  }
  function handleLine(c, line) {
    if (line.indexOf('event:') === 0) { c.event = line.slice(6).trim(); return; }
    if (line.indexOf('data:') === 0) {
      let d = line.slice(5); if (d.charAt(0) === ' ') d = d.slice(1);
      let obj; try { obj = JSON.parse(d); } catch (e) { return; }
      onData(c, c.event, obj);
      return;
    }
    if (line === '') c.event = '';
  }
  function feed(c, chunk) {
    c.buf += chunk;
    let idx;
    while ((idx = c.buf.indexOf('\n')) >= 0) {
      const line = c.buf.slice(0, idx).replace(/\r$/, '');
      c.buf = c.buf.slice(idx + 1);
      handleLine(c, line);
    }
  }
  function finish(c) {
    if (c.done) return;
    if (!c.error && c.status !== 'FINISHED') c.incomplete = true;
    if (!c.gotData && !c.error) c.error = 'empty stream';
    c.done = true;
  }

  const origFetch = window.fetch;
  window.fetch = async function (input, init) {
    const url = typeof input === 'string' ? input : ((input && input.url) || '');
    const target = URL_RE.test(url);
    let c = null;
    if (target) {
      c = newCur(url);
      try {
        const body = init && init.body;
        if (typeof body === 'string') { const j = JSON.parse(body); c.sessionId = j.chat_session_id || null; }
      } catch (e) {}
    }
    const isUp = UP_RE.test(url);
    if (isUp) { B.up.open++; B.up.seen = true; }
    let resp;
    try { resp = await origFetch.apply(this, arguments); }
    catch (e) {
      if (isUp) { B.up.open--; B.up.err = 'upload failed: ' + e; }
      if (c) { c.error = 'fetch failed: ' + e; c.done = true; }
      throw e;
    }
    if (isUp) { B.up.open--; B.up.n++; if (!resp.ok) B.up.err = 'upload HTTP ' + resp.status; }
    if (FF_RE.test(url)) {
      try {
        resp.clone().json().then(j => {
          const files = (((j || {}).data || {}).biz_data || {}).files || [];
          B.up.parsing = files.some(f => /PEND|PARS|UPLOAD|PROCESS|WAIT/i.test(String((f || {}).status || '')));
        }).catch(() => {});
      } catch (e) {}
    }
    if (!target) return resp;
    c.http = resp.status;
    try {
      const clone = resp.clone();
      (async () => {
        try {
          const ct = clone.headers.get('content-type') || '';
          if (!clone.ok) { const t = await clone.text(); c.error = 'HTTP ' + clone.status + ': ' + t.slice(0, 500); c.done = true; return; }
          if (ct.indexOf('event-stream') < 0) { const t = await clone.text(); c.error = 'unexpected response: ' + t.slice(0, 500); c.done = true; return; }
          const reader = clone.body.getReader(); const dec = new TextDecoder('utf-8');
          for (;;) {
            const r = await reader.read();
            if (r.done) break;
            feed(c, dec.decode(r.value, { stream: true }));
          }
          feed(c, dec.decode() + '\n');
          finish(c);
        } catch (e) { c.error = 'stream error: ' + e; c.done = true; }
      })();
    } catch (e) { c.error = 'clone failed: ' + e; c.done = true; }
    return resp;
  };

  const XO = XMLHttpRequest.prototype.open, XS = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (m, u) { this.__dsu = String(u || ''); return XO.apply(this, arguments); };
  XMLHttpRequest.prototype.send = function (body) {
    if (UP_RE.test(this.__dsu || '')) {
      B.up.open++; B.up.seen = true;
      const xx = this;
      xx.addEventListener('loadend', () => { B.up.open--; B.up.n++; if (xx.status >= 400 || xx.status === 0) B.up.err = 'upload HTTP ' + xx.status; });
    }
    if (URL_RE.test(this.__dsu || '')) {
      const c = newCur(this.__dsu); let pos = 0; const xhr = this;
      try { if (typeof body === 'string') { const j = JSON.parse(body); c.sessionId = j.chat_session_id || null; } } catch (e) {}
      const pump = () => { try { const t = xhr.responseText || ''; if (t.length > pos) { feed(c, t.slice(pos)); pos = t.length; } } catch (e) {} };
      xhr.addEventListener('progress', pump);
      xhr.addEventListener('readystatechange', () => { c.http = xhr.status; pump(); });
      xhr.addEventListener('loadend', () => {
        pump(); c.http = xhr.status;
        if (xhr.status >= 400 || xhr.status === 0) c.error = c.error || ('HTTP ' + xhr.status);
        feed(c, '\n'); finish(c);
      });
    }
    return XS.apply(this, arguments);
  };
})();
"""

JS_STATE = r"""
(lastLen) => {
  const b = window.__dsb;
  if (!b) return { hook: false };
  const c = b.cur;
  if (!c) return { hook: true, seq: b.seq, id: 0, none: true };
  return { hook: true, seq: b.seq, id: c.id, done: c.done, len: c.text.length, tlen: c.think.length,
           text: (c.text.length !== lastLen) ? c.text : null, status: c.status, error: c.error,
           http: c.http, incomplete: c.incomplete, sessionId: c.sessionId, gotData: c.gotData };
}
"""

JS_SET_TEXT = r"""
({selector, text}) => {
  const ta = document.querySelector(selector) || document.querySelector('textarea');
  if (!ta) return { ok: false, len: 0, reason: 'no textarea' };
  const proto = ta.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
  const d = Object.getOwnPropertyDescriptor(proto, 'value');
  ta.focus();
  d.set.call(ta, text);
  ta.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: null }));
  ta.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: ta.value === text, len: ta.value.length };
}
"""

JS_SET_GENERIC_TEXT = r"""
({selector, text}) => {
  const el = document.querySelector(selector);
  if (!el) return {ok:false,len:0};
  el.focus();
  if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
    const proto = el.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const d = Object.getOwnPropertyDescriptor(proto, "value");
    if (d && d.set) d.set.call(el, text); else el.value = text;
  } else if (el.isContentEditable) {
    const sel=window.getSelection(); const range=document.createRange(); range.selectNodeContents(el); sel.removeAllRanges(); sel.addRange(range);
    if (!document.execCommand("insertText", false, text)) { el.textContent=text; }
  } else return {ok:false,len:0};
  el.dispatchEvent(new InputEvent("input", {bubbles:true, inputType:"insertText", data:null}));
  el.dispatchEvent(new Event("change", {bubbles:true}));
  const val=el.value !== undefined ? el.value : (el.innerText || el.textContent || "");
  return {ok:val===text,len:val.length};
}
"""

JS_TA_LEN = r"""
(selector) => { const ta = document.querySelector(selector) || document.querySelector('textarea'); if (ta) ta.focus(); return ta ? ta.value.length : -1; }
"""

JS_CLICK_SEND = r"""
(selector) => {
  const ta = document.querySelector(selector) || document.querySelector('textarea');
  if (!ta) return false;
  let root = ta.parentElement;
  for (let i = 0; i < 6 && root; i++, root = root.parentElement) {
    const btns = Array.from(root.querySelectorAll('[role="button"],button')).filter(
      b => b.getAttribute('aria-disabled') !== 'true' && !b.disabled && b.offsetParent !== null);
    if (btns.length) { btns[btns.length - 1].click(); return true; }
  }
  return false;
}
"""

JS_CLICK_CONTINUE = r"""
() => {
  const re = /^\s*(continue( generating)?|ادامه|继续生成|继续)\s*$/i;
  const els = Array.from(document.querySelectorAll('button,[role="button"],div,span')).filter(
    e => e.children.length <= 2 && re.test((e.innerText || '').trim()) && e.offsetParent !== null);
  if (!els.length) return false;
  els[els.length - 1].click();
  return true;
}
"""

JS_DOM_SNAPSHOT = r"""
() => {
  const els = Array.from(document.querySelectorAll('[class~="ds-markdown"]'));
  return { count: els.length, latest: els.length ? (els[els.length - 1].innerText || '') : '' };
}
"""

JS_DELETE_CHAT = r"""
async (sid) => {
  try {
    let t = localStorage.getItem('userToken');
    try { const o = JSON.parse(t); t = o.value || o.token || t; } catch (e) {}
    const r = await fetch('/api/v0/chat_session/delete', { method: 'POST',
      headers: { 'content-type': 'application/json', 'authorization': 'Bearer ' + t,
                 'x-client-platform': 'web', 'x-client-version': '2.5.0', 'x-client-locale': 'en_US' },
      body: JSON.stringify({ chat_session_id: sid }) });
    return r.status;
  } catch (e) { return -1; }
}
"""

TEXTAREA_SELECTORS = [
    "#chat-input",
    "textarea[placeholder='Message DeepSeek']",
    'textarea[placeholder*="message" i]',
    'textarea[placeholder*="ask" i]',
    'textarea[placeholder*="send" i]',
    'textarea[aria-label*="message" i]',
    "textarea",
]
JS_FIND_SELECTOR = "(sels) => sels.find(s => document.querySelector(s)) || null"


# ============================================================================
# DeepSeek browser driver
# ============================================================================

@dataclass
class Exchange:
    text: str
    session_id: Optional[str]
    seconds: float


JS_GENERIC_COMPOSER = r"""() => {
  const sels = [
    'textarea[placeholder*="message" i]', 'textarea[aria-label*="message" i]',
    'textarea[placeholder*="prompt" i]', 'textarea',
    '[contenteditable="true"][role="textbox"]', '[contenteditable="true"]'
  ];
  for (const s of sels) {
    for (const el of document.querySelectorAll(s)) {
      const r = el.getBoundingClientRect(), st = getComputedStyle(el);
      if (r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none' && !el.disabled) return s;
    }
  }
  return null;
}"""

JS_GENERIC_SEND = r"""(selector) => {
  const root = document.querySelector(selector);
  if (!root) return false;
  let p = root;
  for (let i = 0; i < 8 && p; i++, p = p.parentElement) {
    const bs = [...p.querySelectorAll('button,[role="button"]')];
    const b = bs.find(x => {
      const r=x.getBoundingClientRect(), st=getComputedStyle(x), s=((x.getAttribute('aria-label')||'')+' '+(x.getAttribute('title')||'')+' '+(x.textContent||'')).trim();
      return r.width>0&&r.height>0&&st.visibility!=='hidden'&&st.display!=='none'&&!x.disabled && /^(send|submit|ارسال|فرستادن)\b/i.test(s);
    });
    if (b) { b.click(); return true; }
  }
  return false;
}"""

# Start a new conversation in the SAME browser tab when explicitly requested. This is never
# used on the normal hot path; normal requests intentionally reuse the current web chat.
JS_GENERIC_NEW_CHAT = r"""() => {
  const vis=x=>{const r=x.getBoundingClientRect(),s=getComputedStyle(x);return r.width>0&&r.height>0&&s.visibility!=="hidden"&&s.display!=="none"&&!x.disabled};
  const text=x=>((x.getAttribute("aria-label")||"")+" "+(x.getAttribute("title")||"")+" "+(x.textContent||"")).replace(/\s+/g," ").trim();
  const re=/^(new\s+(chat|conversation)|start\s+(a\s+)?new\s+(chat|conversation)|new\s+thread|گفتگوی\s+جدید|چت\s+جدید)$/i;
  const c=[...document.querySelectorAll("button,[role=button]")].filter(vis).filter(x=>re.test(text(x)));
  if(!c.length)return false;
  c[0].click(); return true;
}"""

JS_SET_NATIVE_THINK = r"""(arg) => {
  const cfg=typeof arg==="object"&&arg!==null?arg:{enabled:!!arg,provider:""};
  const want=!!cfg.enabled, provider=String(cfg.provider||"");
  const vis=x=>{const r=x.getBoundingClientRect(),s=getComputedStyle(x);return r.width>0&&r.height>0&&s.visibility!=="hidden"&&s.display!=="none"&&!x.disabled};
  const label=x=>((x.getAttribute("aria-label")||"")+" "+(x.getAttribute("title")||"")+" "+(x.textContent||"")).replace(/\s+/g," ").trim();
  const state=x=>{const s=String(x.getAttribute("aria-pressed")||x.getAttribute("aria-selected")||x.getAttribute("aria-current")||x.dataset.state||x.dataset.selected||"").toLowerCase();return s==="true"||s==="selected"||s==="checked"||s==="on"};
  const isAutoSwitch=s=>/auto\s*[- ]?switch.*(thinking|reasoning|تفکر|استدلال)/i.test(s);
  const isThink=s=>!isAutoSwitch(s)&&/\b(deep\s*think|thinking|reasoning|think|medium|high|extra\s+high|تفکر|استدلال|متوسط|بالا)\b/i.test(s);
  const isFast=s=>/\b(instant|fast|standard|quick|سریع|فوری)\b/i.test(s);
  const controls=()=>[...document.querySelectorAll("button,[role=button],[aria-pressed],[aria-selected]")].filter(vis);
  const pickThink=()=>{const c=controls().filter(x=>isThink(label(x))&&!isAutoSwitch(label(x)));return c.sort((a,b)=>{const score=s=>{s=s.toLowerCase();return /deep\s*think|thinking|reasoning|think|تفکر|استدلال/.test(s)?100:/extra\s+high|high|بالا/.test(s)?90:/medium|متوسط/.test(s)?80:70};return score(label(b))-score(label(a))})[0]||null};
  const inMenu=x=>!!x.closest('[role="menu"], [role="listbox"], [data-radix-menu-content]');
  const pickFast=()=>{const c=controls().filter(x=>isFast(label(x)));return c.sort((a,b)=>Number(inMenu(b))-Number(inMenu(a)))[0]||null};
  let b=want?pickThink():pickFast();
  if(!b){
    const opener=controls().find(x=>/\b(instant|auto|model|medium|high|thinking|reasoning|مدل|فوری)\b/i.test(label(x)));
    if(opener){opener.click();}
  }
  b=want?pickThink():pickFast();
  if(!b){
    // Some ChatGPT plans expose "Instant" as the closed picker itself. If that is what is
    // currently shown, it already represents the requested non-thinking state; do not reopen it.
    if(!want){const shown=controls().find(x=>/^\s*instant\s*$/i.test(label(x)));if(shown)return true;}
    return false;
  }
  if(state(b))return true;
  // An unselected "Instant" control outside a menu is the picker opener, not the option itself.
  if(!want&&/^\s*instant\s*$/i.test(label(b))&&!b.closest('[role="menu"], [role="listbox"], [data-radix-menu-content]'))return true;
  b.click(); return true;
}"""

JS_GENERIC_SNAPSHOT = r"""() => {
  const textOf = (root) => {
    if (!root) return '';
    const c = root.cloneNode(true);
    c.querySelectorAll('button,summary,details,[aria-hidden="true"],[hidden],script,style,[class*="thinking" i],[class*="reasoning" i],[class*="chain-of-thought" i],[data-testid*="thinking" i],[data-testid*="reasoning" i],[aria-label*="thinking" i],[aria-label*="reasoning" i],[data-state*="reasoning" i]').forEach(x=>x.remove());
    return (c.innerText || c.textContent || '').replace(/\u00a0/g,' ').replace(/\n{3,}/g,'\n\n').trim();
  };
  const visible = (el) => { const r=el.getBoundingClientRect(), s=getComputedStyle(el); return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'; };
  const roots = [];
  const sels = [
    '[data-message-author-role="assistant"]', '[data-role="assistant"]',
    '[data-testid*="assistant-message" i]', '[data-testid*="assistant" i]',
    '[class*="assistant-message" i]', '[class*="assistant" i]', '[class*="response" i]'
  ];
  for (const sel of sels) {
    const found = [...document.querySelectorAll(sel)].filter(visible);
    if (!found.length) continue;
    for (const el of found) { const tx=textOf(el); if (tx) roots.push(tx); }
    if (roots.length) break;
  }
  const all = [...new Set(roots)];
  const stop = [...document.querySelectorAll('button,[role="button"]')].some(b => {
    if (!visible(b)) return false;
    const s=((b.getAttribute('aria-label')||'')+' '+(b.getAttribute('title')||'')+' '+(b.textContent||'')).trim();
    return /^(stop|stop generating|cancel generation|توقف|ایست)\b/i.test(s);
  });
  const auth = /\b(sign in|log in|login|continue with google|continue with apple|ورود|ثبت نام)\b/i.test((document.body?.innerText||'').slice(0,6000));
  return {assistant: all, latest: all.length ? all[all.length-1] : '', count: all.length, generating: stop, auth};
}"""


class DeepSeekWeb:
    """Owned and used by ONE thread only (sync Playwright requirement)."""

    def __init__(self, profile_dir: Optional[Path] = None, name: str = "", headed: bool = False,
                 on_state: Optional[Callable[[str], None]] = None,
                 on_exchange: Optional[Callable[[int, int, float], None]] = None,
                 provider: str = "deepseek_web") -> None:
        self.runtime_state = _state()
        self.profile_dir = Path(profile_dir) if profile_dir else _state().PROFILE_DIR
        self.name = name
        self.provider = str(provider or "deepseek_web")
        self.recipe = WEB_RECIPES.get(self.provider, WEB_RECIPES["deepseek_web"])
        self._think_pref_initial = bool(_state().THINK_MODE and self.recipe.get("supports_think"))
        self.headed_pref = headed          # keep the window visible (hands-on mode)
        self.on_state = on_state
        self.on_exchange = on_exchange
        self.abort = False
        self._minimize = True
        self.pw = None
        self.ctx = None
        self.scratch = None       # first page, reused for side requests
        self.headless = False
        self.epoch = 0
        self._sel: Optional[str] = None
        self._last_finished = 0.0
        self._did_login = False
        self.last_timings: Dict[str, float] = {}
        self._warned_dom = False
        self.lifecycle_state = "CREATED"
        self.lifecycle_state_since = time.time()
        self.lifecycle_reason = ""
        self._lifecycle_lock = threading.RLock()

    def _transition(self, state: str, reason: str = "") -> None:
        if state not in BROWSER_STATES:
            raise ValueError(f"unknown browser lifecycle state: {state}")
        allowed = {
            "CREATED": {"STARTING", "CLOSED"},
            "STARTING": {"LOGIN_REQUIRED", "READY", "RECOVERING", "FAILED", "CLOSED"},
            "LOGIN_REQUIRED": {"STARTING", "READY", "RECOVERING", "FAILED", "CLOSED"},
            "READY": {"BUSY", "WAITING_RESPONSE", "RECOVERING", "FAILED", "CLOSED"},
            "BUSY": {"WAITING_RESPONSE", "READY", "RECOVERING", "FAILED", "CLOSED"},
            "WAITING_RESPONSE": {"READY", "BUSY", "RECOVERING", "FAILED", "CLOSED"},
            "RECOVERING": {"STARTING", "READY", "FAILED", "CLOSED"},
            "FAILED": {"STARTING", "RECOVERING", "CLOSED"},
            "CLOSED": {"STARTING", "CLOSED"},
        }
        with self._lifecycle_lock:
            if state != self.lifecycle_state and state not in allowed.get(self.lifecycle_state, set()):
                raise RuntimeError(f"invalid browser lifecycle transition {self.lifecycle_state} -> {state}")
            self.lifecycle_state = state
            self.lifecycle_state_since = time.time()
            self.lifecycle_reason = str(reason or "")[:240]
        status_map = {"CREATED":"stopped","STARTING":"starting","LOGIN_REQUIRED":"login_needed",
                      "READY":"ready","BUSY":"busy","WAITING_RESPONSE":"busy",
                      "RECOVERING":"starting","FAILED":"error","CLOSED":"stopped"}
        try:
            if self.on_state: self.on_state(status_map[state])
        except Exception:
            pass

    @property
    def think_pref(self) -> bool:
        return bool(_state().THINK_MODE and self.recipe.get("supports_think"))

    # ---- launch -----------------------------------------------------------

    def _launch(self, headless: bool):
        args = ["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
        if sys.platform.startswith("linux"):
            args.append("--no-sandbox")
        if not headless and not sys.platform.startswith("linux") and self._minimize:
            args.append("--start-minimized")     # most Linux window managers mishandle it

        profile = self.profile_dir
        profile.mkdir(parents=True, exist_ok=True)
        kwargs = dict(user_data_dir=str(profile), headless=headless, args=args,
                      viewport={"width": 1280, "height": 900}, locale="en-US",
                      ignore_default_args=["--enable-automation"])
        if _state().BROWSER_CHANNEL:
            try:
                return self.pw.chromium.launch_persistent_context(channel=_state().BROWSER_CHANNEL, **kwargs)
            except Exception as exc:
                log(f"[browser] channel '{_state().BROWSER_CHANNEL}' failed ({exc}); using bundled chromium", C.yellow)
        return self.pw.chromium.launch_persistent_context(**kwargs)

    def _setup_page(self, page) -> None:
        try:
            page.set_default_timeout(30000)
            sess = self.ctx.new_cdp_session(page)
            ua = sess.send("Browser.getVersion").get("userAgent", "")
            if "Headless" in ua:
                sess.send("Emulation.setUserAgentOverride", {"userAgent": ua.replace("HeadlessChrome", "Chrome")})
        except Exception:
            pass

    def _close(self) -> None:
        try:
            if self.ctx:
                self.ctx.close()
        except Exception:
            pass
        self.ctx = None
        self.scratch = None

    def _has_token(self, page) -> bool:
        if self.provider == "deepseek_web":
            try:
                tok = page.evaluate("localStorage.getItem('userToken')")
                if not tok or tok in ("null", "undefined", "{}", ""):
                    return False
                try:
                    obj = json.loads(tok)
                    if isinstance(obj, dict):
                        return bool(obj.get("value") or obj.get("token"))
                except Exception:
                    pass
                return True
            except Exception:
                return False
        try:
            if not self._find_textarea(page):
                return False
            return bool(self._find_textarea(page))
        except Exception:
            return False

    def _find_textarea(self, page) -> Optional[str]:
        if self._sel:
            try:
                if page.evaluate("(s) => !!document.querySelector(s)", self._sel):
                    return self._sel
            except Exception:
                pass
            self._sel = None
        if self.provider != "deepseek_web":
            try:
                sel = page.evaluate(JS_GENERIC_COMPOSER)
            except Exception:
                sel = None
            if sel:
                self._sel = sel
            return sel
        try:
            sel = page.evaluate(JS_FIND_SELECTOR, TEXTAREA_SELECTORS)
        except Exception:
            sel = None
        if sel:
            self._sel = sel
        return sel

    def _wait_textarea(self, page, timeout: float) -> Optional[str]:
        end = time.time() + timeout
        while time.time() < end:
            sel = self._find_textarea(page)
            if sel:
                return sel
            time.sleep(0.2)
        return None

    def _logged_in(self, page) -> bool:
        if self.provider == "deepseek_web":
            return self._has_token(page) and self._find_textarea(page) is not None
        try:
            sel = self._find_textarea(page)
            if not sel:
                return False
            host = (urllib.parse.urlsplit(str(page.url or "")).hostname or "").lower()
            expected = str(self.recipe.get("url") or "").split("//", 1)[-1].split("/", 1)[0].lower()
            if expected and host and not (host == expected or host.endswith("." + expected)):
                return False
            body = str(page.locator("body").inner_text(timeout=1500) if page.locator("body").count() else "")[:10000]
            if re.search(r"\b(sign\s*in|log\s*in|create\s+account|ثبت\s*نام|ورود)\b", body, re.I):
                return False
            return True
        except Exception:
            return False

    def _goto_chat(self, page) -> None:
        url = CHAT_URL if self.provider == "deepseek_web" else str(self.recipe.get("url") or self.recipe.get("login_url"))
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            log(f"[browser] navigation warning: {exc}", C.yellow)
        self._wait_textarea(page, 8)

    def _boot(self, headless: bool, login_wait: int, announce: bool = False) -> bool:
        try:
            if self.lifecycle_state not in ("STARTING", "RECOVERING"):
                self._transition("STARTING", "browser boot")
            self.ctx = self._launch(headless)
            self.ctx.add_init_script(HOOK_JS)
            pages = list(self.ctx.pages)
            # Never hijack an arbitrary restored Chrome page. Prefer DeepSeek itself,
            # then a blank/new-tab page, otherwise create a dedicated control page.
            page = next((p for p in pages if CHAT_URL.rstrip("/") in (p.url or "")), None)
            if page is None:
                page = next((p for p in pages if (p.url or "") in ("", "about:blank", "chrome://newtab/", "chrome://new-tab-page/")), None)
            if page is None:
                page = self.ctx.new_page()
            self._setup_page(page)
            self._goto_chat(page)
            if self.provider != "deepseek_web" and not self._logged_in(page):
                login_url = str(self.recipe.get("login_url") or "")
                if login_url and login_url != str(self.recipe.get("url") or ""):
                    try:
                        page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
                    except Exception as exc:
                        log(f"[login:{self.name or self._provider_name()}] navigation warning: {exc}", C.yellow)
            self.scratch = page
            self.headless = headless
            if self._logged_in(page):
                self._transition("READY", "session already authenticated")
                return True
            if announce:
                self._transition("LOGIN_REQUIRED", "provider login required")
                log(f"[login:{self.name or 'account'}] Please log in to {self._provider_name()} in the opened Chrome window "
                    f"(waiting up to {login_wait // 60} minutes)...", C.bold)
            end = time.time() + login_wait
            last_report = 0.0
            while time.time() < end and not self.abort:
                try:
                    if self._logged_in(page):
                        self._did_login = self._did_login or announce
                        if announce:
                            self._transition("READY", "login detected; session saved")
                            log("[login] detected; session saved in the persistent profile.", C.green)
                            time.sleep(1.5)
                        return True
                except Exception:
                    pass
                if announce and time.time() - last_report > 15:
                    last_report = time.time()
                    log(f"  ...still waiting ({int(login_wait - (end - time.time()))}s)", C.dim)
                time.sleep(1.0)
            try: self._transition("FAILED", "login timeout")
            except Exception: pass
            return False
        except Exception as exc:
            try: self._transition("FAILED", str(exc))
            except Exception: pass
            log(f"[startup] launch failed ({'headless' if headless else 'headed'}): {exc}", C.yellow)
            return False

    def _state(self, s: str) -> None:
        if self.on_state:
            try:
                self.on_state(s)
            except Exception:
                pass

    def start(self, known_login: bool = True) -> bool:
        from playwright.sync_api import sync_playwright  # lazy: self-test needs no browser
        self._transition("STARTING", "start requested")
        self.pw = sync_playwright().start()
        self._minimize = bool(known_login and not self.headed_pref)
        # Never hide an account that may still need interactive authentication.
        # The persisted logged_in flag is only a hint; force_login and a missing
        # session must always use a visible browser until authentication succeeds.
        allow_headless = _state().HEADLESS_MODE != "0" and not self.headed_pref and bool(known_login)
        tag = self.name or "account"
        ok = False
        if allow_headless and known_login:
            log(f"[startup:{tag}] trying real headless...", C.dim)
            ok = self._boot(True, _state().HEADLESS_READY_TIMEOUT)
            if ok:
                log(f"[startup:{tag}] headless session ready.", C.green)
        if not ok and not self.abort:
            self._close()
            log(f"[startup:{tag}] opening a visible browser window...", C.dim)
            ok = self._boot(False, _state().LOGIN_WAIT_SECONDS, announce=True)
            if ok and allow_headless and (self._did_login or not known_login):
                log(f"[startup:{tag}] login saved; trying headless again...", C.dim)
                self._close()
                self._minimize = True
                if self._boot(True, _state().HEADLESS_READY_TIMEOUT):
                    log(f"[startup:{tag}] headless session ready.", C.green)
                else:
                    self._close()
                    ok = self._boot(False, _state().LOGIN_WAIT_SECONDS)
                    log(f"[startup:{tag}] headless is not accepted by the site; keeping a visible window.", C.yellow)
            elif ok:
                log(f"[startup:{tag}] session ready (visible window).", C.green)
        return bool(ok) and not self.abort

    def stop(self) -> None:
        self._close()
        try:
            if self.pw:
                self.pw.stop()
        except Exception:
            pass
        self.pw = None
        try: self._transition("CLOSED", "stopped")
        except Exception: self.lifecycle_state = "CLOSED"

    def restart(self) -> None:
        log("[browser] restarting browser session...", C.yellow)
        try: self._transition("RECOVERING", "browser restart")
        except Exception: pass
        self._close()
        self.epoch += 1
        if not self._boot(self.headless, _state().HEADLESS_READY_TIMEOUT):
            self._close()
            if not self._boot(False, _state().LOGIN_WAIT_SECONDS):
                raise BridgeError("browser could not be restarted / login lost", "login")

    def ensure_alive(self) -> None:
        try:
            _ = self.ctx.pages
            if self.scratch is None or self.scratch.is_closed():
                self.scratch = self.ctx.new_page()
                self._setup_page(self.scratch)
                self._goto_chat(self.scratch)
        except Exception:
            self.restart()

    # ---- pages ------------------------------------------------------------

    def new_page(self):
        self.ensure_alive()
        page = self.ctx.new_page()
        self._setup_page(page)
        return page

    def open_chat(self, page) -> None:
        self._goto_chat(page)
        if not self._has_token(page):
            pnm = self.recipe.get("name", self.provider)
            raise BridgeError(f"{pnm} login is not active. Click Login for this account on the dashboard.", "login")
        if not self._find_textarea(page):
            raise BridgeError("chat input box not found (provider layout changed or blocked)", "upstream")
        if self.recipe.get("supports_think"):
            found = self._set_native_think(page, self.think_pref)
            if self.think_pref and not found:
                log(f"[think:{self.name or self._provider_name()}] native thinking control not found; keeping provider default", C.yellow)

    def open_session(self, page, sid: Optional[str]) -> bool:
        if not sid:
            return False
        if self.provider == "deepseek_web":
            url = CHAT_URL.rstrip("/") + "/a/chat/s/" + sid
        else:
            url = sid if re.match(r"^https?://", sid) else str(self.recipe.get("url"))
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            log(f"[browser] navigation warning: {exc}", C.yellow)
        if not self._wait_textarea(page, 12) or not self._has_token(page):
            return False
        if self.provider != "deepseek_web":
            return True
        end = time.time() + 6
        while time.time() < end:
            if self.session_of(page) == sid:
                return True
            time.sleep(0.3)
        return False

    @staticmethod
    def close_page(page) -> None:
        try:
            page.close()
        except Exception:
            pass

    @staticmethod
    def session_of(page) -> Optional[str]:
        try:
            m = re.search(r"/s/([0-9a-fA-F-]{32,40})", page.url)
            if m:
                return m.group(1)
            u = str(page.url or "")
            return u if re.match(r"^https?://", u) else None
        except Exception:
            return None

    def delete_chat(self, sid: str) -> bool:
        if self.provider != "deepseek_web":
            return False
        try:
            page = self.scratch
            if page is None or page.is_closed():
                if self.ctx is None:
                    return False
                self.ensure_alive()                 # recreate the scratch tab first
                page = self.scratch
                if page is None or page.is_closed():
                    return False
            return page.evaluate(JS_DELETE_CHAT, sid) in (200, 204)
        except Exception:
            return False

    # ---- provider-neutral web controls ----------------------------------

    def _set_native_think(self, page, enabled: bool) -> bool:
        if not self.recipe.get("supports_think"):
            return False
        try:
            return bool(page.evaluate(JS_SET_NATIVE_THINK, {"enabled": bool(enabled), "provider": self.provider}))
        except Exception:
            return False

    def _provider_name(self) -> str:
        return str(self.recipe.get("name") or self.provider)

    # ---- exchange ---------------------------------------------------------

    def _seq(self, page) -> int:
        try:
            return int(page.evaluate("window.__dsb ? window.__dsb.seq : -1"))
        except Exception:
            return -1

    def _inject(self, page, sel: str, prompt: str) -> int:
        text = prompt.replace("\r\n", "\n").replace("\r", "\n")
        try:
            res = page.evaluate(JS_SET_TEXT, {"selector": sel, "text": text})
            if res and res.get("ok"):
                return len(text)
            why = f"len {res.get('len') if res else '?'} != {len(text)}"
        except Exception as exc:
            why = str(exc)
        log(f"[send] fast inject not exact ({why}); using fill()", C.yellow)
        try:  # fill REPLACES the content, so nothing is duplicated
            page.locator(sel).first.fill(text, timeout=60000)
            return len(text)
        except Exception as exc:
            raise BridgeError(f"could not put the prompt into the input box: {exc}", "upstream")

    def _attach(self, page, files: List[str], cancel) -> None:
        """Upload files through the page's own <input type=file> and wait until DeepSeek has taken them."""
        t0 = time.time()
        try:
            page.evaluate("() => { const b = window.__dsb; if (b && b.up) b.up.err = null; }")
        except Exception:
            pass
        n0 = int((page.evaluate(JS_UP_STATE) or {}).get("n", 0))
        names = ", ".join(os.path.basename(f) for f in files)
        log(f"[files:{self.name or 'account'}] uploading {len(files)} file(s): {names}", C.dim)
        try:
            loc = page.locator("input[type=file]")
            if loc.count() == 0:
                page.evaluate(JS_OPEN_ATTACH)
                page.wait_for_selector("input[type=file]", state="attached", timeout=4000)
            loc.first.set_input_files(files, timeout=60000)
        except Exception as exc:
            raise BridgeError(f"could not attach the file(s): {str(exc)[:160]}", "upstream")
        quiet_since, last = 0.0, (-1, -1)
        while True:
            if (cancel is not None and cancel.is_set()) or self.abort:
                raise BridgeCancelled()
            el = time.time() - t0
            if el > _state().UPLOAD_TIMEOUT:
                raise BridgeError("file upload timed out", "timeout")
            st = page.evaluate(JS_UP_STATE) or {}
            if st.get("err"):
                raise BridgeError("file upload failed: " + str(st["err"])[:160], "upstream")
            cur = (int(st.get("n", 0)), int(st.get("open", 0)))
            if cur != last:
                last, quiet_since = cur, time.time()
            if not st.get("seen") and el > 20:
                log("[files] could not observe the upload (site changed?); continuing anyway", C.yellow)
                return
            if cur[0] - n0 >= 1 and cur[1] == 0 and not st.get("parsing") and time.time() - quiet_since > 2.5:
                log(f"[files] uploaded in {time.time() - t0:.1f}s", C.dim)
                return
            time.sleep(0.25)

    def _inject_generic(self, page, sel: str, prompt: str) -> int:
        """Insert web prompts without a clipboard/paste event.

        ChatGPT currently turns pastes above 10k characters into attachments. The bridge must
        therefore use a DOM/input path that produces an ordinary text-input event instead of
        a ClipboardEvent. Playwright ``fill()`` is the safe fallback for both textarea and
        contenteditable composers and never uses the clipboard.
        """
        text = prompt.replace("\r\n", "\n").replace("\r", "\n")
        try:
            r = page.evaluate(JS_SET_GENERIC_TEXT, {"selector": sel, "text": text}) or {}
            if r.get("ok") and int(r.get("len") or 0) == len(text):
                return len(text)
        except Exception as exc:
            log(f"[send:{self.name or self._provider_name()}] direct input setter failed: {exc}", C.dim)
        try:
            loc = page.locator(sel).first
            loc.fill(text, timeout=60000)
            return len(text)
        except Exception as exc:
            raise BridgeError(f"could not put the prompt into {self._provider_name()} without paste/upload conversion: {exc}", "upstream")

    def _attach_generic(self, page, files: List[str]) -> None:
        try:
            loc = page.locator("input[type=file]")
            if loc.count() == 0:
                for p in (page.locator("button"), page.locator('[role="button"]')):
                    try:
                        n = p.count()
                    except Exception:
                        n = 0
                    for i in range(min(n, 80)):
                        try:
                            b = p.nth(i); txt = (b.inner_text() or "") + " " + (b.get_attribute("aria-label") or "")
                            if re.search(r"attach|upload|file|ضمیمه|آپلود", txt, re.I):
                                b.click(timeout=1500); break
                        except Exception:
                            continue
                page.wait_for_selector("input[type=file]", state="attached", timeout=5000)
                loc = page.locator("input[type=file]")
            loc.first.set_input_files(files, timeout=60000)
        except Exception as exc:
            raise BridgeError(f"could not attach file(s) to {self._provider_name()}: {str(exc)[:160]}", "upstream")

    def _generic_submit(self, page, sel: str, cancel, timeout: float, before_count: int) -> None:
        page.keyboard.press("Enter")
        start=time.time(); clicked=False
        while time.time()-start < timeout:
            if cancel is not None and cancel.is_set():
                raise BridgeCancelled()
            try:
                st=page.evaluate(JS_GENERIC_SNAPSHOT) or {}
                if st.get("generating") or st.get("count",0)>before_count:
                    return
            except Exception:
                pass
            if time.time()-start > 2 and not clicked:
                clicked=True
                try:
                    page.evaluate(JS_GENERIC_SEND, sel)
                except Exception:
                    pass
            time.sleep(0.2)
        raise BridgeError(f"{self._provider_name()} did not accept the message", "upstream")

    def _collect_generic(self, page, cancel, on_partial, before_count: int) -> str:
        end=time.time()+_state().MAX_REPLY_SECONDS; started=False; last=""; stable=0; seen_count=before_count
        while time.time() < end:
            if cancel is not None and cancel.is_set():
                raise BridgeCancelled()
            if self.abort:
                raise BridgeCancelled()
            try:
                st=page.evaluate(JS_GENERIC_SNAPSHOT) or {}
            except Exception as exc:
                raise BridgeError(f"browser snapshot failed: {exc}", "upstream")
            cur=str(st.get("latest") or "").strip(); cnt=int(st.get("count") or 0); generating=bool(st.get("generating"))
            if cnt>seen_count:
                seen_count=cnt; started=True
            if cur and cur!=last:
                last,stable=cur,0; started=True
                if on_partial:
                    try:on_partial(cur)
                    except Exception:pass
            elif cur:
                stable += 1
            if started and not generating and last and stable >= 8:
                return last
            time.sleep(_state().POLL_SECONDS if not last else min(0.35,max(_state().POLL_SECONDS,0.15)))
        raise BridgeError(f"timeout waiting for the {self._provider_name()} reply", "timeout")

    def _exchange_generic(self, page, prompt: str, cancel=None, on_partial=None, files: Optional[List[str]]=None) -> Exchange:
        if not self._has_token(page):
            raise BridgeError(f"{self._provider_name()} login is not active", "login")
        if self.recipe.get("supports_think"):
            found=self._set_native_think(page, self.think_pref)
            if self.think_pref and not found:
                log(f"[think:{self.name or self._provider_name()}] native thinking control not found; keeping provider default", C.yellow)
        sel=self._wait_textarea(page, 10)
        if not sel:
            raise BridgeError(f"{self._provider_name()} chat input box not found", "upstream")
        if files:
            self._attach_generic(page, files)
        t0=time.perf_counter()
        before_count=0
        try: before_count=int((page.evaluate(JS_GENERIC_SNAPSHOT) or {}).get("count") or 0)
        except Exception: before_count=0
        self._inject_generic(page, sel, prompt)
        self._generic_submit(page, sel, cancel, _state().SUBMIT_TIMEOUT + (_state().UPLOAD_TIMEOUT if files else 0), before_count)
        reply=self._collect_generic(page, cancel, on_partial, before_count)
        sid=self.session_of(page)
        total=time.perf_counter()-t0
        if not reply.strip(): raise BridgeError(f"{self._provider_name()} returned an empty reply", "empty")
        notice = site_notice_kind(reply)
        if notice:
            raise BridgeError(f"{self._provider_name()} notice: {reply.strip()[:160]}", notice)
        if self.on_exchange:
            try:self.on_exchange(len(prompt),len(reply),total)
            except Exception:pass
        return Exchange(text=reply, session_id=sid, seconds=total)

    def _submit(self, page, sel: str, seq0: int, cancel, timeout: Optional[float] = None) -> None:
        timeout = timeout or _state().SUBMIT_TIMEOUT
        long_wait = timeout > _state().SUBMIT_TIMEOUT        # files: the send button stays disabled while they are parsed
        page.keyboard.press("Enter")
        t0 = time.time()
        pressed, clicked = 1, False
        while time.time() - t0 < timeout:
            if cancel is not None and cancel.is_set():
                raise BridgeCancelled()
            if self.abort:
                raise BridgeCancelled()
            if self._seq(page) > seq0:
                return
            el = time.time() - t0
            try:
                remaining = page.evaluate(JS_TA_LEN, sel)
            except Exception:
                remaining = -1
            if remaining == 0 and el < timeout - 3:
                time.sleep(0.15)                    # the box already emptied: the site is submitting
                continue
            if el > 4 and (pressed < 2 or (long_wait and el > 4 + 5 * (pressed - 1))):
                page.keyboard.press("Enter")
                pressed += 1
            elif el > 9 and not clicked:
                clicked = True
                try:
                    page.evaluate(JS_CLICK_SEND, sel)
                except Exception:
                    pass
            time.sleep(0.15)
        raise BridgeError("the site did not accept the message (send button disabled or blocked)", "upstream")

    def _stop_generation(self, page) -> None:
        try:
            page.evaluate(JS_CLICK_SEND, self._sel or "textarea")  # send button turns into "stop"
        except Exception:
            pass

    def _run_wait(self, page, seq_after: int, cancel, on_partial, prefix: str, need_start: float) -> Dict[str, Any]:
        t_start = time.time()
        last_progress = time.time()
        last_len, last_tlen = -1, -1
        text = ""
        while True:
            if cancel is not None and cancel.is_set():
                self._stop_generation(page)
                raise BridgeCancelled()
            if self.abort:
                raise BridgeCancelled()
            if page.is_closed():
                raise BridgeError("the browser tab was closed", "upstream")
            try:
                st = page.evaluate(JS_STATE, last_len)
            except Exception as exc:
                raise BridgeError(f"browser error: {exc}", "upstream")
            if not st or not st.get("hook"):
                raise BridgeError("response hook lost (page reloaded?)", "upstream")
            now = time.time()
            if st.get("id", 0) > seq_after:
                if st.get("text") is not None:
                    text = st["text"]
                    last_len = st["len"]
                    last_progress = now
                    if on_partial:
                        try:
                            on_partial(prefix + text)
                        except Exception:
                            pass
                if st.get("tlen") != last_tlen:
                    last_tlen = st.get("tlen")
                    last_progress = now
                if st.get("error"):
                    err = str(st["error"])
                    kind = classify_error(err)
                    raise BridgeError("DeepSeek: " + err, kind)
                if st.get("done"):
                    return {"text": text, "incomplete": bool(st.get("incomplete")), "seq": st["id"],
                            "sessionId": st.get("sessionId"), "status": st.get("status")}
            elif now - t_start > need_start:
                raise NotStarted("no generation started", "upstream")
            if now - last_progress > _state().STALL_TIMEOUT:
                self._stop_generation(page)
                raise BridgeError(f"DeepSeek stalled for {_state().STALL_TIMEOUT}s", "timeout")
            if now - t_start > _state().MAX_REPLY_SECONDS:
                self._stop_generation(page)
                raise BridgeError("reply exceeded the maximum duration", "timeout")
            # While the model is silent (thinking) every poll is a wasted CDP round-trip.
            time.sleep(_state().POLL_SECONDS if now - last_progress < 3 else max(_state().POLL_SECONDS, 0.3))

    def _collect_dom(self, page, before: int, cancel, on_partial) -> str:
        """Fallback when the network hook is unavailable."""
        end = time.time() + _state().MAX_REPLY_SECONDS
        last, stable, started = "", 0, False
        while time.time() < end:
            if cancel is not None and cancel.is_set():
                self._stop_generation(page)
                raise BridgeCancelled()
            snap = page.evaluate(JS_DOM_SNAPSHOT)
            cur = snap.get("latest", "") or ""
            if snap.get("count", 0) > before:
                started = True
            if cur != last:
                last, stable = cur, 0
                if on_partial and started:
                    on_partial(cur)
            elif cur:
                stable += 1
            if started and last and stable >= 25:
                return last
            time.sleep(_state().POLL_SECONDS)
        raise BridgeError("timeout waiting for the reply (DOM mode)", "timeout")

    def exchange(self, page, prompt: str, cancel=None, on_partial=None, files: Optional[List[str]] = None) -> Exchange:
        if len(prompt) > _state().MAX_PROMPT_CHARS + 20_000:
            raise BridgeError(f"prompt too large ({len(prompt):,} chars)", "bad_request")
        self.ensure_alive()
        self._transition("BUSY", "request accepted")
        if self.provider != "deepseek_web":
            try:
                self._transition("WAITING_RESPONSE", "waiting for provider response")
                result = self._exchange_generic(page, prompt, cancel, on_partial, files)
                self._transition("READY", "request complete")
                return result
            except BridgeCancelled:
                self._transition("READY", "request cancelled")
                raise
            except Exception as exc:
                try: self._transition("RECOVERING", str(exc))
                except Exception: pass
                raise
        if page.is_closed():
            raise BridgeError("the browser tab was closed", "upstream")
        if not self._has_token(page):
            raise BridgeError("DeepSeek login expired. Click Login for this account on the dashboard (or restart the bridge).", "login")
        gap = _state().REQUEST_GAP_SECONDS - (time.time() - self._last_finished)
        if gap > 0:
            time.sleep(gap)
        t0 = time.perf_counter()
        sel = self._wait_textarea(page, 8)
        if not sel:
            raise BridgeError("chat input box not found", "upstream")
        if self.recipe.get("supports_think"):
            _found_think = self._set_native_think(page, self.think_pref)
            if self.think_pref and not _found_think:
                log(f"[think:{self.name or 'DeepSeek'}] native thinking control not found; using provider default", C.yellow)
        dump_debug("prompt", prompt)
        if files:
            self._attach(page, files, cancel)
        seq0 = self._seq(page)
        hook = seq0 >= 0
        if not hook and not self._warned_dom:
            self._warned_dom = True
            log("[hook] network hook unavailable; using the DOM fallback (expect lower fidelity)", C.yellow)
        before = 0
        if not hook:
            try:
                before = int(page.evaluate(JS_DOM_SNAPSHOT).get("count", 0))
            except Exception:
                before = 0
        t_inj = time.perf_counter()
        n = self._inject(page, sel, prompt)
        inj = time.perf_counter() - t_inj
        if hook:
            self._transition("WAITING_RESPONSE", "provider generation active")
            self._submit(page, sel, seq0, cancel, _state().UPLOAD_TIMEOUT if files else None)
        else:
            page.keyboard.press("Enter")
        log(f"[send] {n:,} chars injected in {inj:.2f}s ({'hook' if hook else 'DOM fallback'})", C.dim)

        session_id: Optional[str] = None
        if hook:
            acc, seq_after = "", seq0
            for i in range(_state().MAX_CONTINUES + 1):
                try:
                    r = self._run_wait(page, seq_after, cancel, on_partial, acc,
                                       need_start=_state().SUBMIT_TIMEOUT if i == 0 else 15)
                except NotStarted:
                    if i == 0:
                        raise BridgeError("the message was sent but no reply started", "upstream")
                    break
                acc += r["text"]
                session_id = r["sessionId"] or session_id
                seq_after = r["seq"]
                if not (r["incomplete"] and acc.strip()) or i == _state().MAX_CONTINUES:
                    break
                log(f"[reply] stream ended as '{r.get('status')}'; pressing Continue ({i + 1})", C.yellow)
                try:
                    if not page.evaluate(JS_CLICK_CONTINUE):
                        break
                except Exception:
                    break
            text = acc
        else:
            text = self._collect_dom(page, before, cancel, on_partial)
        self._last_finished = time.time()
        session_id = session_id or self.session_of(page)
        total = time.perf_counter() - t0
        dump_debug("reply", text)
        if self.on_exchange:
            try:
                self.on_exchange(len(prompt), len(text), total)
            except Exception:
                pass
        notice = site_notice_kind(text)
        if notice:
            raise BridgeError("DeepSeek notice: " + text.strip()[:160], notice)
        self.last_timings = {"prompt_chars": float(len(prompt)), "inject_s": inj,
                             "total_s": total, "reply_chars": float(len(text))}
        log(f"[reply] {len(text):,} chars in {total:.2f}s", C.green)
        self._transition("READY", "request complete")
        return Exchange(text=text, session_id=session_id, seconds=total)


# ---- V6.1: files / images sent to DeepSeek ------------------------------------

_MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/gif": ".gif",
             "image/webp": ".webp", "application/pdf": ".pdf", "text/plain": ".txt", "text/markdown": ".md",
             "text/csv": ".csv", "application/json": ".json", "application/msword": ".doc",
             "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
             "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx"}


def extract_attachments(messages: List[Dict[str, Any]], start: int, limit: Optional[int] = None
                        ) -> List[Tuple[str, str, str, str]]:
    """(kind, title, mime, base64) of the images / documents in user messages[start:]; the newest `limit`."""
    found: List[Tuple[str, str, str, str]] = []

    def walk(blocks: List[Any]) -> None:
        for b in blocks:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t in ("image", "document"):
                src = b.get("source")
                if isinstance(src, dict) and src.get("type") == "base64" and isinstance(src.get("data"), str) \
                        and src["data"]:
                    found.append((t, str(b.get("title") or b.get("name") or ""),
                                  str(src.get("media_type") or ""), src["data"]))
            elif t == "tool_result" and isinstance(b.get("content"), list):
                walk(b["content"])

    for m in messages[max(0, start):]:
        c = m.get("content")
        if m.get("role") == "user" and isinstance(c, list):
            walk(c)
    return found[-(limit or _state().ATTACH_MAX_FILES):]


def write_attachments(found: List[Tuple[str, str, str, str]], directory: str) -> List[str]:
    paths: List[str] = []
    used: set = set()
    for i, (kind, title, mime, data) in enumerate(found, 1):
        try:
            raw = base64.b64decode(data)
        except Exception:
            continue
        if not raw or len(raw) > _state().ATTACH_MAX_BYTES:
            log(f"[files] skipped a file ({len(raw):,} bytes): empty or larger than the limit", C.yellow)
            continue
        ext = _MIME_EXT.get(mime.lower(), ".png" if kind == "image" else ".bin")
        base = re.sub(r"[^\w.\- ]", "_", os.path.basename(title)) if title else f"{kind}-{i}"
        if not os.path.splitext(base)[1]:
            base += ext
        stem, suffix = os.path.splitext(base)
        name, k = base, 1
        while name.lower() in used:
            k += 1
            name = f"{stem}-{k}{suffix}"
        used.add(name.lower())
        p = os.path.join(directory, name)
        with open(p, "wb") as f:
            f.write(raw)
        paths.append(p)
    return paths


def cleanup_dir(d: Optional[str]) -> None:
    if d:
        shutil.rmtree(d, ignore_errors=True)


def _data_url_block(url: Any, name: str = "") -> Optional[Dict[str, Any]]:
    m = re.match(r"^data:([^;,]+)?(;base64)?,(.*)$", str(url or ""), re.S)
    if not m or not m.group(2):
        return None
    mime = (m.group(1) or "application/octet-stream").lower()
    if mime.startswith("image/"):
        return {"type": "image", "source": {"type": "base64", "media_type": mime, "data": m.group(3)}}
    return {"type": "document", "title": name or "file",
            "source": {"type": "base64", "media_type": mime, "data": m.group(3)}}


JS_UP_STATE = "() => { const b = window.__dsb; return b && b.up ? b.up : null; }"
JS_OPEN_ATTACH = r"""
() => {
  const ta = document.querySelector('textarea');
  let root = ta && ta.parentElement;
  for (let i = 0; i < 6 && root; i++, root = root.parentElement) {
    const el = root.querySelector('[class*="upload" i],[aria-label*="attach" i],[aria-label*="upload" i],[title*="attach" i],[title*="upload" i]');
    if (el) { el.click(); return true; }
  }
  return false;
}
"""


# ============================================================================
# Conversation engine (runs inside the worker thread)
# ============================================================================

@dataclass
class Conversation:
    cid: str
    page: Any                      # None while hibernated (tab closed, DeepSeek chat kept)
    epoch: int
    sigs: List[str] = field(default_factory=list)
    n: int = 0
    reply_ids: List[str] = field(default_factory=list)
    tools_sig: str = ""
    chars_sent: int = 0
    session_id: Optional[str] = None
    turns: int = 0
    created: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    poisoned: bool = False        # tab state no longer mirrors the client's history


class Engine:
    def __init__(self, ds: DeepSeekWeb, acct: Any = None, pool: Any = None):
        self.ds = ds
        self.acct = acct
        self.pool = pool
        self.convs: List[Conversation] = []
        self.epoch = ds.epoch
        self.created_sessions: set = set()
        self.pending_delete: List[str] = []
        # Generic web providers (ChatGPT/Grok/etc.) deliberately keep one sticky
        # conversation per Engine/account. The website itself owns the conversation
        # history; the bridge sends only the delta after the first turn.
        self.sticky_conv: Optional[Conversation] = None
        # Generic web providers (ChatGPT/Grok) keep one browser conversation per logical lane
        # instead of one chat per request. Main Claude Code traffic uses the project lane; Swarm
        # agents use their stable tag lane. DeepSeek keeps its existing signature-based matcher.
        self.generic_lanes: Dict[str, Conversation] = {}
        self.generic_side_page = None
        self.generic_side_ready = False
        self.term_page = None
        self.term_ready = False
        self._lane_locks: Dict[str, threading.RLock] = {}

    # ---- housekeeping -----------------------------------------------------

    def _sync_epoch(self) -> None:
        if self.ds.epoch != self.epoch:
            self.convs.clear()
            self.sticky_conv = None
            self.generic_lanes.clear()
            self.generic_side_page, self.generic_side_ready = None, False
            self.term_page, self.term_ready = None, False
            self.epoch = self.ds.epoch

    def _schedule_delete(self, sid: Optional[str], force: bool = False) -> None:
        if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
            return
        if sid and (_state().DELETE_OLD_CHATS or force) and sid in self.created_sessions:
            self.pending_delete.append(sid)

    def idle(self) -> None:
        while self.pending_delete:
            sid = self.pending_delete.pop()
            if self.ds.delete_chat(sid):
                self.created_sessions.discard(sid)

    def _drop(self, conv: Optional[Conversation]) -> None:
        if conv is None:
            return
        if conv in self.convs:
            self.convs.remove(conv)
        if conv is self.sticky_conv:
            self.sticky_conv = None
        for key, mapped in list(self.generic_lanes.items()):
            if mapped is conv:
                self.generic_lanes.pop(key, None)
        sid = conv.session_id or (self.ds.session_of(conv.page) if conv.page is not None else None)
        if conv.page is not None:
            # Keep the single generic-provider tab alive; a normal request failure
            # must not cause the next request to spawn another browser tab.
            if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
                try:
                    if self.ds.scratch is conv.page:
                        return
                except Exception:
                    pass
            self.ds.close_page(conv.page)
        self._schedule_delete(sid)

    def _hibernate(self, conv: Conversation) -> None:
        """Close the tab but remember the DeepSeek chat, so the conversation can be resumed later."""
        sid = conv.session_id or self.ds.session_of(conv.page)
        if not sid or conv.poisoned:
            self._drop(conv)
            return
        conv.session_id = sid
        self.ds.close_page(conv.page)
        conv.page = None
        hib = [c for c in self.convs if c.page is None]
        while len(hib) > _state().MAX_KEPT_CONVS:
            oldest = min(hib, key=lambda c: c.last_used)
            hib.remove(oldest)
            self._drop(oldest)

    def _make_room(self, exclude: Optional[Conversation] = None) -> None:
        while True:
            live = [c for c in self.convs if c.page is not None and c is not exclude]
            if len(live) < _state().MAX_TABS:
                return
            oldest = min(live, key=lambda c: c.last_used)
            log(f"[conv] tab limit reached; hibernating conversation {oldest.cid} (chat is kept)", C.dim)
            self._hibernate(oldest)

    def _wake(self, conv: Conversation) -> bool:
        """Re-open a hibernated conversation's DeepSeek chat in a new tab."""
        self._make_room(exclude=conv)
        page = None
        try:
            page = self.ds.new_page()
            if not self.ds.open_session(page, conv.session_id):
                raise BridgeError("could not re-open the saved chat", "upstream")
            conv.page = page
            log(f"[conv {conv.cid}] woke hibernated conversation (session {conv.session_id})", C.cyan)
            return True
        except Exception as exc:
            log(f"[conv {conv.cid}] could not resume the saved chat ({exc}); starting a fresh one", C.yellow)
            if page is not None:
                self.ds.close_page(page)
            return False

    def _generic_lane_key(self, req: Optional[NormReq]) -> str:
        """Stable conversation lane for ChatGPT/Grok without relying on Claude metadata ids."""
        if req is not None:
            tag = str(getattr(req, "tag", None) or "").strip()
            # Only stable, explicitly agent-like tags form separate lanes. Request/session
            # identifiers can change on every turn and must never create a fresh chat.
            if tag and re.match(r"^(?:(?:sw|swarm)\d*[._:-]|(?:agent|team)[._:-])[A-Za-z0-9._:-]{1,120}$", tag, re.I):
                return "tag:" + tag[:160]
            cwd = claude_cwd(req)
            if cwd:
                try:
                    return "project:" + str(Path(cwd).resolve()).casefold()
                except Exception:
                    return "project:" + str(cwd).casefold()
        return "main"

    def _new_conv(self, req: Optional[NormReq] = None) -> Conversation:
        # ChatGPT/Grok and other generic web providers: one persistent chat per logical lane.
        # A normal request never opens a new tab. Only a genuinely different project/agent lane
        # gets another tab, and the normal account's main lane reuses the bootstrapped scratch tab.
        if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
            key = self._generic_lane_key(req)
            existing = self.generic_lanes.get(key)
            if existing is not None:
                if existing.page is None:
                    if self._wake(existing):
                        return existing
                    self._drop(existing)
                elif not existing.page.is_closed():
                    return existing
            self._make_room()
            page = None
            if key == "main" and self.sticky_conv is None:
                self.ds.ensure_alive()
                page = self.ds.scratch
            if page is None or page.is_closed():
                page = self.ds.new_page()
                try:
                    self.ds.open_chat(page)
                except Exception:
                    self.ds.close_page(page)
                    raise
            conv = Conversation(cid=uuid.uuid4().hex[:6], page=page, epoch=self.epoch)
            self.convs.append(conv)
            self.generic_lanes[key] = conv
            if key == "main":
                self.sticky_conv = conv
            return conv
        self._make_room()
        page = self.ds.new_page()
        try:
            self.ds.open_chat(page)
        except Exception:
            self.ds.close_page(page)
            raise
        conv = Conversation(cid=uuid.uuid4().hex[:6], page=page, epoch=self.epoch)
        self.convs.append(conv)
        return conv

    def _find_conv(self, req: NormReq) -> Optional[Conversation]:
        if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
            key = self._generic_lane_key(req)
            c = self.generic_lanes.get(key)
            if c is not None:
                try:
                    if c.epoch == self.epoch and not c.poisoned:
                        self.sticky_conv = c if key == "main" else self.sticky_conv
                        if c.page is None or not c.page.is_closed():
                            return c
                        if c.session_id:
                            return c
                except Exception:
                    pass
            return None
        best: Optional[Conversation] = None
        for c in self.convs:
            try:
                if c.epoch != self.epoch:
                    continue
                if c.page is not None and c.page.is_closed():
                    continue
            except Exception:
                continue
            if match_continuation(c.sigs, c.n, c.reply_ids, req.messages, req.sigs):
                if best is None or c.n > best.n or (c.n == best.n and c.last_used > best.last_used):
                    best = c
        return best

    def describe(self) -> List[str]:
        out = []
        for c in self.convs:
            out.append(f"{c.cid}  msgs={c.n} turns={c.turns} sent={c.chars_sent:,}ch "
                       f"idle={int(time.time() - c.last_used)}s session={c.session_id}"
                       f"{'  [hibernated]' if c.page is None else ''}")
        return out

    def _fresh_generic_chat(self, conv: Optional[Conversation] = None, reason: str = "") -> bool:
        """Start a fresh ChatGPT/Grok chat in the SAME browser tab."""
        if getattr(self.ds, "provider", "deepseek_web") == "deepseek_web":
            return False
        c = conv or self.sticky_conv
        page = c.page if c is not None else self.ds.scratch
        if page is None or page.is_closed():
            self.ds.ensure_alive()
            page = self.ds.scratch
        if page is None:
            return False
        clicked = False
        try:
            clicked = bool(page.evaluate(JS_GENERIC_NEW_CHAT))
        except Exception as exc:
            log(f"[chat:{self.ds._provider_name()}] new-chat control probe failed: {exc}", C.dim)
        if not clicked:
            try:
                page.goto(str(self.ds.recipe.get("url") or "about:blank"), wait_until="domcontentloaded", timeout=30000)
                clicked = True
            except Exception as exc:
                log(f"[chat:{self.ds._provider_name()}] could not reset the current tab: {exc}", C.yellow)
        try:
            self.ds._wait_textarea(page, 10)
        except Exception:
            pass
        if c is None:
            return clicked
        c.page = page
        c.sigs, c.n, c.reply_ids, c.tools_sig = [], 0, [], ""
        c.chars_sent, c.session_id, c.turns, c.poisoned = 0, None, 0, False
        c.last_used = time.time()
        if c not in self.convs:
            self.convs.append(c)
        self.sticky_conv = c
        if reason:
            log(f"[chat:{self.ds._provider_name()}] fresh conversation in same tab ({reason})", C.yellow)
        return clicked

    def reset_all(self) -> int:
        n = len(self.convs)
        if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
            # Reset every generic lane in place. No browser tab is created merely by resetting.
            ok = 0
            for c in list(self.convs):
                if self._fresh_generic_chat(c, reason="explicit reset"):
                    ok += 1
            return n if ok == len(self.convs) else ok
        for c in list(self.convs):
            self._drop(c)
        return n

    def purge_all(self) -> int:
        self.reset_all()
        done = 0
        for sid in list(self.created_sessions):
            if self.ds.delete_chat(sid):
                self.created_sessions.discard(sid)
                done += 1
        return done

    # ---- parse / validate / repair ---------------------------------------

    @staticmethod
    def _tool_choice_problems(req: NormReq, calls: List[Dict[str, Any]], problems: List[str]) -> None:
        """Enforce tool_choice: 'any' needs a call, {'type':'tool'} needs THAT tool."""
        if not req.tools or problems:
            return
        tc = req.tool_choice or {}
        if req.force_tool and not calls:
            problems.append("a tool call is required in this reply")
        elif tc.get("type") == "tool" and tc.get("name") in req.tools \
                and not any(c.get("name") == tc["name"] for c in calls):
            problems.append(f"the tool '{tc['name']}' must be called in this reply")

    def _finalize(self, req: NormReq, page, raw: str, cancel,
                  conv: Optional[Conversation] = None) -> Tuple[str, List[Dict[str, Any]], int]:
        extra_chars = 0
        if not req.tools:
            return sanitize_reply(raw).strip(), [], 0
        clean, calls, problems = parse_tool_calls(raw, req.tools)
        self._tool_choice_problems(req, calls, problems)
        repairs = 0
        while problems and repairs < _state().MAX_REPAIRS:
            repairs += 1
            log(f"[repair {repairs}] {problems[0][:150]}", C.yellow)
            rp = build_repair_prompt(problems, [c["name"] for c in calls])
            try:
                ex = self.ds.exchange(page, rp, cancel, None)
            except BridgeCancelled:
                if conv is not None:
                    conv.poisoned = True     # a half-finished repair turn is sitting in the tab
                raise
            except BridgeError as exc:
                log(f"[repair] failed: {exc}", C.yellow)
                if conv is not None:
                    conv.poisoned = True
                break
            extra_chars += len(rp) + len(ex.text)
            c2, calls2, problems2 = parse_tool_calls(ex.text, req.tools)
            if calls2 and not problems2:
                clean = clean if clean else c2
                calls, problems = merge_repaired(calls, calls2), []
                break
            if calls2:
                calls, problems = merge_repaired(calls, calls2), problems2
        if problems and not calls and not clean:
            clean = "[bridge] The model produced an invalid tool call: " + "; ".join(problems[:3])
        elif problems:
            log(f"[parse] dropped invalid call(s): {problems[:2]}", C.yellow)
        return clean, calls, extra_chars

    # ---- V6 helpers (data only: the router may call owns() from another thread) --------

    def owns(self, req: NormReq) -> int:
        """>= 0 when one of this account's chats is the continuation of `req` (its message count)."""
        best = -1
        if self.ds.epoch != self.epoch:
            return best
        if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
            key = self._generic_lane_key(req)
            c = self.generic_lanes.get(key)
            if c is not None:
                try:
                    if c.epoch == self.epoch and not c.poisoned:
                        # The web page owns the authoritative conversation history.
                        # Claude Code metadata may change between requests, so do not require
                        # strict message/tool-id matching for ChatGPT/Grok routing.
                        return max(0, c.n)
                except Exception:
                    pass
        for c in list(self.convs):
            try:
                if c.epoch == self.epoch and match_continuation(c.sigs, c.n, c.reply_ids, req.messages, req.sigs):
                    best = max(best, c.n)
            except Exception:
                pass
        return best

    def _note_err(self, kind: str, msg: str = "") -> None:
        if self.acct is not None:
            self.acct.stats.note_err(kind, msg)

    def _note_ok(self) -> None:
        if self.acct is not None:
            self.acct.stats.note_ok()

    def _alt_available(self) -> bool:
        try:
            return bool(self.pool is not None and self.acct is not None and self.pool.has_alternative(self.acct))
        except Exception:
            return False

    def ping(self) -> Dict[str, Any]:
        """Health test without polluting a ChatGPT/Grok conversation with a synthetic message."""
        self._sync_epoch()
        self.ds.ensure_alive()
        if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
            page = self.ds.scratch
            if page is None or page.is_closed() or not self.ds._logged_in(page):
                raise BridgeError(f"{self.ds._provider_name()} login is not active", "login")
            return {"seconds": 0.0, "reply": "READY"}
        page = self.ds.scratch
        self.ds.open_chat(page)
        t0 = time.time()
        ex = self.ds.exchange(page, "Reply with exactly one word: OK")
        if ex.session_id:
            self.created_sessions.add(ex.session_id)
            self._schedule_delete(ex.session_id, force=True)
        return {"seconds": round(time.time() - t0, 2), "reply": sanitize_reply(ex.text).strip()[:80]}

    # ---- main entry ---------------------------------------------------------

    def _lane_lock_key(self, req: NormReq) -> str:
        project = claude_cwd(req) if not getattr(req, "side", False) else ""
        tag = getattr(req, "tag", "") or "main"
        provider = getattr(self.ds, "provider", "deepseek_web")
        account = getattr(self.acct, "id", "") or getattr(self.ds, "name", "account")
        kind = "side" if getattr(req, "side", False) else "main"
        return f"{project}|{provider}|{account}|{tag}|{kind}"

    def process(self, req: NormReq, cancel, on_partial) -> Outcome:
        key = self._lane_lock_key(req)
        lock = self._lane_locks.setdefault(key, threading.RLock())
        with lock:
            return self._process_impl(req, cancel, on_partial)

    def _process_impl(self, req: NormReq, cancel, on_partial) -> Outcome:
        self._sync_epoch()
        lane_key = self._lane_lock_key(req)
        log("request start", C.dim, provider=getattr(self.ds, "provider", ""),
            account=getattr(self.acct, "id", "") or getattr(self.ds, "name", ""),
            lane=lane_key, project=claude_cwd(req), request_id=getattr(req, "id", ""), event="request.start")
        if req.side:
            return self._process_side(req, cancel, on_partial)
        conv = self._find_conv(req)
        budget = _state().HISTORY_BUDGET_CHARS
        attempt = 0
        while True:
            if conv is not None and conv.page is None and not self._wake(conv):
                self._drop(conv)
                conv = None
            cont = conv is not None
            if cont:
                delta = req.messages[conv.n + 1:]
                prompt = build_delta_prompt(req, delta, tools_changed=(req.tools_sig != conv.tools_sig))
                if conv.chars_sent + len(prompt) > _state().ROTATE_CHARS:
                    log(f"[conv {conv.cid}] chat is getting long; rotating to a fresh chat", C.yellow)
                    if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
                        if not self._fresh_generic_chat(conv, reason="size cap"):
                            raise BridgeError(f"{self.ds._provider_name()} could not start a fresh chat in the existing tab", "upstream")
                        cont = False
                    else:
                        self._drop(conv)
                        conv, cont = None, False
            if not cont:
                conv = self._new_conv(req)
                prompt = build_full_prompt(req, budget)
            log(f"[conv {conv.cid}] {'CONTINUE +' + str(len(req.messages) - conv.n - 1) + ' msg' if cont else 'NEW chat, ' + str(len(req.messages)) + ' msg'}"
                f" -> prompt {len(prompt):,} chars", C.cyan)
            found = extract_attachments(req.messages, (conv.n + 1) if cont else max(0, len(req.messages) - 8))
            fdir = tempfile.mkdtemp(prefix="dsb_up_") if found else None
            try:
                files = write_attachments(found, fdir) if fdir else []
                ex = self.ds.exchange(conv.page, prompt, cancel, on_partial if attempt == 0 else None,
                                      files=files or None)
                if not ex.text.strip():
                    raise BridgeError("DeepSeek returned an empty reply", "empty")
                break
            except BridgeCancelled:
                if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
                    self._fresh_generic_chat(conv, reason="cancelled request")
                else:
                    self._drop(conv)
                raise
            except BridgeError as exc:
                log(f"[conv {conv.cid}] {exc.kind}: {exc}", C.red)
                if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
                    if not self._fresh_generic_chat(conv, reason=exc.kind):
                        raise
                else:
                    self._drop(conv)
                conv = None
                attempt += 1
                self._note_err(exc.kind, str(exc))
                if exc.kind in ("login", "bad_request") or attempt > _state().MAX_RETRIES:
                    raise
                if self._alt_available() and (exc.kind == "rate_limit" or attempt >= 2):
                    log("[failover] handing the request to another account", C.yellow)
                    raise
                if not cont and attempt <= 2:
                    budget = max(40_000, budget // 2)
                wait = 0.0 if exc.kind == "chat_full" else (min(_state().RETRY_BACKOFF_MAX, 2 ** attempt * 2) if attempt > 1 else 0.5)
                log(f"[retry {attempt}/{_state().MAX_RETRIES}] waiting {wait:.0f}s before trying again", C.yellow)
                t_end = time.time() + wait
                while time.time() < t_end:
                    if cancel is not None and cancel.is_set():
                        raise BridgeCancelled()
                    time.sleep(0.5)
            finally:
                cleanup_dir(fdir)
        if ex.session_id:
            conv.session_id = ex.session_id
            if getattr(self.ds, "provider", "deepseek_web") == "deepseek_web":
                self.created_sessions.add(ex.session_id)
        try:
            clean, calls, extra = self._finalize(req, conv.page, ex.text, cancel, conv)
        except Exception:                        # incl. BridgeCancelled: the tab is in an unknown state
            self._drop(conv)
            raise
        for c in calls:
            c["id"] = make_id(req.id_prefix)
        if conv.poisoned:
            log(f"[conv {conv.cid}] repair round-trip failed; this chat will not be reused", C.yellow)
            self._drop(conv)
        else:
            conv.sigs = list(req.sigs)
            conv.n = len(req.messages)
            conv.reply_ids = [c["id"] for c in calls]
            conv.tools_sig = req.tools_sig
            conv.chars_sent += len(prompt) + len(ex.text) + extra
            conv.turns += 1
            conv.last_used = time.time()
        if not clean and not calls:
            raise BridgeError("the reply contained nothing usable", "empty")
        self._note_ok()
        return Outcome(text=clean, calls=calls, stop_reason="tool_use" if calls else "end_turn")

    def _process_side(self, req: NormReq, cancel, on_partial) -> Outcome:
        self.ds.ensure_alive()
        if getattr(self.ds, "provider", "deepseek_web") != "deepseek_web":
            # ChatGPT/Grok side work (titles, lightweight summaries) must never navigate the
            # account's main sticky chat back to the home URL. Reuse one dedicated side tab instead.
            if self.generic_side_page is None or self.generic_side_page.is_closed():
                self.generic_side_page = self.ds.new_page()
                self.generic_side_ready = False
            page = self.generic_side_page
            if not self.generic_side_ready:
                self.ds.open_chat(page)
                self.generic_side_ready = True
            lane_note = "dedicated side chat"
        else:
            page = self.ds.scratch
            self.ds.open_chat(page)
            lane_note = "scratch chat"
        prompt = build_full_prompt(req, _state().HISTORY_BUDGET_CHARS)
        log(f"[side] {lane_note}, prompt {len(prompt):,} chars", C.cyan)
        ex = self.ds.exchange(page, prompt, cancel, on_partial)
        if ex.session_id:
            if getattr(self.ds, "provider", "deepseek_web") == "deepseek_web":
                self.created_sessions.add(ex.session_id)
                self._schedule_delete(ex.session_id, force=True)   # title-generation etc.: throwaway
        clean, calls, _ = self._finalize(req, page, ex.text, cancel)
        for c in calls:
            c["id"] = make_id(req.id_prefix)
        if not clean and not calls:
            raise BridgeError("empty reply", "empty")
        return Outcome(text=clean, calls=calls, stop_reason="tool_use" if calls else "end_turn")

    # ---- interactive terminal chat -----------------------------------------

    def terminal(self, text: str) -> str:
        self._sync_epoch()
        if self.term_page is None or self.term_page.is_closed():
            self.term_page = self.ds.new_page()
            self.term_ready = False
        if not self.term_ready:
            self.ds.open_chat(self.term_page)
            self.term_ready = True
        ex = self.ds.exchange(self.term_page, text)
        if ex.session_id and getattr(self.ds, "provider", "deepseek_web") == "deepseek_web":
            self.created_sessions.add(ex.session_id)
        return sanitize_reply(ex.text)

    def terminal_reset(self) -> None:
        if self.term_page is not None:
            self._schedule_delete(self.ds.session_of(self.term_page))
        self.term_ready = False


# ============================================================================
# Worker thread
# ============================================================================

@dataclass
class Job:
    fn: Callable[[Engine], Any]
    future: concurrent.futures.Future
    cancel: Optional[threading.Event]


class Bridge:
    """One browser session = one DeepSeek account, driven by its own thread."""

    def __init__(self, acct: Any = None, pool: Any = None, force_login: bool = False,
                 autostart: bool = True) -> None:
        self._q: "queue.PriorityQueue" = queue.PriorityQueue()
        self._seq = itertools.count()
        self._ready = threading.Event()
        self.ok = False
        self.stopping = False
        self.acct, self.pool, self.force_login = acct, pool, force_login
        self.ds: Optional[DeepSeekWeb] = None
        self.engine: Optional[Engine] = None
        self._thread = state_thread(target=self._run, daemon=True,
                                        name=f"DeepSeekWorker-{getattr(acct, 'id', 'main')}")
        if autostart:
            self._thread.start()

    def wait_ready(self, timeout: Optional[float] = None) -> bool:
        return self._ready.wait(timeout)

    def alive(self) -> bool:
        return self.ok and self._thread.is_alive()

    def _status(self, status: str, err: str = "") -> None:
        if self.acct is not None and not self.stopping:
            self.acct.set_status(status, err)
            state = {"starting":"STARTING","login":"LOGIN_REQUIRED","login_needed":"LOGIN_REQUIRED",
                     "ready":"READY","busy":"BUSY","error":"FAILED","stopped":"CLOSED"}.get(status)
            if state:
                try: self.acct.set_browser_state(state, err)
                except Exception: pass

    def _run(self) -> None:
        a = self.acct
        try:
            if a is not None:
                self.ds = DeepSeekWeb(a.profile, a.name, a.headed, on_state=self._status,
                                      on_exchange=a.stats.record_exchange, provider=a.provider)
                known = a.logged_in and not self.force_login
            else:
                self.ds, known = DeepSeekWeb(), True
            self._status("starting")
            self.ok = self.ds.start(known_login=known)
            if self.ok:
                self.engine = Engine(self.ds, a, self.pool)
                if a is not None:
                    a.mark_logged_in()
                self._status("ready")
            else:
                self._status("error", "login was not completed (or the browser could not start)")
        except Exception as exc:
            log(f"[worker] initialization error: {exc}", C.red)
            traceback.print_exc()
            self.ok = False
            self._status("error", str(exc)[:200])
        finally:
            self._ready.set()
        if self.ok:
            try:
                self._serve()
            except BaseException:
                traceback.print_exc()
            finally:
                self.ok = False              # submit() now refuses new work ...
                self._fail_pending()         # ... and nobody waits forever on queued work
                self._status("error", "worker stopped")
        try:
            if self.ds:
                self.ds.stop()
        except Exception:
            traceback.print_exc()

    def _serve(self) -> None:
        while True:
            try:
                _, _, job = self._q.get(timeout=1.0)
            except queue.Empty:
                try:
                    self.engine.idle()
                except Exception:
                    pass
                continue
            if job is None:
                return
            if job.cancel is not None and job.cancel.is_set():
                job.future.set_exception(BridgeCancelled())
                continue
            if not job.future.set_running_or_notify_cancel():
                continue
            try:
                job.future.set_result(job.fn(self.engine))
            except BaseException as exc:     # nothing may leave a future unresolved
                if not isinstance(exc, (BridgeError, BridgeCancelled)):
                    traceback.print_exc()
                job.future.set_exception(
                    exc if isinstance(exc, Exception) else BridgeError(f"worker aborted: {exc!r}", "upstream"))

    def _fail_pending(self) -> None:
        while True:
            try:
                _, _, job = self._q.get_nowait()
            except queue.Empty:
                return
            if job is not None:
                try:
                    job.future.set_exception(BridgeError("bridge worker stopped", "upstream"))
                except Exception:
                    pass

    def submit(self, fn: Callable[[Engine], Any], priority: int = PRIORITY_MAIN,
               cancel: Optional[threading.Event] = None) -> concurrent.futures.Future:
        fut: concurrent.futures.Future = concurrent.futures.Future()
        if not self.ok:
            fut.set_exception(BridgeError("bridge is not ready", "upstream"))
            return fut
        self._q.put((priority, next(self._seq), Job(fn, fut, cancel)))
        if not self.ok:                 # the worker died between the check and the put:
            self._fail_pending()        # nobody else will ever drain this job
        return fut

    def stop(self) -> None:
        self.stopping = True
        if self.ds is not None:
            self.ds.abort = True        # interrupts a login wait / a running generation
        self._q.put((-1, next(self._seq), None))
        if self._thread.is_alive():
            self._thread.join(timeout=25)


# ============================================================================
# API accounts (V6.2): Grok / Claude / OpenAI / OpenRouter / any compatible endpoint
# ============================================================================

TIER_NAMES = {1: "Basic", 2: "Fast", 3: "Standard", 4: "Strong", 5: "Top"}
API_TIMEOUT = _env_int("DS_BRIDGE_API_TIMEOUT", 900)

# Suggested models only: "Fetch models" in the panel asks the provider for the real, current list.
WEB_RECIPES: Dict[str, Dict[str, Any]] = {
    # Selectors are intentionally semantic/learnable rather than brittle site-specific CSS.
    "deepseek_web": {"id": "deepseek_web", "name": "DeepSeek", "url": "https://chat.deepseek.com/",
                     "login_url": "https://chat.deepseek.com/", "icon": "DS", "tier": 3, "supports_think": True},
    "chatgpt_web": {"id": "chatgpt_web", "name": "ChatGPT", "url": "https://chatgpt.com/",
                    "login_url": "https://chatgpt.com/auth/login", "icon": "G", "tier": 4, "supports_think": True},
    "grok_web": {"id": "grok_web", "name": "Grok", "url": "https://grok.com/",
                 "login_url": "https://accounts.x.ai/sign-in?redirect=grok-com", "icon": "X", "tier": 4, "supports_think": False},
}

PROVIDERS: List[Dict[str, Any]] = [
    {"id": "deepseek_web", "kind": "web", "name": "DeepSeek", "sub": "website login (free)", "icon": "DS", "tier": 3,
     "base": "", "models": [], "link": "https://chat.deepseek.com"},
    {"id": "chatgpt_web", "kind": "web", "name": "ChatGPT", "sub": "website login (your account)", "icon": "G", "tier": 4,
     "base": "", "models": [], "link": "https://chatgpt.com/auth/login", "experimental": True},
    {"id": "grok_web", "kind": "web", "name": "Grok", "sub": "website login (your account)", "icon": "X", "tier": 4,
     "base": "", "models": [], "link": "https://accounts.x.ai/sign-in?redirect=grok-com", "experimental": True},
    {"id": "grok", "kind": "openai", "name": "Grok", "sub": "xAI API key", "icon": "X", "tier": 4,
     "base": "https://api.x.ai/v1", "models": ["grok-4", "grok-3", "grok-3-mini"], "link": "https://console.x.ai"},
    {"id": "claude", "kind": "anthropic", "name": "Claude", "sub": "Anthropic API key", "icon": "A", "tier": 5,
     "base": "https://api.anthropic.com", "models": ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-3-5-haiku-latest"],
     "link": "https://console.anthropic.com"},
    {"id": "openai", "kind": "openai", "name": "OpenAI", "sub": "API key", "icon": "G", "tier": 4,
     "base": "https://api.openai.com/v1", "models": ["gpt-4.1", "gpt-4o", "gpt-4o-mini"], "link": "https://platform.openai.com"},
    {"id": "openrouter", "kind": "openai", "name": "OpenRouter", "sub": "one key, hundreds of models", "icon": "↗", "tier": 4,
     "base": "https://openrouter.ai/api/v1", "models": [], "link": "https://openrouter.ai/keys"},
    {"id": "deepseek_api", "kind": "openai", "name": "DeepSeek API", "sub": "paid API key", "icon": "DS", "tier": 3,
     "base": "https://api.deepseek.com/v1", "models": ["deepseek-chat", "deepseek-reasoner"], "link": "https://platform.deepseek.com"},
    {"id": "custom_openai", "kind": "openai", "name": "Custom", "sub": "any OpenAI-compatible endpoint", "icon": "⚙️", "tier": 3,
     "base": "", "models": [], "link": ""},
    {"id": "custom_anthropic", "kind": "anthropic", "name": "Custom", "sub": "any Anthropic-compatible endpoint", "icon": "🧩", "tier": 4,
     "base": "", "models": [], "link": ""},
]
_PROVIDER = {p["id"]: p for p in PROVIDERS}


def guess_tier(model: str, default: int = 3) -> int:
    """1..5 'power' guess from a model name. The panel lets the person override it."""
    m = (model or "").lower()
    if not m:
        return default
    if any(k in m for k in ("mini", "haiku", "flash", "lite", "nano", "small", "instant", "-fast")):
        return 2
    if any(k in m for k in ("opus", "gpt-5", "o3", "o4", "grok-4", "gemini-2.5-pro", "gemini-3", "ultra")):
        return 5
    if any(k in m for k in ("sonnet", "gpt-4.1", "gpt-4o", "gpt-4-turbo", "grok-3", "reasoner", "r1", "gemini", "70b", "405b")):
        return 4
    return default


def api_base(base: str) -> str:
    b = (base or "").strip().rstrip("/")
    return b if re.search(r"/v\d+$", b) else b + "/v1"


def _opener_for(url: str):
    host = urllib.parse.urlsplit(url).hostname or ""
    if host in ("127.0.0.1", "localhost", "::1"):
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))      # never via a system proxy
    return urllib.request.build_opener()


def http_json(method: str, url: str, headers: Dict[str, str], body: Optional[Dict[str, Any]], timeout: float,
              cancel: Optional[threading.Event] = None, abort: Optional[threading.Event] = None) -> Dict[str, Any]:
    """One HTTP request in a helper thread so a cancelled client never has to wait for the provider."""
    result: Dict[str, Any] = {}
    done = threading.Event()

    def run() -> None:
        try:
            rq = urllib.request.Request(url, data=json.dumps(body).encode("utf-8") if body is not None else None,
                                        method=method, headers=headers)
            with _opener_for(url).open(rq, timeout=timeout) as r:
                result.update(status=r.status, data=r.read(), headers=dict(r.headers))
        except urllib.error.HTTPError as exc:
            result.update(status=exc.code, data=exc.read() or b"", headers=dict(exc.headers or {}))
        except Exception as exc:
            result["exc"] = exc
        finally:
            done.set()
    state_thread(target=run, daemon=True, name="api-http").start()
    while not done.wait(0.3):
        if (cancel is not None and cancel.is_set()) or (abort is not None and abort.is_set()):
            raise BridgeCancelled()
    if "exc" in result:
        raise BridgeError(f"network error: {result['exc']}", "upstream")
    return result


def _api_error(status: int, data: bytes) -> BridgeError:
    msg = ""
    try:
        j = json.loads(data.decode("utf-8", "replace"))
        e = j.get("error", j) if isinstance(j, dict) else j
        msg = str(e.get("message") if isinstance(e, dict) else e)
    except Exception:
        msg = data.decode("utf-8", "replace")
    msg = f"HTTP {status}: {msg.strip()[:300]}"
    if status in (401, 402, 403):
        return BridgeError("API key / credit problem - " + msg, "login")
    if status in (429, 502, 503, 504, 529):
        return BridgeError(msg, "rate_limit")
    if status >= 500 or status in (408, 409, 425):
        return BridgeError(msg, "upstream")
    return BridgeError(msg, "bad_request")


def _text_of(c: Any) -> str:
    return content_to_text(c) if not isinstance(c, str) else c


def anthropic_to_openai(raw: Dict[str, Any], model: str, max_tokens: int, token_field: str) -> Dict[str, Any]:
    msgs: List[Dict[str, Any]] = []
    sysx = content_to_text(raw.get("system")) if raw.get("system") else ""
    if sysx:
        msgs.append({"role": "system", "content": sysx})
    for m in raw.get("messages") or []:
        role, c = m.get("role"), m.get("content")
        if isinstance(c, str):
            msgs.append({"role": role, "content": c})
            continue
        if not isinstance(c, list):
            continue
        if role == "assistant":
            text = "".join(str(b.get("text", "")) for b in c if isinstance(b, dict) and b.get("type") == "text")
            calls = [{"id": b.get("id"), "type": "function",
                      "function": {"name": b.get("name"), "arguments": compact_json(b.get("input") or {})}}
                     for b in c if isinstance(b, dict) and b.get("type") == "tool_use"]
            am: Dict[str, Any] = {"role": "assistant", "content": text or None}
            if calls:
                am["tool_calls"] = calls
            if text or calls:
                msgs.append(am)
            continue
        parts: List[Dict[str, Any]] = []
        for b in c:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "tool_result":                         # tool messages must follow the assistant tool_calls
                body = _text_of(b.get("content")) or ""
                msgs.append({"role": "tool", "tool_call_id": b.get("tool_use_id"),
                             "content": ("Error: " + body) if b.get("is_error") else body})
            elif t == "text":
                parts.append({"type": "text", "text": str(b.get("text", ""))})
            elif t == "image" and isinstance(b.get("source"), dict) and b["source"].get("type") == "base64":
                s = b["source"]
                parts.append({"type": "image_url", "image_url": {"url": f"data:{s.get('media_type', 'image/png')};base64,{s.get('data', '')}"}})
            elif t == "document":
                parts.append({"type": "text", "text": f"[file attached: {b.get('title') or 'document'}]"})
        if parts:
            only_text = all(p["type"] == "text" for p in parts)
            msgs.append({"role": "user", "content": "\n".join(p["text"] for p in parts) if only_text else parts})
    body: Dict[str, Any] = {"model": model, "messages": msgs, token_field: max_tokens}
    tools = [t for t in (raw.get("tools") or []) if isinstance(t, dict) and t.get("name")]
    tc = raw.get("tool_choice") if isinstance(raw.get("tool_choice"), dict) else {}
    if tools and tc.get("type") != "none":
        body["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t.get("description", ""),
                                                         "parameters": t.get("input_schema") or {"type": "object", "properties": {}}}}
                         for t in tools]
        if tc.get("type") == "any":
            body["tool_choice"] = "required"
        elif tc.get("type") == "tool" and tc.get("name"):
            body["tool_choice"] = {"type": "function", "function": {"name": tc["name"]}}
    return body


_ANTHROPIC_KEYS = ("model", "max_tokens", "messages", "system", "tools", "tool_choice", "temperature", "top_p",
                   "top_k", "stop_sequences")


def apply_think_mode(body: Dict[str, Any], account: Any) -> Dict[str, Any]:
    """Apply provider-native reasoning explicitly so the app-level toggle is deterministic."""
    provider=str(getattr(account,"provider","") or "")
    model=str(getattr(account,"model","") or "").strip()
    if provider == "deepseek_api":
        enabled = bool(_state().THINK_MODE)
        body["thinking"]={"type":"enabled" if enabled else "disabled"}
        # DeepSeek currently rejects `required` / named tool choices while thinking is enabled.
        # Preserve tool calling by relaxing only that incompatible selection to the provider-safe `auto`.
        if enabled and body.get("tools") and body.get("tool_choice") not in (None, "auto", "none"):
            body["tool_choice"]="auto"
    elif provider == "openai" and re.match(r"^(gpt-5(?:[.-].*)?|o[1-4](?:[.-].*)?)$", model, re.I):
        body["reasoning_effort"]="high" if _state().THINK_MODE else "low"
    return body


class ApiEngine:
    """Talks to a provider's HTTP API. Same interface the pool expects from the browser Engine."""

    def __init__(self, acct: Any, pool: Any) -> None:
        self.acct, self.pool = acct, pool
        self.convs: List[Any] = []
        self.abort = threading.Event()

    def owns(self, req: Any) -> int: return -1            # stateless: nothing to continue
    def idle(self) -> None: pass
    def describe(self) -> List[str]: return []
    def reset_all(self) -> int: return 0
    def purge_all(self) -> int: return 0

    def _alt(self) -> bool:
        try:
            return bool(self.pool is not None and self.pool.has_alternative(self.acct))
        except Exception:
            return False

    def ping(self) -> Dict[str, Any]:
        req = normalize_anthropic({"model": self.acct.model, "max_tokens": 16,
                                   "messages": [{"role": "user", "content": "Reply with exactly one word: OK"}]})
        t0 = time.time()
        out = self._once(req, None)
        return {"seconds": round(time.time() - t0, 2), "reply": out.text.strip()[:80]}

    def _once(self, req: Any, cancel: Optional[threading.Event]) -> Outcome:
        a = self.acct
        base = api_base(a.base_url)
        want = int(req.max_tokens or 8192)
        for shrink in (0, 1):
            mt = min(want, int(getattr(a, "max_out", 0) or want))
            if a.kind == "anthropic":
                body = {k: v for k, v in req.raw.items() if k in _ANTHROPIC_KEYS}
                body.update(model=a.model, max_tokens=mt)
                url = base + "/messages"
                headers = {"content-type": "application/json", "x-api-key": a.api_key, "anthropic-version": "2023-06-01"}
            else:
                field = "max_completion_tokens" if a.provider == "openai" else "max_tokens"
                body = anthropic_to_openai(req.raw, a.model, mt, field)
                body = apply_think_mode(body, a)
                url = base + "/chat/completions"
                headers = {"content-type": "application/json", "authorization": "Bearer " + a.api_key}
            t0 = time.time()
            r = http_json("POST", url, headers, body, API_TIMEOUT, cancel, self.abort)
            if r["status"] == 200:
                break
            exc = _api_error(r["status"], r["data"])
            nums = [int(x) for x in re.findall(r"\d{3,7}", str(exc)) if int(x) < mt]
            if shrink == 0 and exc.kind == "bad_request" and "max" in str(exc).lower() and nums:
                a.max_out = max(nums)                           # the provider told us its output limit: remember it
                continue
            raise exc
        try:
            j = json.loads(r["data"].decode("utf-8", "replace"))
        except Exception:
            raise BridgeError("the provider returned something that is not JSON", "upstream")
        secs = time.time() - t0
        text, calls, tin, tout, stop = "", [], 0, 0, "end_turn"
        if a.kind == "anthropic":
            for b in j.get("content") or []:
                if b.get("type") == "text":
                    text += str(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    calls.append({"id": b.get("id"), "name": b.get("name"), "arguments": b.get("input") or {}})
            u = j.get("usage") or {}
            tin = int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0)
            tout = int(u.get("output_tokens") or 0)
            stop = {"tool_use": "tool_use", "max_tokens": "max_tokens"}.get(j.get("stop_reason"), "end_turn")
        else:
            ch = ((j.get("choices") or [{}])[0]) or {}
            msg = ch.get("message") or {}
            text = msg.get("content") or ""
            if isinstance(text, list):
                text = "".join(str(p.get("text", "")) for p in text if isinstance(p, dict))
            for tc in msg.get("tool_calls") or []:
                fn = tc.get("function") or {}
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except Exception:
                    args = {}
                calls.append({"id": tc.get("id") or "call_" + uuid.uuid4().hex[:12], "name": fn.get("name"),
                              "arguments": args if isinstance(args, dict) else {}})
            u = j.get("usage") or {}
            tin, tout = int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
            stop = "tool_use" if calls else ("max_tokens" if ch.get("finish_reason") == "length" else "end_turn")
        if not text.strip() and not calls:
            raise BridgeError("the provider returned an empty reply", "empty")
        if not tin:
            tin = estimate_tokens([req.system_text, req.messages])
        if not tout:
            tout = estimate_tokens([text, calls])
        a.stats.record_tokens(tin, tout, secs)
        return Outcome(text=text, calls=calls, stop_reason="tool_use" if calls else stop, usage=(tin, tout))

    def process(self, req: Any, cancel: Optional[threading.Event], on_partial: Any) -> Outcome:
        a = self.acct
        attempt = 0
        while True:
            attempt += 1
            try:
                out = self._once(req, cancel)
                a.stats.note_ok()
                return out
            except BridgeCancelled:
                raise
            except BridgeError as exc:
                a.stats.note_err(exc.kind, str(exc))
                if exc.kind in ("login", "bad_request") or attempt > _state().MAX_RETRIES or self._alt():
                    raise
                end = time.time() + min(_state().RETRY_BACKOFF_MAX, 2 ** attempt)
                while time.time() < end:
                    if (cancel is not None and cancel.is_set()) or self.abort.is_set():
                        raise BridgeCancelled()
                    time.sleep(0.3)


class ApiWorker:
    """Worker for an API account: no browser, `max_parallel` requests at the same time."""

    def __init__(self, acct: Any, pool: Any, force_login: bool = False, autostart: bool = True) -> None:
        self.acct, self.pool = acct, pool
        self.ok = False
        self.stopping = False
        self.engine = ApiEngine(acct, pool)
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._ex = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, int(acct.max_parallel or 1)),
                                                         thread_name_prefix=f"api-{acct.id}")
        self._thread = state_thread(target=self._run, daemon=True, name=f"ApiWorker-{acct.id}")
        if autostart:
            self._thread.start()

    def _run(self) -> None:
        a = self.acct
        problem = ("API key is missing" if not a.api_key else "model is missing" if not a.model
                   else "base URL is invalid" if not re.match(r"^https?://", a.base_url or "") else "")
        if problem:
            a.set_status("login_needed" if "key" in problem else "error", problem)
        else:
            self.ok = True
            a.set_status("ready")
        self._ready.set()
        self._stop.wait()
        self.ok = False

    def wait_ready(self, timeout: Optional[float] = None) -> bool:
        return self._ready.wait(timeout)

    def alive(self) -> bool:
        return self.ok and self._thread.is_alive()

    def submit(self, fn: Callable[[Any], Any], priority: int = PRIORITY_MAIN,
               cancel: Optional[threading.Event] = None) -> concurrent.futures.Future:
        if not self.ok:
            f: concurrent.futures.Future = concurrent.futures.Future()
            f.set_exception(BridgeError("this API account is not ready", "upstream"))
            return f

        def call() -> Any:
            if cancel is not None and cancel.is_set():
                raise BridgeCancelled()
            return fn(self.engine)
        ctx = contextvars.copy_context()
        return self._ex.submit(lambda: ctx.run(call))

    def stop(self) -> None:
        self.stopping = True
        self.ok = False
        self.engine.abort.set()
        self._ex.shutdown(wait=False, cancel_futures=True)
        self._stop.set()



# ============================================================================
# Live activity feed: a read-only mirror of what Claude Code (or any client) is doing
# ============================================================================



def emit_dash_event(kind: str, payload: Dict[str, Any]) -> None:
    """Broadcast a bounded real-time dashboard event without adding polling load."""
    event = {"id": next(_state().DASH_EVENT_SEQ), "t": time.time(), "kind": str(kind), "data": payload}
    _state().CLAUDE_MIRROR.append(event)
    with _state().DASH_EVENT_LOCK:
        dead: List["queue.Queue[Dict[str, Any]]"] = []
        for q in list(_state().DASH_EVENT_SUBS):
            try:
                q.put_nowait(event)
            except queue.Full:
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    dead.append(q)
        for q in dead:
            if q in _state().DASH_EVENT_SUBS:
                _state().DASH_EVENT_SUBS.remove(q)


def add_dash_subscription(q: "queue.Queue[Dict[str, Any]]") -> None:
    with _state().DASH_EVENT_LOCK:
        _state().DASH_EVENT_SUBS.append(q)


def remove_dash_subscription(q: "queue.Queue[Dict[str, Any]]") -> None:
    with _state().DASH_EVENT_LOCK:
        if q in _state().DASH_EVENT_SUBS:
            _state().DASH_EVENT_SUBS.remove(q)


_PRIMARY_ARG = ("command", "file_path", "path", "pattern", "url", "query", "description", "prompt", "text")


def _brief_call(c: Dict[str, Any]) -> str:
    a = c.get("arguments") or {}
    v = ""
    for k in _PRIMARY_ARG:
        if isinstance(a.get(k), (str, int)):
            v = str(a[k])
            break
    if not v:
        v = next((str(x) for x in a.values() if isinstance(x, (str, int))), "")
    return f"{c.get('name')}: {' '.join(v.split())[:110]}"


def summarize_last(req: Any) -> str:
    """One line describing what the client just sent (its newest message / tool results)."""
    names: Dict[Any, str] = {}
    for m in req.messages:
        if m.get("role") == "assistant" and isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    names[b.get("id")] = str(b.get("name"))
    last = req.messages[-1] if req.messages else {}
    c = last.get("content")
    if isinstance(c, str):
        return " ".join(c.split())[:300]
    parts: List[str] = []
    for b in c if isinstance(c, list) else []:
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text":
            parts.append(" ".join(_REMINDER_RE.sub("", str(b.get("text", ""))).split()))
        elif t == "tool_result":
            body = " ".join(content_to_text(b.get("content")).split())[:120]
            parts.append(f"↩ {names.get(b.get('tool_use_id'), 'tool')}: {body}")
        elif t in ("image", "document"):
            parts.append(f"[{t}]")
    return " ".join(p for p in parts if p)[:300]


def record_activity(req: Any, outcome: Optional[Outcome], secs: float, in_tokens: int, err: str = "") -> None:
    try:
        tin, tout = (outcome.usage if outcome is not None and outcome.usage else
                     (in_tokens, estimate_tokens([outcome.text, outcome.calls]) if outcome is not None else 0))
        item = {
            "n": next(_state()._ACT_SEQ), "t": time.time(), "tag": req.tag or "", "role": req.role or "",
            "kind": "agent" if req.tag else ("side" if req.side else "main"), "model": req.model,
            "account": getattr(outcome, "account", "") if outcome is not None else "",
            "tier": getattr(outcome, "tier", 0) if outcome is not None else 0, "secs": round(secs, 1),
            "tin": int(tin), "tout": int(tout), "msgs": len(req.messages), "stream": req.stream,
            "user": summarize_last(req), "reply": (outcome.text[:1500] if outcome is not None else ""),
            "calls": [_brief_call(c) for c in (outcome.calls if outcome is not None else [])][:8], "err": err[:300]}
        _state().ACTIVITY.append(item)
        emit_dash_event("activity", item)
    except Exception:
        pass


def claude_cwd(req: Any) -> str:
    """The working directory Claude Code reports in its system prompt (used by /swarm)."""
    m = re.search(r"(?:Primary working directory|Working directory)\s*:\s*([^\r\n]+)", getattr(req, "system_text", "") or "")
    if m:
        p = m.group(1).strip().strip("`'\"")
        try:
            if Path(p).is_dir():
                return p
        except Exception:
            pass
    return ""


PANEL_PAGES = ("dash", "live", "chat", "swarm", "launch", "console", "connect", "settings")


def open_panel(pool: Any, page: str = "") -> str:
    base = f"http://127.0.0.1:{pool.cfg.get('port')}"
    open_dashboard(base, str(pool.cfg.get("api_key")), page if page in PANEL_PAGES else "")
    return f"{base}/dash"


# ============================================================================
# Swarm (V6.2): several agents develop DIFFERENT parts of a project in parallel
# Every agent is a normal Claude Code process running in its OWN git worktree + branch, so agents can never
# overwrite each other. Finished work is verified, optionally reviewed, merged one by one into an integration
# branch (conflicts are auto-resolved or reported) and applied to your branch only when you say so.
# ============================================================================

SW_ACTIVE = ("starting", "running", "verifying", "reviewing")
SW_BAD = ("failed", "conflict", "skipped", "stopped")
SW_DONE = ("merged", "done") + SW_BAD


def git(args: List[str], cwd: Any, check: bool = True, timeout: int = 180) -> "subprocess.CompletedProcess[str]":
    p = subprocess.run(["git", "-c", "user.name=DeepSeek Bridge Swarm", "-c", "user.email=swarm@localhost",
                        "-c", "core.autocrlf=false", *args], cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if check and p.returncode != 0:
        raise ValueError(f"git {' '.join(args[:2])} failed: {(p.stderr or p.stdout).strip()[:300]}")
    return p


def _glob_re(pat: str) -> Optional["re.Pattern[str]"]:
    pat = pat.strip().replace("\\", "/").lstrip("./")
    if not pat:
        return None
    if pat.endswith("/"):
        pat += "**"
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
            continue
        if pat.startswith("**", i):
            out, i = out + ".*", i + 2
            continue
        c = pat[i]
        out += "[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


def in_scope(path: str, patterns: List[str]) -> bool:
    if not patterns:
        return True
    path = path.replace("\\", "/")
    for p in patterns:
        r = _glob_re(p)
        bare = p.strip().replace("\\", "/").strip("/")
        if (r and r.match(path)) or (bare and not any(ch in bare for ch in "*?") and (path == bare or path.startswith(bare + "/"))):
            return True
    return False


def detect_verify(cwd: Any) -> str:
    p = Path(cwd)
    try:
        if (p / "package.json").exists():
            t = (json.loads((p / "package.json").read_text(encoding="utf-8")).get("scripts") or {}).get("test", "")
            if t and "no test specified" not in t:
                return "npm test --silent"
        if (p / "go.mod").exists():
            return "go test ./..."
        if (p / "Cargo.toml").exists():
            return "cargo test --quiet"
        import importlib.util
        if importlib.util.find_spec("pytest") and (any((p / n).exists() for n in ("pytest.ini", "tox.ini", "conftest.py", "tests"))
                                                   or list(p.glob("test_*.py"))):
            return f'"{sys.executable}" -m pytest -q -x'
    except Exception:
        pass
    return ""


def parse_plan(text: str, max_tasks: int = 12) -> Dict[str, Any]:
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.M)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("the planner did not return JSON")
    try:
        d = json.loads(t[i:j + 1])
    except Exception as exc:
        raise ValueError(f"the planner returned invalid JSON ({exc})")
    raw = [x for x in (d.get("tasks") or []) if isinstance(x, dict) and str(x.get("prompt", "")).strip()]
    if not raw:
        raise ValueError("the plan has no tasks")
    tasks, ids = [], {}
    for n, x in enumerate(raw[:max_tasks], 1):
        aid = re.sub(r"[^A-Za-z0-9_-]", "", str(x.get("id") or f"a{n}"))[:12] or f"a{n}"
        if aid in ids:
            aid = f"{aid}-{n}"
        ids[aid] = True
        tasks.append({"id": aid, "title": str(x.get("title") or f"Task {n}")[:80], "prompt": str(x["prompt"]).strip(),
                      "files": [str(f) for f in (x.get("files") or []) if isinstance(f, str)][:30],
                      "deps": [str(k) for k in (x.get("depends_on") or [])]})
    for tk in tasks:
        tk["deps"] = [k for k in tk["deps"] if k in ids and k != tk["id"]]
    return {"summary": str(d.get("summary") or "")[:300], "contracts": str(d.get("contracts") or "")[:4000], "tasks": tasks}


class SwarmAgent:
    def __init__(self, aid: str, title: str, prompt: str, files: List[str], deps: List[str], account_id: str = "") -> None:
        self.id, self.title, self.prompt, self.files, self.deps = aid, title, prompt, files, deps
        self.account_id = str(account_id or "")
        self.status = "queued"           # queued starting running verifying reviewing merging merged done failed conflict skipped stopped
        self.activity, self.note = "", ""
        self.log: "deque" = deque(maxlen=400)
        self.log_n = 0
        self.proc: Optional["subprocess.Popen[str]"] = None
        self.branch, self.worktree, self.base = "", "", ""
        self.changed: List[str] = []
        self.violations: List[str] = []
        self.attempts = 1
        self.started = self.finished = 0.0
        self.verify_ok: Optional[bool] = None
        self.verify_out = ""
        self.result = ""

    def add_log(self, line: str) -> None:
        self.log_n += 1
        self.log.append((self.log_n, line[:400]))


class SwarmRun:
    def __init__(self, rid: str, goal: str, project: Path, base: str, branch: str, opts: Dict[str, Any]) -> None:
        self.id, self.goal, self.project, self.base, self.base_branch = rid, goal, project, base, branch
        self.opts = opts
        self.status = "planning"         # planning running verifying done done_with_issues failed stopped
        self.agents: List[SwarmAgent] = []
        self.max_agents = int(opts.get("agents") or 1)
        self.dir = project / SWARM_DIR_NAME / rid
        self.merged_branch = f"swarm/{rid}/merged"
        self.merge_dir = self.dir / "_merge"
        self.created, self.finished = time.time(), 0.0
        self.summary_plan, self.contracts, self.summary = "", "", ""
        self.final_verify: Dict[str, Any] = {}
        self.events: "deque" = deque(maxlen=200)
        self.stop = threading.Event()
        self.merge_lock = threading.Lock()
        self.lock = threading.RLock()
        self.applied = self.cleaned = False
        self.review_on = False
        self.verify = str(opts.get("verify") or "auto")

    def ev(self, msg: str) -> None:
        item = {"t": time.time(), "msg": msg}
        self.events.append(item)
        emit_dash_event("swarm", {"run": self.id, "status": self.status, "project": str(self.project),
                                    "message": str(msg)[:500]})

    def get(self, aid: str) -> Optional[SwarmAgent]:
        return next((a for a in self.agents if a.id == aid), None)

    def view(self, full: bool = True) -> Dict[str, Any]:
        d = {"id": self.id, "goal": self.goal, "project": str(self.project), "status": self.status,
             "created": self.created, "finished": self.finished, "max_agents": self.max_agents,
             "attachments": list(self.opts.get("attachments") or []),
             "account_ids": list(self.opts.get("account_ids") or []),
             "verify": self.verify, "review": self.review_on, "mode": self.opts.get("mode"), "applied": self.applied,
             "cleaned": self.cleaned, "base_branch": self.base_branch, "merged_branch": self.merged_branch,
             "plan": self.summary_plan, "summary": self.summary, "final_verify": self.final_verify,
             "counts": {s: sum(1 for a in self.agents if a.status == s) for s in {a.status for a in self.agents}}}
        if full:
            d["contracts"] = self.contracts
            d["events"] = list(self.events)[::-1]
            d["agents"] = [{"id": a.id, "title": a.title, "status": a.status, "prompt": a.prompt, "files": a.files,
                            "deps": a.deps, "activity": a.activity, "note": a.note, "attempts": a.attempts,
                            "changed": a.changed, "violations": a.violations, "verify_ok": a.verify_ok,
                            "verify_out": a.verify_out[-1500:], "started": a.started, "finished": a.finished,
                            "tail": [x[1] for x in list(a.log)[-6:]]} for a in self.agents]
        return d


class Swarm:
    def __init__(self, pool: Any) -> None:
        self.pool = pool
        try:
            cleanup_swarm_attachments(7)
        except Exception as exc:
            _warn_once("swarm_attachment_cleanup", f"could not prune old swarm attachments: {exc}")
        self.runs: Dict[str, SwarmRun] = {}
        self.roles: Dict[str, str] = {}
        self.lock = threading.RLock()
        self._n = 0

    def role_of(self, tag: Optional[str]) -> Optional[str]:
        return self.roles.get(tag or "")

    def latest(self) -> Optional[SwarmRun]:
        return max(self.runs.values(), key=lambda r: r.created, default=None)

    # ---- start -------------------------------------------------------------------

    def start(self, goal: str, project: str, agents: Any = "auto", verify: str = "auto", review: str = "",
              mode: str = "", tasks_text: str = "", strict: bool = False, init_git: bool = True,
              attachments: Optional[List[str]] = None, account_ids: Optional[List[str]] = None) -> SwarmRun:
        goal = (goal or "").strip()
        if not goal and not tasks_text.strip():
            raise ValueError("describe what the team should build")
        if not shutil.which("git"):
            raise ValueError("git is not installed - the swarm needs it to keep the agents apart")
        if not shutil.which("claude"):
            raise ValueError("Claude Code is not installed (Launch page -> Install Claude Code)")
        proj = Path(project or self.pool.cfg.get("project_dir") or "").expanduser()
        if not proj.is_dir():
            raise ValueError(f"not a folder: {proj}")
        proj = proj.resolve()
        if git(["rev-parse", "--is-inside-work-tree"], proj, check=False).returncode != 0:
            if not init_git:
                raise ValueError("this folder is not a git repository")
            git(["init", "-q"], proj)
            self.pool.event("info", f"swarm: initialised a git repository in {proj}")
        if git(["rev-parse", "--verify", "-q", "HEAD"], proj, check=False).returncode != 0:
            git(["add", "-A"], proj, check=False)
            git(["commit", "-q", "--allow-empty", "-m", "Initial snapshot (DeepSeek Bridge swarm)"], proj)
        top = Path(git(["rev-parse", "--show-toplevel"], proj).stdout.strip())
        selected_accounts=[x for x in (account_ids or []) if self.pool.get(x) is not None and self.pool.get(x).enabled]
        if not selected_accounts:
            selected_accounts=self.pool.project_accounts_for(str(top))
        if not selected_accounts:
            selected_accounts=[a.id for a in self.pool.accounts if a.enabled]
        if not selected_accounts:
            raise ValueError("no enabled AI account is available for this swarm")
        base = git(["rev-parse", "HEAD"], proj).stdout.strip()
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], proj).stdout.strip()
        try:
            ex = top / ".git" / "info" / "exclude"
            ex.parent.mkdir(parents=True, exist_ok=True)
            if SWARM_DIR_NAME not in (ex.read_text(encoding="utf-8") if ex.exists() else ""):
                with open(ex, "a", encoding="utf-8") as f:
                    f.write(f"\n{SWARM_DIR_NAME}/\n")
        except Exception:
            pass
        with self.lock:
            self._n += 1
            rid = f"sw{self._n}-{secrets.token_hex(2)}"
        if str(agents) in ("auto", "", "0"):
            n = _state().SWARM_AGENTS if _state().SWARM_AGENTS > 0 else self.pool.parallel_capacity(selected_accounts, _state().PARALLEL_MODE)
        else:
            n = int(agents)
        n = max(1, min(_state().SWARM_MAX_AGENTS, n or 1))
        run = SwarmRun(rid, goal, top, base, branch, {"agents": n, "mode": mode or _norm_mode(self.pool.cfg.get("permission_mode")) or DEFAULT_MODE,
                                                       "strict": bool(strict), "tasks_text": tasks_text,
                                                       "attachments": list(attachments or [])[:_state().ATTACH_MAX_FILES],
                                                       "account_ids": list(dict.fromkeys(selected_accounts))})
        run.verify = verify or "auto"
        self.pool.set_project_accounts(str(top), list(dict.fromkeys(selected_accounts)))
        rv = (review or _state().SWARM_REVIEW).lower()
        run.review_on = rv == "on" or (rv == "auto" and len({a.tier for a in self.pool.accounts if a.usable()}) > 1)
        with self.lock:
            self.runs[rid] = run
        run.ev(f"started on {branch} @ {base[:8]} with up to {n} agent(s)")
        self.pool.event("ok", f"swarm {rid} started: {goal[:80]}")
        state_thread(target=self._drive, args=(run,), daemon=True, name=f"swarm-{rid}").start()
        return run

    # ---- driver ------------------------------------------------------------------

    def _drive(self, run: SwarmRun) -> None:
        try:
            self._plan(run)
            run.dir.mkdir(parents=True, exist_ok=True)
            git(["worktree", "add", "-b", run.merged_branch, str(run.merge_dir), run.base], run.project)
            run.status = "running"
            self._schedule(run)
            if not run.stop.is_set():
                self._finish(run)
        except Exception as exc:
            run.status, run.finished = "failed", time.time()
            run.summary = f"The swarm could not continue: {exc}"
            run.ev("FAILED: " + str(exc))
            self.pool.event("error", f"swarm {run.id} failed: {exc}")
            traceback.print_exc()

    def _plan(self, run: SwarmRun) -> None:
        txt = str(run.opts.get("tasks_text") or "").strip()
        if txt:
            tasks = [{"id": f"a{i}", "title": " ".join(l.split()[:7]), "prompt": l.strip(), "files": [], "deps": []}
                     for i, l in enumerate((l for l in txt.splitlines() if l.strip()), 1)]
            plan = {"summary": "manual task list", "contracts": "", "tasks": tasks}
        else:
            run.ev("asking the planner to split the goal into independent tasks...")
            tree = git(["ls-files"], run.project, check=False).stdout.splitlines()
            tree_txt = "\n".join(tree[:300])[:6000] or "(empty repository)"
            q = (f"You are the tech lead of a team of {run.max_agents} AI developers working IN PARALLEL on ONE code repository.\n"
                 f"GOAL:\n{run.goal}\n\nCURRENT FILES (git ls-files, may be truncated):\n{tree_txt}\n\n"
                 f"Split the goal into at most {max(run.max_agents, 1)} tasks that can be built at the same time WITHOUT touching the same files. Rules:\n"
                 "- every task owns a disjoint set of paths (\"files\": glob patterns such as \"src/api/**\" or \"tests/test_api.py\"),\n"
                 "- shared decisions (function names, data shapes, routes, file formats) go into \"contracts\" so every developer follows the same interfaces,\n"
                 "- if task B truly needs the code of task A first, put A's id in B's \"depends_on\" (use sparingly: parallel is the point),\n"
                 "- if the goal is small or cannot be split safely, return ONE task,\n"
                 "- each \"prompt\" must be a complete, self-contained instruction for one developer.\n"
                 "Reply with ONLY JSON, no prose, exactly in this shape:\n"
                 "{\"summary\":\"one line\",\"contracts\":\"...\",\"tasks\":[{\"id\":\"a1\",\"title\":\"...\",\"prompt\":\"...\",\"files\":[\"...\"],\"depends_on\":[]}]}")
            plan = None
            for attempt in (1, 2):
                try:
                    plan = parse_plan(self.pool.ask(q if attempt == 1 else q + "\n\nIMPORTANT: output raw JSON only.",
                                                    "planner", tag=f"{run.id}.plan"))
                    break
                except ValueError as exc:
                    run.ev(f"planner attempt {attempt}: {exc}")
            if plan is None:
                run.ev("falling back to a single agent that does the whole goal")
                plan = {"summary": "single agent (the planner did not produce a usable plan)", "contracts": "",
                        "tasks": [{"id": "a1", "title": run.goal[:60], "prompt": run.goal, "files": [], "deps": []}]}
        run.summary_plan, run.contracts = plan["summary"], plan["contracts"]
        aids=list(run.opts.get("account_ids") or [])
        run.agents = [SwarmAgent(t["id"], t["title"], t["prompt"], t["files"], t["deps"], aids[i % len(aids)])
                      for i,t in enumerate(plan["tasks"])]
        run.ev(f"plan: {len(run.agents)} task(s) - " + "; ".join(f"{a.id} {a.title}" for a in run.agents))

    def _schedule(self, run: SwarmRun) -> None:
        while not run.stop.is_set():
            with run.lock:
                active = sum(1 for a in run.agents if a.status in SW_ACTIVE)
                for a in run.agents:
                    if a.status == "queued" and any((run.get(d) is not None and run.get(d).status in SW_BAD) for d in a.deps):
                        a.status, a.note = "skipped", "a task it depends on did not finish"
                ready = [a for a in run.agents if a.status == "queued"
                         and all(run.get(d) is None or run.get(d).status in ("merged", "done") for d in a.deps)]
                for a in ready[:max(0, max(1, run.max_agents) - active)]:
                    a.status = "starting"
                    state_thread(target=self._agent_main, args=(run, a), daemon=True, name=f"agent-{run.id}-{a.id}").start()
                if all(a.status in SW_DONE for a in run.agents):
                    return
            time.sleep(0.4)

    # ---- one agent ---------------------------------------------------------------

    def _agent_prompt(self, run: SwarmRun, ag: SwarmAgent, attachment_paths: Optional[List[str]] = None) -> str:
        others = "\n".join(f"- {o.id} {o.title}: {', '.join(o.files) or '(unspecified)'}" for o in run.agents if o is not ag) or "(none)"
        attachments = ("\nATTACHMENTS AVAILABLE TO YOU (read-only inputs unless your task explicitly requires extracting/processing them):\n"
                       + "\n".join(f"- {p}" for p in (attachment_paths or []))
                       if attachment_paths else "")
        return (f"You are developer {ag.id} (\"{ag.title}\") in a team of {len(run.agents)} developers building one project IN PARALLEL. "
                f"You work alone in your own git worktree/branch; the others work at the same time in theirs.\n\n"
                f"OVERALL GOAL: {run.goal}\n\nYOUR TASK:\n{ag.prompt}\n\n"
                f"ASSIGNED BRIDGE ACCOUNT: {self.pool.get(ag.account_id).name if self.pool.get(ag.account_id) else ag.account_id or '(auto)'}\n"
                f"YOU OWN THESE PATHS (create / modify only these): {', '.join(ag.files) or 'whatever your task needs'}\n"
                f"OTHER DEVELOPERS AND THEIR PATHS (do NOT touch them; assume their code exists as described in the contracts):\n{others}\n\n"
                f"SHARED CONTRACTS (interfaces everybody follows):\n{run.contracts or '(none)'}\n" + attachments + "\n\n"
                "RULES: stay inside your paths; do not commit (the orchestrator does it); run the tests/build for YOUR part when they exist; "
                "do not add the supplied attachments to git; finish with a short summary of what you changed.")

    def _claude(self, run: SwarmRun, ag: SwarmAgent, prompt: str, role: str, cwd: Any, tag: str, account_id: str = "") -> int:
        exe = shutil.which("claude")
        if not exe:
            raise ValueError("Claude Code is not installed")
        self.roles[tag] = role
        cfg = self.pool.cfg
        endpoint_account = account_id or ag.account_id
        if endpoint_account:
            # Carry both the hard account pin and the agent tag so parallel swarm activity
            # stays attributable to the correct agent in the live panel.
            endpoint = (f"http://127.0.0.1:{cfg['port']}/a/{urllib.parse.quote(endpoint_account, safe='')}"
                        f"/s/{urllib.parse.quote(tag, safe='')}")
        else:
            endpoint = f"http://127.0.0.1:{cfg['port']}/s/{urllib.parse.quote(tag, safe='')}"
        env = claude_env(cfg, endpoint)
        cmd = [exe, *permission_args(run.opts.get("mode") or DEFAULT_MODE, []), "-p", "--output-format", "stream-json", "--verbose"]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=flags)
        ag.proc = p
        timer = threading.Timer(_state().SWARM_AGENT_TIMEOUT, lambda: p.kill())
        timer.daemon = True
        timer.start()
        try:
            try:
                p.stdin.write(prompt)                            # via stdin: no quoting problems on any OS
                p.stdin.close()
            except Exception:
                pass
            for line in p.stdout:                                # type: ignore[union-attr]
                self._line(ag, line, tag)
                if run.stop.is_set():
                    p.kill()
            return p.wait()
        finally:
            timer.cancel()
            ag.proc = None

    @staticmethod
    def _line(ag: SwarmAgent, line: str, tag: str = "") -> None:
        line = line.strip()
        if not line:
            return
        try:
            o = json.loads(line)
        except Exception:
            ag.add_log(line)
            ag.activity = line[:120]
            emit_dash_event("agent", {"tag": tag, "agent": ag.id, "status": ag.status, "activity": ag.activity[:180]})
            return
        if not isinstance(o, dict):
            return
        if o.get("type") == "assistant":
            for b in (o.get("message") or {}).get("content") or []:
                if b.get("type") == "tool_use":
                    ag.activity = "⌁ " + _brief_call({"name": b.get("name"), "arguments": b.get("input")})
                    ag.add_log(ag.activity)
                    emit_dash_event("agent", {"tag": tag, "agent": ag.id, "status": ag.status, "activity": ag.activity[:180],
                                                "tool": b.get("name")})
                elif b.get("type") == "text" and str(b.get("text", "")).strip():
                    ag.activity = "» " + str(b["text"]).strip().splitlines()[0][:120]
                    ag.add_log(ag.activity)
                    emit_dash_event("agent", {"tag": tag, "agent": ag.id, "status": ag.status, "activity": ag.activity[:180]})
        elif o.get("type") == "result":
            ag.result = str(o.get("result") or "")
            ag.add_log("✓ " + ag.result.strip().splitlines()[0][:160] if ag.result.strip() else "✓ finished")
            emit_dash_event("agent", {"tag": tag, "agent": ag.id, "status": ag.status, "activity": "✓ finished"})

    def _commit(self, ag: SwarmAgent, wt: Any, msg: str) -> bool:
        git(["add", "-A"], wt, check=False)
        if git(["diff", "--cached", "--quiet"], wt, check=False).returncode == 0:
            return False
        git(["commit", "-q", "-m", msg], wt)
        return True

    def _changed(self, ag: SwarmAgent, wt: Any) -> List[str]:
        return [x for x in git(["diff", "--name-only", f"{ag.base}..HEAD"], wt, check=False).stdout.splitlines() if x]

    def _link_deps(self, run: SwarmRun, wt: Path) -> None:
        for name in ("node_modules", ".venv", "venv"):
            src, dst = run.project / name, wt / name
            if src.is_dir() and not dst.exists():
                try:
                    if os.name == "nt":
                        subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)], capture_output=True)
                    else:
                        os.symlink(src, dst, target_is_directory=True)
                    with open(run.project / ".git" / "info" / "exclude", "a", encoding="utf-8") as f:
                        f.write(f"\n/{name}\n")
                except Exception:
                    pass

    def _verify(self, run: SwarmRun, ag: Optional[SwarmAgent], cwd: Any) -> Tuple[Optional[bool], str, str]:
        cmd = detect_verify(cwd) if run.verify == "auto" else ("" if run.verify == "off" else run.verify)
        if not cmd:
            return None, "", ""
        try:
            p = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=900, env={**os.environ, "CI": "1"})
            return p.returncode == 0, cmd, ((p.stdout or "") + (p.stderr or ""))[-3000:]
        except Exception as exc:
            return False, cmd, f"could not run the check: {exc}"

    def _materialize_attachments(self, run: SwarmRun, ag: SwarmAgent, wt: Path) -> List[str]:
        ids = [str(x) for x in (run.opts.get("attachments") or [])]
        if not ids:
            return []
        dest = wt / ".dsb-agent-input"
        dest.mkdir(parents=True, exist_ok=True)
        paths: List[str] = []
        excludes = None
        try:
            gp = git(["rev-parse", "--git-path", "info/exclude"], wt, check=False).stdout.strip()
            if gp:
                excludes = Path(gp)
                if not excludes.is_absolute():
                    excludes = (wt / excludes).resolve()
            else:
                excludes = None
            if excludes is not None:
                excludes.parent.mkdir(parents=True, exist_ok=True)
                text = excludes.read_text(encoding="utf-8") if excludes.exists() else ""
                if "/.dsb-agent-input/" not in text:
                    with excludes.open("a", encoding="utf-8") as f:
                        f.write("\n/.dsb-agent-input/\n")
        except Exception as exc:
            _warn_once("agent_input_exclude", f"could not exclude agent attachments from git: {exc}")
        for index, aid in enumerate(ids, 1):
            meta = get_swarm_attachment(aid)
            src = Path(meta["path"])
            dst = dest / f"{index:02d}-{_safe_upload_name(meta['name'])}"
            if dst.exists():
                dst.unlink()
            try:
                os.link(src, dst)
            except Exception:
                shutil.copy2(src, dst)
            paths.append(str(dst))
        ag.add_log(f"＋ {len(paths)} attachment(s) available in .dsb-agent-input")
        return paths

    def _agent_main(self, run: SwarmRun, ag: SwarmAgent) -> None:
        try:
            ag.started = time.time()
            emit_dash_event("agent", {"tag": f"{run.id}.{ag.id}", "agent": ag.id, "status": "starting",
                                       "activity": "starting"})
            ag.branch = f"swarm/{run.id}/{ag.id}"
            with run.merge_lock:
                ag.base = git(["rev-parse", run.merged_branch], run.project).stdout.strip() if ag.deps else run.base
                wt = run.dir / ag.id
                git(["worktree", "add", "-b", ag.branch, str(wt), ag.base], run.project)
            ag.worktree = str(wt)
            self._link_deps(run, wt)
            attachment_paths = self._materialize_attachments(run, ag, wt)
            prompt, rounds = self._agent_prompt(run, ag, attachment_paths), 0
            while True:
                ag.status = "running"
                rc = self._claude(run, ag, prompt, "coder", wt, f"{run.id}.{ag.id}")
                if run.stop.is_set():
                    ag.status = "stopped"
                    return
                changed = self._commit(ag, wt, f"swarm({ag.id}): {ag.title}")
                if rc != 0 and not changed and not self._changed(ag, wt):
                    tail = ag.log[-1][1] if ag.log else ""
                    raise ValueError(f"Claude Code exited with code {rc}. {tail}")
                files = self._changed(ag, wt)
                ag.violations = [f for f in files if not in_scope(f, ag.files)]
                if ag.violations and run.opts.get("strict"):
                    for f in ag.violations:
                        git(["checkout", ag.base, "--", f], wt, check=False) if git(["cat-file", "-e", f"{ag.base}:{f}"], wt, check=False).returncode == 0 \
                            else git(["rm", "-qf", "--", f], wt, check=False)
                    self._commit(ag, wt, f"swarm({ag.id}): revert out-of-scope files")
                    run.ev(f"{ag.id}: reverted out-of-scope files {', '.join(ag.violations)}")
                ag.status = "verifying"
                ok, cmd, out = self._verify(run, ag, wt)
                ag.verify_ok, ag.verify_out = ok, out
                if ok is not False or rounds >= _state().SWARM_FIX_ROUNDS:
                    break
                rounds += 1
                ag.attempts = rounds + 1
                run.ev(f"{ag.id}: check failed, fix round {rounds}")
                prompt = (f"Verification command `{cmd}` FAILED with this output:\n{out}\n\nFix the problems in YOUR area, re-run the command until it "
                          f"passes, then reply.\n\nYOUR TASK (for reference):\n{ag.prompt}")
            if run.review_on and self._changed(ag, wt):
                ag.status = "reviewing"
                self._claude(run, ag, (f"You are the reviewer of developer {ag.id}'s work (task: {ag.title}). Run `git diff {ag.base}..HEAD` and review it for "
                                       "correctness bugs, missed edge cases, security problems and broken interfaces. Fix only REAL problems directly in "
                                       "the code - no style refactors. Reply with a one-line verdict."), "reviewer", wt, f"{run.id}.{ag.id}r")
                self._commit(ag, wt, f"swarm({ag.id}): review fixes")
            ag.changed = self._changed(ag, wt)
            if run.stop.is_set():
                ag.status = "stopped"
                return
            if not ag.changed:
                ag.status, ag.note = "done", "no file changes"
                return
            ag.status = "merging"
            self._merge(run, ag)
        except Exception as exc:
            ag.status, ag.note = "failed", str(exc)[:300]
            run.ev(f"{ag.id} failed: {exc}")
        finally:
            ag.finished = time.time()
            emit_dash_event("agent", {"tag": f"{run.id}.{ag.id}", "agent": ag.id,
                                       "status": ag.status, "activity": ag.activity[:180]})

    def _merge(self, run: SwarmRun, ag: SwarmAgent) -> None:
        with run.merge_lock:
            md = run.merge_dir
            p = git(["merge", "--no-ff", "-m", f"swarm: {ag.id} {ag.title}", ag.branch], md, check=False)
            if p.returncode == 0:
                ag.status = "merged"
                run.ev(f"{ag.id} merged")
                return
            conflicts = [x for x in git(["diff", "--name-only", "--diff-filter=U"], md, check=False).stdout.splitlines() if x]
            if conflicts:
                run.ev(f"{ag.id}: merge conflict in {', '.join(conflicts)} - asking an agent to resolve it")
                try:
                    self._claude(run, ag, ("A git merge is in progress in this directory and has CONFLICTS. Resolve every conflict so that BOTH "
                                           "developers' intentions are kept and the code works. Remove all conflict markers. Do not commit.\n"
                                           "CONFLICTED FILES:\n" + "\n".join(f"- {c}" for c in conflicts)),
                                 "reviewer", md, f"{run.id}.{ag.id}m")
                except Exception as exc:
                    run.ev(f"conflict resolver could not run: {exc}")
                left = [x for x in git(["diff", "--name-only", "--diff-filter=U"], md, check=False).stdout.splitlines() if x]
                marks = [c for c in conflicts if (md / c).is_file() and re.search(r"^(<<<<<<<|>>>>>>>) ", (md / c).read_text(encoding="utf-8", errors="replace"), re.M)]
                if not marks:
                    git(["add", "-A"], md, check=False)
                    if git(["commit", "-q", "--no-edit"], md, check=False).returncode == 0 or git(["diff", "--cached", "--quiet"], md, check=False).returncode == 0:
                        ag.status, ag.note = "merged", "conflict auto-resolved: " + ", ".join(conflicts)
                        run.ev(f"{ag.id} merged (conflict resolved)")
                        return
                left = left or marks
            git(["merge", "--abort"], md, check=False)
            git(["reset", "-q", "--hard", "HEAD"], md, check=False)
            ag.status = "conflict"
            ag.note = "could not be merged automatically: " + ", ".join(conflicts or [p.stderr.strip()[:120]])
            run.ev(f"{ag.id}: CONFLICT - {ag.note}")

    def _finish(self, run: SwarmRun) -> None:
        merged = [a for a in run.agents if a.status == "merged"]
        if merged and run.verify != "off":
            run.status = "verifying"
            rounds = 0
            while True:
                ok, cmd, out = self._verify(run, None, run.merge_dir)
                run.final_verify = {"ok": ok, "cmd": cmd, "out": out[-1500:]}
                if ok is not False or rounds >= _state().SWARM_FIX_ROUNDS or run.stop.is_set():
                    break
                rounds += 1
                run.ev(f"integration check failed - integrator round {rounds}")
                ag = SwarmAgent("integrator", "integration fixes", "", [], [])
                try:
                    self._claude(run, ag, f"The merged project fails its check `{cmd}`:\n{out}\n\nFix the integration problems (mismatched interfaces, "
                                          "missing glue code, broken imports) until it passes, then reply.", "reviewer", run.merge_dir, f"{run.id}.int")
                    self._commit(ag, run.merge_dir, "swarm: integration fixes")
                except Exception as exc:
                    run.ev(f"integrator failed: {exc}")
                    break
        bad = [a for a in run.agents if a.status in SW_BAD]
        run.status = "done" if not bad and run.final_verify.get("ok") is not False else "done_with_issues"
        run.finished = time.time()
        files = sorted({f for a in merged for f in a.changed})
        run.summary = (f"{len(merged)}/{len(run.agents)} agents merged into branch {run.merged_branch} ({len(files)} files). "
                       + (f"Final check: {'PASSED' if run.final_verify.get('ok') else 'FAILED' if run.final_verify.get('ok') is False else 'not run'}. "
                          if run.final_verify else "")
                       + ("Problems: " + "; ".join(f"{a.id} {a.status}" + (f" ({a.note})" if a.note else "") for a in bad) if bad else "Everything merged cleanly."))
        run.ev(run.summary)
        self.pool.event("ok" if run.status == "done" else "warn", f"swarm {run.id} {run.status}: {run.summary[:140]}")

    # ---- controls ----------------------------------------------------------------

    def set_agents(self, run: SwarmRun, n: int) -> None:
        run.max_agents = max(1, min(_state().SWARM_MAX_AGENTS * 2, int(n)))
        run.ev(f"parallel agents set to {run.max_agents}")

    def stop(self, run: SwarmRun) -> None:
        run.stop.set()
        for a in run.agents:
            try:
                if a.proc:
                    a.proc.kill()
            except Exception:
                pass
            if a.status not in SW_DONE:
                a.status = "stopped"
        if run.status in ("planning", "running", "verifying"):
            run.status, run.finished = "stopped", time.time()
        run.ev("stopped by the user")

    def apply(self, run: SwarmRun) -> str:
        if run.status not in ("done", "done_with_issues"):
            raise ValueError("the run has not finished yet")
        if run.applied:
            raise ValueError("already applied")
        dirty = git(["status", "--porcelain"], run.project, check=False).stdout.strip()
        if dirty:
            raise ValueError("your working folder has uncommitted changes - commit or stash them first")
        p = git(["merge", "--no-ff", "-m", f"swarm {run.id}: {run.goal[:60]}", run.merged_branch], run.project, check=False)
        if p.returncode != 0:
            git(["merge", "--abort"], run.project, check=False)
            raise ValueError("could not merge into your branch: " + (p.stdout + p.stderr).strip()[:300])
        run.applied = True
        run.ev(f"applied to {run.base_branch}")
        return f"Merged into {run.base_branch}."

    def cleanup(self, run: SwarmRun) -> None:
        self.stop(run) if run.status in ("planning", "running", "verifying") else None
        for a in run.agents:
            if a.worktree:
                git(["worktree", "remove", "--force", a.worktree], run.project, check=False)
            if a.branch:
                git(["branch", "-D", a.branch], run.project, check=False)
        git(["worktree", "remove", "--force", str(run.merge_dir)], run.project, check=False)
        if run.applied or run.opts.get("discard"):
            git(["branch", "-D", run.merged_branch], run.project, check=False)
        shutil.rmtree(run.dir, ignore_errors=True)
        git(["worktree", "prune"], run.project, check=False)
        run.cleaned = True
        run.ev("worktrees removed")

    def status_text(self) -> str:
        if not self.runs:
            return "No swarm runs yet. Start one with:  /swarm <what the team should build>"
        out = []
        for r in sorted(self.runs.values(), key=lambda x: x.created)[-4:]:
            out.append(f"{r.id} [{r.status}] {r.goal[:60]}  (max {r.max_agents} agents)")
            out += [f"   {a.id} {a.title[:40]}: {a.status}{' - ' + a.activity[:50] if a.status in SW_ACTIVE and a.activity else ''}" for a in r.agents]
        return "\n".join(out)

    def command(self, arg: str, ctx: Dict[str, Any]) -> str:
        parts = arg.split(None, 1)
        sub = parts[0].lower() if parts else "status"
        run = self.latest()
        try:
            if sub in ("status", "list", "ls"):
                return self.status_text()
            if sub in ("stop", "apply", "cleanup", "agents"):
                if run is None:
                    return "There is no swarm run yet."
                if sub == "stop":
                    self.stop(run)
                    return f"{run.id} stopped."
                if sub == "apply":
                    return self.apply(run)
                if sub == "cleanup":
                    self.cleanup(run)
                    return f"{run.id}: worktrees removed."
                self.set_agents(run, int((parts[1] if len(parts) > 1 else "").split()[0]))
                return f"{run.id}: up to {run.max_agents} agents at the same time."
            run = self.start(arg, str(ctx.get("cwd") or ""))
            try:
                open_panel(self.pool, "swarm")
            except Exception:
                pass
            return (f"Swarm {run.id} started on {run.project} (up to {run.max_agents} agents in parallel).\n"
                    "A planner is splitting the goal now; watch it live in the panel (Swarm page).\n"
                    "Commands: /swarm status | /swarm agents N | /swarm stop | /swarm apply")
        except (ValueError, IndexError) as exc:
            return f"Swarm: {exc}"


# ============================================================================
# Multi-account pool (V6): accounts, statistics, routing, fail-over, commands
# ============================================================================

STRATEGIES = ("balanced", "round_robin", "failover", "pinned")
ROUTING_DEFAULTS: Dict[str, Any] = {"strategy": "balanced", "pinned": "", "auto_failover": True,
                                    "rotate_requests": 30, "rotate_minutes": 30,
                                    "smart_routing": True, "tier_strong": 4, "tier_balanced": 3}


class AcctStats:
    """Cheap, thread-safe counters. Token numbers are ESTIMATES (chars / CHARS_PER_TOKEN)."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.req = self.ok = self.err = self.rate_limits = 0
        self.in_tok = self.out_tok = 0
        self.active_s = 0.0
        self.since = time.time()
        self.last_used = 0.0
        self.streak_start = 0.0
        self.minutes: Dict[int, int] = {}
        self.days: Dict[str, List[int]] = {}
        self.last_error = ""
        self.last_error_at = 0.0
        self.dirty = False

    def reset(self) -> None:
        with self.lock:
            self.req = self.ok = self.err = self.rate_limits = self.in_tok = self.out_tok = 0
            self.active_s, self.since = 0.0, time.time()
            self.last_used = self.streak_start = 0.0
            self.minutes.clear()
            self.days.clear()
            self.last_error, self.last_error_at, self.dirty = "", 0.0, True

    def record_exchange(self, prompt_chars: int, reply_chars: int, seconds: float) -> None:
        self.record_tokens(int(prompt_chars / _state().CHARS_PER_TOKEN), int(reply_chars / _state().CHARS_PER_TOKEN), seconds)

    def record_tokens(self, tin: int, tout: int, seconds: float) -> None:
        now = time.time()
        with self.lock:
            if not self.last_used or (now - seconds) - self.last_used > _state().STREAK_GAP:
                self.streak_start = now - seconds
            self.last_used = now
            self.req += 1
            self.in_tok += tin
            self.out_tok += tout
            self.active_s += max(0.0, seconds)
            mk = int(now // 60)
            self.minutes[mk] = self.minutes.get(mk, 0) + tin + tout
            for k in [k for k in self.minutes if k < mk - 180]:
                del self.minutes[k]
            day = time.strftime("%Y-%m-%d")
            d = self.days.setdefault(day, [0, 0, 0])
            d[0] += tin
            d[1] += tout
            d[2] += 1
            for k in sorted(self.days)[:-14]:
                del self.days[k]
            self.dirty = True

    def note_ok(self) -> None:
        with self.lock:
            self.ok += 1
            self.dirty = True

    def note_err(self, kind: str, msg: str = "") -> None:
        with self.lock:
            self.err += 1
            if kind == "rate_limit":
                self.rate_limits += 1
            self.last_error = f"[{kind}] {msg}"[:220]
            self.last_error_at = time.time()
            self.dirty = True

    def recent_tokens(self, window_s: int = 600) -> int:
        lo = int((time.time() - window_s) // 60)
        with self.lock:
            return sum(v for k, v in self.minutes.items() if k >= lo)

    def snapshot(self, now: float) -> Dict[str, Any]:
        with self.lock:
            mk = int(now // 60)
            spark = [self.minutes.get(mk - 59 + i, 0) for i in range(60)]
            today = self.days.get(time.strftime("%Y-%m-%d"), [0, 0, 0])
            live = bool(self.last_used) and now - self.last_used <= _state().STREAK_GAP
            streak = (now - self.streak_start) if live else (self.last_used - self.streak_start if self.last_used else 0)
            return {"req": self.req, "ok": self.ok, "err": self.err, "rate_limits": self.rate_limits,
                    "in_tok": self.in_tok, "out_tok": self.out_tok,
                    "today_in": today[0], "today_out": today[1], "today_req": today[2],
                    "active_s": round(self.active_s, 1), "streak_s": round(max(0.0, streak), 1),
                    "streak_live": live, "avg_s": round(self.active_s / self.req, 2) if self.req else 0.0,
                    "last_used_ago": round(now - self.last_used, 1) if self.last_used else None,
                    "spark": spark, "last_error": self.last_error,
                    "last_error_ago": round(now - self.last_error_at, 1) if self.last_error_at else None}

    def to_json(self) -> Dict[str, Any]:
        with self.lock:
            return {"req": self.req, "ok": self.ok, "err": self.err, "rate_limits": self.rate_limits,
                    "in_tok": self.in_tok, "out_tok": self.out_tok, "active_s": self.active_s,
                    "since": self.since, "days": self.days}

    def load(self, d: Optional[Dict[str, Any]]) -> None:
        if not isinstance(d, dict):
            return
        with self.lock:
            try:
                for k in ("req", "ok", "err", "rate_limits", "in_tok", "out_tok"):
                    setattr(self, k, int(d.get(k, 0)))
                self.active_s = float(d.get("active_s", 0.0))
                self.since = float(d.get("since", self.since))
                days = d.get("days")
                if isinstance(days, dict):
                    self.days = {str(k): [int(x) for x in v][:3] for k, v in days.items()
                                 if isinstance(v, list) and len(v) >= 3}
            except Exception:
                pass


class Account:
    def __init__(self, d: Dict[str, Any]) -> None:
        self.id = str(d["id"])
        self.name = str(d.get("name") or self.id)
        requested_profile = Path(d.get("profile") or (_state().ACCOUNTS_DIR / self.id)).expanduser().resolve()
        instance_home = _state().paths.home.resolve()
        try:
            requested_profile.relative_to(instance_home)
            self.profile = requested_profile
        except ValueError:
            self.profile = (_state().ACCOUNTS_DIR / self.id).resolve()
            log(f"[profile] account {self.id!r} pointed outside this instance; using {self.profile}", C.yellow)
        self.deleted = bool(d.get("deleted", False))
        self.enabled = bool(d.get("enabled", True)) and not self.deleted
        self.headed = bool(d.get("headed", False))          # keep the browser window visible
        self.logged_in = bool(d.get("logged_in", False))
        self.kind = str(d.get("kind") or "web")                  # web | openai | anthropic
        self.provider = str(d.get("provider") or ("deepseek_web" if self.kind == "web" else "custom_openai"))
        self.base_url = str(d.get("base_url") or "")
        self.api_key = str(d.get("api_key") or "")
        self.model = str(d.get("model") or "")
        try:
            self.tier = max(1, min(5, int(d.get("tier") or (3 if self.kind == "web" else guess_tier(self.model)))))
        except (TypeError, ValueError):
            self.tier = 3
        try:
            self.max_parallel = 1 if self.kind == "web" else max(1, min(32, int(d.get("max_parallel") or 4)))
            self.price_in, self.price_out = float(d.get("price_in") or 0), float(d.get("price_out") or 0)
            self.budget = float(d.get("budget") or 0)
        except (TypeError, ValueError):
            self.max_parallel, self.price_in, self.price_out, self.budget = 1, 0.0, 0.0, 0.0
        self.max_out = 0                                           # learnt output-token limit (API accounts)
        self.created = float(d.get("created") or time.time())
        self.stats = AcctStats()
        self.status = "stopped"      # starting | login | login_needed | ready | error | disabled | stopped
        self.browser_state = "CLOSED" if self.deleted else "CREATED"
        self.browser_state_since = time.time()
        self.browser_state_reason = "soft-deleted" if self.deleted else ""
        self.status_since = time.time()
        self.status_err = ""
        self.cooldown_until = 0.0
        self.cooldown_reason = ""
        self.rl_streak = 0
        self.fail_streak = 0
        self.inflight = 0
        self.stint_reqs = 0
        self.stint_start = time.time()
        self.worker: Optional[Bridge] = None
        self.on_change: Optional[Callable[[], None]] = None
        self.op_lock = threading.Lock()
        self.restarts: List[float] = []
        self.cool_notified = True

    def to_cfg(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "profile": str(self.profile), "enabled": self.enabled,
                "deleted": self.deleted, "headed": self.headed, "logged_in": self.logged_in, "created": self.created,
                "kind": self.kind, "provider": self.provider, "base_url": self.base_url, "api_key": self.api_key,
                "model": self.model, "tier": self.tier, "max_parallel": self.max_parallel,
                "price_in": self.price_in, "price_out": self.price_out, "budget": self.budget}

    def set_status(self, status: str, err: str = "") -> None:
        if status != self.status:
            self.status, self.status_since = status, time.time()
        if err:
            self.status_err = err

    def set_browser_state(self, state: str, reason: str = "") -> None:
        if state not in BROWSER_STATES:
            raise ValueError(f"unknown browser state: {state}")
        if state != self.browser_state:
            self.browser_state, self.browser_state_since = state, time.time()
        if reason:
            self.browser_state_reason = str(reason)[:240]

    def mark_logged_in(self) -> None:
        if not self.logged_in:
            self.logged_in = True
            if self.on_change:
                self.on_change()

    def cost(self) -> float:
        return self.stats.in_tok * self.price_in / 1e6 + self.stats.out_tok * self.price_out / 1e6

    def over_budget(self) -> bool:
        return bool(self.budget > 0 and self.cost() >= self.budget)

    def usable(self, now: Optional[float] = None) -> bool:
        now = now or time.time()
        w = self.worker
        return bool(self.enabled and self.status == "ready" and w is not None and w.ok
                    and self.cooldown_until <= now and not self.over_budget())

    def state(self, now: float) -> str:
        if self.deleted:
            return "deleted"
        if not self.enabled:
            return "disabled"
        if self.status == "ready":
            if self.over_budget():
                return "budget"
            if self.cooldown_until > now:
                return "cooldown"
            return "busy" if self.inflight else "ready"
        return self.status


class ResourceGovernor:
    """Small cached resource sampler; it never runs on the request hot path more often than every 3s."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last = 0.0
        self._snapshot: Dict[str, Any] = {"level":"normal","browser_count":0,"page_count":0,
                                          "active_requests":0,"queue_length":0,"cpu_pressure":None,
                                          "ram_pressure":None,"recommended":1}

    @staticmethod
    def _ram_pressure() -> Optional[float]:
        try:
            if os.name == "nt":
                import ctypes
                class _MEM(ctypes.Structure):
                    _fields_=[("dwLength",ctypes.c_ulong),("dwMemoryLoad",ctypes.c_ulong),
                              ("ullTotalPhys",ctypes.c_ulonglong),("ullAvailPhys",ctypes.c_ulonglong),
                              ("ullTotalPageFile",ctypes.c_ulonglong),("ullAvailPageFile",ctypes.c_ulonglong),
                              ("ullTotalVirtual",ctypes.c_ulonglong),("ullAvailVirtual",ctypes.c_ulonglong),
                              ("ullAvailExtendedVirtual",ctypes.c_ulonglong)]
                m=_MEM(); m.dwLength=ctypes.sizeof(_MEM)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                    return float(m.dwMemoryLoad)/100.0
            mem=Path("/proc/meminfo")
            if mem.exists():
                vals={}
                for line in mem.read_text(errors="ignore").splitlines():
                    if ":" in line:
                        k,v=line.split(":",1); mt=re.search(r"\d+",v)
                        if mt: vals[k]=int(mt.group())
                total,avail=vals.get("MemTotal"),vals.get("MemAvailable")
                if total and avail is not None: return max(0.0,min(1.0,1.0-avail/total))
        except Exception:
            pass
        return None

    def snapshot(self, pool: "Pool") -> Dict[str, Any]:
        now=time.time()
        with self._lock:
            if now-self._last < 3.0: return dict(self._snapshot)
            browsers=pages=active=queues=0
            for a in list(pool.accounts):
                if a.deleted: continue
                active += max(0,int(a.inflight))
                w=a.worker
                if not w: continue
                try: queues += int(w.jobs.qsize()) if hasattr(w,"jobs") else 0
                except Exception: pass
                if a.kind == "web":
                    try:
                        if w.ok: browsers += 1
                        ctx=getattr(getattr(w.engine,"ds",None),"ctx",None)
                        if ctx is not None: pages += len(getattr(ctx,"pages",[]) or [])
                    except Exception: pass
            cpu=None
            try:
                if hasattr(os,"getloadavg"): cpu=max(0.0,min(2.0,os.getloadavg()[0]/max(1,os.cpu_count() or 2)))
            except Exception: pass
            ram=self._ram_pressure()
            high=(cpu is not None and cpu>=0.9) or (ram is not None and ram>=0.90) or active>=max(2,browsers+1)
            low=browsers<=1 and active==0 and queues==0 and (ram is None or ram<0.65)
            level="high" if high else ("low" if low else "normal")
            cap=max(1,pool.capacity())
            rec=1 if level=="high" else min(2 if level=="low" else 3,cap)
            self._snapshot={"level":level,"browser_count":browsers,"page_count":pages,"active_requests":active,
                            "queue_length":queues,"cpu_pressure":cpu,"ram_pressure":ram,"recommended":rec}
            self._last=now
            return dict(self._snapshot)


class Pool:
    """Routes requests over several DeepSeek accounts. Exposes the interface the HTTP layer needs."""

    def __init__(self, cfg: Dict[str, Any], autostart: bool = True) -> None:
        self.runtime_state = _state()
        self.cfg = cfg
        self.lock = threading.RLock()
        self.accounts: List[Account] = []
        self.events: "deque" = deque(maxlen=200)
        self.started = time.time()
        self._rr = -1
        self.current: Optional[str] = None
        self._last_route: Optional[str] = None
        self._stop = threading.Event()
        self._usage_saved = 0.0
        self.governor = ResourceGovernor()
        raw_pa = cfg.get("project_accounts")
        self.project_accounts: Dict[str, List[str]] = {str(k): [str(x) for x in v if str(x)]
                                                         for k, v in raw_pa.items() if isinstance(v, list)} if isinstance(raw_pa, dict) else {}
        self.swarm = Swarm(self)
        routing = cfg.get("routing")
        if not isinstance(routing, dict):
            routing = cfg["routing"] = {}
        for k, v in ROUTING_DEFAULTS.items():
            routing.setdefault(k, v)
        if routing["strategy"] not in STRATEGIES:
            routing["strategy"] = "balanced"
        self.routing = routing
        self._load_accounts()
        self._load_usage()
        if autostart:
            state_thread(target=self._watchdog, daemon=True, name="DeepSeekPool").start()

    # ---- persistence ------------------------------------------------------------

    def _load_accounts(self) -> None:
        raw = self.cfg.get("accounts")
        items = [d for d in raw if isinstance(d, dict) and d.get("id")] if isinstance(raw, list) else []
        # Accounts marked deleted by older bridge versions are no longer restorable:
        # remove their records on startup and clean their trusted browser profiles.
        legacy_deleted = [d for d in items if bool(d.get("deleted", False))]
        items = [d for d in items if not bool(d.get("deleted", False))]
        for d in legacy_deleted:
            self._remove_account_profile_path(Path(d.get("profile") or ""))

        # Backward compatibility: only a truly missing `accounts` key means an older
        # pre-multi-account config. An explicit [] is an intentional empty account pool
        # and must stay empty (critical for explicit Multi-AI / Dashboard startup).
        if raw is None:
            try:
                had = _state().PROFILE_DIR.exists() and any(_state().PROFILE_DIR.iterdir())
            except Exception:
                had = False
            items = [{"id": "main", "name": "Account 1", "profile": str(_state().PROFILE_DIR), "enabled": True,
                      "logged_in": had, "created": time.time()}]
        for d in items:
            a = Account(d)
            a.on_change = self._save
            self.accounts.append(a)
        if self.accounts:
            if not self.get_by_id(self.routing.get("pinned")):
                self.routing["pinned"] = self.accounts[0].id
        else:
            self.routing["pinned"] = None
        self._save()

    @staticmethod
    def _remove_account_profile_path(profile: Path) -> None:
        """Delete only browser profiles owned by this bridge; never arbitrary paths from config."""
        try:
            if not str(profile):
                return
            resolved = profile.expanduser().resolve(strict=False)
            trusted_roots = [_state().ACCOUNTS_DIR.resolve(strict=False), _state().PROFILE_DIR.resolve(strict=False)]
            trusted = any(resolved == root or root in resolved.parents for root in trusted_roots)
            if trusted and resolved.exists():
                shutil.rmtree(resolved, ignore_errors=False)
        except Exception as exc:
            _warn_once("profile_cleanup", f"could not remove account browser profile {profile!s}: {exc}")

    def _remove_usage_account(self, account_id: str) -> None:
        """Remove one account's persisted usage/stats entry immediately."""
        try:
            path = self._usage_path()
            if not path.exists():
                return
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return
            accounts = data.get("accounts")
            if isinstance(accounts, dict) and account_id in accounts:
                accounts.pop(account_id, None)
                tmp = path.with_suffix(path.suffix + ".tmp")
                tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                os.replace(tmp, path)
        except Exception as exc:
            self.event("warn", f"usage record for deleted account could not be removed: {exc}")

    def _save(self) -> None:
        with self.lock:
            self.cfg["accounts"] = [a.to_cfg() for a in self.accounts]
            self.cfg["routing"] = self.routing
            self.cfg["project_accounts"] = self.project_accounts
            save_config(self.cfg)

    def _usage_path(self) -> Path:
        return _state().CONFIG_PATH.with_name(".deepseek_bridge_usage.json")

    def _load_usage(self) -> None:
        try:
            data = json.loads(self._usage_path().read_text(encoding="utf-8"))
            for a in self.accounts:
                a.stats.load((data.get("accounts") or {}).get(a.id))
        except Exception:
            pass

    def save_usage(self) -> None:
        try:
            if not any(a.stats.dirty for a in self.accounts):
                return
            for a in self.accounts:
                a.stats.dirty = False
            path = self._usage_path()
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps({"version": 1, "accounts": {a.id: a.stats.to_json() for a in self.accounts}}),
                           encoding="utf-8")
            os.replace(tmp, path)
        except Exception:
            pass

    # ---- small helpers ----------------------------------------------------------

    def event(self, level: str, msg: str) -> None:
        item = {"t": time.time(), "level": level, "msg": msg}
        self.events.append(item)
        emit_dash_event("pool", item)
        log(f"[pool] {msg}", {"warn": C.yellow, "error": C.red, "ok": C.green}.get(level, C.dim))

    def get_by_id(self, aid: Any) -> Optional[Account]:
        return next((a for a in self.accounts if a.id == aid), None)

    def get(self, ref: Any) -> Optional[Account]:
        s = str(ref or "").strip()
        if not s:
            return None
        a = self.get_by_id(s)
        if a:
            return a
        if s.isdigit() and 1 <= int(s) <= len(self.accounts):
            return self.accounts[int(s) - 1]
        low = s.lower()
        a = next((x for x in self.accounts if x.name.lower() == low), None)
        if a:
            return a
        part = [x for x in self.accounts if low in x.name.lower() or low in x.id.lower()]
        return part[0] if len(part) == 1 else None

    @property
    def ok(self) -> bool:
        return any(a.enabled for a in self.accounts)

    def alive(self) -> bool:
        return not self._stop.is_set()

    # ---- lifecycle ----------------------------------------------------------------

    def start_account(self, a: Account, force_login: bool = False) -> None:
        if a.deleted or not a.enabled:
            a.set_status("disabled")
            try: a.set_browser_state("CLOSED", "disabled")
            except Exception: pass
            return
        a.set_status("starting")
        a.worker = Bridge(a, self, force_login) if a.kind == "web" else ApiWorker(a, self)

    def start_all(self) -> None:
        for a in self.accounts:
            self.start_account(a)

    def start_selected(self, account_ids: List[str]) -> List[str]:
        wanted = {str(x) for x in account_ids if str(x)}
        started: List[str] = []
        for a in self.accounts:
            if a.enabled and a.id in wanted:
                self.start_account(a)
                started.append(a.id)
        return started

    def wait_selected_ready(self, account_ids: List[str], timeout: float) -> bool:
        wanted = {str(x) for x in account_ids if str(x)}
        if not wanted:
            return False
        end = time.time() + timeout
        while time.time() < end:
            if any(a.status == "ready" for a in self.accounts if a.id in wanted):
                return True
            # A web account may legitimately sit in `login_needed` while the user
            # is still completing the interactive browser login.  Treat that as a
            # live startup state; otherwise the main thread immediately calls
            # Pool.stop(), which closes the just-opened login window.  API accounts
            # use `login_needed` for invalid/missing keys, so keep those as failures.
            live = [
                a for a in self.accounts
                if a.id in wanted
                and a.enabled
                and (a.status in ("starting", "login") or
                     (a.status == "login_needed" and a.kind == "web"))
            ]
            if not live:
                return False
            time.sleep(0.3)
        return False

    def restart_account(self, a: Account, force_login: bool = False) -> None:
        def run() -> None:
            with a.op_lock:
                old = a.worker
                a.set_status("starting")
                if old is not None:
                    old.stop()
                if not a.enabled:
                    a.set_status("disabled")
                    return
                self.start_account(a, force_login)
        state_thread(target=run, daemon=True, name=f"restart-{a.id}").start()

    def wait_any_ready(self, timeout: float) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if any(a.status == "ready" for a in self.accounts):
                return True
            # Keep waiting while a website-login account is waiting for the user.
            # Do not treat API `login_needed` (e.g. a bad/missing key) as a live state.
            live = [
                a for a in self.accounts
                if a.enabled
                and (a.status in ("starting", "login") or
                     (a.status == "login_needed" and a.kind == "web"))
            ]
            if not live:
                return False
            time.sleep(0.3)
        return False

    def stop(self) -> None:
        self._stop.set()
        ths = []
        for a in self.accounts:
            w = a.worker
            if w is not None:
                t = state_thread(target=w.stop, daemon=True)
                t.start()
                ths.append(t)
        for t in ths:
            t.join(timeout=30)
        self.save_usage()

    # ---- account management ------------------------------------------------------

    @staticmethod
    def _project_key(project: str) -> str:
        try:
            return str(Path(project).expanduser().resolve()) if project else ""
        except Exception:
            return str(project or "").strip()

    def project_accounts_for(self, project: str) -> List[str]:
        key=self._project_key(project)
        raw=self.project_accounts.get(key, [])
        ids={a.id for a in self.accounts}
        return [x for x in raw if x in ids]

    def set_project_accounts(self, project: str, account_ids: List[str]) -> List[str]:
        key=self._project_key(project)
        if not key:
            raise ValueError("project path is required")
        clean=[]; seen=set()
        for x in account_ids or []:
            a=self.get(str(x))
            if a and a.id not in seen:
                clean.append(a.id); seen.add(a.id)
        if not clean:
            self.project_accounts.pop(key, None)
        else:
            self.project_accounts[key]=clean
        self._save()
        self.event("info", f"project account routing updated for {key}: {len(clean)} account(s)")
        return clean

    def add_web_account(self, provider: str, name: str = "", tier: int = 0, headed: bool = True, start: bool = True) -> Account:
        pv=_PROVIDER.get(provider)
        if not pv or pv.get("kind") != "web":
            raise ValueError("unknown web-login provider")
        with self.lock:
            n=len(self.accounts)+1
            name=(name or "").strip()[:40] or f"{pv['name']} {n}"
            if any(x.name.lower()==name.lower() for x in self.accounts): name=f"{name} {n}"
            aid=f"{re.sub(r'[^a-z0-9]+','-',provider.lower())[:12] or 'web'}-{secrets.token_hex(2)}"
            a=Account({"id":aid,"name":name,"profile":str(_state().ACCOUNTS_DIR/aid),"enabled":True,"headed":bool(headed),
                       "logged_in":False,"created":time.time(),"kind":"web","provider":provider,
                       "tier":tier or int(pv.get("tier") or 3),"max_parallel":1})
            a.on_change=self._save; self.accounts.append(a); self._save()
        self.event("info", f"{pv['name']} web account '{name}' added - login in its dedicated browser profile")
        if start: self.start_account(a, force_login=True)
        return a

    def add_account(self, name: str = "", start: bool = True) -> Account:
        with self.lock:
            n = len(self.accounts) + 1
            name = (name or "").strip()[:40] or f"Account {n}"
            if any(x.name.lower() == name.lower() for x in self.accounts):
                name = f"{name} {n}"
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()[:16] or "acct"
            aid = f"{slug}-{secrets.token_hex(2)}"
            a = Account({"id": aid, "name": name, "profile": str(_state().ACCOUNTS_DIR / aid), "enabled": True,
                         "logged_in": False, "created": time.time()})
            a.on_change = self._save
            self.accounts.append(a)
            self._save()
        self.event("info", f"account '{name}' added" +
                   (" - log in to DeepSeek in the browser window that opens" if start else ""))
        if start:
            self.start_account(a)
        return a

    def add_api_account(self, provider: str, name: str = "", base_url: str = "", api_key: str = "", model: str = "",
                        tier: int = 0, max_parallel: int = 4, price_in: float = 0.0, price_out: float = 0.0,
                        budget: float = 0.0, start: bool = True) -> Account:
        pv = _PROVIDER.get(provider) or _PROVIDER["custom_openai"]
        if pv["kind"] == "web":
            raise ValueError("DeepSeek website accounts are added with their own login window")
        base_url = (base_url or pv["base"]).strip()
        if not re.match(r"^https?://", base_url):
            raise ValueError("the base URL must start with http:// or https://")
        if not (api_key or "").strip():
            raise ValueError("an API key is required")
        model = (model or (pv["models"][0] if pv["models"] else "")).strip()
        if not model:
            raise ValueError("a model name is required (use 'Fetch models')")
        with self.lock:
            n = len(self.accounts) + 1
            name = (name or "").strip()[:40] or f"{pv['name']} {n}"
            if any(x.name.lower() == name.lower() for x in self.accounts):
                name = f"{name} {n}"
            aid = f"{re.sub(r'[^a-z0-9]+', '-', provider.lower())[:12]}-{secrets.token_hex(2)}"
            a = Account({"id": aid, "name": name, "enabled": True, "logged_in": True, "created": time.time(),
                         "kind": pv["kind"], "provider": provider, "base_url": base_url, "api_key": api_key.strip(),
                         "model": model, "tier": tier or guess_tier(model, pv["tier"]), "max_parallel": max_parallel,
                         "price_in": price_in, "price_out": price_out, "budget": budget})
            a.on_change = self._save
            self.accounts.append(a)
            self._save()
        self.event("info", f"{pv['name']} account '{name}' added (tier {a.tier}, model {model})")
        if start:
            self.start_account(a)
        return a

    def update_account(self, a: Account, d: Dict[str, Any]) -> None:
        restart = False
        if d.get("name") is not None and str(d["name"]).strip():
            a.name = str(d["name"]).strip()[:40]
        if "tier" in d and d["tier"] not in (None, ""):
            a.tier = max(1, min(5, int(d["tier"])))
        for k in ("price_in", "price_out", "budget"):
            if d.get(k) not in (None, ""):
                setattr(a, k, max(0.0, float(d[k])))
        if a.kind != "web":
            for k in ("base_url", "model"):
                if d.get(k) and str(d[k]).strip() != getattr(a, k):
                    if k == "base_url" and not re.match(r"^https?://", str(d[k]).strip()):
                        raise ValueError("the base URL must start with http:// or https://")
                    setattr(a, k, str(d[k]).strip())
                    restart = True
            if d.get("api_key") and str(d["api_key"]).strip() != a.api_key:
                a.api_key, restart = str(d["api_key"]).strip(), True
            if d.get("max_parallel") not in (None, "") and int(d["max_parallel"]) != a.max_parallel:
                a.max_parallel, restart = max(1, min(32, int(d["max_parallel"]))), True
        self._save()
        if restart:
            self.restart_account(a)

    def capacity(self) -> int:
        """How many requests can really run at the same time right now."""
        now = time.time()
        return sum(a.max_parallel for a in self.accounts if a.usable(now))

    def parallel_capacity(self, account_ids: Optional[List[str]] = None, mode: str = "auto") -> int:
        mode = str(mode or "auto").lower()
        if mode not in PARALLEL_MODES: mode = "auto"
        now=time.time()
        chosen=[a for a in self.accounts if a.enabled and not a.deleted and a.status=="ready"
                and a.cooldown_until<=now and not a.over_budget() and (not account_ids or a.id in account_ids)]
        if not chosen: return 0
        if mode=="serial": return 1
        if mode=="light": return max(1,len({a.provider for a in chosen}))
        full=max(1,sum(a.max_parallel for a in chosen))
        if mode=="full": return full
        return min(full,max(1,int(self.governor.snapshot(self)["recommended"])))

    def ask(self, prompt: str, role: str = "planner", system: str = "", max_tokens: int = 4096,
            tag: Optional[str] = None, timeout: float = 900) -> str:
        """One internal question to the model pool (used by the swarm planner / reviewer)."""
        data: Dict[str, Any] = {"model": "claude-opus-4-20250514" if role in ("planner", "reviewer") else "claude-sonnet-4-20250514",
                                "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        if system:
            data["system"] = system
        req = normalize_anthropic(data)
        req.role, req.tag = role, tag
        return self.dispatch(req, None, None, None, _state().PRIORITY_MAIN).result(timeout=timeout).text

    def remove_account(self, a: Account, purge: bool = False) -> None:
        """Permanently remove an account and every bridge-owned reference to it.

        `purge` is retained only for API compatibility with older dashboard clients;
        deletion is now always permanent.
        """
        del purge
        if a is None:
            raise ValueError("account not found")
        with self.lock:
            if a not in self.accounts:
                return
            account_id = a.id
            account_name = a.name

            # Mark disabled/closed before stopping the worker so the watchdog cannot
            # race and resurrect an account that is in the middle of deletion.
            a.enabled = False
            a.logged_in = False
            a.status = "disabled"
            a.status_since = time.time()
            try:
                a.set_browser_state("CLOSED", "permanently deleted")
            except Exception:
                a.browser_state = "CLOSED"

            # Remove all persistent/in-memory routing references while the account is
            # still addressable by object identity. This includes project routing.
            self.project_accounts = {
                project: [x for x in ids if x != account_id]
                for project, ids in self.project_accounts.items()
            }
            self.project_accounts = {project: ids for project, ids in self.project_accounts.items() if ids}
            if self.routing.get("pinned") == account_id:
                remaining = [x for x in self.accounts if x is not a and x.enabled and not x.deleted]
                self.routing["pinned"] = remaining[0].id if remaining else None
            if self.current == account_id:
                remaining = [x for x in self.accounts if x is not a and x.enabled and not x.deleted]
                self.current = remaining[0].id if remaining else None
            if self._last_route == account_id:
                self._last_route = None

            # Remove from the live account registry before releasing the lock. Any new
            # request can therefore never pick or address the deleted account.
            self.accounts.remove(a)
            self._save()

        # A running web/account worker owns the Playwright browser context. Stop it
        # synchronously so the browser cannot survive the deletion operation.
        if a.worker is not None:
            try:
                a.worker.stop()
            except Exception as exc:
                self.event("warn", f"account '{account_name}' worker shutdown reported: {exc}")

        # A deleted account can also be the owner of live swarm processes. Stop those
        # processes cleanly and remove the deleted ID from all run metadata so future
        # scheduler operations never try to address a missing account.
        try:
            with self.swarm.lock:
                for run in list(self.swarm.runs.values()):
                    run.opts["account_ids"] = [x for x in (run.opts.get("account_ids") or []) if x != account_id]
                    for ag in run.agents:
                        if ag.account_id != account_id:
                            continue
                        proc = ag.proc
                        if proc is not None and proc.poll() is None:
                            try:
                                proc.terminate()
                            except Exception:
                                pass
                        replacement = next((x for x in self.accounts if x.enabled and x.status == "ready"), None)
                        ag.account_id = replacement.id if replacement is not None else ""
                        if ag.status in SW_ACTIVE or ag.status == "queued":
                            ag.status = "stopped"
                            ag.note = f"account '{account_name}' was deleted"
                        ag.add_log(f"account '{account_name}' was permanently deleted")
        except Exception as exc:
            self.event("warn", f"swarm cleanup for deleted account reported: {exc}")

        # Remove the persisted usage/stats entry and the browser profile on disk.
        self._remove_usage_account(account_id)
        try:
            self._remove_account_profile_path(a.profile)
        except Exception as exc:
            self.event("warn", f"account '{account_name}' profile cleanup reported: {exc}")

        # Persist once more after the live cleanup so no stale account ID can be written
        # back by a concurrent save callback.
        with self.lock:
            self.cfg["accounts"] = [x.to_cfg() for x in self.accounts]
            self.cfg["routing"] = self.routing
            self.cfg["project_accounts"] = self.project_accounts
            save_config(self.cfg)
        self.event("warn", f"account '{account_name}' permanently deleted")

    def restore_account(self, a: Account, start: bool = False) -> None:
        """Legacy API compatibility: deleted accounts are no longer restorable."""
        del start
        raise ValueError("deleted accounts are permanent and cannot be restored; add the account again")

    def rename(self, a: Account, name: str) -> None:
        name = (name or "").strip()[:40]
        if not name:
            raise ValueError("name is empty")
        a.name = name
        self._save()

    def set_enabled(self, a: Account, on: bool) -> None:
        a.enabled = bool(on)
        self._save()
        self.event("info", f"account '{a.name}' {'enabled' if on else 'disabled'}")
        self.restart_account(a)

    def set_headed(self, a: Account, on: bool) -> None:
        a.headed = bool(on)
        self._save()
        self.event("info", f"account '{a.name}': browser window {'shown' if on else 'hidden'} "
                           "(its open chats restart with the full history)")
        self.restart_account(a)

    def login(self, a: Account) -> None:
        pname=(_PROVIDER.get(a.provider) or {}).get("name", "DeepSeek")
        self.event("info", f"account '{a.name}': log in to {pname} in the window that opens")
        a.enabled = True
        self._save()
        self.restart_account(a, force_login=True)

    def move(self, a: Account, delta: int) -> None:
        with self.lock:
            i = self.accounts.index(a)
            j = max(0, min(len(self.accounts) - 1, i + (1 if delta > 0 else -1)))
            self.accounts.insert(j, self.accounts.pop(i))
            self._save()

    def clear_cooldown(self, a: Optional[Account] = None) -> None:
        for x in ([a] if a else self.accounts):
            x.cooldown_until, x.rl_streak, x.fail_streak = 0.0, 0, 0

    def set_pinned(self, a: Account) -> None:
        self.routing["strategy"] = "pinned"
        self.routing["pinned"] = a.id
        self._save()
        self.event("ok", f"switched to '{a.name}' (pinned)")

    def set_routing(self, **kw: Any) -> None:
        r = self.routing
        if kw.get("strategy") in STRATEGIES:
            r["strategy"] = kw["strategy"]
        if kw.get("auto_failover") is not None:
            r["auto_failover"] = bool(kw["auto_failover"])
        for k in ("rotate_requests", "rotate_minutes"):
            if kw.get(k) is not None:
                r[k] = max(0, min(100000, int(kw[k])))
        if kw.get("pinned") and self.get_by_id(kw["pinned"]):
            r["pinned"] = kw["pinned"]
        if kw.get("smart_routing") is not None:
            r["smart_routing"] = bool(kw["smart_routing"])
        for k in ("tier_strong", "tier_balanced"):
            if kw.get(k) is not None:
                r[k] = max(1, min(5, int(kw[k])))
        self._save()
        self.event("info", f"routing: {r['strategy']}, failover={'on' if r['auto_failover'] else 'off'}, "
                           f"rotate every {r['rotate_requests']} msgs / {r['rotate_minutes']} min")

    # ---- routing -------------------------------------------------------------------

    @staticmethod
    def _need(req: Any) -> str:
        """strong | balanced | fast - from the swarm role, else from the model name Claude Code asked for."""
        role = getattr(req, "role", None) if req is not None else None
        if role in ("planner", "reviewer", "strong"):
            return "strong"
        if role == "fast":
            return "fast"
        m = (getattr(req, "model", "") or "").lower() if req is not None else ""
        if (req is not None and getattr(req, "side", False)) or "haiku" in m:
            return "fast"
        return "strong" if "opus" in m else "balanced"

    def _tier_filter(self, elig: List[Account], need: str) -> List[Account]:
        tiers = sorted({a.tier for a in elig})
        if len(tiers) <= 1:
            return elig
        if need == "strong":
            t = tiers[-1]                                    # the most capable account that is available
        elif need == "fast":
            t = tiers[0]                                     # the cheapest one
        else:
            ok = [x for x in tiers if x >= int(self.routing.get("tier_balanced", 3))]
            t = ok[0] if ok else tiers[-1]                   # the cheapest one that is good enough
        return [a for a in elig if a.tier == t]

    def _needs_rotation(self, a: Account) -> bool:
        rr = int(self.routing.get("rotate_requests") or 0)
        rm = int(self.routing.get("rotate_minutes") or 0)
        if rr and a.stint_reqs >= rr:
            return True
        return bool(rm and a.stint_reqs > 0 and time.time() - a.stint_start >= rm * 60)

    def has_alternative(self, a: Account) -> bool:
        now = time.time()
        return any(x is not a and x.usable(now) for x in self.accounts)

    def pick(self, req: Any, exclude: Any = ()) -> Tuple[Optional[Account], str]:
        now = time.time()
        accts = list(self.accounts)
        pin = getattr(req, "pin", None) if req is not None else None
        if pin:                                   # /a/<account>/... endpoint: exactly that account, no fail-over
            pa = self.get(pin)
            if pa is None:
                return None, f"unknown account '{pin}'"
            if pa.enabled and pa.status == "ready" and pa.worker is not None and pa.worker.ok \
                    and pa.id not in exclude:
                return pa, "account endpoint"
            return None, f"account '{pa.name}' is not ready"
        elig = [a for a in accts if a.usable(now) and a.id not in exclude]
        project = claude_cwd(req) if req is not None and not getattr(req, "side", False) else ""
        assigned = self.project_accounts_for(project) if project else []
        if assigned:
            elig = [a for a in elig if a.id in assigned]
            if not elig:
                return None, f"assigned project account(s) not ready: {', '.join(assigned)}"
        if not elig:
            enabled = [a for a in accts if a.enabled]
            if (len(enabled) == 1 and enabled[0].status == "ready" and enabled[0].worker is not None
                    and enabled[0].worker.ok and enabled[0].id not in exclude):
                return enabled[0], "only account"
            configured = sorted({a.provider for a in accts if a.enabled and not a.deleted})
            providers = ", ".join(configured) if configured else "none"
            return None, f"no selected provider account is ready (configured: {providers})"
        elig_all = list(elig)
        if self.routing.get("smart_routing", True):
            elig = self._tier_filter(elig, self._need(req))
        strat = self.routing.get("strategy", "balanced")
        why = strat
        if strat == "pinned":
            p = self.get_by_id(self.routing.get("pinned"))
            if p is not None and p in elig_all:
                return p, "pinned"
            if not self.routing.get("auto_failover"):
                return None, "the pinned account is unavailable and failover is off"
            strat, why = "failover", "failover (pinned account unavailable)"
        owner: Optional[Account] = None
        if req is not None and not getattr(req, "side", False):
            best = -1
            for a in elig:
                eng = a.worker.engine if a.worker else None
                try:
                    n = eng.owns(req) if eng is not None else -1
                except Exception:
                    n = -1
                if n > best:
                    best, owner = n, a
            if best < 0:
                owner = None
        cands = elig
        if owner is not None:
            if strat in ("balanced", "round_robin") and len(elig) > 1 and self._needs_rotation(owner):
                cands, why = [a for a in elig if a is not owner], "rotation"
            else:
                return owner, "continuation"
        if strat == "failover" or why.startswith("failover"):
            return cands[0], why
        if strat == "round_robin":
            idx = {a.id: i for i, a in enumerate(accts)}
            after = [a for a in cands if idx[a.id] > self._rr]
            a = (after or cands)[0]
            self._rr = idx[a.id]
            return a, why
        a = min(cands, key=lambda x: (x.inflight / max(1, x.max_parallel) * 10_000_000 + x.stats.recent_tokens(600), x.stats.last_used))
        return a, why

    def _route_note(self, a: Account, why: str, req: Any) -> None:
        if why != "continuation":
            a.stint_reqs, a.stint_start = 0, time.time()
        a.stint_reqs += 1
        if req is not None and (getattr(req, "side", False) or getattr(req, "pin", None)):
            return
        self.current = a.id
        if self._last_route != a.id:
            prev = self.get_by_id(self._last_route)
            self._last_route = a.id
            self.event("info", f"now using '{a.name}' ({why})" + (f", was '{prev.name}'" if prev else ""))

    def _failed(self, a: Account, exc: BridgeError) -> None:
        now = time.time()
        k = exc.kind
        if k == "login":
            a.set_status("login_needed", str(exc)[:200])
            self.event("error", f"'{a.name}': login expired - click Login on the dashboard")
        elif k == "rate_limit":
            a.rl_streak += 1
            cool = min(_state().COOLDOWN_MAX, _state().COOLDOWN_BASE * 2 ** (a.rl_streak - 1))
            a.cooldown_until, a.cooldown_reason, a.cool_notified = now + cool, "rate limit / server busy", False
            self.event("warn", f"'{a.name}' is busy / rate limited -> cooling down {fmt_dur(cool)}")
        elif k in ("upstream", "timeout", "empty"):
            a.fail_streak += 1
            if a.fail_streak >= 2:
                cool = min(300, 30 * a.fail_streak)
                a.cooldown_until, a.cooldown_reason, a.cool_notified = now + cool, "repeated errors", False
                self.event("warn", f"'{a.name}' failed {a.fail_streak}x -> resting {fmt_dur(cool)}: {str(exc)[:80]}")

    def _succeeded(self, a: Account) -> None:
        a.rl_streak = max(0, a.rl_streak - 1)
        a.fail_streak = 0

    def _can_wait(self) -> bool:
        now = time.time()
        return any(a.enabled and (a.status == "starting" or (a.status == "ready" and a.cooldown_until > now))
                   for a in self.accounts)

    def dispatch(self, req: Any, cancel: Optional[threading.Event], on_partial: Any,
                 streamed: Optional[Callable[[], bool]] = None, priority: int = PRIORITY_MAIN
                 ) -> concurrent.futures.Future:
        """Run `req` on the best account; on failure move on to the next one (if nothing was streamed yet)."""
        out: concurrent.futures.Future = concurrent.futures.Future()

        def run() -> None:
            tried: List[str] = []
            last: Optional[BaseException] = None
            attempts, max_attempts = 0, 2 * len(self.accounts) + 2
            wait_end = time.time() + _state().ACCOUNT_WAIT_SECONDS
            try:
                while True:
                    if cancel is not None and cancel.is_set():
                        raise BridgeCancelled()
                    a, why = self.pick(req, tried)
                    if a is None:
                        if time.time() < wait_end and self._can_wait():
                            tried.clear()
                            time.sleep(1.0)
                            continue
                        raise last or BridgeError(f"no AI account is available ({why})", "upstream")
                    attempts += 1
                    self._route_note(a, why, req)
                    with self.lock:
                        a.inflight += 1
                    try:
                        fut = a.worker.submit(lambda eng: eng.process(req, cancel, on_partial), priority, cancel)
                        res = fut.result()
                        try:
                            res.account, res.tier = a.name, a.tier
                        except Exception:
                            pass
                        self._succeeded(a)
                        out.set_result(res)
                        return
                    except BridgeCancelled:
                        if cancel is not None and cancel.is_set():
                            raise
                        last = BridgeError(f"account '{a.name}' was stopped", "upstream")
                    except BridgeError as exc:
                        last = exc
                        if exc.kind == "bad_request":
                            raise
                        self._failed(a, exc)
                    except Exception as exc:
                        last = BridgeError(f"{type(exc).__name__}: {exc}", "upstream")
                        self._failed(a, last)
                    finally:
                        with self.lock:
                            a.inflight -= 1
                    if getattr(req, "pin", None):
                        raise last                          # an account endpoint never moves to another account
                    if streamed is not None and streamed():
                        raise last                      # the client already got text: cannot switch silently
                    if attempts >= max_attempts:
                        raise last
                    tried.append(a.id)
                    nxt, _ = self.pick(req, tried)
                    if nxt is not None:
                        self.event("warn", f"request moved from '{a.name}' to '{nxt.name}'")
            except BaseException as exc:
                out.set_exception(exc if isinstance(exc, Exception) else BridgeError(repr(exc), "upstream"))

        state_thread(target=run, daemon=True, name="DeepSeekDispatch").start()
        return out

    def submit(self, fn: Callable[[Engine], Any], priority: int = PRIORITY_MAIN,
               cancel: Optional[threading.Event] = None) -> concurrent.futures.Future:
        a, why = self.pick(None, ())
        if a is None:
            fut: concurrent.futures.Future = concurrent.futures.Future()
            fut.set_exception(BridgeError(f"no AI account is available ({why})", "upstream"))
            return fut
        return a.worker.submit(fn, priority, cancel)

    # ---- watchdog ------------------------------------------------------------------

    def _watchdog(self) -> None:
        while not self._stop.wait(5.0):
            try:
                now = time.time()
                for a in list(self.accounts):
                    if not a.cool_notified and a.cooldown_until <= now:
                        a.cool_notified = True
                        self.event("ok", f"'{a.name}' is available again")
                    w = a.worker
                    if (a.enabled and w is not None and not w.stopping and not w._thread.is_alive()
                            and a.status not in ("starting", "login", "disabled")
                            and not a.op_lock.locked()):
                        a.restarts = [t for t in a.restarts if now - t < 600]
                        if len(a.restarts) < 3:
                            a.restarts.append(now)
                            self.event("warn", f"worker of '{a.name}' died - restarting it")
                            self.restart_account(a)
                if now - self._usage_saved > 30:
                    self._usage_saved = now
                    self.save_usage()
            except Exception:
                traceback.print_exc()

    # ---- views ---------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        accts: List[Dict[str, Any]] = []
        tot = {"req": 0, "in_tok": 0, "out_tok": 0, "err": 0, "rate_limits": 0, "today_in": 0, "today_out": 0, "cost": 0.0}
        for i, a in enumerate(list(self.accounts)):
            s = a.stats.snapshot(now)
            for k in tot:
                tot[k] += s.get(k, 0)
            eng = a.worker.engine if a.worker else None
            try:
                chats = len(eng.convs) if eng is not None else 0
            except Exception:
                chats = 0
            accts.append({"id": a.id, "name": a.name, "idx": i + 1, "enabled": a.enabled, "deleted": a.deleted, "headed": a.headed,
                          "state": a.state(now), "status_err": a.status_err if a.status in ("error", "login_needed") else "",
                          "state_for": round(now - a.status_since, 1),
                          "cooldown_left": max(0, int(a.cooldown_until - now)), "cooldown_reason": a.cooldown_reason,
                          "inflight": a.inflight, "chats": chats, "logged_in": a.logged_in,
                          "kind": a.kind, "provider": a.provider, "model": a.model, "tier": a.tier,
                          "max_parallel": a.max_parallel, "cost": round(a.cost(), 4), "budget": a.budget,
                          "price_in": a.price_in, "price_out": a.price_out, "base_url": a.base_url,
                          "key_hint": ("••••" + a.api_key[-4:]) if a.api_key else "",
                          "current": a.id == self.current, "pinned": a.id == self.routing.get("pinned"),
                          "stint_reqs": a.stint_reqs, "stats": s})
        tot["cost"] = round(sum(a["cost"] for a in accts), 4)
        ready = sum(1 for a in accts if a["state"] in ("ready", "busy"))
        return {"version": VERSION, "now": now, "uptime": round(now - self.started, 1),
                "settings": dict(self.routing), "totals": tot, "current": self.current, "ready": ready,
                "accounts": accts, "capacity": self.capacity(), "resources": self.governor.snapshot(self),
                "parallel_mode": _state().PARALLEL_MODE, "events": list(self.events)[-60:][::-1]}

    def status_text(self) -> str:
        snap = self.snapshot()
        st = snap["settings"]
        lines = [f"DeepSeek accounts - strategy: {st['strategy']}"
                 f"{' (pinned: ' + (self.get_by_id(st.get('pinned')).name if self.get_by_id(st.get('pinned')) else '?') + ')' if st['strategy'] == 'pinned' else ''}"
                 f", failover {'on' if st['auto_failover'] else 'off'}"]
        for a in snap["accounts"]:
            s = a["stats"]
            state = a["state"] + (f" {a['cooldown_left']}s" if a["state"] == "cooldown" else "")
            lines.append(f"{'>' if a['current'] else ' '} {a['idx']}. {a['name']} [{state}] T{a['tier']}"
                         f"{' ' + a['model'] if a['kind'] != 'web' else ''}  "
                         f"in {fmt_tok(s['in_tok'])} / out {fmt_tok(s['out_tok'])} tok (est.)  "
                         f"{s['req']} msgs  use {fmt_dur(s['streak_s'])}{' (live)' if s['streak_live'] else ''}")
        t = snap["totals"]
        lines.append(f"total: {t['req']} msgs, in {fmt_tok(t['in_tok'])} / out {fmt_tok(t['out_tok'])} tok (est.)")
        return "\n".join(lines)

    def describe_all(self) -> List[str]:
        out: List[str] = []
        for a in self.accounts:
            eng = a.worker.engine if a.worker else None
            if eng is not None:
                try:
                    out += [f"[{a.name}] {x}" for x in eng.describe()]
                except Exception:
                    pass
        return out

    # ---- text commands (/ds ..., terminal, --ctl) -------------------------------------

    HELP = ("commands: status | next | prev | use <n|name> | auto | rr | failover | on <n> | off <n> | add <name> | "
            "test [n] | login <n> | show <n> | hide <n> | restart <n> | reset [n] | purge [n] | clear | usage-reset | "
            "settings | set <NAME> <value> | tier <acct> <1-5> | add-api <provider> <key> [model] | url | key | panel [page] | swarm <goal|status|agents N|stop|apply> | help")

    def run_command(self, text: str, secret: bool = False, ctx: Optional[Dict[str, Any]] = None) -> str:
        parts = (text or "").strip().split()
        cmd = parts[0].lower().lstrip("/") if parts else "status"
        arg = " ".join(parts[1:])
        try:
            if cmd in ("status", "list", "ls", "s"):
                return self.status_text()
            if cmd in ("help", "?"):
                return self.HELP
            if cmd in ("next", "prev", "n", "p"):
                step = 1 if cmd in ("next", "n") else -1
                accts = self.accounts
                cur = self.get_by_id(self.routing.get("pinned")) if self.routing["strategy"] == "pinned" \
                    else self.get_by_id(self.current)
                i = accts.index(cur) if cur in accts else -1
                now = time.time()
                for k in range(1, len(accts) + 1):
                    c = accts[(i + step * k) % len(accts)]
                    if c.usable(now):
                        self.set_pinned(c)
                        return f"Switched to '{c.name}'. The next message continues there (full history is re-sent).\n" \
                               f"Use 'auto' to return to load balancing."
                return "No other account is ready right now."
            if cmd == "use":
                a = self.get(arg)
                if a is None:
                    return f"Unknown account '{arg}'.\n" + self.status_text()
                self.set_pinned(a)
                return f"Switched to '{a.name}' (pinned)."
            if cmd in ("auto", "balanced", "balance"):
                self.set_routing(strategy="balanced")
                return "Load balancing on: new chats go to the least-used account; long chats rotate."
            if cmd in ("rr", "roundrobin", "round_robin"):
                self.set_routing(strategy="round_robin")
                return "Round-robin on."
            if cmd in ("failover", "priority"):
                self.set_routing(strategy="failover")
                return "Failover mode: the first healthy account in the list is used."
            if cmd in ("on", "off", "enable", "disable"):
                a = self.get(arg)
                if a is None:
                    return f"Unknown account '{arg}'."
                self.set_enabled(a, cmd in ("on", "enable"))
                return f"'{a.name}' {'enabled' if cmd in ('on', 'enable') else 'disabled'}."
            if cmd == "add":
                a = self.add_account(arg)
                return f"Account '{a.name}' added. Log in to DeepSeek in the browser window that just opened."
            if cmd in ("settings", "config"):
                return "\n".join(f"{v['name']} = {v['value']}" + (f"   (default {v['default']})" if v["value"] != v["default"] else "")
                                 for v in settings_view(self.cfg))
            if cmd == "set":
                p = arg.split(None, 1)
                name = next((k for k in _SCHEMA if p and k.lower() == p[0].lower()), None)
                if not name or len(p) < 2:
                    return "Usage: set <SETTING_NAME> <value>   (list them with:  settings)"
                need = settings_set(self.cfg, {name: p[1].strip()}, [])
                return f"{name} = {_setting_get(name, self.cfg)}" + ("   (takes effect after a restart)" if need else "")
            if cmd == "tier":
                p = arg.rsplit(None, 1)
                a = self.get(p[0]) if len(p) == 2 else None
                if a is None or not p[1].isdigit():
                    return "Usage: tier <account> <1-5>"
                self.update_account(a, {"tier": int(p[1])})
                return f"'{a.name}' is now tier {a.tier} ({TIER_NAMES.get(a.tier, '')})."
            if cmd in ("add-api", "addapi"):
                if not secret:
                    return ("Never type an API key into a chat - the model would see it. Add the account in the panel "
                            "(Add account), or use the panel Console:  add-api <grok|claude|openai|openrouter> <key> [model]")
                p = arg.split()
                if len(p) < 2:
                    return "Usage: add-api <grok|claude|openai|openrouter|deepseek_api> <key> [model]"
                a = self.add_api_account(p[0], "", "", p[1], p[2] if len(p) > 2 else "")
                return f"Added '{a.name}' (tier {a.tier}, model {a.model}). Test it from the panel."
            if cmd in ("panel", "dash", "dashboard"):
                page = arg.split()[0].lower() if arg else ""
                return f"Panel opened in your browser: {open_panel(self, page)}"
            if cmd == "swarm":
                return self.swarm.command(arg, ctx or {})
            if cmd == "clear":
                self.clear_cooldown()
                return "All cooldowns cleared."
            if cmd in ("url", "base"):
                return f"http://127.0.0.1:{self.cfg.get('port')}   (per account: .../a/<account-id>)"
            if cmd == "key":
                return str(self.cfg.get("api_key")) if secret else "The API key is not shown inside chats - open the panel (Connect page)."
            if cmd in ("usage-reset", "usage_reset"):
                for x in self.accounts:
                    x.stats.reset()
                return "Usage statistics were reset."
            if cmd in ("test", "login", "show", "hide", "restart", "reset", "purge"):
                targets = [self.get(arg)] if arg else ([] if cmd in ("login", "show", "hide", "restart") else
                                                        [a for a in self.accounts if a.enabled and a.status == "ready"])
                if arg and targets[0] is None:
                    return f"Unknown account '{arg}'."
                if not targets:
                    return f"Usage: {cmd} <account>"
                lines = []
                for a in targets:
                    r = dash_action(self, {"reset": "reset_convs"}.get(cmd, cmd), {"id": a.id})
                    lines.append(f"{a.name}: " + (f"OK in {r['seconds']}s ({r['reply']})" if cmd == "test" and r.get("ok")
                                                  else r.get("error", "done")))
                return "\n".join(lines)
            return f"Unknown command '{cmd}'.\n{self.HELP}"
        except Exception as exc:
            return f"Error: {exc}"


# ============================================================================
# Dashboard (served by the same local HTTP server at /dash)
# ============================================================================

def probe_models(kind: str, base_url: str, api_key: str) -> List[str]:
    """Asks the provider which models this key can use (done here, server-side: no CORS, key never leaves the PC)."""
    if not re.match(r"^https?://", base_url or ""):
        raise ValueError("enter the base URL first")
    if not api_key:
        raise ValueError("enter the API key first")
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"} if kind == "anthropic" \
        else {"authorization": "Bearer " + api_key}
    r = http_json("GET", api_base(base_url) + "/models", headers, None, 30)
    if r["status"] != 200:
        raise ValueError(str(_api_error(r["status"], r["data"])))
    try:
        j = json.loads(r["data"].decode("utf-8", "replace"))
        ids = sorted({str(m.get("id")) for m in (j.get("data") or j.get("models") or []) if isinstance(m, dict) and m.get("id")})
    except Exception:
        raise ValueError("the provider did not return a model list")
    return ids[:300]


def remember_project(cfg: Dict[str, Any], project: Any, *, persist: bool = True) -> Path:
    """Make the selected project the bridge-wide active project and remember it.

    This is deliberately separate from Claude Code's process cwd: the dashboard and
    the swarm page need the same canonical project context as the launcher.
    """
    raw = str(project or "").strip().strip('"').strip("'")
    if not raw:
        raise ValueError("project folder is required")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"not a folder: {path}")
    value = str(path)
    cfg["project_dir"] = value
    recent = [str(x) for x in (cfg.get("recent_projects") or []) if str(x) != value]
    cfg["recent_projects"] = [value, *recent][:8]
    if persist:
        save_config(cfg)
    return path


def set_project_context(pool: Any, project: Any) -> Dict[str, Any]:
    """Update the running bridge's canonical project context.

    Used when a second launcher process starts while the bridge is already alive;
    the running bridge, not the short-lived launcher process, is the source of truth
    for the dashboard.
    """
    path = remember_project(pool.cfg, project, persist=True)
    try:
        pool.event("info", f"active project changed to {path}")
    except Exception:
        pass
    emit_dash_event("project", {"project": str(path)})
    return {"ok": True, "project": str(path)}



def _safe_upload_name(name: str) -> str:
    name = Path(str(name or "attachment")).name
    name = re.sub(r"[^A-Za-z0-9._()\- ]+", "_", name).strip(" .")
    return name[:180] or "attachment"


def store_swarm_attachment(name: str, mime: str, data: bytes) -> Dict[str, Any]:
    if len(data) > _state().ATTACH_MAX_BYTES:
        raise ValueError(f"attachment exceeds {_state().ATTACH_MAX_BYTES:,} bytes")
    _state().SWARM_ATTACH_DIR.mkdir(parents=True, exist_ok=True)
    aid = uuid.uuid4().hex[:16]
    safe = _safe_upload_name(name)
    path = _state().SWARM_ATTACH_DIR / f"{aid}-{safe}"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    meta = {"id": aid, "name": safe, "mime": (mime or "application/octet-stream")[:120],
            "size": len(data), "path": str(path), "created": time.time()}
    (_state().SWARM_ATTACH_DIR / f"{aid}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    emit_dash_event("attachment", {k: meta[k] for k in ("id", "name", "mime", "size")})
    return meta


def get_swarm_attachment(aid: str) -> Dict[str, Any]:
    safe = re.sub(r"[^0-9a-f]", "", str(aid).lower())[:32]
    if not safe:
        raise ValueError("invalid attachment id")
    meta_path = _state().SWARM_ATTACH_DIR / f"{safe}.json"
    if not meta_path.is_file():
        raise ValueError("attachment not found or expired")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict) or meta.get("id") != safe:
        raise ValueError("invalid attachment metadata")
    path = Path(str(meta.get("path") or ""))
    if not path.is_file() or path.parent.resolve() != _state().SWARM_ATTACH_DIR.resolve():
        raise ValueError("attachment storage is invalid")
    return meta


def cleanup_swarm_attachments(max_age_days: int = 7) -> int:
    cutoff = time.time() - max_age_days * 86400
    removed = 0
    try:
        for meta_path in _state().SWARM_ATTACH_DIR.glob("*.json"):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if float(meta.get("created", 0)) >= cutoff:
                    continue
                data_path = Path(str(meta.get("path") or ""))
                if data_path.is_file() and data_path.parent.resolve() == _state().SWARM_ATTACH_DIR.resolve():
                    data_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
                removed += 1
            except Exception as exc:
                _warn_once("attach_cleanup:" + meta_path.name, f"attachment cleanup failed for {meta_path.name}: {exc}")
    except Exception as exc:
        _warn_once("attach_cleanup_root", f"attachment cleanup failed: {exc}")
    return removed


def dash_action(pool: Any, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if pool is None or not hasattr(pool, "snapshot"):
        raise ValueError("the account pool is not available")

    def acct() -> Account:
        a = pool.get(str(data.get("id", "")))
        if a is None:
            raise ValueError("unknown account")
        return a

    def web_acct() -> Account:
        a = acct()
        if a.kind != "web":
            raise ValueError("this only applies to DeepSeek website accounts")
        return a

    def on_worker(fn: Callable[[Engine], Any], timeout: float = 180) -> Any:
        a = acct()
        if a.worker is None or not a.worker.ok:
            raise ValueError("this account is not running")
        return a.worker.submit(fn, _state().PRIORITY_MAIN).result(timeout=timeout)

    if action == "add":
        return {"ok": True, "id": pool.add_account(str(data.get("name", ""))).id}
    if action == "add_web":
        a=pool.add_web_account(str(data.get("provider", "")), str(data.get("name", "")),
                               int(data.get("tier") or 0), bool(data.get("headed", True)), True)
        return {"ok": True, "id": a.id}
    if action == "remove":
        # Dashboard deletion is always permanent. Keep accepting the old `purge` field
        # from older clients, but the server no longer has a reversible delete mode.
        pool.remove_account(acct(), bool(data.get("purge", False)))
    elif action == "restore":
        pool.restore_account(acct(), start=bool(data.get("start", False)))
    elif action == "rename":
        pool.rename(acct(), str(data.get("name", "")))
    elif action == "enable":
        pool.set_enabled(acct(), True)
    elif action == "disable":
        pool.set_enabled(acct(), False)
    elif action == "login":
        pool.login(web_acct())
    elif action == "show":
        pool.set_headed(web_acct(), True)
    elif action == "hide":
        pool.set_headed(web_acct(), False)
    elif action == "add_api":
        a = pool.add_api_account(str(data.get("provider", "custom_openai")), str(data.get("name", "")),
                                 str(data.get("base_url", "")), str(data.get("api_key", "")), str(data.get("model", "")),
                                 int(data.get("tier") or 0), int(data.get("max_parallel") or 4),
                                 float(data.get("price_in") or 0), float(data.get("price_out") or 0),
                                 float(data.get("budget") or 0))
        return {"ok": True, "id": a.id}
    elif action == "update_account":
        pool.update_account(acct(), data)
    elif action == "models_probe":
        return {"ok": True, "models": probe_models(str(data.get("kind", "openai")), str(data.get("base_url", "")),
                                                   str(data.get("api_key", "")))}
    elif action == "restart":
        pool.restart_account(acct())
    elif action == "use":
        pool.set_pinned(acct())
    elif action == "move":
        pool.move(acct(), int(data.get("dir", 1)))
    elif action == "clear_cooldown":
        pool.clear_cooldown(acct())
    elif action == "settings":
        pool.set_routing(strategy=data.get("strategy"), auto_failover=data.get("auto_failover"),
                         rotate_requests=data.get("rotate_requests"), rotate_minutes=data.get("rotate_minutes"),
                         smart_routing=data.get("smart_routing"), tier_strong=data.get("tier_strong"),
                         tier_balanced=data.get("tier_balanced"))
    elif action == "command":
        return {"ok": True, "text": pool.run_command(str(data.get("text", "")), secret=True)}
    elif action == "project_accounts":
        project=str(data.get("project", "")).strip()
        ids=[str(x) for x in (data.get("account_ids") or [])][:32]
        chosen=pool.set_project_accounts(project, ids)
        return {"ok": True, "project": str(Path(project).expanduser().resolve()), "account_ids": chosen}
    elif action == "settings_set":
        vals = data.get("values") if isinstance(data.get("values"), dict) else {}
        resets = [str(x) for x in (data.get("reset") or [])]
        restart = settings_set(pool.cfg, vals, resets)
        changed = list(vals) + resets
        pool.event("info", f"settings saved ({', '.join(changed) or 'no change'})")
        emit_dash_event("settings", {"changed": changed, "restart": restart,
                                       "settings": settings_view(pool.cfg),
                                       "project": pool.cfg.get("project_dir") or str(SCRIPT_DIR)})
        return {"ok": True, "restart": restart, "settings": settings_view(pool.cfg)}
    elif action == "launch":
        return launch_claude_from_panel(pool, data)
    elif action == "project_context":
        return set_project_context(pool, data.get("project", ""))
    elif action == "swarm_prompt_improve":
        original = str(data.get("prompt", "")).strip()
        current = str(data.get("current", "")).strip()
        custom = str(data.get("custom", "")).strip()
        if not original:
            raise ValueError("enter a prompt to improve")
        instruction = (
            "Improve the following software-engineering agent task prompt. Preserve the user's original intent, "
            "requested outcome, scope, technologies, constraints and desired behavior. Make it clearer, more "
            "actionable and more complete. Add useful acceptance criteria, verification steps, edge cases and "
            "implementation clarity only when they naturally follow from the intent. NEVER invent a different goal, "
            "remove a requested capability, or silently broaden the scope. Return ONLY the improved prompt, no preamble.\n\n"
            f"ORIGINAL USER PROMPT:\n{original}\n"
        )
        if current:
            instruction += f"\nCURRENT AI-IMPROVED VERSION (preserve it unless the custom notes require a change):\n{current}\n"
        if custom:
            instruction += f"\nADDITIONAL CUSTOMIZATION / NOTES FROM USER:\n{custom}\n"
        improved = pool.ask(instruction, role="planner", max_tokens=6000, tag="panel.prompt-improve", timeout=900).strip()
        if not improved:
            raise ValueError("the AI did not return an improved prompt")
        emit_dash_event("prompt_improved", {"original": original[:400], "chars": len(improved)})
        return {"ok": True, "original": original, "current": current, "improved": improved, "custom": custom}
    elif action == "fs":
        return {"ok": True, **fs_list(str(data.get("path", "")))}
    elif action == "mkdir":
        base = Path(str(data.get("path", ""))).expanduser()
        nm = re.sub(r'[\\/:*?"<>|]+', "_", str(data.get("name", "")).strip())
        if not base.is_dir() or not nm or nm in (".", ".."):
            raise ValueError("invalid folder")
        (base / nm).mkdir(exist_ok=True)
        return {"ok": True, "path": str(base / nm)}
    elif action == "task":
        return run_task(pool, str(data.get("name", "")))
    elif action == "swarm_start":
        swarm_project = str(data.get("project", ""))
        attachment_ids = [str(x) for x in (data.get("attachments") or [])][:_state().ATTACH_MAX_FILES]
        for aid in attachment_ids:
            get_swarm_attachment(aid)
        account_ids=[str(x) for x in (data.get("account_ids") or [])][:32]
        run = pool.swarm.start(str(data.get("goal", "")), swarm_project, data.get("agents", "auto"),
                               str(data.get("verify", "auto")), str(data.get("review", "")), str(data.get("mode", "")),
                               str(data.get("tasks", "")), bool(data.get("strict")), bool(data.get("init_git", True)),
                               attachments=attachment_ids, account_ids=account_ids)
        remember_project(pool.cfg, swarm_project, persist=True)
        pool.event("info", f"swarm project selected: {run.project}")
        emit_dash_event("swarm_started", {"id": run.id, "project": str(run.project), "attachments": attachment_ids,
                                             "account_ids": list(run.opts.get("account_ids") or [])})
        return {"ok": True, "id": run.id, "project": run.project, "attachments": attachment_ids,
                "account_ids": list(run.opts.get("account_ids") or [])}
    elif action in ("swarm_stop", "swarm_agents", "swarm_apply", "swarm_cleanup"):
        run = pool.swarm.runs.get(str(data.get("run", "")))
        if run is None:
            raise ValueError("unknown run")
        if action == "swarm_stop":
            pool.swarm.stop(run)
        elif action == "swarm_agents":
            pool.swarm.set_agents(run, int(data.get("n", 1)))
        elif action == "swarm_apply":
            return {"ok": True, "text": pool.swarm.apply(run)}
        else:
            pool.swarm.cleanup(run)
    elif action == "bridge":
        return bridge_control(pool, str(data.get("action", "")))
    elif action == "reset_usage":
        for x in pool.accounts:
            x.stats.reset()
    elif action == "test":
        try:
            return {"ok": True, **on_worker(lambda e: e.ping(), 150)}
        except (BridgeError, concurrent.futures.TimeoutError) as exc:
            return {"ok": False, "error": str(exc) or "timeout"}
    elif action == "reset_convs":
        return {"ok": True, "dropped": on_worker(lambda e: e.reset_all(), 60)}
    elif action == "purge":
        return {"ok": True, "deleted": on_worker(lambda e: e.purge_all(), 180)}
    else:
        raise ValueError(f"unknown action '{action}'")
    return {"ok": True}


# ============================================================================
# Settings exposed in the web panel (everything that used to need env variables / flags)
# ============================================================================


# name, kind, group, English label, Persian label, min (or choices), max, when it takes effect
SETTINGS_SCHEMA: Tuple[Tuple[Any, ...], ...] = (
    ("permission_mode", "choice", "claude", "Default Claude Code mode", "حالت پیش‌فرض Claude Code", ["safe", "ask", "auto"], 0, "launch"),
    ("KEEP_GOING", "bool", "claude", "Autonomous mode: do not let Claude stop before PROGRESS.md says done",
     "حالت خودکار: Claude قبل از پایان کار متوقف نشود", 0, 0, "launch"),
    ("KEEP_GOING_MAX", "int", "claude", "Autonomous mode: maximum forced continues", "حداکثر تعداد ادامه اجباری", 1, 5000, "launch"),
    ("STALL_TIMEOUT", "int", "rel", "Give up when DeepSeek shows no progress for (s)", "توقف اگر دیپ‌سیک این مدت پیشرفتی نداشت (ثانیه)", 30, 7200, "live"),
    ("MAX_REPLY_SECONDS", "int", "rel", "Longest allowed single reply (s)", "بیشترین زمان یک پاسخ (ثانیه)", 60, 86400, "live"),
    ("MAX_RETRIES", "int", "rel", "Retries on the same account before giving up", "تعداد تلاش مجدد روی همان اکانت", 0, 20, "live"),
    ("RETRY_BACKOFF_MAX", "int", "rel", "Longest wait between retries (s)", "بیشترین فاصله بین تلاش‌ها (ثانیه)", 1, 600, "live"),
    ("COOLDOWN_BASE", "int", "rel", "First rest of a busy / limited account (s)", "اولین استراحت اکانت شلوغ/محدود (ثانیه)", 5, 3600, "live"),
    ("COOLDOWN_MAX", "int", "rel", "Longest rest of an account (s)", "بیشترین استراحت اکانت (ثانیه)", 10, 86400, "live"),
    ("ACCOUNT_WAIT_SECONDS", "int", "rel", "How long a request waits when every account is resting (s)", "مدت انتظار درخواست وقتی همه اکانت‌ها استراحت می‌کنند", 0, 1800, "live"),
    ("ROTATE_CHARS", "int", "ctx", "Start a fresh DeepSeek chat after this many characters", "شروع چت جدید بعد از این تعداد کاراکتر", 50000, 5000000, "live"),
    ("HISTORY_BUDGET_CHARS", "int", "ctx", "History size sent into a new chat (chars)", "حجم تاریخچه در چت جدید (کاراکتر)", 20000, 2000000, "live"),
    ("MAX_PROMPT_CHARS", "int", "ctx", "Hard prompt size limit (chars)", "سقف حجم پیام (کاراکتر)", 50000, 5000000, "live"),
    ("DELTA_BLOCK_LIMIT", "int", "ctx", "Largest single tool result in a follow-up (chars, 0 = unlimited)", "بزرگ‌ترین نتیجه ابزار در پیام بعدی (۰ = نامحدود)", 0, 5000000, "live"),
    ("KEEP_RECENT_MESSAGES_FULL", "int", "ctx", "Recent messages kept in full when compacting", "پیام‌های اخیر که هنگام فشرده‌سازی کامل می‌مانند", 2, 200, "live"),
    ("MAX_TABS", "int", "browser", "Open browser tabs per account", "تعداد تب باز به ازای هر اکانت", 1, 40, "live"),
    ("MAX_KEPT_CONVS", "int", "browser", "Sleeping conversations kept per account", "گفتگوهای خوابیده نگه‌داشته‌شده", 1, 500, "live"),
    ("DELETE_OLD_CHATS", "bool", "browser", "Delete old chats on chat.deepseek.com", "حذف چت‌های قدیمی در سایت دیپ‌سیک", 0, 0, "live"),
    ("HEADLESS_MODE", "choice", "browser", "Browser windows: auto / always hidden / always visible", "پنجره مرورگر: خودکار / همیشه مخفی / همیشه نمایان", ["auto", "1", "0"], 0, "browser"),
    ("THINK_MODE", "bool", "browser", "Native thinking for DeepSeek and ChatGPT (default off)", "تفکر بومی برای DeepSeek و ChatGPT (پیش‌فرض خاموش)", 0, 0, "live"),
    ("PARALLEL_MODE", "choice", "swarm", "Scheduler: serial / light / full / auto", "زمان‌بندی موازی: تک‌به‌تک / سبک / کامل / خودکار", list(PARALLEL_MODES), 0, "live"),
    ("UI_MODE", "choice", "panel", "UI detail level: beginner / pro", "سطح جزئیات رابط: مبتدی / حرفه‌ای", ["beginner", "pro"], 0, "live"),
    ("UI_PERFORMANCE_MODE", "choice", "panel", "Panel performance: automatic / balanced / lightweight / maximum", "کارایی پنل: خودکار / متعادل / سبک / حداکثر", ["auto", "balanced", "light", "max"], 0, "live"),
    ("UPLOAD_TIMEOUT", "int", "browser", "Wait for file uploads up to (s)", "انتظار برای آپلود فایل (ثانیه)", 10, 1800, "live"),
    ("CHARS_PER_TOKEN", "float", "panel", "Characters per token (for the estimates)", "کاراکتر در هر توکن (برای تخمین)", 1.0, 10.0, "live"),
    ("DASH_AUTOOPEN", "bool", "panel", "Open this panel automatically on start", "باز شدن خودکار پنل هنگام اجرا", 0, 0, "launch"),
    ("DEBUG_DIR", "str", "panel", "Folder for debug dumps of every prompt / reply (empty = off)", "پوشه ذخیره پیام‌ها برای عیب‌یابی (خالی = خاموش)", 0, 0, "live"),
    ("SWARM_AGENTS", "int", "swarm", "Parallel agents per swarm run (0 = automatic: what the accounts can serve)", "تعداد ایجنت موازی (۰ = خودکار)", 0, 32, "live"),
    ("SWARM_MAX_AGENTS", "int", "swarm", "Upper limit for the automatic number of agents", "سقف خودکار تعداد ایجنت", 1, 32, "live"),
    ("SWARM_REVIEW", "choice", "swarm", "Review every agent's work (auto = only when a stronger account exists)", "بازبینی کار هر ایجنت", ["auto", "on", "off"], 0, "live"),
    ("SWARM_FIX_ROUNDS", "int", "swarm", "Automatic fix rounds when a check fails", "تعداد دور رفع خطای خودکار", 0, 10, "live"),
    ("SWARM_AGENT_TIMEOUT", "int", "swarm", "Longest time one agent may run (s)", "بیشترین زمان یک ایجنت (ثانیه)", 60, 86400, "live"),
    ("port", "int", "panel", "Local port of the bridge", "پورت محلی bridge", 1, 65535, "bridge"),
)
_SCHEMA = {s[0]: s for s in SETTINGS_SCHEMA}
SETTING_DEFAULTS: Dict[str, Any] = {}


def _setting_get(name: str, cfg: Dict[str, Any]) -> Any:
    if name == "permission_mode":
        return _norm_mode(cfg.get("permission_mode")) or DEFAULT_MODE
    if name == "port":
        return int(cfg.get("port", DEFAULT_PORT))
    return getattr(_state(), name)


def _setting_apply(name: str, value: Any, cfg: Dict[str, Any]) -> None:
    if name in ("permission_mode", "port"):
        cfg[name] = value
    else:
        setattr(_state(), name, value)


def _coerce_setting(spec: Tuple[Any, ...], raw: Any) -> Any:
    name, kind, lo, hi = spec[0], spec[1], spec[5], spec[6]
    if kind == "bool":
        return raw if isinstance(raw, bool) else str(raw).strip().lower() in ("1", "true", "yes", "on")
    if kind == "choice":
        if str(raw) not in lo:
            raise ValueError(f"{name}: must be one of {', '.join(lo)}")
        return str(raw)
    if kind == "str":
        return str(raw or "").strip()
    try:
        v = float(raw)
    except Exception:
        raise ValueError(f"{name}: not a number")
    if not math.isfinite(v) or v < lo or v > hi:
        raise ValueError(f"{name}: must be between {lo} and {hi}")
    return int(v) if kind == "int" else v


def init_settings(cfg: Dict[str, Any]) -> None:
    """Remember the defaults, then apply what the person saved in the panel."""
    for name, *_ in SETTINGS_SCHEMA:
        _state().SETTING_DEFAULTS.setdefault(name, DEFAULT_MODE if name == "permission_mode"
                                    else DEFAULT_PORT if name == "port" else getattr(_state(), name))
    saved = cfg.get("settings")
    if isinstance(saved, dict):
        for name, raw in saved.items():
            spec = _SCHEMA.get(name)
            if spec is None or name in ("permission_mode", "port"):
                continue
            try:
                _setting_apply(name, _coerce_setting(spec, raw), cfg)
            except ValueError:
                pass


def settings_view(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for name, kind, group, en, fa, lo, hi, when in SETTINGS_SCHEMA:
        out.append({"name": name, "kind": kind, "group": group, "en": en, "fa": fa, "when": when,
                    "choices": lo if kind == "choice" else None, "min": lo if kind in ("int", "float") else None,
                    "max": hi if kind in ("int", "float") else None, "value": _setting_get(name, cfg),
                    "default": _state().SETTING_DEFAULTS.get(name)})
    return out


def settings_set(cfg: Dict[str, Any], values: Dict[str, Any], reset: List[str]) -> List[str]:
    """Validates EVERYTHING first, then applies + saves. Returns the names that need a restart to take effect."""
    changes: Dict[str, Any] = {}
    for name, raw in (values or {}).items():
        spec = _SCHEMA.get(name)
        if spec is None:
            raise ValueError(f"unknown setting '{name}'")
        changes[name] = _coerce_setting(spec, raw)
    for name in reset or []:
        if name not in _SCHEMA:
            raise ValueError(f"unknown setting '{name}'")
        changes[name] = _state().SETTING_DEFAULTS.get(name)
    saved = cfg.setdefault("settings", {})
    if "port" in changes:
        # A dashboard settings edit is an explicit persistence action, even when the
        # process was launched with a transient --port / DS_BRIDGE_PORT override.
        _state().PORT_PERSIST_ALLOWED = True
        _state().PERSISTED_PORT = int(changes["port"])
    for name, v in changes.items():
        _setting_apply(name, v, cfg)
        if name in (values or {}):
            if name not in ("permission_mode", "port"):
                saved[name] = v
        else:
            saved.pop(name, None)
            if name in ("permission_mode", "port"):
                cfg.pop(name, None) if name == "permission_mode" else cfg.__setitem__("port", DEFAULT_PORT)
    save_config(cfg)
    return [n for n in changes if _SCHEMA[n][7] in ("bridge", "browser")]


# ============================================================================
# Launcher / folder browser / tasks / bridge control (web replacements for flags + terminal)
# ============================================================================

def _shq(s: str) -> str:
    return shlex.quote(s)


def build_launch(cfg: Dict[str, Any], opts: Dict[str, Any], dry: bool = False) -> Dict[str, Any]:
    project = Path(str(opts.get("project") or cfg.get("project_dir") or SCRIPT_DIR)).expanduser()
    if not project.is_dir():
        raise ValueError(f"not a folder: {project}")
    project = project.resolve()
    mode = _norm_mode(opts.get("mode")) or _norm_mode(cfg.get("permission_mode")) or DEFAULT_MODE
    try:
        extra = shlex.split(str(opts.get("extra") or ""), posix=(os.name != "nt"))
    except ValueError as exc:
        raise ValueError(f"extra options: {exc}")
    for flag, key in (("--continue", "continue"), ("--resume", "resume")):
        if opts.get(key) and flag not in extra:
            extra.append(flag)
    text = str(opts.get("prompt") or "").strip()
    if text:
        if not dry:
            (project / "AUTONOMOUS_PROMPT.md").write_text(text, encoding="utf-8")
        extra.append("Read AUTONOMOUS_PROMPT.md completely (it is the full specification) and execute it now, fully "
                     "autonomously. Never ask me anything. Keep PROGRESS.md up to date; if you are ever unsure where "
                     "you are, re-read AUTONOMOUS_PROMPT.md and PROGRESS.md.")
    exe = shutil.which("claude")
    if not exe:
        raise ValueError("Claude Code is not installed. Use 'Install Claude Code' on this page (needs Node.js).")
    url = f"http://127.0.0.1:{cfg['port']}"
    cmd = [exe, *permission_args(mode, extra), *extra]
    env = claude_env(cfg, url)
    diff = {k: v for k, v in env.items() if os.environ.get(k) != v}
    ps = "\n".join(f'$env:{k}="{v}"' for k, v in diff.items()) + f'\nSet-Location "{project}"\n& ' + \
         " ".join('"' + c.replace('"', '`"') + '"' for c in cmd)
    cm = "\n".join(f"set {k}={v}" for k, v in diff.items()) + f'\ncd /d "{project}"\n' + \
         " ".join('"' + c + '"' for c in cmd)
    sh = "\n".join(f"export {k}={_shq(v)}" for k, v in diff.items()) + f"\ncd {_shq(str(project))}\n" + \
         " ".join(_shq(c) for c in cmd)
    return {"cmd": cmd, "env": env, "diff": diff, "project": str(project), "mode": mode,
            "preview": {"powershell": ps, "cmd": cm, "bash": sh}}


def spawn_terminal(cmd: List[str], cwd: str, diff: Dict[str, str], env: Dict[str, str]) -> str:
    """Open a NEW terminal window running `cmd` (so a non-technical person never types a command)."""
    if os.name == "nt":
        subprocess.Popen(cmd, cwd=cwd, env=env, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        return "a new console window"
    import tempfile
    body = "#!/bin/bash\n" + "".join(f"export {k}={_shq(v)}\n" for k, v in diff.items()) + \
           f"cd {_shq(cwd)}\nexec {' '.join(_shq(c) for c in cmd)}\n"
    fd, path = tempfile.mkstemp(prefix="dsb_claude_", suffix=".command" if sys.platform == "darwin" else ".sh")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(body)
    os.chmod(path, 0o700)
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "Terminal", path])
        return "Terminal"
    for term in (["x-terminal-emulator", "-e"], ["gnome-terminal", "--"], ["konsole", "-e"],
                 ["xfce4-terminal", "-e"], ["xterm", "-e"]):
        if shutil.which(term[0]):
            subprocess.Popen([*term, "bash", path])
            return term[0]
    raise ValueError("no terminal program found - use 'Copy command' and paste it in a terminal")


def launch_claude_from_panel(pool: Any, opts: Dict[str, Any]) -> Dict[str, Any]:
    cfg = pool.cfg
    dry = bool(opts.get("dry"))
    b = build_launch(cfg, opts, dry)
    if dry:
        return {"ok": True, "preview": b["preview"], "project": b["project"], "mode": b["mode"]}
    where = spawn_terminal(b["cmd"], b["project"], b["diff"], b["env"])
    remember_project(cfg, b["project"], persist=True)
    pool.event("ok", f"Claude Code started in {where}: {b['project']} [{b['mode']}]")
    return {"ok": True, "where": where, "project": b["project"], "mode": b["mode"]}


def fs_list(path: str = "") -> Dict[str, Any]:
    p = Path(path).expanduser() if path else Path.home()
    try:
        p = p.resolve()
    except Exception:
        p = Path.home()
    while not p.is_dir() and p.parent != p:
        p = p.parent
    dirs, err = [], ""
    try:
        dirs = sorted((d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")), key=str.lower)[:600]
    except Exception as exc:
        err = str(exc)
    drives = [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")] if os.name == "nt" else []
    links = [("Home", str(Path.home())), ("This script's folder", str(SCRIPT_DIR))]
    for n in ("Desktop", "Documents", "Downloads"):
        if (Path.home() / n).is_dir():
            links.append((n, str(Path.home() / n)))
    return {"path": str(p), "parent": str(p.parent) if p.parent != p else "", "dirs": dirs, "drives": drives,
            "links": links, "error": err}


def run_task(pool: Any, name: str) -> Dict[str, Any]:
    script = str(Path(__file__).resolve())
    if name == "selftest":
        args = [sys.executable, script, "--self-test"]
    elif name == "verify":
        args = [sys.executable, script, "--verify-safe"]
    elif name == "install_claude":
        npm = shutil.which("npm")
        if not npm:
            raise ValueError("npm was not found - install Node.js from https://nodejs.org first")
        args = [npm, "install", "-g", "@anthropic-ai/claude-code"]
    else:
        raise ValueError("unknown task")
    if name in _state()._TASKS:
        raise ValueError("this task is already running (see the Console page)")
    _state()._TASKS.add(name)

    def run() -> None:
        try:
            log(f"[task:{name}] started", C.cyan)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 encoding="utf-8", errors="replace")
            for line in p.stdout:                                   # type: ignore[union-attr]
                if line.strip():
                    log(f"[task:{name}] {line.rstrip()}")
            log(f"[task:{name}] finished with exit code {p.wait()}", C.green if p.returncode == 0 else C.red)
        except Exception as exc:
            log(f"[task:{name}] failed: {exc}", C.red)
        finally:
            _state()._TASKS.discard(name)
    state_thread(target=run, daemon=True, name=f"task-{name}").start()
    return {"ok": True}


def bridge_control(pool: Any, action: str) -> Dict[str, Any]:
    if _state().RUN_MODE == "claude":
        raise ValueError("The bridge runs inside your Claude Code window. Close Claude Code to stop it, or start "
                         "the bridge with  --panel  to control it from here.")

    def later() -> None:
        time.sleep(0.6)
        # release the port BEFORE the child boots, otherwise the child cannot bind
        try:
            pool.stop()
            stop_server(_state().SERVER)
        except Exception:
            pass
        if action == "restart":
            time.sleep(1.5)
            try:
                devnull = open(os.devnull, "wb")
                args = [sys.executable] + sys.argv
                if os.name == "nt":
                    flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                    subprocess.Popen(args, cwd=str(SCRIPT_DIR), stdin=devnull, stdout=devnull,
                                     stderr=devnull, creationflags=flags, close_fds=True)
                else:
                    subprocess.Popen(args, cwd=str(SCRIPT_DIR), stdin=devnull, stdout=devnull,
                                     stderr=devnull, start_new_session=True, close_fds=True)
            except Exception as exc:
                log(f"restart failed: {exc}", C.red)
        os._exit(0)
    state_thread(target=later, daemon=True).start()
    return {"ok": True}


def panel_info(pool: Any) -> Dict[str, Any]:
    cfg = pool.cfg
    port = int(_state().RESOLVED_PORT or cfg.get("port", DEFAULT_PORT))
    base = f"http://127.0.0.1:{port}"
    mode, src = resolve_mode(None, cfg)
    return {"version": VERSION, "base": base, "key": cfg.get("api_key", ""),
            "instance_name": _state().instance_name, "instance_home": str(_state().paths.home), "pid": _state().PID, "models": MODELS,
            "model": "claude-sonnet-4-20250514", "haiku": "claude-haiku-4-20250514", "opus": "claude-opus-4-20250514",
            "deepseek_model": "deepseek-v4-pro", "port": port, "platform": sys.platform,
            "claude": shutil.which("claude") or "", "project": cfg.get("project_dir") or str(SCRIPT_DIR),
            "recent": cfg.get("recent_projects") or [], "mode": mode, "mode_src": src, "run_mode": _state().RUN_MODE,
            "ui_performance_mode": _state().UI_PERFORMANCE_MODE, "ui_mode": _state().UI_MODE, "parallel_mode": _state().PARALLEL_MODE,
            "script": str(Path(__file__).resolve()), "log": str(_state().paths.log), "config": str(_state().CONFIG_PATH),
            "profiles": str(_state().ACCOUNTS_DIR), "home": str(Path.home()), "settings": settings_view(cfg),
            "providers": PROVIDERS, "tiers": TIER_NAMES, "routing": dict(pool.routing),
            "project_accounts": dict(pool.project_accounts),
            "accounts": [{"id": a.id, "name": a.name, "url": f"{base}/a/{a.id}", "profile": str(a.profile),
                          "created": a.created, "logged_in": a.logged_in, "kind": a.kind, "provider": a.provider,
                          "status": a.state(time.time()), "enabled": a.enabled, "tier": a.tier,
                          "max_parallel": a.max_parallel, "key_hint": ((a.api_key[:3]+"…"+a.api_key[-3:]) if a.api_key else "")} for a in pool.accounts],
            "limits": {"files": _state().ATTACH_MAX_FILES, "file_bytes": _state().ATTACH_MAX_BYTES, "body_bytes": _state().MAX_HTTP_BODY_BYTES}}


def dash_get(pool: Any, name: str, q: Dict[str, List[str]]) -> Dict[str, Any]:
    if pool is None or not hasattr(pool, "snapshot"):
        raise ValueError("the account pool is not available")
    if name == "state":
        return pool.snapshot()
    if name == "info":
        return panel_info(pool)
    if name == "logs":
        try:
            since = int((q.get("since") or ["0"])[0] or 0)
        except ValueError:
            since = 0
        lines = [{"n": n, "t": t, "l": lv, "m": m} for (n, t, lv, m) in list(_state().LOG_RING) if n > since][-500:]
        return {"last": _state().LOG_RING[-1][0] if _state().LOG_RING else 0, "lines": lines}
    if name == "activity":
        try:
            since = int((q.get("since") or ["0"])[0] or 0)
        except ValueError:
            since = 0
        return {"last": _state().ACTIVITY[-1]["n"] if _state().ACTIVITY else 0, "items": [x for x in list(_state().ACTIVITY) if x["n"] > since][-200:]}
    if name == "swarm":
        return {"runs": [r.view(False) for r in sorted(pool.swarm.runs.values(), key=lambda r: -r.created)],
                "capacity": pool.capacity(), "max_agents": _state().SWARM_MAX_AGENTS, "git": bool(shutil.which("git")),
                "claude": bool(shutil.which("claude")), "default_agents": _state().SWARM_AGENTS}
    if name in ("swarm_run", "swarm_log"):
        run = pool.swarm.runs.get((q.get("run") or q.get("id") or [""])[0])
        if run is None:
            raise ValueError("unknown run")
        if name == "swarm_run":
            return run.view(True)
        ag = run.get((q.get("agent") or [""])[0])
        since = int((q.get("since") or ["0"])[0] or 0)
        return {"lines": [l for (n, l) in (list(ag.log) if ag else []) if n > since], "last": ag.log_n if ag else 0}
    raise ValueError(f"unknown resource '{name}'")


CLAUDE_COMMANDS = {
    "ds.md": ("---\ndescription: DeepSeek bridge - switch account / show usage (next, prev, use N, status, auto, add NAME)\n"
              "argument-hint: [next | prev | use <n|name> | status | auto | rr | failover | on <n> | off <n> | add <name>]\n"
              "---\nDS-BRIDGE-CMD $ARGUMENTS\n"),
    "panel.md": ("---\ndescription: Open the DeepSeek Bridge web panel (live view, swarm, accounts, settings)\n"
                 "argument-hint: [live | swarm | chat | launch | console | connect | settings]\n---\nDS-BRIDGE-CMD panel $ARGUMENTS\n"),
    "swarm.md": ("---\ndescription: Develop several parts of this project in parallel with a team of agents (git worktrees)\n"
                 "argument-hint: <what the team should build> | status | agents N | stop | apply\n---\nDS-BRIDGE-CMD swarm $ARGUMENTS\n"),
    "ds-next.md": ("---\ndescription: DeepSeek bridge - switch to the next DeepSeek account\n---\nDS-BRIDGE-CMD next\n"),
}


def _command_header() -> str:
    return f"# DeepSeek Bridge instance: {_state().instance_name} | config: {_state().CONFIG_PATH}\n"


def install_claude_commands(target_dir: Optional[Path] = None, force: bool = False) -> None:
    """Install slash commands without letting instances overwrite each other's generated files."""
    try:
        base_cfg = Path(target_dir).expanduser().resolve() if target_dir else Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")).expanduser().resolve()
        base = base_cfg / "commands"
        marker = f"DeepSeek Bridge instance: {_state().instance_name} | config: {_state().CONFIG_PATH}"
        header = _command_header()
        for name, text_body in CLAUDE_COMMANDS.items():
            text = text_body
            if text.startswith("---"):
                text = "---\n" + header.rstrip("\n") + "\n" + text[len("---\n"):]
            else:
                text = header + text
            f = base / name
            if f.exists():
                old = f.read_text(encoding="utf-8", errors="replace")
                if marker in old and old == text:
                    continue
                if "DS-BRIDGE-CMD" not in old:
                    continue
                if not force:
                    _warn_once("claude_cmd_conflict:" + str(f),
                                f"Claude command {f} was generated by a different bridge instance; skipping it. Use --force-claude-commands to overwrite.")
                    continue
            base.mkdir(parents=True, exist_ok=True)
            f.write_text(text, encoding="utf-8")
    except Exception as exc:
        _warn_once("claude_cmds", f"could not install the /ds slash commands ({exc})")


def ctl_project(cfg: Dict[str, Any], project: Any) -> int:
    """Tell the already-running bridge which project the new launcher selected."""
    import urllib.request
    url = f"http://127.0.0.1:{cfg['port']}/dash/api/project_context"
    req = urllib.request.Request(url, data=json.dumps({"project": str(project)}).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + str(cfg["api_key"])})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode("utf-8", "replace"))
        if result.get("project"):
            print(C.green(f"[project] running bridge context updated: {result['project']}"))
        return 0
    except Exception as exc:
        print(C.red(f"[project] could not update the running bridge context on port {cfg['port']} ({exc})"))
        return 1


def ctl_client(cfg: Dict[str, Any], command: str) -> int:
    import urllib.request
    url = f"http://127.0.0.1:{cfg['port']}/dash/api/command"
    req = urllib.request.Request(url, data=json.dumps({"text": command}).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + str(cfg["api_key"])})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(json.loads(r.read().decode("utf-8", "replace")).get("text", ""))
        return 0
    except Exception as exc:
        print(C.red(f"[ctl] the bridge is not reachable on port {cfg['port']} ({exc}). Start it first."))
        return 1


def open_dashboard(url: str, key: str, page: str = "") -> None:
    try:
        import webbrowser
        webbrowser.open(f"{url}/dash#k={key}" + (f"&p={page}" if page else ""))
    except Exception:
        pass


DASH_HTML = r"""<!doctype html>
<html lang="fa" dir="rtl" data-theme="dark" data-acc="violet"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0d1117"><link rel="icon" href="data:,"><title>DeepSeek Bridge — __INSTANCE_NAME__</title>
<style>
:root{--ac:#7c8cff;--ac2:#b37cff;--ok:#34d399;--warn:#fbbf24;--bad:#fb7185;--info:#60c8ff;--r:14px}
[data-acc=emerald]{--ac:#34d399;--ac2:#22d3ee}[data-acc=amber]{--ac:#fbbf24;--ac2:#fb7185}[data-acc=sky]{--ac:#38bdf8;--ac2:#818cf8}
[data-theme=dark]{--bg:#090c16;--p:#101627;--p2:#172038;--ln:#232d4a;--tx:#e9edfb;--mut:#8d99bd;--glass:rgba(16,22,39,.8);color-scheme:dark}
[data-theme=light]{--bg:#f2f4fb;--p:#fff;--p2:#eef1fb;--ln:#dce1f3;--tx:#182041;--mut:#5b668f;--glass:rgba(255,255,255,.85);color-scheme:light}
*{box-sizing:border-box;margin:0}[hidden]{display:none!important}
body{background:var(--bg);background-attachment:fixed;color:var(--tx);font:14px/1.6 Vazirmatn,"Segoe UI",Tahoma,system-ui,sans-serif;min-height:100vh}
button,input,select,textarea{font:inherit;color:inherit}::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-thumb{background:var(--ln);border-radius:9px}
.mono,code,pre,#p-chat,#cw{font-family:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace}
#app{display:flex;min-height:100vh}
#rail{width:80px;flex:none;position:sticky;top:0;height:100vh;display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 8px;background:var(--glass);backdrop-filter:blur(16px);border-inline-end:1px solid var(--ln);z-index:30}
.logo{width:44px;height:44px;border-radius:14px;background:var(--ac);display:grid;place-items:center;font-size:22px;margin-bottom:10px;box-shadow:0 10px 28px -10px var(--ac)}
.nb{width:64px;padding:8px 0;border-radius:14px;border:0;background:none;cursor:pointer;display:grid;gap:1px;justify-items:center;color:var(--mut);transition:.18s;font-size:10.5px}
.nb i{font-style:normal;font-size:20px;transition:.18s}.nb:hover{background:var(--p2);color:var(--tx)}.nb:hover i{transform:scale(1.15)}
.nb.on{background:var(--ac);color:#fff;box-shadow:0 10px 24px -10px var(--ac)}.sp{flex:1}
#main{flex:1;min-width:0;display:flex;flex-direction:column}
#top{display:flex;align-items:center;gap:12px;padding:12px 22px;border-bottom:1px solid var(--ln);position:sticky;top:0;background:var(--glass);backdrop-filter:blur(16px);z-index:20;flex-wrap:wrap}
#top h1{font-size:18px}.chip{background:var(--p2);border:1px solid var(--ln);border-radius:99px;padding:3px 11px;font-size:12px;color:var(--mut);display:inline-flex;gap:6px;align-items:center}
.dot{width:8px;height:8px;border-radius:9px;background:var(--ok);box-shadow:0 0 10px var(--ok)}.dot.off{background:var(--bad);box-shadow:0 0 10px var(--bad)}
#off{background:var(--bad);color:#fff;text-align:center;padding:5px;display:none}
.btn{background:var(--p2);border:1px solid var(--ln);border-radius:10px;padding:7px 13px;cursor:pointer;transition:.15s;display:inline-flex;gap:6px;align-items:center;white-space:nowrap}
.btn:hover{border-color:var(--ac);transform:translateY(-1px)}.btn:active{transform:none}.btn.pri{background:var(--ac);border:0;color:#fff;font-weight:600;box-shadow:0 8px 20px -10px var(--ac)}
.btn.sm{padding:4px 10px;font-size:12px;border-radius:8px}.btn.dng:hover{border-color:var(--bad);color:var(--bad)}.btn.wide{width:100%;justify-content:center}.btn[disabled]{opacity:.5;pointer-events:none}
.ib{background:none;border:0;cursor:pointer;font-size:17px;padding:4px 8px;border-radius:8px;color:var(--mut)}.ib:hover{background:var(--p2);color:var(--tx)}
.inp,select.inp,textarea.inp{background:var(--p2);border:1px solid var(--ln);border-radius:10px;padding:8px 11px;width:100%;outline:0;transition:.15s}.inp:focus{border-color:var(--ac);box-shadow:0 0 0 3px color-mix(in srgb,var(--ac) 22%,transparent)}
select.inp{width:auto}.page{display:none;padding:22px;max-width:1340px;margin:0 auto;width:100%;animation:in .28s}.page.on{display:block}
@keyframes in{from{opacity:0;transform:translateY(8px)}}
.box{background:var(--p);border:1px solid var(--ln);border-radius:var(--r);padding:16px 18px;margin-bottom:16px;box-shadow:0 14px 40px -26px #000}
.box h3{font-size:13px;color:var(--mut);font-weight:600;margin-bottom:12px;display:flex;gap:8px;align-items:center}.tip{color:var(--mut);font-size:12px}
details.sgrp{padding:0}details.sgrp>summary{list-style:none;cursor:pointer;padding:14px 18px;display:flex;gap:10px;align-items:center;user-select:none}details.sgrp>summary::-webkit-details-marker{display:none}details.sgrp>summary:before{content:"▸";color:var(--mut);transition:.15s;display:inline-block}details.sgrp[open]>summary:before{transform:rotate(90deg)}details.sgrp>summary h3{margin:0;flex:1}details.sgrp>summary .dim{color:var(--mut);font-size:11px;background:var(--p2);border-radius:99px;padding:1px 9px}details.sgrp>summary:hover{background:var(--p2);border-radius:var(--r) var(--r) 0 0}details.sgrp:not([open])>summary:hover{border-radius:var(--r)}details.sgrp>*:not(summary){padding-inline:18px}details.sgrp>div:last-child{padding-bottom:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:16px}
.tile{background:var(--p);border:1px solid var(--ln);border-radius:var(--r);padding:14px 16px;position:relative;overflow:hidden}
.tile:before{content:"";position:absolute;inset-inline-end:-30px;top:-30px;width:90px;height:90px;border-radius:50%;background:var(--ac);opacity:.14}
.tile b{display:block;font-size:26px}.tile span{color:var(--mut);font-size:12px}
.seg{display:flex;gap:10px;flex-wrap:wrap}.seg label{flex:1;min-width:160px;background:var(--p2);border:1px solid var(--ln);border-radius:12px;padding:10px 13px;cursor:pointer;transition:.15s}
.seg label:hover{border-color:var(--ac)}.seg label:has(input:checked){border-color:var(--ac);box-shadow:0 0 0 1px var(--ac) inset,0 8px 24px -14px var(--ac)}.seg input{display:none}.seg b{display:block}.seg small{color:var(--mut)}
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-top:12px;color:var(--mut)}.row input[type=number]{width:76px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(370px,1fr));gap:14px;margin-bottom:16px}
.card{background:var(--p);border:1px solid var(--ln);border-radius:18px;padding:15px;position:relative;transition:.2s}.card:hover{transform:translateY(-2px)}
.card.cur{border-color:var(--ac);box-shadow:0 0 0 1px var(--ac) inset,0 18px 40px -22px var(--ac)}.card.off{opacity:.6}
.ch{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}.ch b{font-size:15px}.idx{color:var(--mut)}
.tag{font-size:10px;padding:2px 8px;border-radius:99px;font-weight:700}.tag.live{background:var(--ac);color:#fff}.tag.pin{background:#3a2f63;color:#cdbbff}
.pill{margin-inline-start:auto;font-size:11px;padding:3px 10px;border-radius:99px;border:1px solid}
.st-ready{color:var(--ok);border-color:#1c6b51;background:#10302a}.st-busy,.st-starting,.st-login{color:var(--info);border-color:#1c5a77;background:#0f2a38}
.st-cooldown{color:var(--warn);border-color:#7a5a1f;background:#33270f}.st-login_needed,.st-error{color:var(--bad);border-color:#7a2a36;background:#33121a}.st-disabled,.st-stopped{color:var(--mut);border-color:var(--ln)}
.kv{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0}.kv div{background:var(--p2);border-radius:11px;padding:7px 10px}.kv span{display:block;color:var(--mut);font-size:11px}.kv b{font-size:14px}
.bar{height:6px;background:var(--p2);border-radius:9px;overflow:hidden;margin:6px 0}.bar i{display:block;height:100%;width:0;background:var(--ac);transition:width .6s}
svg.sp{width:100%;height:38px;display:block}.err{color:var(--bad);font-size:12px;margin:6px 0;word-break:break-word}.err:empty{display:none}
.act{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;align-items:center}
.more{position:relative}.more summary{list-style:none;cursor:pointer}.more summary::-webkit-details-marker{display:none}
.menu{position:absolute;inset-inline-end:0;top:110%;background:var(--p);border:1px solid var(--ln);border-radius:12px;padding:6px;display:grid;gap:2px;min-width:170px;z-index:10;box-shadow:0 20px 50px -20px #000}
.menu button{background:none;border:0;text-align:start;padding:6px 10px;border-radius:8px;cursor:pointer}.menu button:hover{background:var(--p2)}.menu .dng:hover{color:var(--bad)}
.ev{max-height:240px;overflow:auto;font:12px ui-monospace,Consolas,monospace}.ev div{padding:3px 0;border-bottom:1px dashed var(--ln)}.ev .warn{color:var(--warn)}.ev .error{color:var(--bad)}.ev .ok{color:var(--ok)}.ev time{color:var(--mut);margin-inline-end:8px}
#toast{position:fixed;bottom:20px;inset-inline-start:100px;display:flex;flex-direction:column;gap:8px;z-index:90}
#toast div{background:var(--p);border:1px solid var(--ac);border-radius:12px;padding:9px 15px;max-width:440px;animation:in .2s;box-shadow:0 14px 40px -16px #000;white-space:pre-wrap}
.ov{position:fixed;inset:0;background:rgba(3,5,12,.6);backdrop-filter:blur(4px);display:grid;place-items:center;z-index:80;opacity:0;transition:.18s;padding:16px}.ov.on{opacity:1}
.mdl{background:var(--p);border:1px solid var(--ln);border-radius:18px;padding:20px;width:min(520px,100%);max-height:88vh;overflow:auto;box-shadow:0 30px 80px -30px #000;transform:translateY(10px);transition:.18s}.ov.on .mdl{transform:none}.mdl.big{width:min(680px,100%)}
.mdl h3{margin-bottom:10px}.rowb{display:flex;gap:8px;justify-content:flex-end;margin-top:14px;flex-wrap:wrap}.mdl p{margin-bottom:8px}
.sw{position:relative;display:inline-block;width:42px;height:24px}.sw input{opacity:0;width:0;height:0}.sw i{position:absolute;inset:0;background:var(--ln);border-radius:24px;cursor:pointer;transition:.2s}
.sw i:before{content:"";position:absolute;width:18px;height:18px;inset-inline-start:3px;top:3px;background:#fff;border-radius:50%;transition:.2s}.sw input:checked+i{background:var(--ac)}.sw input:checked+i:before{transform:translateX(18px)}[dir=rtl] .sw input:checked+i:before{transform:translateX(-18px)}
/* chat */
#p-chat{padding:0;max-width:none;height:calc(100vh - 62px);min-height:0;overflow:hidden}#p-chat.on{display:grid;grid-template-columns:250px 1fr;min-height:0}
#cl{border-inline-end:1px solid var(--ln);padding:12px;overflow:auto;background:var(--glass);min-height:0}#clist{margin-top:10px;display:grid;gap:4px}
.ci{padding:8px 10px;border-radius:10px;cursor:pointer;display:flex;gap:6px;align-items:center;color:var(--mut);font-size:13px}.ci span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ci:hover{background:var(--p2);color:var(--tx)}.ci.on{background:var(--p2);color:var(--tx);box-shadow:0 0 0 1px var(--ac) inset}.ci button{opacity:0}.ci:hover button{opacity:1}
#cm{display:flex;flex-direction:column;min-width:0;height:100%;min-height:0;overflow:hidden}#chd{display:flex;gap:8px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--ln);flex:0 0 auto}#chd b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#cscroll{flex:1 1 0;min-height:0;overflow:auto;padding:18px 22px}#ctx{max-width:900px;margin:0 auto;display:grid;gap:14px}
.wel{border:1px solid var(--ac);border-radius:14px;padding:14px 18px;width:fit-content;max-width:100%;background:color-mix(in srgb,var(--ac) 8%,transparent)}.wel b{color:var(--ac)}.wel div{color:var(--mut)}
.um{display:flex;gap:10px;background:var(--p2);border:1px solid var(--ln);border-radius:12px;padding:9px 13px}.um .pr{color:var(--ac);font-weight:700}.ub{min-width:0;overflow-wrap:anywhere;white-space:pre-wrap;direction:auto}
.am{display:flex;gap:10px}.am .bl{color:var(--ac);line-height:1.6}.md{min-width:0;flex:1;overflow-wrap:anywhere;direction:auto}.md h2,.md h3,.md h4,.md h5{margin:10px 0 4px}.md ul,.md ol{padding-inline-start:22px}.md blockquote{border-inline-start:3px solid var(--ac);padding-inline-start:10px;color:var(--mut)}
.md code{background:var(--p2);padding:1px 6px;border-radius:6px}.md a{color:var(--ac)}.nt{color:var(--mut);padding-inline-start:4px;white-space:pre-wrap}.nt.e{color:var(--bad)}
.code{border:1px solid var(--ln);border-radius:12px;overflow:hidden;margin:8px 0;direction:ltr;text-align:left}.cb{display:flex;justify-content:space-between;background:var(--p2);padding:4px 10px;color:var(--mut);font-size:11px}.cb button{background:none;border:0;cursor:pointer;color:var(--mut)}.code pre{padding:10px 12px;overflow:auto;font-size:12.5px}.code code{background:none;padding:0}
.th{max-height:120px;border-radius:8px;display:block;margin:4px 0}.fc{display:inline-flex;gap:6px;align-items:center;background:var(--p);border:1px solid var(--ln);border-radius:9px;padding:2px 9px;margin:2px;font-size:12px}
.stat{color:var(--ac);display:flex;gap:8px;align-items:center}.stat .dim{color:var(--mut)}.spin{display:inline-block;animation:sp 1.2s linear infinite}@keyframes sp{to{transform:rotate(360deg)}}
#cbar{padding:10px 16px 14px;position:relative;flex:0 0 auto}#cbox{max-width:900px;margin:0 auto;display:flex;gap:8px;align-items:flex-end;border:1px solid var(--ln);border-radius:16px;padding:8px 10px;background:var(--p);transition:.15s}#cbox:focus-within{border-color:var(--ac);box-shadow:0 0 0 3px color-mix(in srgb,var(--ac) 20%,transparent)}
#cbox .pr{color:var(--ac);font-weight:700;padding-bottom:6px}#cin{flex:1;background:none;border:0;outline:0;resize:none;max-height:200px;padding:5px 0;direction:auto}.snd{background:var(--ac);color:#fff!important;border-radius:11px}
#chips2{max-width:900px;margin:0 auto 6px;display:flex;gap:6px;flex-wrap:wrap}.ach{display:flex;gap:6px;align-items:center;background:var(--p2);border:1px solid var(--ln);border-radius:10px;padding:3px 8px;font-size:12px}.ach img{height:30px;border-radius:5px}.ach button{background:none;border:0;cursor:pointer;color:var(--mut)}
#pal{position:absolute;bottom:100%;inset-inline:16px;max-width:900px;margin:0 auto;background:var(--p);border:1px solid var(--ln);border-radius:12px;padding:5px;box-shadow:0 20px 50px -20px #000;z-index:5}.pi{padding:6px 10px;border-radius:8px;cursor:pointer;display:flex;gap:12px}.pi:hover,.pi.on{background:var(--p2)}.pi b{color:var(--ac)}.pi span{color:var(--mut)}
#p-chat.drag:after{content:"＋";position:absolute;inset:0;display:grid;place-items:center;font-size:80px;background:color-mix(in srgb,var(--ac) 18%,transparent);border:3px dashed var(--ac);z-index:9}
/* console / connect / settings / launch */
#cw{display:flex;flex-direction:column;height:calc(100vh - 150px);min-height:380px}#clog{flex:1;overflow:auto;background:#05070e;border:1px solid var(--ln);border-radius:14px 14px 0 0;padding:10px 14px;font-size:12.5px;color:#cfd6f3}[data-theme=light] #clog{background:#10162b}
.ll{white-space:pre-wrap;word-break:break-word}.ll time{color:#6b7599;margin-inline-end:10px}.ll.warn{color:#fbbf24}.ll.error{color:#fb7185}.ll.ok{color:#34d399}.ll.cmd{color:#7c8cff}
#cin2{display:flex;gap:8px;align-items:center;background:#0b1020;border:1px solid var(--ln);border-top:0;border-radius:0 0 14px 14px;padding:8px 12px}#cin2 span{color:var(--ac)}#cin2 input{flex:1;background:none;border:0;outline:0;color:#e9edfb}
.tb{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;align-items:center}.fchip{padding:3px 11px;border-radius:99px;border:1px solid var(--ln);cursor:pointer;background:var(--p2);font-size:12px}.fchip.on{border-color:var(--ac);color:var(--ac)}
.srow{display:grid;grid-template-columns:1fr 240px 34px;gap:12px;align-items:center;padding:9px 0;border-bottom:1px dashed var(--ln)}.srow small{display:block;color:var(--mut);font-size:11px}.srow:last-child{border:0}
.srow.chg .ctl{outline:2px solid var(--ac);border-radius:10px}#savebar{position:sticky;bottom:12px;display:flex;gap:10px;justify-content:center;align-items:center;background:var(--glass);backdrop-filter:blur(12px);border:1px solid var(--ac);border-radius:14px;padding:10px;margin-top:12px;box-shadow:0 20px 50px -20px var(--ac)}
.sn{border:1px solid var(--ln);border-radius:12px;overflow:hidden;margin-top:10px;direction:ltr}.sn .cb{align-items:center}.sn pre{padding:10px 12px;overflow:auto;font-size:12.5px;background:var(--p2);white-space:pre-wrap;word-break:break-all}
.kvl{display:grid;grid-template-columns:130px 1fr auto;gap:8px;align-items:center;padding:6px 0;border-bottom:1px dashed var(--ln)}.kvl code{background:var(--p2);padding:4px 9px;border-radius:8px;overflow-wrap:anywhere;direction:ltr;text-align:left}
.g2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}.mode{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}.mode label{cursor:pointer;background:var(--p2);border:1px solid var(--ln);border-radius:14px;padding:12px;transition:.15s}.mode label:has(input:checked){border-color:var(--ac);box-shadow:0 0 0 1px var(--ac) inset}.mode input{display:none}.mode b{display:block}.mode small{color:var(--mut)}
.fl{display:grid;gap:2px;max-height:300px;overflow:auto;margin:8px 0}.fl div{padding:6px 10px;border-radius:8px;cursor:pointer}.fl div:hover{background:var(--p2)}.pth{background:var(--p2);border-radius:9px;padding:6px 10px;direction:ltr;text-align:left;word-break:break-all;font-size:12px}
#dockp{display:none;width:410px;flex:none;position:sticky;top:0;height:100vh;border-inline-start:1px solid var(--ln);background:var(--glass);backdrop-filter:blur(16px);flex-direction:column;z-index:15}#app.dock #dockp{display:flex}
.dh{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border-bottom:1px solid var(--ln)}.feed{overflow:auto;flex:1;padding:10px;display:grid;gap:8px;align-content:start}
.fcard{background:var(--p);border:1px solid var(--ln);border-radius:12px;padding:8px 11px;font-size:12.5px;cursor:pointer;animation:in .25s}.fcard.agent{border-inline-start:3px solid var(--ac2)}.fcard.main{border-inline-start:3px solid var(--ac)}.fcard.side{opacity:.7}
.fh{display:flex;gap:8px;flex-wrap:wrap;color:var(--mut);font-size:11px;align-items:center}.bd{padding:1px 8px;border-radius:99px;background:var(--p2);color:var(--tx);font-weight:600}.fu{color:var(--mut);margin-top:4px;overflow-wrap:anywhere}
.fr{margin-top:3px;overflow-wrap:anywhere;white-space:pre-wrap;max-height:3.3em;overflow:hidden}.fcard.x .fr{max-height:none}.fcs{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}.fcs span{background:var(--p2);border-radius:7px;padding:1px 8px;font:11px ui-monospace,monospace}
.pvg{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}.pv{background:var(--p2);border:1px solid var(--ln);border-radius:14px;padding:12px;cursor:pointer;transition:.15s;display:grid;gap:2px}.pv:hover{border-color:var(--ac);transform:translateY(-2px)}.pv i{font-style:normal;font-size:26px}.pv small{color:var(--mut)}
.fg{display:grid;gap:10px}.fg label{display:grid;gap:3px;color:var(--mut);font-size:12px}.fg2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.tb2{display:inline-block;width:fit-content;padding:1px 9px;border-radius:99px;background:var(--ac);color:#fff;font-size:10px;font-weight:700}
.sub{color:var(--mut);font-size:12px;margin:-4px 0 8px}.st-budget{color:var(--warn);border-color:#7a5a1f;background:#33270f}
.runs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}.rn{padding:6px 12px;border-radius:12px;background:var(--p2);border:1px solid var(--ln);cursor:pointer}.rn.on{border-color:var(--ac)}
.ags{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:12px}.ag{background:var(--p2);border:1px solid var(--ln);border-radius:14px;padding:12px;cursor:pointer;transition:.15s}.ag:hover{border-color:var(--ac)}.ag .act2{color:var(--info);font-size:12px;margin-top:6px;min-height:1.4em;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.stp{font-size:11px;padding:2px 9px;border-radius:99px;border:1px solid;white-space:nowrap}.sg-queued,.sg-skipped,.sg-stopped{color:var(--mut);border-color:var(--ln)}.sg-starting,.sg-running,.sg-verifying,.sg-reviewing,.sg-merging,.sg-planning{color:var(--info);border-color:#1c5a77;background:#0f2a38}
.sg-merged,.sg-done{color:var(--ok);border-color:#1c6b51;background:#10302a}.sg-failed,.sg-conflict,.sg-done_with_issues{color:var(--bad);border-color:#7a2a36;background:#33121a}.gp{font:11px ui-monospace,monospace;background:var(--p);border-radius:6px;padding:1px 7px;margin:2px;display:inline-block}
.stepper{display:inline-flex;align-items:center;gap:6px}.stepper button{width:28px;height:28px;border-radius:8px;border:1px solid var(--ln);background:var(--p2);cursor:pointer;color:var(--tx)}
@media(max-width:1100px){#app.dock #dockp{display:none}}
@media(max-width:760px){#app{flex-direction:column-reverse}#rail{width:100%;height:auto;position:fixed;bottom:0;flex-direction:row;padding:6px;overflow-x:auto;justify-content:space-around}.logo{display:none}.nb{width:auto;padding:5px 8px}#main{padding-bottom:70px}#p-chat.on{grid-template-columns:1fr}#cl{display:none}.srow{grid-template-columns:1fr}.kvl{grid-template-columns:1fr}#toast{inset-inline-start:10px;bottom:80px}}

/* adaptive performance / compact UX */
:root{--perf-shadow:0 14px 40px -26px #000}
html[data-perf="light"] body{background-attachment:scroll}
html[data-perf="light"] #rail,html[data-perf="light"] #top,html[data-perf="light"] #dockp,html[data-perf="light"] #cl{backdrop-filter:none!important;box-shadow:none!important;background:var(--p)!important}
html[data-perf="light"] .box,html[data-perf="light"] .card,html[data-perf="light"] #toast div{box-shadow:none!important}
html[data-perf="light"] .btn,html[data-perf="light"] .card,html[data-perf="light"] .nb,html[data-perf="light"] .pv,html[data-perf="light"] .ag{transition:none!important}
html[data-perf="light"] .btn:hover,html[data-perf="light"] .card:hover,html[data-perf="light"] .pv:hover,html[data-perf="light"] .nb:hover i{transform:none!important}
html[data-perf="light"] .page,html[data-perf="light"] .fcard{animation:none!important}
html[data-perf="light"] .ov{backdrop-filter:none!important}
#ccmirror{margin-bottom:12px}.ccm{background:var(--p);border:1px solid var(--ln);border-radius:14px;padding:11px 13px}.ccmhead{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.ccmstate{margin-inline-start:auto;color:var(--ok);font-size:11px}
#ccterm{margin-bottom:12px;background:#05070e;border:1px solid var(--ln);border-radius:14px;overflow:hidden;display:flex;flex-direction:column}
[data-theme=light] #ccterm{background:#10162b}
#ccterm .cthead{display:flex;align-items:center;gap:8px;padding:9px 12px;background:rgba(255,255,255,.03);border-bottom:1px solid var(--ln);color:#cfd6f3;font-size:12px}
#ccterm .cthead b{font-weight:600}#ccterm .ctdot{width:9px;height:9px;border-radius:50%;background:#3ddc84;box-shadow:0 0 6px #3ddc84;flex:0 0 auto}
#ccterm .cthead .sp{margin-inline-start:auto}#ccterm .cthead .ctb{cursor:pointer;padding:2px 8px;border-radius:7px;background:rgba(255,255,255,.06);color:#cfd6f3;font-size:11px}
#ccterm .cthead .ctb:hover{background:rgba(255,255,255,.12)}
#ctlog{flex:1 1 auto;overflow:auto;padding:8px 12px;font-family:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;font-size:12.5px;line-height:1.55;color:#cfd6f3;max-height:calc(100vh - 430px);min-height:180px;white-space:pre-wrap;word-break:break-word}
#ctlog .ctl{display:block;padding:1px 0}
#ctlog .ctl .cts{color:#5b6489;margin-inline-end:8px;user-select:none}
#ctlog .ct-prompt{color:#8ab4ff}#ctlog .ct-prompt .ctk{color:#ffd479}
#ctlog .ct-asst{color:#cfd6f3}
#ctlog .ct-tool{color:#7ee0c0}#ctlog .ct-tool .ctn{color:#ffd479;font-weight:600}
#ctlog .ct-toolerr{color:#ff8f8f}
#ctlog .ct-notice{color:#c79bff}
#ctlog .ct-sys{color:#5b6489}#ctlog .ct-ok{color:#3ddc84}#ctlog .ct-err{color:#ff6b6b}
#ctlog .ctc{cursor:pointer;opacity:.55}#ctlog .ctc:hover{opacity:1}.ccmrow{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:6px;color:var(--mut);font-size:12px}.ccmrow .pth{color:var(--tx);overflow-wrap:anywhere}.ccmagents{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.ccma{padding:4px 8px;border-radius:9px;background:var(--p2);font-size:11px}.ccma span{color:var(--mut)}.swpreview{display:grid;gap:8px;margin-top:8px}.swpreview textarea{resize:vertical;min-height:120px}.swu{border:1px dashed var(--ln);border-radius:11px;padding:10px}.swu .lbl{display:flex;justify-content:space-between;gap:8px;align-items:center;color:var(--mut);font-size:11px}.sactions{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.swattach{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-top:9px}.achip{display:inline-flex;align-items:center;gap:5px;max-width:100%;background:var(--p2);border:1px solid var(--ln);border-radius:9px;padding:4px 8px;font-size:11px}.achip span{max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.achip button{border:0;background:none;color:var(--mut);cursor:pointer;padding:0 2px}
@media(max-width:980px){.grid{grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}.fg2{grid-template-columns:1fr}.ags{grid-template-columns:1fr}#top{padding:10px 14px}.page{padding:14px}}
@media(max-width:600px){.tiles{grid-template-columns:1fr 1fr}.tile b{font-size:21px}.kv{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.btn{min-height:38px}.inp{min-height:40px}.ccma{max-width:100%}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
/* GitHub-like, low-RAM skin + mobile drawer. No external fonts, icons or effects. */
:root{--r:8px;--ok:#3fb950;--bad:#f85149;--warn:#d29922;--info:#58a6ff}
[data-acc=sky]{--ac:#58a6ff;--ac2:#79c0ff}
[data-theme=dark]{--bg:#0d1117;--p:#161b22;--p2:#21262d;--ln:#30363d;--tx:#f0f6fc;--mut:#8b949e;--glass:#161b22}
[data-theme=light]{--bg:#ffffff;--p:#ffffff;--p2:#f6f8fa;--ln:#d0d7de;--tx:#1f2328;--mut:#656d76;--glass:#ffffff}
body{background:var(--bg);background-attachment:scroll}
#rail{width:72px;background:var(--p);backdrop-filter:none;border-inline-end:1px solid var(--ln);padding:10px 7px;gap:4px}
.logo{width:40px;height:40px;border-radius:8px;background:var(--p2);color:var(--tx);font-size:13px;font-weight:700;box-shadow:none;margin-bottom:8px}
.nb{width:58px;border-radius:8px;padding:7px 3px;transition:none;font-size:10px}.nb i{font-size:16px;line-height:1.1;transition:none}.nb.on{background:var(--p2);color:var(--tx);box-shadow:inset 2px 0 var(--ac)}.nb:hover i{transform:none}
#top{background:var(--p);backdrop-filter:none;padding:9px 16px;gap:8px;min-height:52px}.btn{border-radius:7px;padding:6px 11px;transition:none}.btn:hover{transform:none}.btn.pri{background:var(--ac);box-shadow:none}.box,.card{border-radius:var(--r);box-shadow:none}.card:hover,.pv:hover,.ag:hover{transform:none}.inp{border-radius:7px;box-shadow:none}.seg label,.menu,.fcard,.pv,.ag,.rn,.ccm,.swu{border-radius:8px;box-shadow:none}.tag.live,.tb2{background:var(--ac)}
#dockp{background:var(--p);backdrop-filter:none;box-shadow:none}.ov{backdrop-filter:none;background:rgba(1,4,9,.58)}
#mobileNav{display:none}#navshade{display:none}
@media(max-width:760px){#navshade{display:block;position:fixed;inset:0;background:rgba(1,4,9,.28);z-index:110}}
@media(max-width:760px){
  #app{display:block;min-height:100vh}
  #rail{position:fixed;inset-block:0;inset-inline-start:0;width:min(82vw,280px);height:100vh;transform:translateX(-105%);z-index:120;align-items:stretch;padding:10px 9px;background:var(--p);border-inline-end:1px solid var(--ln);overflow:auto;transition:transform .12s ease}
  [dir=rtl] #rail{transform:translateX(105%)}
  #app.navopen #rail{transform:none}
  #rail .logo{display:grid;align-self:flex-start;width:40px}.nb{width:100%;display:flex;justify-content:flex-start;gap:10px;padding:10px 12px;font-size:13px}.nb i{width:22px;text-align:center;font-size:16px}.railbottom{display:flex}
  #main{padding-bottom:0;min-width:0}
  #top{position:sticky;top:0;padding:8px 10px;z-index:100;overflow:hidden}
  #mobileNav{display:inline-flex;flex:none;width:34px;height:34px;padding:0;align-items:center;justify-content:center;border:1px solid var(--ln);background:var(--p2);border-radius:7px;color:var(--tx);font-size:18px}
  #ttl{font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
  #chips{display:none}
  #top .sp{display:none}
  #hdock,#hnext{display:none}
  #hadd{margin-inline-start:auto}
  .page{padding:10px;max-width:none;animation:none}
  #p-chat.on{grid-template-columns:1fr;height:calc(100vh - 52px)}
  #cl{display:none}
  #cbar{padding:8px 8px 10px}
  #cbox{border-radius:9px;padding:6px 8px}
  #cscroll{padding-inline:8px}
  .tiles{grid-template-columns:1fr 1fr;gap:8px}.tile{padding:11px 12px}.tile b{font-size:19px}
  .grid{grid-template-columns:1fr;gap:8px}.box,.card{padding:12px;margin-bottom:10px}.row{gap:10px}.row input[type=number]{width:70px}
  .kvl{grid-template-columns:1fr;gap:4px}.g2{grid-template-columns:1fr}.mode{grid-template-columns:1fr}.pvg{grid-template-columns:1fr}.fg2{grid-template-columns:1fr}.ags{grid-template-columns:1fr}
  #toast{inset-inline:10px;bottom:10px}.fcard{padding:8px;font-size:12px}
  #ccmirror{margin-bottom:8px}.ccm{padding:9px}.ccmrow{gap:6px}.ccmagents{gap:4px}
  .mdl,.mdl.big{width:100%;max-height:92vh;padding:14px}
}

/* V6.4 low-resource / responsive UI hardening */
html[data-ux="beginner"] .pro-only{display:none!important}
html[data-ux="pro"] .pro-only{display:block}
.top,.topbar,.modal,.drawer-overlay{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
.tile,.card,.panel,.box,.fcard,.modal-card{background-image:none!important}
pre,code,.path,.url,.mono{direction:ltr!important;text-align:left!important;unicode-bidi:plaintext}
@media (max-width:430px){.wrap{padding:10px!important}.top{min-height:46px!important}.top button,.btn,.iconbtn{min-width:40px;min-height:40px}.table-wrap,.list-wrap,.grid-scroll{overflow-x:auto!important;max-width:100%!important}.modal,.modal-card{max-width:calc(100vw - 20px)!important;width:auto!important;margin:10px!important}#rail{width:min(82vw,280px)!important}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style></head><body>
<div id="app"><aside id="rail"><div class="logo" aria-label="DeepSeek Bridge">DB</div>
<button class="nb" data-go="dash"><i>⌂</i><span data-t="n_dash"></span></button><button class="nb" data-go="live"><i>◉</i><span data-t="n_live"></span></button><button class="nb" data-go="chat"><i>▱</i><span data-t="n_chat"></span></button><button class="nb" data-go="swarm"><i>✣</i><span data-t="n_swarm"></span></button>
<button class="nb" data-go="launch"><i>↗</i><span data-t="n_launch"></span></button><button class="nb" data-go="console"><i>&gt;_</i><span data-t="n_console"></span></button>
<button class="nb" data-go="connect"><i>⊕</i><span data-t="n_connect"></span></button><button class="nb" data-go="settings"><i>⚙</i><span data-t="n_settings"></span></button>
<div class="sp"></div><button class="nb" id="bpal"><i>⌕</i><span>Ctrl+K</span></button><button class="nb" id="bth"><i>◐</i><span data-t="theme"></span></button><button class="nb" id="blang"><i>A</i><span>EN</span></button></aside>
<div id="main"><div id="off"></div><header id="top"><button id="mobileNav" aria-label="Menu" title="Menu">☰</button><h1 id="ttl"></h1><span id="chips"></span><div class="sp"></div><button class="btn" id="hdock">▣ <span data-t="dock"></span></button><button class="btn" id="hnext">› <span data-t="nextAcct"></span></button><button class="btn pri" id="hadd">＋ <span data-t="add"></span></button></header>
<section class="page" id="p-dash"><div class="tiles" id="tiles"></div>
<div class="box"><h3>↗ <span data-t="routing"></span></h3><div class="seg" id="seg"></div>
<div class="row"><label><span class="sw"><input type="checkbox" id="fo"><i></i></span> <span data-t="autofo"></span></label><label><span data-t="rotReq"></span> <input class="inp" type="number" id="rr" min="0"></label><label><span data-t="rotMin"></span> <input class="inp" type="number" id="rm" min="0"></label><span class="tip" data-t="rotTip"></span></div>
<div class="row"><label><span class="sw"><input type="checkbox" id="sm"><i></i></span> <span data-t="smart"></span></label><label><span data-t="tierStrong"></span> <select class="inp" id="ts"><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select></label><label><span data-t="tierBal"></span> <select class="inp" id="tbl"><option>1</option><option>2</option><option>3</option><option>4</option><option>5</option></select></label><span class="tip" data-t="tierTip"></span></div></div>
<div class="grid" id="grid"></div><div class="box"><h3>≡ <span data-t="events"></span></h3><div class="ev" id="ev"></div></div></section>
<section class="page" id="p-chat"><aside id="cl"><button class="btn pri wide" id="cnew">＋ <span data-t="newchat"></span></button><div id="clist"></div></aside>
<div id="cm"><div id="chd"><b id="ctitle"></b><span class="sp"></span><select class="inp" id="cacct"></select><select class="inp" id="cpow"><option value="" data-t="powAuto"></option><option value="strong" data-t="powStrong"></option></select><button class="btn sm" id="cexp">⬇ <span data-t="export"></span></button><button class="btn sm dng" id="cdel">🗑</button></div>
<div id="cscroll"><div id="ctx"></div></div><div id="cbar"><div id="pal" hidden></div><div id="chips2"></div><div id="cbox"><span class="pr">&gt;</span><textarea id="cin" rows="1"></textarea><button class="ib" id="catt" title="Attach">＋</button><button class="ib snd" id="csend">→</button></div><div class="tip" id="chint" style="text-align:center;margin-top:6px"></div></div></div></section>
<section class="page" id="p-live"><div id="ccmirror"></div><div id="ccterm"><div class="cthead"><span class="ctdot"></span><b id="ctttl">Claude Code</b><span id="ctmeta" class="mut"></span><span class="sp"></span><span class="ctb" id="ctpause">Ⅱ</span><span class="ctb" id="ctclear">×</span><span class="ctb" id="ctwrap">↵</span></div><div id="ctlog" class="mono"></div></div><div class="tb" id="livetb"></div><div class="feed" id="livefeed" style="max-height:calc(100vh - 180px)"></div></section><section class="page" id="p-swarm"><div id="swf"></div><div id="swr"></div></section><section class="page" id="p-launch"><div id="lw"></div></section><section class="page" id="p-console"><div id="cw"></div></section>
<section class="page" id="p-connect"><div id="kw"></div></section><section class="page" id="p-settings"><div id="sw"></div></section></div><aside id="dockp"><div class="dh"><b>▣ <span data-t="n_live"></span></b><button class="ib" id="dockx">✕</button></div><div class="feed" id="dockfeed"></div></aside></div>
<div id="navshade" hidden></div><div id="toast"></div><input type="file" id="cfile" multiple hidden><input type="file" id="sfiles" multiple hidden>
<script>
"use strict";
/* Storage can be denied in hardened/opaque browser contexts. Never let that abort the entire UI boot. */
const localStorage=(()=>{try{return window.localStorage}catch(_){const mem=Object.create(null);return new Proxy({getItem:k=>Object.prototype.hasOwnProperty.call(mem,k)?mem[k]:null,setItem:(k,v)=>{mem[k]=String(v)},removeItem:k=>{delete mem[k]},clear:()=>{for(const k of Object.keys(mem))delete mem[k]},key:i=>Object.keys(mem)[i]||null},{get:(t,k)=>k in t?t[k]:mem[k],set:(_t,k,v)=>{mem[k]=String(v);return true},deleteProperty:(_t,k)=>{delete mem[k];return true},ownKeys:()=>Reflect.ownKeys(mem),getOwnPropertyDescriptor:(_t,k)=>({enumerable:true,configurable:true,value:mem[k]})})}})();
/* Define live-mirror state before any boot-time callback can touch it. */
var CC_SESSION=window.CC_SESSION={cwd:"",model:"",tool:"",text:"",event:"",status:"idle"},CC_AGENTS={},CC_SWARM={},CC_LOGS=[];
/* Terminal mirror of the real Claude Code console. */
var CT_LINES=[],CT_SEQ=0,CT_PAUSE=false,CT_AUTOSCROLL=true,CT_STREAM=null,CT_STATUS="idle",CT_LASTT=0;
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const K={
n_dash:["داشبورد","Dashboard"],n_chat:["گفتگو","Chat"],n_launch:["اجرا","Launch"],n_console:["کنسول","Console"],n_connect:["اتصال","Connect"],n_settings:["تنظیمات","Settings"],theme:["تم","Theme"],
nextAcct:["اکانت بعدی","Next account"],add:["افزودن اکانت","Add account"],cancel:["انصراف","Cancel"],yes:["بله","Yes"],save:["ذخیره","Save"],copy:["کپی","Copy"],copied:["کپی شد","Copied"],close:["بستن","Close"],
routing:["مسیریابی درخواست‌ها","Request routing"],autofo:["تعویض خودکار در صورت خطا/شلوغی","Auto-switch on error / busy"],rotReq:["چرخش بعد از (پیام)","Rotate after (msgs)"],rotMin:["یا (دقیقه)","or (min)"],rotTip:["۰ = غیرفعال","0 = off"],
events:["رویدادها","Events"],balanced:["متعادل","Balanced"],round_robin:["چرخشی","Round-robin"],failover:["اولویت","Priority"],pinned:["قفل روی یک اکانت","Pinned"],
balancedD:["گفتگوی جدید به کم‌مصرف‌ترین اکانت؛ گفتگوهای طولانی می‌چرخند","New chats go to the least-used account; long chats rotate"],round_robinD:["نوبتی بین اکانت‌ها","Take turns across accounts"],failoverD:["اولین اکانت سالم لیست؛ بقیه فقط هنگام خطا","First healthy account; others only on errors"],pinnedD:["همه درخواست‌ها به اکانت انتخابی","Everything goes to the chosen account"],
tin:["توکن ورودی","tokens in"],tout:["توکن خروجی","tokens out"],ready:["آماده","Ready"],accounts:["اکانت آماده","accounts ready"],msgs:["پیام","messages"],up:["مدت کارکرد","uptime"],
k_tin:["ورودی ~","in ~"],k_tout:["خروجی ~","out ~"],k_today:["امروز","today"],k_msgs:["پیام","msgs"],k_errs:["خطا / محدودیت","errors / limits"],k_avg:["میانگین","avg"],k_active:["زمان فعالیت","active time"],k_streak:["استفاده پیوسته","continuous use"],k_last:["آخرین استفاده","last used"],
inuse:["در حال استفاده","IN USE"],pin:["قفل‌شده","PINNED"],use:["استفاده","Use"],test:["تست","Test"],login:["ورود مجدد","Re-login"],show:["نمایش پنجره","Show window"],hide:["مخفی‌سازی","Hide window"],restart:["ریستارت","Restart"],enable:["فعال کردن","Enable"],disable:["غیرفعال","Disable"],
reset_convs:["ریست چت‌ها","Reset chats"],purge:["حذف چت‌ها","Purge chats"],rename:["تغییر نام","Rename"],remove:["حذف","Remove"],restore:["بازگردانی","Restore"],chatw:["گفتگو","Chat"],conn:["اتصال","Connect"],chats:["چت باز","open chats"],ago:["پیش","ago"],never:["—","—"],
s_ready:["آماده","Ready"],s_busy:["در حال پاسخ","Generating"],s_cooldown:["استراحت","Cooling"],s_starting:["در حال اجرا","Starting"],s_login:["منتظر ورود","Waiting for login"],s_login_needed:["نیاز به ورود","Login needed"],s_error:["خطا","Error"],s_disabled:["غیرفعال","Disabled"],s_stopped:["متوقف","Stopped"],
addTitle:["افزودن اکانت جدید","Add a new account"],addTip:["یک پنجره کروم باز می‌شود؛ در آن وارد DeepSeek شوید.","A Chrome window opens - log in to DeepSeek there."],create:["ساخت و ورود","Create & log in"],
confirmRm:["این اکانت به‌صورت کامل حذف شود؟ اطلاعات ورود، پروفایل مرورگر، آمار، مسیرهای پروژه و ارجاعات آن برای همیشه حذف می‌شوند.","Permanently delete this account? Its login profile, browser data, usage stats, project routing and references will be removed permanently."],confirmPurge:["همه چت‌های ساخته‌شده توسط bridge در سایت DeepSeek حذف شوند؟","Delete every chat the bridge created on DeepSeek?"],
testing:["در حال تست…","Testing…"],okTest:["سالم","OK"],newName:["نام جدید","New name"],offline:["ارتباط با bridge قطع است","Lost connection to the bridge"],keyPrompt:["API key را وارد کنید","Enter the API key"],
newchat:["گفتگوی جدید","New chat"],export:["خروجی","Export"],autoAcct:["خودکار (متعادل)","Auto (balanced)"],cph:["پیام بنویسید…  ( / برای دستورها )","Message…  ( / for commands )"],
chint:["Enter ارسال · Shift+Enter خط جدید · / دستورها · فایل را بکشید و رها کنید یا Ctrl+V · Esc توقف","Enter send · Shift+Enter newline · / commands · drop files or Ctrl+V · Esc stop"],
welcome:["* به پل DeepSeek خوش آمدید","* Welcome to DeepSeek Bridge"],w1:["/help راهنما · /ds next تعویض اکانت · ＋ ارسال فایل و عکس","/help for help · /ds next switches account · ＋ send files & images"],w2:["حساب:","account:"],
spin:[["در حال فکر کردن","در حال بررسی","در حال نوشتن","در حال پختن","در حال کاویدن"],["Thinking","Pondering","Cooking","Brewing","Noodling"]],esc:["Esc برای توقف","esc to interrupt"],interrupted:["متوقف شد","interrupted"],seeAtt:["(فایل پیوست را ببین)","(see the attached file)"],
tooBig:["فایل بزرگ است","File is too large"],tooMany:["تعداد فایل‌ها زیاد است","Too many files"],
hlp:["/new گفتگوی جدید · /clear پاک کردن · /account [n|نام|auto] · /system متن · /ds دستور · /attach · /copy · /export · /retry","/new · /clear · /account [n|name|auto] · /system text · /ds cmd · /attach · /copy · /export · /retry"],
sysSet:["پرامپت سیستمی تنظیم شد","System prompt set"],acctSet:["اکانت این گفتگو:","This chat uses:"],noAcct:["اکانت پیدا نشد","Account not found"],
lProj:["پوشه پروژه","Project folder"],browse:["انتخاب…","Browse…"],recent:["اخیر","Recent"],lMode:["حالت دسترسی Claude Code","Claude Code permission mode"],
m_safe:["امن","Safe"],m_ask:["پرسشی","Ask"],m_auto:["خودکار","Auto"],m_safeD:["بدون هیچ پرسشی؛ ابزارهای مجاز از پیش تأیید شده‌اند و موارد خطرناک بسته است","No prompts; vetted tools pre-approved, risky ones blocked"],m_askD:["برای هر کار حساس از شما می‌پرسد","Asks before anything sensitive"],m_autoD:["همه چیز بدون پرسش مجاز است (فقط در پوشه‌ی مطمئن)","Everything allowed without asking (trusted folders only)"],
lOpts:["گزینه‌های شروع","Start options"],cont:["ادامه‌ی آخرین نشست (--continue)","Continue last session (--continue)"],resume:["انتخاب نشست قبلی (--resume)","Pick a previous session (--resume)"],extra:["گزینه‌های اضافه (اختیاری)","Extra options (optional)"],
longp:["دستور بلند (مثل یک فایل prompt)","Long task (like a prompt file)"],longpH:["متن کامل کار را اینجا بنویسید؛ در پوشه پروژه به‌صورت AUTONOMOUS_PROMPT.md ذخیره می‌شود","Write the full task here; it is saved as AUTONOMOUS_PROMPT.md in the project folder"],
openCC:["باز کردن Claude Code","Open Claude Code"],copyCmd:["کپی دستور","Copy command"],ccOk:["Claude Code نصب است","Claude Code is installed"],ccNo:["Claude Code نصب نیست","Claude Code is not installed"],install:["نصب Claude Code","Install Claude Code"],
opened:["Claude Code باز شد در","Claude Code opened in"],newF:["پوشه جدید","New folder"],chooseF:["انتخاب این پوشه","Choose this folder"],up1:["بالاتر","Up"],
cons:["دستور بنویسید (help برای راهنما)","type a command (help for the list)"],all:["همه","all"],warn:["هشدار","warnings"],error:["خطا","errors"],pause:["توقف","pause"],clearv:["پاک‌سازی","clear"],dl:["دانلود","download"],run:["اجرا","run"],
cBase:["آدرس","Base URL"],cKey:["کلید API","API key"],cModel:["مدل","Model"],reveal:["نمایش","Show"],cAuto:["همه اکانت‌ها (متعادل)","All accounts (balanced)"],cOnly:["فقط این اکانت","This account only"],
cNote:["مدل نادیده گرفته می‌شود؛ همان گفتگوی DeepSeek استفاده می‌شود. هر نامی بنویسید کار می‌کند.","The model name is ignored; the DeepSeek chat is used. Any name works."],
cProf:["پوشه ورود (پروفایل)","Login profile folder"],
g_claude:["Claude Code","Claude Code"],g_rel:["پایداری و تلاش مجدد","Reliability & retries"],g_ctx:["حافظه و طول گفتگو","Context & chat length"],g_browser:["مرورگر و فایل‌ها","Browser & files"],g_panel:["پنل و شبکه","Panel & network"],
w_live:["فوری","instant"],w_launch:["اجرای بعدی","next launch"],w_browser:["ریستارت اکانت","account restart"],w_bridge:["ریستارت bridge","bridge restart"],
look:["ظاهر","Appearance"],accent:["رنگ","Accent"],maint:["نگهداری","Maintenance"],restartB:["ریستارت bridge","Restart bridge"],stopB:["توقف bridge","Stop bridge"],resetU:["صفر کردن آمار","Reset usage stats"],selftest:["اجرای تست داخلی","Run self-test"],verify:["بررسی حالت امن","Verify safe mode"],
saveChg:["ذخیره تغییرات","Save changes"],saved:["ذخیره شد","Saved"],needRestart:["برای اعمال، ریستارت لازم است:","Restart needed for:"],unsaved:["تغییر ذخیره‌نشده","unsaved change(s)"],
palPh:["جست‌وجوی دستور…","Search commands…"],lang:["تغییر زبان","Switch language"],started:["شروع شد — خروجی در کنسول","Started - output is in Console"],
n_live:["زنده","Live"],n_swarm:["تیم ایجنت","Swarm"],dock:["نمای زنده","Live dock"],g_swarm:["تیم ایجنت (Swarm)","Swarm (parallel agents)"],
smart:["مسیریابی هوشمند بر اساس کیفیت مدل","Smart routing by model quality"],tierStrong:["حداقل سطح برای کار سنگین","Min tier for hard work"],tierBal:["حداقل سطح کار عادی","Min tier for normal work"],
tierTip:["opus ← قوی‌ترین حساب · sonnet ← ارزان‌ترینِ کافی · haiku ← ارزان‌ترین","opus → strongest account · sonnet → cheapest good enough · haiku → cheapest"],
cost:["هزینه","cost"],capacity:["ظرفیت موازی","parallel capacity"],editAcc:["ویرایش","Edit"],keep:["خالی = بدون تغییر","empty = keep"],
wizTitle:["چه اکانتی اضافه کنیم؟","Which account do you want to add?"],f_name:["نام","Name"],f_base:["آدرس API","API base URL"],f_key:["کلید API","API key"],f_model:["مدل","Model"],f_tier:["سطح کیفیت","Quality tier"],f_par:["درخواست همزمان","Parallel requests"],
f_pin:["قیمت ورودی ($ هر میلیون توکن)","Input price ($ per M tokens)"],f_pout:["قیمت خروجی ($ هر میلیون توکن)","Output price ($ per M tokens)"],f_budget:["سقف بودجه ($، ۰ = نامحدود)","Budget limit ($, 0 = none)"],fetchM:["دریافت مدل‌ها","Fetch models"],testAdd:["افزودن و تست","Add & test"],
tier1:["پایه","Basic"],tier2:["سریع","Fast"],tier3:["استاندارد","Standard"],tier4:["قوی","Strong"],tier5:["برتر","Top"],s_budget:["بودجه تمام شد","Budget used"],powAuto:["قدرت: خودکار","Power: auto"],powStrong:["قدرت: بالا","Power: strong"],
lv_all:["همه","all"],lv_main:["اصلی","main"],lv_agent:["ایجنت‌ها","agents"],lv_side:["جانبی","side"],lvEmpty:["هنوز فعالیتی نیست؛ Claude Code را اجرا کنید یا پیامی بفرستید.","No activity yet - start Claude Code or send a message."],
swNew:["شروع یک تیم ایجنت موازی","Start a parallel agent team"],swGoalPh:["چه چیزی ساخته شود؟ (مثلاً: بک‌اند API + رابط کاربری + تست‌ها)","What should the team build? (e.g. backend API + UI + tests)"],swAgents:["ایجنت همزمان","parallel agents"],swAuto:["خودکار","auto"],swOff:["خاموش","off"],swOn:["روشن","on"],
swVerify:["اجرای تست/بیلد","Run tests / build"],swReview:["بازبینی با حساب قوی‌تر","Review with a stronger account"],swStrict:["محدودیت سخت‌گیرانه‌ی مسیرها","Strict path ownership"],swInit:["اگر git نیست، بساز","git init if needed"],
swManual:["لیست دستی تسک‌ها (به‌جای برنامه‌ریزی خودکار)","Manual task list (instead of auto-planning)"],swManualPh:["هر خط یک تسک","one task per line"],swStart:["شروع","Start"],
swTip:["هر ایجنت در worktree و branch جدا کار می‌کند؛ تا «اعمال» نزنید به پروژه‌تان دست نمی‌خورد.","Each agent works in its own worktree/branch; nothing touches your project until you press Apply."],
swNone:["هنوز اجرایی نیست","No runs yet"],swStop:["توقف","Stop"],swApply:["اعمال روی پروژه","Apply to project"],swApplied:["اعمال شد","APPLIED"],swCleanup:["پاک‌سازی worktreeها","Clean up worktrees"],
swApplyQ:["نتیجه با branch فعلی شما ادغام شود؟","Merge the result into your current branch?"],swCleanQ:["worktreeها و branchهای موقت پاک شوند؟","Remove the temporary worktrees and branches?"],swContracts:["قراردادهای مشترک","Shared contracts"],swTask:["تسک","Task"],
sg_queued:["در صف","queued"],sg_starting:["شروع","starting"],sg_running:["در حال کار","working"],sg_verifying:["بررسی","checking"],sg_reviewing:["بازبینی","reviewing"],sg_merging:["ادغام","merging"],sg_merged:["ادغام شد","merged"],sg_done:["تمام","done"],
sg_failed:["ناموفق","failed"],sg_conflict:["تداخل","conflict"],sg_skipped:["رد شد","skipped"],sg_stopped:["متوقف","stopped"],sg_planning:["برنامه‌ریزی","planning"],sg_done_with_issues:["تمام با مشکل","done with issues"],
ccMirror:["آینه زنده Claude Code","Claude Code live mirror"],ccConnected:["متصل","connected"],ccSnapshot:["نمای ایستا","snapshot"],ccEvent:["رویداد","event"],ccProject:["پروژه","Project"],ccAgents:["ایجنت‌ها","Agents"],ccNoAgents:["هنوز ایجنتی فعال نیست","No active agents"],
swImprove:["＋ بهبود با AI","＋ Improve with AI"],swImproving:["در حال بهبود…","Improving…"],swOriginal:["پرامپت اصلی","Original prompt"],swImproved:["نسخه بهبود‌یافته","AI-improved prompt"],swCustom:["تغییرات/توضیحات بیشتر","Additional changes / instructions"],swUseImproved:["استفاده به‌عنوان نهایی","Use as final"],swImproveAgain:["بهبود دوباره","Improve again"],swApplyCustom:["اعمال تغییرات به نسخه AI","Apply changes to AI version"],swFinalReady:["این نسخه برای ایجنت‌ها ارسال می‌شود","This version will be sent to the agents"],swAttach:["پیوست فایل","Attach files"],swAttachTip:["هر فرمت فایل قابل ارسال است؛ فایل‌ها در ورودی ایزوله Agent قرار می‌گیرند.","Any file format is accepted; files are placed in an isolated Agent input folder."],swUploading:["در حال آپلود فایل…","Uploading files…"],swAttached:["پیوست","attachments"],swRemoveAttachment:["حذف پیوست","Remove attachment"],
};
let L=localStorage.dsb_lang||"fa";const t=k=>(K[k]||[k,k])[L==="fa"?0:1];
let KEY=localStorage.dsb_key||"";const hm=location.hash.match(/[#&]k=([^&]+)/);if(hm){KEY=decodeURIComponent(hm[1]);localStorage.dsb_key=KEY}
const tok=n=>n>=1e6?(n/1e6).toFixed(2)+"M":n>=1e3?(n/1e3).toFixed(1)+"k":String(n|0);
const dur=s=>{s=Math.max(0,s|0);const H=s/3600|0,M=(s%3600)/60|0,X=s%60;return H?H+"h "+String(M).padStart(2,"0")+"m":M?M+"m "+String(X).padStart(2,"0")+"s":X+"s"};
const strip=s=>String(s).replace(/\x1b\[[0-9;]*m/g,"");
function toast(m){const d=document.createElement("div");d.textContent=m;$("#toast").append(d);setTimeout(()=>d.remove(),4800)}
async function api(p,b){const o={headers:{Authorization:"Bearer "+KEY}};if(b!==undefined){o.method="POST";o.headers["Content-Type"]="application/json";o.body=JSON.stringify(b)}
const r=await fetch("/dash/api/"+p,o);if(r.status===401){KEY=prompt(t("keyPrompt"))||"";localStorage.dsb_key=KEY;const e=new Error("401");e.status=401;throw e}
const j=await r.json().catch(()=>({}));if(!r.ok){const e=new Error(j.error&&j.error.message||r.status);e.status=r.status;throw e}return j}
async function act(a,b){try{const r=await api(a,b||{});if(r.text)toast(r.text);return r}catch(e){toast("! "+e.message);return null}}
function modal(html,cls="",dismiss=true){const ov=document.createElement("div");ov.className="ov";ov.innerHTML=`<div class="mdl ${cls}">${html}</div>`;
if(dismiss)ov.addEventListener("mousedown",e=>{if(e.target===ov)ov.close()});document.body.append(ov);requestAnimationFrame(()=>ov.classList.add("on"));ov.close=()=>{ov.classList.remove("on");setTimeout(()=>ov.remove(),180)};return ov}
const ask=(msg,ok)=>new Promise(res=>{const o=modal(`<p>${esc(msg)}</p><div class="rowb"><button class="btn" data-x>${t("cancel")}</button><button class="btn pri" data-ok>${ok||t("yes")}</button></div>`,"",false);
o.onclick=e=>{const b=e.target.closest("button");if(!b)return;o.close();res(b.hasAttribute("data-ok"))}});
const inputBox=(title,val="",ph="")=>new Promise(res=>{const o=modal(`<h3>${esc(title)}</h3><input class="inp" id="mi" placeholder="${esc(ph)}" value="${esc(val)}"><div class="rowb"><button class="btn" data-x>${t("cancel")}</button><button class="btn pri" data-ok>OK</button></div>`,"",false);
const i=$("#mi",o);i.focus();i.select();const done=v=>{o.close();res(v)};o.onclick=e=>{const b=e.target.closest("button");if(b)done(b.hasAttribute("data-ok")?i.value.trim():null)};i.onkeydown=e=>{if(e.key==="Enter")done(i.value.trim());if(e.key==="Escape")done(null)}});
const copyText=async s=>{try{await navigator.clipboard.writeText(s)}catch{const x=document.createElement("textarea");x.value=s;document.body.append(x);x.select();document.execCommand("copy");x.remove()}toast(t("copied"))};
const mk=h=>{const d=document.createElement("div");d.innerHTML=h.trim();return d.firstChild};
/* ---------- theme / language / router ---------- */
function applyTheme(){document.documentElement.dataset.theme=localStorage.dsb_theme||"light";document.documentElement.dataset.acc=localStorage.dsb_acc||"sky"}
function applyUiMode(){document.documentElement.dataset.ux=localStorage.dsb_ux||((INFO&&INFO.ui_mode)==="pro"?"pro":"beginner")}
let S=null,INFO=null,page="dash";const PAGES=["dash","live","chat","swarm","launch","console","connect","settings"];
let dashStream=null,dashStreamReady=false,dashReconnectTimer=null;

function applyUiPerformance(){const configured=(INFO&&INFO.ui_performance_mode)||"auto";let mode=configured;if(mode==="auto"){const ram=Number(navigator.deviceMemory||0),cpu=Number(navigator.hardwareConcurrency||0);mode=(ram&&ram<=8)||(cpu&&cpu<=4)?"light":"balanced"}document.documentElement.dataset.perf=mode}
function renderClaudeMirror(){
 const box=$("#ccmirror");
 if(!box)return;
 const sess=window.CC_SESSION||(window.CC_SESSION={cwd:"",model:"",tool:"",text:"",event:"",status:"idle"});
 const project=(sess.cwd||(INFO&&INFO.project))||"—";
 const active=Object.values(CC_AGENTS).filter(a=>["starting","running","verifying","reviewing","merging"].includes(a.status));
 const rs=CC_SWARM.status||"idle";
 const chips=active.length?active.slice(-8).map(a=>`<span class="ccma"><b>${esc(a.agent||"agent")}</b> <span>${esc(a.activity||a.status||"")}</span></span>`).join(""):`<span class="tip">${t("ccNoAgents")}</span>`;
 const logs=CC_LOGS.slice(-4).map(x=>`<div class="ccmrow"><span>${esc(x.level||"info")}:</span><span>${esc(x.message||"")}</span></div>`).join("");
 const liveText=sess.text?`<div class="ccmtext" dir="auto">${esc(sess.text)}</div>`:"";
 const model=sess.model?`<span class="chip">${esc(sess.model)}</span>`:"";
 const evt=sess.event?`<div class="ccmrow"><span>${t("ccEvent")}:</span><span>${esc(sess.event)}${sess.tool?` · ${esc(sess.tool)}`:""}</span></div>`:"";
 box.innerHTML=`<div class="ccm"><div class="ccmhead"><b>* ${t("ccMirror")}</b><span class="ccmstate">• ${dashStreamReady?t("ccConnected"):t("ccSnapshot")}</span></div><div class="ccmrow"><span>${t("ccProject")}:</span><span class="pth">${esc(project)}</span>${model}<span class="chip">${esc(rs)}</span><span class="chip">${t("ccAgents")}: ${active.length}</span></div>${evt}<div class="ccmagents">${chips}</div>${liveText}${logs}</div>`;
}
/* ---------- Claude Code console (terminal mirror) ---------- */
const ctNow=()=>{const d=new Date();return d.toTimeString().slice(0,8)};
function ctPush(kind,text,meta){
 const line={n:++CT_SEQ,k:kind,t:ctNow(),m:text||"",x:meta||""};
 CT_LINES.push(line);if(CT_LINES.length>800)CT_LINES.splice(0,CT_LINES.length-800);
 ctRenderOne(line);
}
function ctRenderOne(l){
 const box=$("#ctlog");if(!box)return;
 const near=CT_AUTOSCROLL&&(box.scrollHeight-box.scrollTop-box.clientHeight<60);
 const el=document.createElement("span");el.className="ctl ct-"+l.k;el.dataset.n=l.n;
 el.innerHTML=`<span class="cts">${esc(l.t)}</span><span class="ctc">${esc(l.m)}</span>${l.x?` <span class="ctn">${esc(l.x)}</span>`:""}`;
 box.appendChild(el);while(box.childElementCount>800)box.firstChild.remove();
 if(near&&!CT_PAUSE)box.scrollTop=box.scrollHeight;
}
function ctRenderAll(){
 const box=$("#ctlog");if(!box)return;box.innerHTML="";
 const near=CT_AUTOSCROLL;
 CT_LINES.forEach(l=>{const el=document.createElement("span");el.className="ctl ct-"+l.k;el.dataset.n=l.n;
  el.innerHTML=`<span class="cts">${esc(l.t)}</span><span class="ctc">${esc(l.m)}</span>${l.x?` <span class="ctn">${esc(l.x)}</span>`:""}`;
  box.appendChild(el)});
 if(near&&!CT_PAUSE)box.scrollTop=box.scrollHeight;
}
function ctStatus(txt){CT_STATUS=txt;const m=$("#ctmeta");if(m)m.textContent=txt?("· "+txt):""}
function ctFromClaude(d){
 const ev=d.event||"";
 if(ev==="UserPromptSubmit"){ctPush("prompt","› "+String(d.text||"").trim());ctStatus("prompt");}
 else if(ev==="MessageDisplay"){const txt=String(d.text||"");if(!txt)return;
  const last=CT_LINES[CT_LINES.length-1];
  if(d.final){if(last&&last.k==="asst"&&last.__stream){last.m+=txt;const n=last.n;const b=$(`#ctlog .ctl[data-n="${n}"] .ctc`);if(b){b.textContent=last.m;const box=$("#ctlog");if(box&&CT_AUTOSCROLL&&!CT_PAUSE)box.scrollTop=box.scrollHeight}delete last.__stream}else{ctPush("asst",txt)}ctStatus("idle")}
  else{if(last&&last.k==="asst"&&last.__stream){last.m+=txt;const n=last.n;const b=$(`#ctlog .ctl[data-n="${n}"] .ctc`);if(b){b.textContent=last.m;const box=$("#ctlog");if(box&&CT_AUTOSCROLL&&!CT_PAUSE)box.scrollTop=box.scrollHeight}}else{CT_LINES.push({n:++CT_SEQ,k:"asst",t:ctNow(),m:txt,x:"",__stream:true});ctRenderOne(CT_LINES[CT_LINES.length-1])}ctStatus("working…")}}
 else if(ev==="PreToolUse"){const i=d.input||{};const arg=i.command||i.file_path||i.path||i.pattern||i.query||"";ctPush("tool","→ "+String(d.tool_name||"tool"),arg?`${arg}`:"");ctStatus(String(d.tool_name||"tool"));}
 else if(ev==="PostToolUse"){ctPush("ok","✓ "+String(d.tool_name||"tool"),d.duration_ms?d.duration_ms+"ms":"");ctStatus("idle");}
 else if(ev==="PostToolUseFailure"){ctPush("toolerr","✗ "+String(d.tool_name||"tool"),(d.duration_ms?d.duration_ms+"ms ":"")+String(d.reason||""));ctStatus("tool failed");}
 else if(ev==="Notification"){ctPush("notice","! "+String(d.text||"").trim());}
 else if(ev==="SessionStart"){ctPush("sys","session · "+String(d.model||""),String(d.source||""));ctStatus("ready");}
 else{ctPush("sys",ev,function(){const i=d.input||{};return i.command||i.file_path||i.path||""}());}
}
function ctBind(){
 const log=$("#ctlog");if(log&&!log.__bound){log.__bound=true;
  log.addEventListener("scroll",()=>{const b=$("#ctlog");CT_AUTOSCROLL=b.scrollHeight-b.scrollTop-b.clientHeight<60});}
 const p=$("#ctpause");if(p&&!p.__b){p.__b=true;p.onclick=()=>{CT_PAUSE=!CT_PAUSE;p.classList.toggle("on",CT_PAUSE)};}
 const c=$("#ctclear");if(c&&!c.__b){c.__b=true;c.onclick=()=>{CT_LINES=[];ctRenderAll()};}
 const w=$("#ctwrap");if(w&&!w.__b){w.__b=true;w.onclick=()=>{const b=$("#ctlog");if(b)b.style.whiteSpace=b.style.whiteSpace==="pre"?"pre-wrap":"pre"};}
}
function renderClaudeTerm(){ctBind();ctRenderAll();}

function applyDashEvent(kind,data){
 if(kind==="settings"){
  if(INFO&&Array.isArray(data.settings))INFO.settings=data.settings;
  if(INFO&&data.project)INFO.project=data.project;
  applyUiPerformance();
  if(page==="settings")renderSettings();
  renderClaudeMirror();
 }else if(kind==="project"){
  if(INFO&&data.project){
   INFO.project=data.project;
   const p=$("#sp");
   if(p&&p.dataset.autoProject!=="0")p.value=data.project;
  }
  renderClaudeMirror();
 }else if(kind==="activity"){
  if(data&&data.n){
   FEED.push(data);feedLast=Math.max(feedLast,data.n);
   if(FEED.length>400)FEED.splice(0,FEED.length-400);
   addFeed(data);renderClaudeMirror();
  }
 }else if(kind==="agent"){
  if(data&&data.agent)CC_AGENTS[data.agent]={...(CC_AGENTS[data.agent]||{}),...data};
  renderClaudeMirror();
 }else if(kind==="swarm"){
  if(data&&data.run)CC_SWARM={...CC_SWARM,...data};
  renderClaudeMirror();
 }else if(kind==="pool"){
  CC_LOGS.push({level:data.level||"info",message:data.msg||""});
  if(CC_LOGS.length>60)CC_LOGS.splice(0,CC_LOGS.length-60);
  renderClaudeMirror();
 }else if(kind==="console"){
  CC_LOGS.push({level:data.level||"info",message:data.message||""});
  if(CC_LOGS.length>60)CC_LOGS.splice(0,CC_LOGS.length-60);
  renderClaudeMirror();
 }else if(kind==="request"){
  CC_LOGS.push({level:"info",message:`request · ${data.model||""}${data.tag?` · ${data.tag}`:""}`});
  if(CC_LOGS.length>60)CC_LOGS.splice(0,CC_LOGS.length-60);
  renderClaudeMirror();
 }else if(kind==="claude"){
  window.CC_SESSION={...(window.CC_SESSION||{}),...data,status:data.event||"active",cwd:data.cwd||(window.CC_SESSION&&window.CC_SESSION.cwd)||"",model:data.model||(window.CC_SESSION&&window.CC_SESSION.model)||"",tool:data.tool_name||"",text:data.text||"",event:data.event||""};
  if(data.event!=="MessageDisplay"){
   CC_LOGS.push({level:"info",message:`Claude · ${data.event||"event"}${data.tool_name?` · ${data.tool_name}`:""}`});
   if(CC_LOGS.length>60)CC_LOGS.splice(0,CC_LOGS.length-60);
  }
  ctFromClaude(data);
  renderClaudeMirror();
 }else if(kind==="prompt_improved"){
  renderClaudeMirror();
 }
}

function connectDashStream(){if(!KEY||dashStream||document.hidden)return;try{dashStream=new EventSource("/dash/api/stream?key="+encodeURIComponent(KEY));dashStreamReady=false;for(const k of ["activity","agent","swarm","pool","console","request","project","settings","attachment","prompt_improved","claude"])dashStream.addEventListener(k,e=>{try{applyDashEvent(k,JSON.parse(e.data||"{}"))}catch{}});dashStream.onopen=()=>{dashStreamReady=true;syncFeed()};dashStream.onerror=()=>{dashStreamReady=false;if(dashStream){dashStream.close();dashStream=null}if(!dashReconnectTimer&&!document.hidden)dashReconnectTimer=setTimeout(()=>{dashReconnectTimer=null;connectDashStream()},2500)}}catch{dashStream=null;dashStreamReady=false}}
function closeDashStream(){if(dashReconnectTimer){clearTimeout(dashReconnectTimer);dashReconnectTimer=null}if(dashStream){dashStream.close();dashStream=null}dashStreamReady=false}
document.addEventListener("visibilitychange",()=>{if(document.hidden)closeDashStream();else{connectDashStream();tick()}});
async function loadInfo(force){if(!INFO||force){INFO=await api("info");applyUiPerformance();applyUiMode()}connectDashStream();return INFO}
function applyLang(){document.documentElement.lang=L;document.documentElement.dir=L==="fa"?"rtl":"ltr";$("#blang span").textContent=L==="fa"?"EN":"فا";
$$("[data-t]").forEach(e=>e.textContent=t(e.dataset.t));$("#cin").placeholder=t("cph");$("#chint").textContent=t("chint");for(const k in cards){cards[k].remove();delete cards[k]}segKey="";go(page,true)}
function go(p,again){if(!PAGES.includes(p))p="dash";page=p;document.querySelector("#app")?.classList.remove("navopen");const ns=document.querySelector("#navshade");if(ns)ns.hidden=true;$$(".page").forEach(e=>e.classList.toggle("on",e.id==="p-"+p));$$('.nb[data-go]').forEach(e=>e.classList.toggle('on',e.dataset.go===p));
$("#ttl").textContent=t("n_"+p);history.replaceState(null,"","#/"+p);if(p!=="console")stopLogs();
({dash:()=>S&&renderDash(),live:enterLive,chat:enterChat,swarm:enterSwarm,launch:renderLaunch,console:enterConsole,connect:renderConnect,settings:renderSettings})[p]();syncFeed()}
/* ---------- state poll + dashboard ---------- */
let segKey="";const cards={};
function cardTpl(a){return `<div class="card" data-id="${a.id}"><div class="ch"><span class="idx" data-f="idx"></span><b data-f="name"></b><span class="tag live" data-f="live">${t("inuse")}</span><span class="tag pin" data-f="pin">${t("pin")}</span><span class="pill" data-f="pill"></span></div><div class="sub" data-f="sub"></div>
<div class="kv pro-only">${["tin","tout","today","msgs","errs","avg","active","streak","last"].map(k=>`<div><span>${t("k_"+k)}</span><b data-f="kv_${k}"></b></div>`).join("")}</div>
<div class="bar"><i data-f="bar"></i></div><div data-f="spark"></div><div class="err" data-f="err"></div><div class="tip" data-f="chats"></div>
<div class="act"><button class="btn sm pri" data-a="use">${t("use")}</button><button class="btn sm" data-a="chat">» ${t("chatw")}</button><button class="btn sm" data-a="connect">⌁ ${t("conn")}</button><button class="btn sm" data-a="test">${t("test")}</button>
<details class="more"><summary class="btn sm">⋯</summary><div class="menu"><button data-a="edit">${t("editAcc")}</button><button data-a="login" data-web>${t("login")}</button><button data-a="show" data-f="bshow">${t("show")}</button><button data-a="hide" data-f="bhide">${t("hide")}</button><button data-a="restart">${t("restart")}</button>
<button data-a="enable" data-f="ben">${t("enable")}</button><button data-a="disable" data-f="bdis">${t("disable")}</button><button data-a="reset_convs" data-web>${t("reset_convs")}</button><button data-a="purge" data-web>${t("purge")}</button><button data-a="rename">${t("rename")}</button><button data-a="up">▲</button><button data-a="down">▼</button><button class="dng" data-a="remove" data-f="remove">${t("remove")}</button></div></details></div></div>`}
const F=(el,f)=>el.querySelector(`[data-f=${f}]`),setf=(el,f,v)=>{const n=F(el,f);if(n&&n.textContent!==String(v))n.textContent=v};
const pvIcon=id=>{const p=((INFO&&INFO.providers)||[]).find(x=>x.id===id);return p?p.icon:"⌁"};
function spark(v){const m=Math.max(1,...v),w=240,H=34;return `<svg class="sp" viewBox="0 0 ${w} ${H}" preserveAspectRatio="none"><polyline fill="none" stroke="var(--ac)" stroke-width="1.7" stroke-linejoin="round" points="${v.map((x,i)=>(i*w/59).toFixed(1)+","+(H-2-x/m*(H-6)).toFixed(1)).join(" ")}"/></svg>`}
function updCard(el,a,tt){const s=a.stats;el.classList.toggle("cur",a.current);el.classList.toggle("off",!a.enabled);el.classList.toggle("deleted",!!a.deleted);setf(el,"idx","#"+a.idx);setf(el,"name",a.name);
F(el,"live").hidden=!a.current;F(el,"pin").hidden=!(S.settings.strategy==="pinned"&&a.pinned);const p=F(el,"pill");p.className="pill st-"+a.state;p.textContent=t("s_"+a.state)+(a.state==="cooldown"?" "+dur(a.cooldown_left):"");
const v={tin:tok(s.in_tok),tout:tok(s.out_tok),today:tok(s.today_in+s.today_out),msgs:s.req,errs:s.err+" / "+s.rate_limits,avg:s.avg_s+"s",active:dur(s.active_s),streak:dur(s.streak_s)+(s.streak_live?" •":""),last:s.last_used_ago==null?t("never"):dur(s.last_used_ago)+" "+t("ago")};
for(const k in v)setf(el,"kv_"+k,v[k]);F(el,"bar").style.width=((s.in_tok+s.out_tok)/tt*100).toFixed(0)+"%";F(el,"spark").innerHTML=spark(s.spark);
setf(el,"err",a.status_err||(s.last_error&&s.last_error_ago<1800?s.last_error:""));const web=a.kind==="web";setf(el,"sub",pvIcon(a.provider)+" "+(web?"DeepSeek":a.model)+" · T"+a.tier+" "+stars(a.tier));const rm=F(el,"remove");if(rm)rm.hidden=!!a.deleted;
setf(el,"chats",web?a.chats+" "+t("chats")+(a.headed?" · □":""):"⚡ ×"+a.max_parallel+(a.cost>0||a.budget>0?" · $"+a.cost.toFixed(4)+(a.budget>0?" / $"+a.budget:""):""));
el.querySelectorAll("[data-web]").forEach(b=>b.hidden=!web);F(el,"bshow").hidden=!web||a.headed;F(el,"bhide").hidden=!web||!a.headed;F(el,"ben").hidden=a.enabled;F(el,"bdis").hidden=!a.enabled}
function renderDash(){const T=S.totals,A=S.accounts,st=S.settings;
$("#tiles").innerHTML=[[S.ready+" / "+A.length,t("accounts")],[T.req,t("msgs")],["~"+tok(T.in_tok),t("tin")],["~"+tok(T.out_tok),t("tout")],[S.capacity,t("capacity")],[dur(S.uptime),t("up")],...(T.cost>0?[["$"+T.cost.toFixed(4),t("cost")]]:[])].map(x=>`<div class="tile"><b>${esc(x[0])}</b><span>${esc(x[1])}</span></div>`).join("");
if(segKey!==st.strategy+L){segKey=st.strategy+L;$("#seg").innerHTML=["balanced","round_robin","failover","pinned"].map(k=>`<label><input type="radio" name="sg" value="${k}" ${st.strategy===k?"checked":""}><b>${t(k)}</b><small>${t(k+"D")}</small></label>`).join("")}
for(const [id,k] of [["rr","rotate_requests"],["rm","rotate_minutes"]])if(document.activeElement.id!==id)$("#"+id).value=st[k];$("#fo").checked=st.auto_failover;$("#sm").checked=st.smart_routing;if(document.activeElement.id!=="ts")$("#ts").value=st.tier_strong;if(document.activeElement.id!=="tbl")$("#tbl").value=st.tier_balanced;
const tt=A.reduce((s,a)=>s+a.stats.in_tok+a.stats.out_tok,0)||1,grid=$("#grid"),seen=new Set();
A.forEach((a,i)=>{seen.add(a.id);let el=cards[a.id];if(!el)el=cards[a.id]=mk(cardTpl(a));updCard(el,a,tt);if(grid.children[i]!==el)grid.insertBefore(el,grid.children[i]||null)});
for(const id in cards)if(!seen.has(id)){cards[id].remove();delete cards[id]}
$("#ev").innerHTML=S.events.map(e=>`<div class="${e.level}"><time>${new Date(e.t*1e3).toLocaleTimeString()}</time>${esc(e.msg)}</div>`).join("")}
function renderChips(){const a=S.accounts.find(x=>x.current);$("#chips").innerHTML=`<span class="chip"><i class="dot ${S.ready?"":"off"}"></i>${S.ready}/${S.accounts.length}</span> <span class="chip">${t(S.settings.strategy)}</span>${a?` <span class="chip">▶ ${esc(a.name)}</span>`:""}`}
let timer;async function tick(){clearTimeout(timer);try{S=await api("state");$("#off").style.display="none";renderChips();if(page==="dash")renderDash();if(page==="chat")fillAcct()}catch(e){if(e.status!==401){$("#off").textContent=t("offline");$("#off").style.display="block"}}timer=setTimeout(tick,document.hidden?8000:(dashStreamReady?4500:2200))}
$("#grid").addEventListener("click",async e=>{const b=e.target.closest("button[data-a]");if(!b)return;const id=b.closest(".card").dataset.id,a=b.dataset.a,acc=S.accounts.find(x=>x.id===id);const dt=b.closest("details");if(dt)dt.removeAttribute("open");
if(a==="remove"){if(await ask(t("confirmRm"))){const removedId=id;const r=await act("remove",{id});if(r!==false){if(chatAcctPref===removedId)chatAcctPref="";let changed=false;for(const c of chats){if(c.acct===removedId){c.acct="";changed=true}}if(connAcct===removedId)connAcct="";if(changed)persist();}}}
else if(a==="rename"){const n=await inputBox(t("newName"),acc.name);if(n)await act("rename",{id,name:n})}else if(a==="up"||a==="down")await act("move",{id,dir:a==="up"?-1:1});
else if(a==="chat"){chatAcctPref=id;go("chat")}else if(a==="connect"){connAcct=id;go("connect")}
else if(a==="test"){toast(t("testing"));const r=await act("test",{id});if(r)toast(r.ok?`✓ ${acc.name}: ${t("okTest")} (${r.seconds}s)`:"× "+r.error)}else await act(a,{id});tick()});
$("#seg").addEventListener("change",async e=>{await act("settings",{strategy:e.target.value});tick()});
const sv=async()=>{await act("settings",{auto_failover:$("#fo").checked,rotate_requests:+$("#rr").value||0,rotate_minutes:+$("#rm").value||0,smart_routing:$("#sm").checked,tier_strong:+$("#ts").value,tier_balanced:+$("#tbl").value})};["fo","rr","rm","sm","ts","tbl"].forEach(i=>$("#"+i).onchange=sv);
$("#hnext").onclick=async()=>{await act("command",{text:"next"});tick()};
async function addAccount(){const n=await inputBox(t("addTitle"),"",t("addTip"));if(n===null)return;const r=await act("add",{name:n});if(r){toast(t("addTip"));tick()}}$("#hadd").onclick=addAccount;
/* ---------- chat (Claude-Code style) ---------- */
let chats=[],cur=null,atts=[],busy=null,chatAcctPref="",lastAtts=[];try{chats=JSON.parse(localStorage.dsb_chats||"[]")}catch{}
const persist=()=>{try{localStorage.dsb_chats=JSON.stringify(chats.slice(0,40).map(c=>({...c,msgs:c.msgs.map(m=>m.role==="note"?m:{role:m.role,content:typeof m.content==="string"?m.content:m.content.map(b=>b.type==="text"?b:{type:"text",text:"["+(b.title||b.type)+"]"})})})))}catch{}};
function newChat(){cur={id:"c"+Date.now().toString(36),title:"",msgs:[],system:"",acct:chatAcctPref};chats.unshift(cur);persist();renderList();renderTx();return cur}
function enterChat(){loadInfo().catch(()=>{});if(!cur)cur=chats[0]||null;if(chatAcctPref&&cur&&!cur.msgs.length)cur.acct=chatAcctPref;fillAcct();renderList();renderTx();$("#cin").focus()}
function fillAcct(){if(!S)return;const sel=$("#cacct"),want=cur?cur.acct:chatAcctPref,sig=S.accounts.map(a=>a.id+a.name).join()+L;if(sel.dataset.sig!==sig){sel.dataset.sig=sig;sel.innerHTML=`<option value="">${t("autoAcct")}</option>`+S.accounts.map(a=>`<option value="${a.id}">${esc(a.name)}</option>`).join("")}sel.value=want||"";$("#cpow").value=(cur&&cur.power)||""}
function renderList(){$("#clist").innerHTML=chats.map(c=>`<div class="ci ${cur&&c.id===cur.id?"on":""}" data-id="${c.id}"><span>${esc(c.title||t("newchat"))}</span><button class="ib" data-del>✕</button></div>`).join("");$("#ctitle").textContent=cur?cur.title||t("newchat"):t("newchat")}
$("#clist").addEventListener("click",e=>{const it=e.target.closest(".ci");if(!it)return;const id=it.dataset.id;if(e.target.closest("[data-del]")){chats=chats.filter(c=>c.id!==id);if(cur&&cur.id===id)cur=chats[0]||null;persist()}else{cur=chats.find(c=>c.id===id)}fillAcct();renderList();renderTx()});
$("#cnew").onclick=()=>{newChat();fillAcct()};$("#cdel").onclick=async()=>{if(!cur||!await ask(t("remove")+"?"))return;chats=chats.filter(c=>c!==cur);cur=chats[0]||null;persist();fillAcct();renderList();renderTx()};
$("#cacct").onchange=e=>{chatAcctPref=e.target.value;if(cur)cur.acct=e.target.value;persist()};
function inl(s){s=esc(s).replace(/`([^`\n]+)`/g,"<code>$1</code>").replace(/\*\*([^*\n]+)\*\*/g,"<b>$1</b>").replace(/(^|[\s(])\*([^*\n]+)\*/g,"$1<i>$2</i>").replace(/\[([^\]\n]+)\]\((https?:[^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
let out="",li=null;const close=()=>{if(li){out+=`</${li}>`;li=null}};for(const ln of s.split("\n")){let m;
if(m=/^(#{1,4})\s+(.*)$/.exec(ln)){close();out+=`<h${m[1].length+1}>${m[2]}</h${m[1].length+1}>`}
else if(m=/^\s*[-*]\s+(.*)$/.exec(ln)){if(li!=="ul"){close();out+="<ul>";li="ul"}out+=`<li>${m[1]}</li>`}
else if(m=/^\s*\d+[.)]\s+(.*)$/.exec(ln)){if(li!=="ol"){close();out+="<ol>";li="ol"}out+=`<li>${m[1]}</li>`}
else if(m=/^&gt;\s?(.*)$/.exec(ln)){close();out+=`<blockquote>${m[1]}</blockquote>`}else if(!ln.trim()){close();out+="<br>"}else{close();out+=ln+"<br>"}}close();return out}
function md(src){return String(src).split(/(```[\s\S]*?(?:```|$))/g).map(p=>{if(p.startsWith("```")){const m=/^```([\w+#.-]*)\n?([\s\S]*?)(?:```)?$/.exec(p);return `<div class="code"><div class="cb"><span>${esc(m[1]||"text")}</span><button data-copy>□ ${t("copy")}</button></div><pre><code>${esc(m[2].replace(/\n$/,""))}</code></pre></div>`}return inl(p)}).join("")}
function userEl(m){const bl=typeof m.content==="string"?[{type:"text",text:m.content}]:m.content;let h="",txt="";for(const b of bl){if(b.type==="image")h+=`<img class="th" src="data:${b.source.media_type};base64,${b.source.data}">`;else if(b.type==="document")h+=`<span class="fc">□ ${esc(b.title||"file")}</span>`;else txt+=b.text}
return mk(`<div class="um"><span class="pr">&gt;</span><div class="ub">${h}${esc(txt)}</div></div>`)}
const asstEl=txt=>mk(`<div class="am"><span class="bl">•</span><div class="md">${md(txt)}</div></div>`);
function renderTx(){const box=$("#ctx");box.innerHTML="";if(!cur||!cur.msgs.length){const a=S&&S.accounts.find(x=>x.id===(cur?cur.acct:chatAcctPref));box.append(mk(`<div class="wel"><b>${t("welcome")}</b><div>${t("w1")}</div><div>${t("w2")} ${esc(a?a.name:t("autoAcct"))}</div></div>`))}
if(cur)for(const m of cur.msgs){if(m.role==="user")box.append(userEl(m));else if(m.role==="assistant")box.append(asstEl(typeof m.content==="string"?m.content:m.content.map(b=>b.text||"").join("")));else box.append(mk(`<div class="nt ${m.err?"e":""}">⎿ ${esc(m.text)}</div>`))}
scrollEnd(true)}
function scrollEnd(f){const s=$("#cscroll");if(f||s.scrollHeight-s.scrollTop-s.clientHeight<140)s.scrollTop=s.scrollHeight}
$("#ctx").addEventListener("click",e=>{const b=e.target.closest("[data-copy]");if(b)copyText(b.closest(".code").querySelector("code").textContent)});
function setBusy(b){$("#csend").textContent=b?"■":"→"}
async function sendMsg(){if(busy){busy.abort();return}const ta=$("#cin"),txt=ta.value.trim();if(!txt&&!atts.length)return;
if(txt[0]==="/"&&!atts.length){ta.value="";autosize();hidePal();await slash(txt);return}
const c=cur||newChat();const bl=atts.map(a=>a.kind==="image"?{type:"image",source:{type:"base64",media_type:a.mime,data:a.data}}:{type:"document",title:a.name,source:{type:"base64",media_type:a.mime,data:a.data}});
bl.push({type:"text",text:txt||t("seeAtt")});c.msgs.push({role:"user",content:bl});if(!c.title)c.title=(txt||(atts[0]&&atts[0].name)||"").slice(0,40);
lastAtts=atts;const keep=txt;atts=[];renderAtts();ta.value="";autosize();persist();renderList();renderTx();await runChat(c,keep)}
async function runChat(c,keepText){const ctl=new AbortController();busy=ctl;setBusy(true);const verbs=K.spin[L==="fa"?0:1];const live=mk(`<div class="stat"><span class="spin">*</span><span data-v></span><span class="dim" data-m></span></div>`);$("#ctx").append(live);
const am=asstEl("");am.hidden=true;$("#ctx").append(am);scrollEnd(true);const t0=Date.now();let acc="",err="",abort=false,raf=0;
const tm=setInterval(()=>{const s=(Date.now()-t0)/1e3;live.querySelector("[data-v]").textContent=verbs[(s/4|0)%verbs.length]+"…";live.querySelector("[data-m]").textContent=`(${s|0}s · ↓ ${tok(acc.length/4)} tokens · ${t("esc")})`},250);
const paint=()=>{raf=0;am.hidden=!acc;am.querySelector(".md").innerHTML=md(acc);scrollEnd()};
try{const body={model:c.power==="strong"?"claude-opus-4-20250514":(INFO&&INFO.model)||"claude-sonnet-4-20250514",max_tokens:8192,stream:true,messages:c.msgs.filter(m=>m.role!=="note").map(m=>({role:m.role,content:m.content}))};if(c.system)body.system=c.system;
const r=await fetch((c.acct?"/a/"+encodeURIComponent(c.acct):"")+"/v1/messages",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+KEY},body:JSON.stringify(body),signal:ctl.signal});
if(!r.ok){let m=r.status;try{m=(await r.json()).error.message}catch{}throw new Error(m)}
const rd=r.body.getReader(),dec=new TextDecoder();let buf="";for(;;){const {done,value}=await rd.read();if(done)break;buf+=dec.decode(value,{stream:true});let i;
while((i=buf.indexOf("\n\n"))>=0){const blk=buf.slice(0,i);buf=buf.slice(i+2);const ln=blk.split("\n").find(l=>l.startsWith("data:"));if(!ln)continue;let o;try{o=JSON.parse(ln.slice(5))}catch{continue}
if(o.type==="content_block_delta"&&o.delta&&o.delta.type==="text_delta"){acc+=o.delta.text;if(!raf)raf=requestAnimationFrame(paint)}else if(o.type==="error")err=(o.error&&o.error.message)||"error"}}}
catch(e){if(e.name==="AbortError")abort=true;else err=e.message||String(e)}
clearInterval(tm);busy=null;setBusy(false);const sec=((Date.now()-t0)/1e3).toFixed(1);
if(acc){c.msgs.push({role:"assistant",content:acc+(abort?`\n\n*[${t("interrupted")}]*`:"")});if(err)c.msgs.push({role:"note",text:"× "+err,err:1})}
else{c.msgs.pop();if(err)c.msgs.push({role:"note",text:"× "+err,err:1});else if(abort)c.msgs.push({role:"note",text:t("interrupted")});$("#cin").value=keepText||"";atts=lastAtts;renderAtts();autosize()}
if(acc&&!err&&!abort)c.msgs.push({role:"note",text:`${sec}s · ~${tok(acc.length/4)} tokens`});persist();renderList();renderTx()}
function note(text,err){const c=cur||newChat();c.msgs.push({role:"note",text,err});persist();renderTx()}
const SLASH=[["/new",{fa:"گفتگوی جدید",en:"new chat"}],["/clear",{fa:"پاک کردن",en:"clear"}],["/account",{fa:"انتخاب اکانت",en:"pick account"}],["/system",{fa:"پرامپت سیستمی",en:"system prompt"}],["/ds",{fa:"دستور bridge",en:"bridge command"}],["/attach",{fa:"پیوست فایل",en:"attach files"}],["/copy",{fa:"کپی آخرین پاسخ",en:"copy last reply"}],["/export",{fa:"خروجی Markdown",en:"export markdown"}],["/retry",{fa:"ارسال دوباره",en:"retry"}],["/help",{fa:"راهنما",en:"help"}]];
async function slash(line){const [cmd,...r]=line.split(/\s+/),arg=r.join(" ");switch(cmd){case"/new":case"/clear":newChat();fillAcct();break;
case"/account":{let id="";if(arg&&arg!=="auto"){const a=S.accounts.find(x=>String(x.idx)===arg||x.name.toLowerCase()===arg.toLowerCase()||x.id===arg);if(!a){note(t("noAcct"),1);break}id=a.id}const c=cur||newChat();c.acct=id;chatAcctPref=id;fillAcct();persist();note(t("acctSet")+" "+(id?S.accounts.find(x=>x.id===id).name:t("autoAcct")));break}
case"/system":{const c=cur||newChat();c.system=arg;persist();note(t("sysSet"));break}
case"/ds":{const r2=await act("command",{text:arg||"status"});if(r2)note(r2.text);break}case"/attach":$("#cfile").click();break;
case"/copy":{const m=cur&&[...cur.msgs].reverse().find(x=>x.role==="assistant");if(m)copyText(typeof m.content==="string"?m.content:"");break}
case"/export":exportChat();break;case"/retry":{if(cur){while(cur.msgs.length&&cur.msgs[cur.msgs.length-1].role!=="user")cur.msgs.pop();if(cur.msgs.length)await runChat(cur,"")}break}
default:note(t("hlp"))}}
function exportChat(){if(!cur)return;const md=cur.msgs.filter(m=>m.role!=="note").map(m=>`### ${m.role==="user"?"You":"DeepSeek"}\n\n${typeof m.content==="string"?m.content:m.content.map(b=>b.text||"["+(b.title||b.type)+"]").join("\n")}`).join("\n\n");
const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([md],{type:"text/markdown"}));a.download=(cur.title||"chat").replace(/[^\w\u0600-\u06FF-]+/g,"_")+".md";a.click()}$("#cexp").onclick=exportChat;
const autosize=()=>{const x=$("#cin");x.style.height="auto";x.style.height=Math.min(200,x.scrollHeight)+"px"};let palI=0;
function hidePal(){$("#pal").hidden=true}function showPal(v){const q=v.toLowerCase(),L2=SLASH.filter(s=>s[0].startsWith(q));if(!L2.length)return hidePal();palI=Math.min(palI,L2.length-1);$("#pal").hidden=false;$("#pal").innerHTML=L2.map((s,i)=>`<div class="pi ${i===palI?"on":""}" data-c="${s[0]}"><b>${s[0]}</b><span>${s[1][L]}</span></div>`).join("")}
$("#pal").addEventListener("mousedown",e=>{const p=e.target.closest(".pi");if(p){e.preventDefault();$("#cin").value=p.dataset.c+" ";hidePal();$("#cin").focus()}});
$("#cin").addEventListener("input",()=>{autosize();const v=$("#cin").value;if(v[0]==="/"&&!v.includes(" "))showPal(v);else hidePal()});
$("#cin").addEventListener("keydown",e=>{const pal=!$("#pal").hidden,items=$$(".pi");if(pal&&(e.key==="ArrowDown"||e.key==="ArrowUp")){e.preventDefault();palI=(palI+(e.key==="ArrowDown"?1:-1)+items.length)%items.length;showPal($("#cin").value)}
else if(pal&&(e.key==="Tab"||(e.key==="Enter"&&$("#cin").value.trim()!==items[palI].dataset.c))){e.preventDefault();$("#cin").value=items[palI].dataset.c+" ";hidePal()}else if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();sendMsg()}});
$("#csend").onclick=sendMsg;$("#catt").onclick=()=>$("#cfile").click();
const MIME={pdf:"application/pdf",txt:"text/plain",md:"text/markdown",csv:"text/csv",json:"application/json",doc:"application/msword",docx:"application/vnd.openxmlformats-officedocument.wordprocessingml.document",xlsx:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",pptx:"application/vnd.openxmlformats-officedocument.presentationml.presentation",png:"image/png",jpg:"image/jpeg",jpeg:"image/jpeg",gif:"image/gif",webp:"image/webp"};
async function addFiles(list){await loadInfo().catch(()=>{});const lim=(INFO&&INFO.limits)||{files:6,file_bytes:25e6,body_bytes:32e6};for(const f of list){if(atts.length>=lim.files){toast(t("tooMany")+" ("+lim.files+")");break}
const tot=atts.reduce((s,a)=>s+a.size,0)+f.size;if(f.size>lim.file_bytes||tot*1.4>lim.body_bytes*.9){toast(t("tooBig")+": "+f.name);continue}
const data=await new Promise(res=>{const r=new FileReader();r.onload=()=>res(String(r.result).split(",")[1]||"");r.readAsDataURL(f)});const ext=(f.name.split(".").pop()||"").toLowerCase(),mime=f.type||MIME[ext]||"application/octet-stream";
atts.push({name:f.name||"pasted."+(mime.split("/")[1]||"png"),mime,data,size:f.size,kind:mime.startsWith("image/")?"image":"document"})}renderAtts()}
function renderAtts(){$("#chips2").innerHTML=atts.map((a,i)=>`<span class="ach">${a.kind==="image"?`<img src="data:${a.mime};base64,${a.data}">`:"□"} ${esc(a.name)} <small>${(a.size/1024).toFixed(0)}KB</small><button data-i="${i}">✕</button></span>`).join("")}
$("#chips2").addEventListener("click",e=>{const b=e.target.closest("button[data-i]");if(b){atts.splice(+b.dataset.i,1);renderAtts()}});
$("#cfile").onchange=async e=>{await addFiles([...e.target.files]);e.target.value=""};
$("#cin").addEventListener("paste",e=>{const fs=[...(e.clipboardData&&e.clipboardData.files||[])];if(fs.length){e.preventDefault();addFiles(fs)}});
const pc=$("#p-chat");["dragenter","dragover"].forEach(n=>pc.addEventListener(n,e=>{e.preventDefault();pc.classList.add("drag")}));["dragleave","drop"].forEach(n=>pc.addEventListener(n,e=>{e.preventDefault();if(n==="drop"||e.target===pc)pc.classList.remove("drag")}));
pc.addEventListener("drop",e=>{if(e.dataTransfer&&e.dataTransfer.files.length)addFiles([...e.dataTransfer.files])});
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&busy)busy.abort()});
</script>
<script>
"use strict";
/* ---------- launch ---------- */
let LS={};try{LS=JSON.parse(localStorage.dsb_launch||"{}")}catch{}
function pickFolder(start){return new Promise(res=>{let cur=start;const o=modal(`<h3>□ ${t("lProj")}</h3><div class="pth" data-fp></div><div class="tb" data-lk style="margin-top:8px"></div><div class="fl" data-fl></div><div class="rowb"><button class="btn" data-nf>＋ ${t("newF")}</button><button class="btn" data-x>${t("cancel")}</button><button class="btn pri" data-ok>${t("chooseF")}</button></div>`,"big",false);
async function load(p){const r=await act("fs",{path:p});if(!r)return;cur=r.path;$("[data-fp]",o).textContent=cur;$("[data-lk]",o).innerHTML=[...r.drives.map(d=>[d,d]),...r.links].map(([n,q])=>`<span class="fchip" data-p="${esc(q)}">${esc(n)}</span>`).join("");
$("[data-fl]",o).innerHTML=(r.parent?`<div data-p="${esc(r.parent)}">↑ ${t("up1")}</div>`:"")+r.dirs.map(d=>`<div data-d="${esc(d)}">□ ${esc(d)}</div>`).join("")+(r.error?`<div class="err">${esc(r.error)}</div>`:"")}
o.onclick=async e=>{const el=e.target.closest("[data-p],[data-d],button");if(!el)return;if(el.dataset.p!==undefined)load(el.dataset.p);else if(el.dataset.d!==undefined){const sep=cur.includes("\\")&&!cur.includes("/")?"\\":"/";load(cur.replace(/[\\/]$/,"")+sep+el.dataset.d)}
else if(el.hasAttribute("data-nf")){const n=await inputBox(t("newF"));if(n){const r=await act("mkdir",{path:cur,name:n});if(r)load(r.path)}}else{o.close();res(el.hasAttribute("data-ok")?cur:null)}};load(start)})}
function collectLaunch(){LS={project:$("#lproj").value.trim(),mode:($("input[name=lm]:checked")||{}).value||"safe",extra:$("#lextra").value,cont:$("#lcont").checked,resume:$("#lres").checked,prompt:$("#lprompt").value};localStorage.dsb_launch=JSON.stringify({...LS,prompt:""});
return {project:LS.project,mode:LS.mode,extra:LS.extra,continue:LS.cont,resume:LS.resume,prompt:LS.prompt}}
async function renderLaunch(){const I=await loadInfo(true);LS.project=LS.project||I.project;LS.mode=LS.mode||I.mode;
$("#lw").innerHTML=`<div class="box"><h3>AI Claude Code</h3>${I.claude?`<div>✓ ${t("ccOk")} <span class="tip mono">${esc(I.claude)}</span></div>`:`<div>× ${t("ccNo")}</div><div class="rowb" style="justify-content:flex-start"><button class="btn pri" data-task="install_claude">⬇ ${t("install")}</button></div>`}</div>
<div class="g2"><div class="box"><h3>□ ${t("lProj")}</h3><div style="display:flex;gap:8px"><input class="inp mono" id="lproj" value="${esc(LS.project)}"><button class="btn" id="lbrowse">${t("browse")}</button></div>
<div class="tb" style="margin-top:10px">${I.recent.length?`<span class="tip">${t("recent")}:</span>`:""}${I.recent.map(p=>`<span class="fchip" data-rp="${esc(p)}">${esc(p.split(/[\\/]/).filter(Boolean).pop()||p)}</span>`).join("")}</div></div>
<div class="box"><h3>[] ${t("lMode")}</h3><div class="mode">${["safe","ask","auto"].map(m=>`<label><input type="radio" name="lm" value="${m}" ${LS.mode===m?"checked":""}><b>${m==="safe"?"[]":m==="ask"?"🙋":"⚡"} ${t("m_"+m)}</b><small>${t("m_"+m+"D")}</small></label>`).join("")}</div></div></div>
<div class="box"><h3>≡ ${t("lOpts")}</h3><div class="row" style="margin:0 0 10px"><label><span class="sw"><input type="checkbox" id="lcont" ${LS.cont?"checked":""}><i></i></span> ${t("cont")}</label><label><span class="sw"><input type="checkbox" id="lres" ${LS.resume?"checked":""}><i></i></span> ${t("resume")}</label></div>
<input class="inp mono" id="lextra" placeholder="${t("extra")}" value="${esc(LS.extra||"")}" style="margin-bottom:10px"><textarea class="inp mono" id="lprompt" rows="5" placeholder="${esc(t("longpH"))}">${esc(LS.prompt||"")}</textarea></div>
<div class="rowb" style="justify-content:flex-start"><button class="btn pri" id="lgo">→ ${t("openCC")}</button><button class="btn" id="lcopy">≡ ${t("copyCmd")}</button></div>`}
$("#lw").addEventListener("click",async e=>{const el=e.target.closest("button,[data-rp]");if(!el)return;if(el.dataset.rp){$("#lproj").value=el.dataset.rp;return}
if(el.id==="lbrowse"){const p=await pickFolder($("#lproj").value);if(p)$("#lproj").value=p}
else if(el.id==="lgo"){const r=await act("launch",collectLaunch());if(r)toast(`→ ${t("opened")} ${r.where}\n${r.project}`)}
else if(el.id==="lcopy"){const r=await act("launch",{...collectLaunch(),dry:true});if(r){const P=r.preview,order=INFO.platform==="win32"?["powershell","cmd","bash"]:["bash","powershell","cmd"];
modal(`<h3>≡ ${t("copyCmd")}</h3>${order.map(k=>`<div class="sn"><div class="cb"><span>${k}</span><button data-cp="${k}">□ ${t("copy")}</button></div><pre>${esc(P[k])}</pre></div>`).join("")}<div class="rowb"><button class="btn" data-x>${t("close")}</button></div>`,"big").onclick=ev=>{const c=ev.target.closest("[data-cp]");if(c)copyText(P[c.dataset.cp]);if(ev.target.closest("[data-x]"))ev.currentTarget.close()}}}
else if(el.dataset.task){const r=await act("task",{name:el.dataset.task});if(r){toast(t("started"));go("console")}}});
/* ---------- console ---------- */
let LOGS=[],logLast=0,logTimer=null,logF="all",logQ="",logPause=false,hist=[],hi=0;const CMDS=["status","next","prev","use ","auto","rr","failover","on ","off ","add ","test","login ","show ","hide ","restart ","reset","purge","clear","usage-reset","url","key","help"];
function lineEl(l){const d=document.createElement("div");d.className="ll "+l.l;d.dataset.l=l.l;d.innerHTML=`<time>${new Date(l.t*1e3).toLocaleTimeString()}</time>`;d.append(document.createTextNode(strip(l.m)));return d}
const lineOk=l=>(logF==="all"||(logF==="warn"&&(l.l==="warn"||l.l==="error"))||(logF==="error"&&l.l==="error"))&&(!logQ||strip(l.m).toLowerCase().includes(logQ));
function addLine(l){LOGS.push(l);if(LOGS.length>2500)LOGS.shift();if(!lineOk(l))return;const box=$("#clog"),near=box.scrollHeight-box.scrollTop-box.clientHeight<60;box.append(lineEl(l));while(box.childElementCount>1200)box.firstChild.remove();if(near&&!logPause)box.scrollTop=box.scrollHeight}
function refilter(){const box=$("#clog");box.innerHTML="";LOGS.filter(lineOk).slice(-1000).forEach(l=>box.append(lineEl(l)));box.scrollTop=box.scrollHeight}
function buildConsole(){$("#cw").innerHTML=`<div class="tb"><span class="fchip on" data-f="all">${t("all")}</span><span class="fchip" data-f="warn">${t("warn")}</span><span class="fchip" data-f="error">${t("error")}</span><input class="inp" id="lq" placeholder="🔍" style="width:180px"><span class="fchip" id="lpause">Ⅱ ${t("pause")}</span><span class="fchip" id="lclr">× ${t("clearv")}</span><span class="fchip" id="ldl">⬇ ${t("dl")}</span></div>
<div class="tb">${["status","next","auto","test","clear","reset","url","help"].map(c=>`<span class="fchip" data-c="${c}">${c}</span>`).join("")}</div><div id="clog" class="mono"></div><div id="cin2"><span>bridge ›</span><input id="cmd" autocomplete="off" placeholder="${t("cons")}"></div>`;
$("#cw").onclick=e=>{const f=e.target.closest("[data-f]");if(f){logF=f.dataset.f;$$(".tb [data-f]").forEach(x=>x.classList.toggle("on",x===f));refilter()}const c=e.target.closest("[data-c]");if(c)runCmd(c.dataset.c);
if(e.target.id==="lpause"){logPause=!logPause;e.target.classList.toggle("on",logPause)}if(e.target.id==="lclr"){LOGS=[];$("#clog").innerHTML=""}
if(e.target.id==="ldl"){const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([LOGS.map(l=>new Date(l.t*1e3).toISOString()+" "+strip(l.m)).join("\n")],{type:"text/plain"}));a.download="bridge-console.log";a.click()}};
$("#lq").oninput=e=>{logQ=e.target.value.toLowerCase();refilter()};
$("#cmd").onkeydown=e=>{if(e.key==="Enter"){const v=e.target.value.trim();e.target.value="";if(v){hist.push(v);hi=hist.length;runCmd(v)}}else if(e.key==="ArrowUp"){hi=Math.max(0,hi-1);e.target.value=hist[hi]||"";e.preventDefault()}else if(e.key==="ArrowDown"){hi=Math.min(hist.length,hi+1);e.target.value=hist[hi]||"";e.preventDefault()}
else if(e.key==="Tab"){e.preventDefault();const v=e.target.value,m=CMDS.filter(c=>c.startsWith(v));if(m.length===1)e.target.value=m[0]}}}
async function runCmd(c){addLine({n:0,t:Date.now()/1e3,l:"cmd",m:"› "+c});const r=await act("command",{text:c});if(r)r.text.split("\n").forEach(x=>addLine({n:0,t:Date.now()/1e3,l:"info",m:x}))}
async function pollLogs(){try{const r=await api("logs?since="+logLast);if(r.last<logLast)logLast=0;r.lines.forEach(l=>{addLine(l);logLast=Math.max(logLast,l.n)});if(!r.lines.length&&r.last>logLast)logLast=r.last}catch{}}
function enterConsole(){if(!$("#clog"))buildConsole();pollLogs();clearInterval(logTimer);logTimer=setInterval(pollLogs,1000);setTimeout(()=>{const b=$("#clog");b.scrollTop=b.scrollHeight},50)}
function stopLogs(){clearInterval(logTimer)}
/* ---------- connect (details for other agents) ---------- */
let connAcct="",keyShown=false,SN=[];
async function renderConnect(){const I=await loadInfo(true);if(S&&!S.accounts.find(a=>a.id===connAcct))connAcct="";const ac=I.accounts.find(a=>a.id===connAcct),base=ac?ac.url:I.base,key=I.key,m=I.deepseek_model;
const ex={files:'{ "type": "document", "title": "report.pdf", "source": { "type": "base64", "media_type": "application/pdf", "data": "<BASE64>" } }',img:'{ "type": "image", "source": { "type": "base64", "media_type": "image/png", "data": "<BASE64>" } }'};
SN=[["Claude Code · PowerShell",`$env:ANTHROPIC_BASE_URL="${base}"\n$env:ANTHROPIC_API_KEY="${key}"\n$env:ANTHROPIC_MODEL="${I.model}"\n$env:ANTHROPIC_DEFAULT_HAIKU_MODEL="${I.haiku}"\nclaude`],
["Claude Code · CMD",`set ANTHROPIC_BASE_URL=${base}\nset ANTHROPIC_API_KEY=${key}\nset ANTHROPIC_MODEL=${I.model}\nset ANTHROPIC_DEFAULT_HAIKU_MODEL=${I.haiku}\nclaude`],
["Claude Code · bash / zsh",`export ANTHROPIC_BASE_URL="${base}"\nexport ANTHROPIC_API_KEY="${key}"\nexport ANTHROPIC_MODEL="${I.model}"\nexport ANTHROPIC_DEFAULT_HAIKU_MODEL="${I.haiku}"\nclaude`],
["OpenAI-compatible · Cline / Roo / Continue / Cursor / Open WebUI",`Provider : OpenAI Compatible\nBase URL : ${base}/v1\nAPI key  : ${key}\nModel ID : ${m}`],
["Aider",`aider --openai-api-base ${base}/v1 --openai-api-key ${key} --model openai/${m}`],
["Continue (config.json)",JSON.stringify({models:[{title:"DeepSeek Bridge",provider:"openai",model:m,apiBase:base+"/v1",apiKey:key}]},null,2)],
["Python · openai",`from openai import OpenAI\nc = OpenAI(base_url="${base}/v1", api_key="${key}")\nr = c.chat.completions.create(model="${m}", messages=[{"role": "user", "content": "Hello"}])\nprint(r.choices[0].message.content)`],
["Python · anthropic",`import anthropic\nc = anthropic.Anthropic(base_url="${base}", api_key="${key}")\nr = c.messages.create(model="${I.model}", max_tokens=1024, messages=[{"role": "user", "content": "Hello"}])\nprint(r.content[0].text)`],
["curl",`curl ${base}/v1/messages \\\n  -H "x-api-key: ${key}" -H "content-type: application/json" \\\n  -d '{"model":"${I.model}","max_tokens":512,"messages":[{"role":"user","content":"Hello"}]}'`],
["Files & images (Anthropic content blocks)",`${ex.img}\n${ex.files}\n\n// OpenAI style: {"type":"image_url","image_url":{"url":"data:image/png;base64,<BASE64>"}}\n//               {"type":"file","file":{"filename":"a.pdf","file_data":"data:application/pdf;base64,<BASE64>"}}`]];
const row=(k,v,i)=>`<div class="kvl"><b>${k}</b><code>${esc(v)}</code><button class="btn sm" data-cv="${i}">□ ${t("copy")}</button></div>`;const kv=[base,keyShown?key:key.slice(0,6)+"••••••••••••",m];
$("#kw").innerHTML=`<div class="box"><div class="tb"><select class="inp" id="cscope"><option value="">${t("cAuto")}</option>${I.accounts.map(a=>`<option value="${a.id}" ${a.id===connAcct?"selected":""}>${t("cOnly")}: ${esc(a.name)}</option>`).join("")}</select></div>
<div class="kvl"><b>${t("cBase")}</b><code>${esc(base)}</code><button class="btn sm" data-copy="${esc(base)}">□ ${t("copy")}</button></div><div class="kvl"><b>${t("cKey")}</b><code>${esc(kv[1])}</code><span><button class="btn sm" id="kshow">👁 ${t("reveal")}</button> <button class="btn sm" data-copy="${esc(key)}">□ ${t("copy")}</button></span></div>
<div class="kvl"><b>${t("cModel")}</b><code>${esc(m)}</code><button class="btn sm" data-copy="${esc(m)}">□ ${t("copy")}</button></div><div class="tip" style="margin-top:8px">${t("cNote")}</div>${ac?`<div class="kvl"><b>${t("cProf")}</b><code>${esc(ac.profile)}</code><span></span></div>`:""}</div>
${SN.map((s,i)=>`<div class="sn"><div class="cb"><span>${esc(s[0])}</span><button data-cs="${i}">□ ${t("copy")}</button></div><pre>${esc(s[1])}</pre></div>`).join("")}`;
$("#cscope").onchange=e=>{connAcct=e.target.value;renderConnect()};$("#kshow").onclick=()=>{keyShown=!keyShown;renderConnect()}}
$("#kw").addEventListener("click",e=>{const c=e.target.closest("[data-copy]");if(c)copyText(c.dataset.copy);const s=e.target.closest("[data-cs]");if(s)copyText(SN[+s.dataset.cs][1])});
/* ---------- settings ---------- */
let pend={};
let openGroups=JSON.parse(localStorage.dsb_sgrp||'{}');
async function renderSettings(){const I=await loadInfo(true);pend={};const lab=s=>L==="fa"?s.fa:s.en;
const ctl=s=>{const n=esc(s.name);if(s.kind==="bool")return `<label class="sw"><input type="checkbox" data-n="${n}" ${s.value?"checked":""}><i></i></label>`;
if(s.kind==="choice")return `<select class="inp" data-n="${n}" style="width:100%">${s.choices.map(c=>`<option ${c===s.value?"selected":""}>${c}</option>`).join("")}</select>`;
if(s.kind==="str")return `<input class="inp" data-n="${n}" value="${esc(s.value)}">`;return `<input class="inp" type="number" data-n="${n}" value="${s.value}" min="${s.min}" max="${s.max}" step="${s.kind==="int"?1:.1}">`};
const grp=g=>`<details class="box sgrp" data-g="${g}" ${openGroups[g]!==false?"open":""}><summary><h3>${t("g_"+g)}</h3><span class="dim">${I.settings.filter(s=>s.group===g).length}</span></summary>${I.settings.filter(s=>s.group===g).map(s=>`<div class="srow" data-r="${esc(s.name)}"><div><b>${esc(lab(s))}</b><small>${esc(s.name)} · ${t("w_"+s.when)}</small></div><div class="ctl">${ctl(s)}</div><button class="ib" data-reset="${esc(s.name)}" title="↺">↺</button></div>`).join("")}</details>`;
const th=localStorage.dsb_theme||"dark",ac=localStorage.dsb_acc||"violet";
$("#sw").innerHTML=`<div class="box"><h3>🎨 ${t("look")}</h3><div class="tb"><button class="btn ${th==="dark"?"pri":""}" data-th="dark">◐ Dark</button><button class="btn ${th==="light"?"pri":""}" data-th="light">○ Light</button><button class="btn" id="slang">🌐 ${t("lang")}</button>
<span class="tip">${t("accent")}:</span>${["violet","emerald","amber","sky"].map(c=>`<button class="btn sm ${ac===c?"pri":""}" data-ac="${c}">${c}</button>`).join("")}</div></div>
${["claude","rel","ctx","browser","swarm","panel"].map(grp).join("")}<div class="box"><h3>＋ ${t("maint")}</h3><div class="tb"><button class="btn" data-m="restart">↻ ${t("restartB")}</button><button class="btn dng" data-m="stop">⏹ ${t("stopB")}</button><button class="btn" data-m="usage">× ${t("resetU")}</button><button class="btn" data-task="selftest">🧪 ${t("selftest")}</button><button class="btn" data-task="verify">[] ${t("verify")}</button></div>
<div class="tip mono"><b>${esc(I.instance_name||"Bridge")}</b><br>home: ${esc(I.instance_home||"")}<br>config: ${esc(I.config||"")}<br>pid: ${esc(I.pid||"")} · port: ${esc(I.port||"")}<br>log: ${esc(I.log||"")}<br>profiles: ${esc(I.profiles||"")}<br><br><b>Running multiple instances</b><br>Each instance owns its home, config, profiles, logs and swarm attachments. Run a copied bridge with a different <code>--instance</code> and <code>--port</code>; never reuse another instance's port.</div></div><div id="savebar" hidden><span id="sbn"></span><button class="btn pri" id="sbsave">${t("saveChg")}</button></div>`}
function setPend(el){const n=el.dataset.n,s=INFO.settings.find(x=>x.name===n);let v=el.type==="checkbox"?el.checked:el.value;if(s.kind==="int"||s.kind==="float")v=el.value===""?s.value:+el.value;
if(v===s.value)delete pend[n];else pend[n]=v;el.closest(".srow").classList.toggle("chg",n in pend);const c=Object.keys(pend).length;$("#savebar").hidden=!c;$("#sbn").textContent=c+" "+t("unsaved")}
$("#sw").addEventListener("input",e=>{if(e.target.dataset.n)setPend(e.target)});$("#sw").addEventListener("change",e=>{if(e.target.dataset.n)setPend(e.target)});
$("#sw").addEventListener("toggle",e=>{const d=e.target;if(d.dataset&&d.dataset.g&&d.classList.contains("sgrp")){openGroups[d.dataset.g]=d.open;localStorage.dsb_sgrp=JSON.stringify(openGroups)}},true);
$("#sw").addEventListener("click",async e=>{const el=e.target.closest("button");if(!el)return;
if(el.dataset.reset){const s=INFO.settings.find(x=>x.name===el.dataset.reset),i=$(`[data-n="${s.name}"]`);if(i.type==="checkbox")i.checked=!!s.default;else i.value=s.default;setPend(i)}
else if(el.dataset.th){localStorage.dsb_theme=el.dataset.th;applyTheme();renderSettings()}else if(el.dataset.ac){localStorage.dsb_acc=el.dataset.ac;applyTheme();renderSettings()}else if(el.id==="slang")$("#blang").click();
else if(el.id==="sbsave"){const r=await act("settings_set",{values:pend});if(r){toast("✓ "+t("saved")+(r.restart.length?"\n"+t("needRestart")+" "+r.restart.join(", "):""));await loadInfo(true);renderSettings()}}
else if(el.dataset.m==="usage"){if(await ask(t("resetU")+"?")){await act("reset_usage");toast("✓")}}
else if(el.dataset.m){if(await ask(t(el.dataset.m==="restart"?"restartB":"stopB")+"?")){const r=await act("bridge",{action:el.dataset.m});if(r)toast("…")}}
else if(el.dataset.task){const r=await act("task",{name:el.dataset.task});if(r){toast(t("started"));go("console")}}});
/* ---------- command palette ---------- */
function openPalette(){const both=k=>{const e=K[k]||[k,k];return e[0]+" "+e[1]};const items=[...PAGES.map(p=>({n:"→ "+t("n_"+p),s:"→ "+both("n_"+p),r:()=>go(p)})),{n:"› "+t("nextAcct"),s:"› "+both("nextAcct"),r:()=>act("command",{text:"next"})},{n:"⚖ "+t("balanced"),s:"⚖ "+both("balanced"),r:()=>act("settings",{strategy:"balanced"})},{n:"＋ "+t("newchat"),s:"＋ "+both("newchat"),r:()=>{go("chat");newChat()}},{n:"＋ "+t("add"),s:"＋ "+both("add"),r:addWizard},
{n:"🌓 "+t("theme"),s:"🌓 "+both("theme"),r:()=>$("#bth").click()},{n:"🌐 "+t("lang"),s:"🌐 "+both("lang"),r:()=>$("#blang").click()},{n:"→ "+t("openCC"),s:"→ "+both("openCC"),r:async()=>{const r=await act("launch",{project:LS.project,mode:LS.mode});if(r)toast(`→ ${t("opened")} ${r.where}`)}},
...(S?S.accounts.map(a=>({n:"▶ "+t("use")+": "+a.name,s:"▶ "+both("use")+": "+a.name,r:()=>act("use",{id:a.id})})):[])];
const o=modal(`<input class="inp" id="pq" placeholder="${t("palPh")}"><div class="fl" id="pl"></div>`);let q="",ix=0,list=items;const draw=()=>{$("#pl",o).innerHTML=list.map((x,i)=>`<div data-i="${i}" ${i===ix?'style="background:var(--p2)"':""}>${esc(x.n)}</div>`).join("")};
const pick=i=>{const x=list[i];o.close();if(x)x.r()};$("#pq",o).focus();draw();$("#pq",o).oninput=e=>{q=e.target.value.toLowerCase();list=items.filter(x=>(x.s||x.n).toLowerCase().includes(q));ix=0;draw()};
$("#pq",o).onkeydown=e=>{if(e.key==="ArrowDown"){ix=Math.min(list.length-1,ix+1);draw()}else if(e.key==="ArrowUp"){ix=Math.max(0,ix-1);draw()}else if(e.key==="Enter")pick(ix);else if(e.key==="Escape")o.close()};$("#pl",o).onclick=e=>{const d=e.target.closest("[data-i]");if(d)pick(+d.dataset.i)}}
document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();openPalette()}});
</script>
<script>
"use strict";
/* ---------- account wizard (DeepSeek website, Grok, Claude, OpenAI, OpenRouter, custom ...) ---------- */
const guessTier=m=>{m=(m||"").toLowerCase();if(!m)return 3;if(/mini|haiku|flash|lite|nano|small|instant|-fast/.test(m))return 2;if(/opus|gpt-5|o3|o4|grok-4|gemini-2\.5-pro|gemini-3|ultra/.test(m))return 5;if(/sonnet|gpt-4\.1|gpt-4o|gpt-4-turbo|grok-3|reasoner|r1|gemini|70b|405b/.test(m))return 4;return 3};
const stars=n=>"★".repeat(n)+"☆".repeat(5-n),tierName=n=>t("tier"+n);
async function addWizard(){await loadInfo(true);const prov=INFO.providers;const o=modal(`<h3>${t("wizTitle")}</h3><div class="pvg">${prov.map(p=>`<div class="pv" data-p="${p.id}"><i>${p.icon}</i><b>${esc(p.name)}</b><small>${esc(p.sub)}</small><span class="tb2">T${p.tier} · ${tierName(p.tier)}</span></div>`).join("")}</div><div class="rowb"><button class="btn" data-x>${t("cancel")}</button></div>`,"big");
o.onclick=async e=>{if(e.target.closest("[data-x]"))return o.close();const c=e.target.closest(".pv");if(!c)return;const p=prov.find(x=>x.id===c.dataset.p);o.close();if(p.kind==="web"){const n=await inputBox(t("addTitle"),p.name,"Login account name / نام اکانت");if(n===null)return;const r=await act("add_web",{provider:p.id,name:n,headed:true,tier:p.tier});if(r){toast(`🔐 ${p.name}: login window opened`);tick()}}else accForm(p,null)}}
function accForm(p,acc){const edit=!!acc,web=edit&&acc.kind==="web",v=acc||{name:p.name,base_url:p.base,model:p.models[0]||"",tier:p.tier,max_parallel:4,price_in:0,price_out:0,budget:0};let touched=edit;
const o=modal(`<h3>${p?p.icon:""} ${edit?t("editAcc")+": "+esc(acc.name):esc(p.name)}</h3><div class="fg"><label>${t("f_name")}<input class="inp" id="fn" value="${esc(v.name)}"></label>
<label>${t("f_base")}<input class="inp mono" id="fb" value="${esc(v.base_url||"")}" ${web?"disabled":""}></label>
<label>${t("f_key")}<input class="inp mono" id="fk" type="password" autocomplete="off" ${web?"disabled":""} placeholder="${edit&&!web?esc(acc.key_hint)+" ("+t("keep")+")":""}"></label>
<label>${t("f_model")}<div style="display:flex;gap:8px"><input class="inp mono" id="fm" list="fml" value="${esc(v.model||"")}" ${web?"disabled":""}><datalist id="fml">${(p?p.models:[]).map(m=>`<option>${esc(m)}</option>`).join("")}</datalist><button class="btn" id="ffetch" ${web?"disabled":""}>${t("fetchM")}</button></div></label>
<div class="fg2"><label>${t("f_tier")} <b id="ftl"></b><input type="range" id="ft" min="1" max="5" value="${v.tier}"></label><label>${t("f_par")}<input class="inp" id="fp" type="number" min="1" max="32" value="${v.max_parallel}" ${web?"disabled":""}></label></div>
<div class="fg2"><label>${t("f_pin")}<input class="inp" id="fpi" type="number" step="0.01" min="0" value="${v.price_in}"></label><label>${t("f_pout")}<input class="inp" id="fpo" type="number" step="0.01" min="0" value="${v.price_out}"></label></div>
<label>${t("f_budget")}<input class="inp" id="fbu" type="number" step="0.5" min="0" value="${v.budget}"></label>${p&&p.link?`<div class="tip"># <a href="${esc(p.link)}" target="_blank" rel="noopener" style="color:var(--ac)">${esc(p.link)}</a></div>`:""}</div>
<div class="rowb"><button class="btn" data-x>${t("cancel")}</button><button class="btn pri" data-ok>${edit?t("save"):t("testAdd")}</button></div>`,"big",false);
const q=s=>$(s,o),tl=()=>q("#ftl").textContent=q("#ft").value+" · "+tierName(q("#ft").value);tl();q("#ft").oninput=()=>{touched=true;tl()};
q("#fm").oninput=()=>{if(!touched){q("#ft").value=guessTier(q("#fm").value);tl()}};
q("#ffetch").onclick=async()=>{const r=await act("models_probe",{kind:acc?acc.kind:p.kind,base_url:q("#fb").value,api_key:q("#fk").value});if(r){q("#fml").innerHTML=r.models.map(m=>`<option>${esc(m)}</option>`).join("");toast(r.models.length+" models");if(r.models.length&&!q("#fm").value)q("#fm").value=r.models[0]}};
o.onclick=async e=>{const b=e.target.closest("button");if(!b)return;if(b.hasAttribute("data-x"))return o.close();if(!b.hasAttribute("data-ok"))return;
const d={name:q("#fn").value,base_url:q("#fb").value,api_key:q("#fk").value,model:q("#fm").value,tier:+q("#ft").value,max_parallel:+q("#fp").value,price_in:+q("#fpi").value,price_out:+q("#fpo").value,budget:+q("#fbu").value};
if(edit){const r=await act("update_account",{id:acc.id,...d});if(r){o.close();tick()}}else{const r=await act("add_api",{provider:p.id,...d});if(r){o.close();toast(t("testing"));const x=await act("test",{id:r.id});toast(x&&x.ok?`✓ ${d.name||p.name}: ${t("okTest")} (${x.seconds}s)`:"× "+(x?x.error:"?"));tick()}}}}
$("#hadd").onclick=addWizard;
document.addEventListener("click",e=>{const b=e.target.closest('#grid button[data-a="edit"]');if(!b)return;const dt=b.closest("details");if(dt)dt.removeAttribute("open");const a=S.accounts.find(x=>x.id===b.closest(".card").dataset.id);accForm((INFO.providers||[]).find(p=>p.id===a.provider)||null,a)});
$("#cpow").onchange=e=>{if(cur){cur.power=e.target.value;persist()}};
/* ---------- live feed (mirror of Claude Code + dock) ---------- */
let FEED=[],feedLast=0,feedTimer=null,feedF="all",feedPause=false;
function fcardEl(it){const d=mk(`<div class="fcard ${it.kind}"><div class="fh"><time>${new Date(it.t*1e3).toLocaleTimeString()}</time><span class="bd">${esc(it.tag||t("lv_"+it.kind))}</span>${it.role?`<span>${esc(it.role)}</span>`:""}<span>${esc(it.account||"—")}${it.tier?" T"+it.tier:""}</span><span class="mono">${esc(it.model||"")}</span><span>${it.secs}s</span><span>↓${tok(it.tin)} ↑${tok(it.tout)}</span></div>
<div class="fu">› ${esc(it.user||"")}</div>${it.reply?`<div class="fr">• ${esc(it.reply)}</div>`:""}${it.calls.length?`<div class="fcs">${it.calls.map(c=>`<span>⌁ ${esc(c)}</span>`).join("")}</div>`:""}${it.err?`<div class="err">× ${esc(it.err)}</div>`:""}</div>`);d.onclick=()=>d.classList.toggle("x");return d}
const feedOk=(it,f)=>f==="all"||it.kind===f;
function addFeed(it){for(const [box,f] of [[$("#livefeed"),feedF],[$("#dockfeed"),"all"]]){if(!box||!feedOk(it,f)||(box.id==="livefeed"&&page!=="live"))continue;const near=box.scrollHeight-box.scrollTop-box.clientHeight<80;box.append(fcardEl(it));while(box.childElementCount>300)box.firstChild.remove();if(near&&!feedPause)box.scrollTop=box.scrollHeight}}
function refeed(){for(const [box,f] of [[$("#livefeed"),feedF],[$("#dockfeed"),"all"]]){box.innerHTML="";FEED.filter(it=>feedOk(it,f)).slice(-200).forEach(it=>box.append(fcardEl(it)));box.scrollTop=box.scrollHeight}if(!FEED.length){$("#livefeed").innerHTML=`<div class="tip" style="padding:20px;text-align:center">${t("lvEmpty")}</div>`;$("#dockfeed").innerHTML=`<div class="tip" style="padding:20px;text-align:center">${t("lvEmpty")}</div>`}}
async function pollFeed(){if(dashStreamReady)return;try{const r=await api("activity?since="+feedLast);if(r.last<feedLast){feedLast=0;FEED=[];refeed()}if(r.items.length&&!FEED.length){$("#livefeed").innerHTML="";$("#dockfeed").innerHTML=""}r.items.forEach(it=>{FEED.push(it);feedLast=Math.max(feedLast,it.n);addFeed(it)});if(FEED.length>400)FEED.splice(0,FEED.length-400)}catch{}}
function syncFeed(){clearInterval(feedTimer);if(page==="live"||$("#app").classList.contains("dock")){pollFeed();if(!dashStreamReady)feedTimer=setInterval(pollFeed,5000)}}
function enterLive(){connectDashStream();renderClaudeMirror();renderClaudeTerm();$("#livetb").innerHTML=["all","main","agent","side"].map(k=>`<span class="fchip ${feedF===k?"on":""}" data-lf="${k}">${t("lv_"+k)}</span>`).join("")+`<span class="fchip ${feedPause?"on":""}" id="lvp">Ⅱ ${t("pause")}</span><span class="fchip" id="lvc">× ${t("clearv")}</span>`;refeed();syncFeed()}
$("#p-live").addEventListener("click",e=>{const f=e.target.closest("[data-lf]");if(f){feedF=f.dataset.lf;enterLive()}if(e.target.id==="lvp"){feedPause=!feedPause;enterLive()}if(e.target.id==="lvc"){FEED=[];refeed()}});
function setDock(on){$("#app").classList.toggle("dock",on);localStorage.dsb_dock=on?"1":"";refeed();syncFeed()}$("#hdock").onclick=()=>setDock(!$("#app").classList.contains("dock"));$("#dockx").onclick=()=>setDock(false);
/* ---------- swarm (parallel agents) ---------- */
let swSel="",swMeta={runs:[],capacity:1},swOpen=new Set(),swPrev={},SW=null,swTimer=null;
const beep=()=>{try{const a=new (window.AudioContext||window.webkitAudioContext)(),o=a.createOscillator(),g=a.createGain();o.connect(g);g.connect(a.destination);o.frequency.value=880;g.gain.value=.06;o.start();setTimeout(()=>{o.stop();a.close()},180)}catch{}};
function swForm(){const I=INFO||{};const project=I.project||LS.project||"";swFinalPrompt="";swAttachments=[];$("#swf").innerHTML=`<div class="box"><h3>* ${t("swNew")}</h3><div class="fg"><div class="swu"><div class="lbl"><span>${t("swOriginal")}</span><button class="btn sm" id="spImprove">${t("swImprove")}</button></div><textarea class="inp" id="sg" rows="4" placeholder="${esc(t("swGoalPh"))}"></textarea><div id="spp" hidden><div class="swpreview"><div><div class="lbl"><span>${t("swImproved")}</span><span class="tip">AI</span></div><textarea class="inp" id="sp2" rows="6"></textarea><div class="sactions"><button class="btn pri sm" id="spUse">${t("swUseImproved")}</button><button class="btn sm" id="spAgain">${t("swImproveAgain")}</button></div></div><div><div class="lbl"><span>${t("swCustom")}</span><span class="tip">${t("swFinalReady")}</span></div><textarea class="inp" id="sp3" rows="4" placeholder="${esc(t("swCustom"))}"></textarea><div class="sactions"><button class="btn sm" id="spApplyCustom">${t("swApplyCustom")}</button></div></div></div></div></div><div class="fg2"><label>${t("lProj")}<div style="display:flex;gap:8px"><input class="inp mono" id="sp" data-auto-project="1" value="${esc(project)}"><button class="btn" id="sbrowse">${t("browse")}</button></div></label><label>AI accounts<div id="swAccounts" class="accsel"></div></label><label>${t("swAgents")} <span class="tip" id="scap"></span><input class="inp" id="sa" type="number" min="1" max="32" placeholder="${t("swAuto")}"></label></div><div class="fg2"><label>${t("swVerify")}<select class="inp" id="sv2" style="width:100%"><option value="auto">${t("swAuto")}</option><option value="off">${t("swOff")}</option></select></label><label>${t("swReview")}<select class="inp" id="sr" style="width:100%"><option value="">${t("swAuto")}</option><option value="on">${t("swOn")}</option><option value="off">${t("swOff")}</select></label></div><div class="row" style="margin:0"><label><span class="sw"><input type="checkbox" id="sst"><i></i></span> ${t("swStrict")}</label><label><span class="sw"><input type="checkbox" id="sgi" checked><i></i></span> ${t("swInit")}</label></div><div class="swattach"><button class="btn sm" id="sattach">＋ ${t("swAttach")}</button><span class="tip">${t("swAttachTip")}</span><div id="satts"></div></div><details><summary class="tip" style="cursor:pointer">${t("swManual")}</summary><textarea class="inp mono" id="stk" rows="4" placeholder="${esc(t("swManualPh"))}" style="margin-top:8px"></textarea></details><div class="rowb" style="justify-content:flex-start"><button class="btn pri" id="sgo">→ ${t("swStart")}</button><span class="tip">${t("swTip")}</span></div></div></div>`;renderSwarmAttachments();renderSwarmAccounts()}
function renderSwarmAccounts(){const box=$("#swAccounts");if(!box)return;const project=$("#sp")?.value.trim()||INFO?.project||"";const map=INFO?.project_accounts||{};let assigned=[];try{assigned=map[project]||map[project.replace(/\\/g,"/")]||[]}catch{};const enabled=(S?.accounts||[]).filter(a=>a.enabled);const chosen=assigned.length?new Set(assigned):new Set(enabled.map(a=>a.id));box.innerHTML=enabled.length?enabled.map(a=>`<label style="display:inline-flex;align-items:center;gap:6px;margin:3px 8px 3px 0"><input type="checkbox" value="${esc(a.id)}" ${chosen.has(a.id)?"checked":""}>${esc(a.name)} <span class="tip">T${a.tier}</span></label>`).join(""):`<span class="tip">No enabled accounts</span>`}
let swFinalPrompt="",swAttachments=[];function renderSwarmAttachments(){const b=$("#satts");if(!b)return;b.innerHTML=swAttachments.map((a,i)=>`<span class="achip"><span>＋ ${esc(a.name)}</span><small>${Math.round((a.size||0)/1024)} KB</small><button data-rm-att="${i}" title="${t("swRemoveAttachment")}">✕</button></span>`).join("")}
async function uploadSwarmFiles(list){await loadInfo();const lim=(INFO&&INFO.limits)||{files:6,file_bytes:25e6};for(const f of list){if(swAttachments.length>=lim.files){toast(t("tooMany")+" ("+lim.files+")");break}if(f.size>lim.file_bytes){toast(t("tooBig")+": "+f.name);continue}toast(t("swUploading")+" "+f.name);try{const r=await fetch("/dash/api/swarm_attachment",{method:"POST",headers:{Authorization:"Bearer "+KEY,"X-Filename":encodeURIComponent(f.name),"X-Mime":f.type||"application/octet-stream"},body:f});const j=await r.json();if(!r.ok)throw new Error(j.error?.message||String(r.status));swAttachments.push(j.attachment);renderSwarmAttachments()}catch(e){toast("! "+(e.message||e))}}}
async function improveSwarmPrompt(){const original=$("#sg").value.trim();const current=$("#sp2")?.value.trim()||"";const custom=$("#sp3")?.value.trim()||"";if(!original){toast(t("swGoalPh"));$("#sg").focus();return}$("#spImprove").disabled=true;$("#spImprove").textContent=t("swImproving");try{const r=await act("swarm_prompt_improve",{prompt:original,current,custom});if(r){$("#sp2").value=r.improved;$("#spp").hidden=false;swFinalPrompt=r.improved}}finally{$("#spImprove").disabled=false;$("#spImprove").textContent=t("swImprove")}}
async function refineSwarmPrompt(){const improved=$("#sp2").value.trim();const custom=$("#sp3").value.trim();const original=$("#sg").value.trim();if(!improved){return}$("#spApplyCustom").disabled=true;try{const r=await act("swarm_prompt_improve",{prompt:original,current:improved,custom});if(r){$("#sp2").value=r.improved;swFinalPrompt=r.improved}}finally{$("#spApplyCustom").disabled=false}}

async function enterSwarm(){try{await loadInfo(true);S=await api("state")}catch{};if(!$("#sg"))swForm();else if($("#sp")&&$("#sp").dataset.autoProject!=="0")$("#sp").value=INFO&&INFO.project?INFO.project:($("#sp").value||LS.project||"");renderSwarmAccounts();pollSwarm();clearInterval(swTimer);if(!dashStreamReady)swTimer=setInterval(pollSwarm,5000)}
const sgp=s=>`<span class="stp sg-${s}">${t("sg_"+s)}</span>`;
async function pollSwarm(){if(page!=="swarm"){clearInterval(swTimer);return}try{swMeta=await api("swarm");$("#scap").textContent=`(${t("capacity")}: ${swMeta.capacity})`;if(!swSel&&swMeta.runs[0])swSel=swMeta.runs[0].id;SW=swSel&&swMeta.runs.find(r=>r.id===swSel)?await api("swarm_run?id="+swSel):null;renderRuns()}catch{}}
function renderRuns(){const R=SW,box=$("#swr");let h=`<div class="runs">${swMeta.runs.map(r=>`<div class="rn ${r.id===swSel?"on":""}" data-r="${r.id}">${sgp(r.status)} <b>${esc(r.id)}</b> <span class="tip">${esc(r.goal.slice(0,34))}</span></div>`).join("")||`<div class="tip">${t("swNone")}</div>`}</div>`;
if(R){if(swPrev[R.id]&&swPrev[R.id]!==R.status&&/^done/.test(R.status)){beep();toast("* "+R.id+": "+t("sg_"+R.status))}swPrev[R.id]=R.status;const live=["planning","running","verifying"].includes(R.status),fin=/^done/.test(R.status);
h+=`<div class="box"><div class="ch"><b>${esc(R.id)}</b>${sgp(R.status)}<span class="tip">${esc(R.project)} · ${esc(R.base_branch)}</span></div><div style="margin:6px 0">${esc(R.goal)}</div>${R.plan?`<div class="tip">≡ ${esc(R.plan)}</div>`:""}
<div class="act" style="margin-top:10px">${R.attachments&&R.attachments.length?`<span class="chip">＋ ${R.attachments.length} ${t("swAttached")}</span>`:""}<span class="stepper"><button data-sa="-1">−</button><b>${R.max_agents}</b><button data-sa="1">＋</button><span class="tip">${t("swAgents")}</span></span>${R.review?`<span class="tip">🔎 ${t("swReview")}</span>`:""}
${live?`<button class="btn sm dng" data-sw="stop">⏹ ${t("swStop")}</button>`:""}${fin&&!R.applied?`<button class="btn sm pri" data-sw="apply">✓ ${t("swApply")}</button>`:""}${R.applied?`<span class="tag live">${t("swApplied")}</span>`:""}${!R.cleaned&&!live?`<button class="btn sm" data-sw="cleanup">× ${t("swCleanup")}</button>`:""}</div>
${R.summary?`<div class="box" style="margin:10px 0 0;background:var(--p2)">${esc(R.summary)}</div>`:""}${R.final_verify&&R.final_verify.cmd?`<div class="tip" style="margin-top:6px">${R.final_verify.ok?"✓":"×"} ${esc(R.final_verify.cmd)}</div>`:""}
<div class="ags">${R.agents.map(a=>`<div class="ag" data-ag="${a.id}"><div class="ch"><b>${esc(a.id)}</b><span>${esc(a.title)}</span><span class="pill" style="border:0;padding:0">${sgp(a.status)}</span><span class="tip">· ${esc((S?.accounts||[]).find(x=>x.id===a.account_id)?.name||a.account_id||"")}</span></div><div>${a.files.map(f=>`<span class="gp">${esc(f)}</span>`).join("")}</div>
<div class="act2">${esc(a.activity||a.note||"")}</div><div class="tip">${a.changed.length?`· ${a.changed.length} · `:""}${a.verify_ok===true?"✓ check · ":a.verify_ok===false?"× check · ":""}${a.attempts>1?`↻ ${a.attempts} · `:""}${a.violations.length?`! ${a.violations.length} out of scope`:""}</div></div>`).join("")}</div>
${R.contracts?`<details data-o="c" ${swOpen.has("c")?"open":""}><summary class="tip" style="cursor:pointer;margin-top:10px">≡ ${t("swContracts")}</summary><pre class="mono" style="white-space:pre-wrap;color:var(--mut)">${esc(R.contracts)}</pre></details>`:""}
<details data-o="e" ${swOpen.has("e")?"open":""}><summary class="tip" style="cursor:pointer;margin-top:6px">≡ ${t("events")}</summary><div class="ev">${R.events.map(e=>`<div><time>${new Date(e.t*1e3).toLocaleTimeString()}</time>${esc(e.msg)}</div>`).join("")}</div></details></div>`}
if(box.dataset.h!==h){box.dataset.h=h;box.innerHTML=h}}
$("#swr").addEventListener("toggle",e=>{const d=e.target;if(d.dataset&&d.dataset.o){d.open?swOpen.add(d.dataset.o):swOpen.delete(d.dataset.o)}},true);
$("#sfiles").addEventListener("change",async e=>{await uploadSwarmFiles([...e.target.files]);e.target.value=""});
$("#p-swarm").addEventListener("input",e=>{if(e.target.id==="sp"){e.target.dataset.autoProject="0";renderSwarmAccounts()}});
$("#p-swarm").addEventListener("dragover",e=>e.preventDefault());$("#p-swarm").addEventListener("drop",e=>{if(e.dataTransfer&&e.dataTransfer.files.length){e.preventDefault();uploadSwarmFiles([...e.dataTransfer.files])}});
$("#p-swarm").addEventListener("click",async e=>{const rn=e.target.closest("[data-r]");if(rn){swSel=rn.dataset.r;$("#swr").dataset.h="";pollSwarm();return}
if(e.target.id==="spImprove"){improveSwarmPrompt();return}
if(e.target.id==="spUse"){swFinalPrompt=$("#sp2").value.trim();toast("✓ "+t("swFinalReady"));return}
if(e.target.id==="spAgain"){improveSwarmPrompt();return}
if(e.target.id==="spApplyCustom"){await refineSwarmPrompt();return}
const rm=e.target.closest("[data-rm-att]");if(rm){swAttachments.splice(+rm.dataset.rmAtt,1);renderSwarmAttachments();return}
if(e.target.id==="sattach"){$("#sfiles").click();return}
if(e.target.id==="sbrowse"){const p=await pickFolder($("#sp").value);if(p){$("#sp").value=p;$("#sp").dataset.autoProject="0";await act("project_context",{project:p})}return}
if(e.target.id==="sgo"){const finalPrompt=($("#spp")&&!$("#spp").hidden?($("#sp2").value.trim()||swFinalPrompt):$("#sg").value.trim()).trim();if(!finalPrompt){toast(t("swGoalPh"));return}const project=$("#sp").value.trim();if(!project){toast(t("lProj"));return}const account_ids=[...document.querySelectorAll("#swAccounts input[type=checkbox]:checked")].map(x=>x.value);if(!account_ids.length){toast("Select at least one AI account");return}const d={goal:finalPrompt,project,agents:$("#sa").value||"auto",verify:$("#sv2").value,review:$("#sr").value,strict:$("#sst").checked,init_git:$("#sgi").checked,tasks:$("#stk").value,attachments:swAttachments.map(a=>a.id),account_ids};const r=await act("swarm_start",d);if(r){swSel=r.id;$("#swr").dataset.h="";toast("* "+r.id);LS.project=d.project;localStorage.dsb_launch=JSON.stringify({...LS,project:d.project});await act("project_context",{project:d.project});pollSwarm()}return}
const sa=e.target.closest("[data-sa]");if(sa&&SW){await act("swarm_agents",{run:SW.id,n:SW.max_agents+ +sa.dataset.sa});pollSwarm();return}
const sw=e.target.closest("[data-sw]");if(sw&&SW){const k=sw.dataset.sw;if(k==="stop"){if(await ask(t("swStop")+"?"))await act("swarm_stop",{run:SW.id})}else if(k==="apply"){if(await ask(t("swApplyQ"))){const r=await act("swarm_apply",{run:SW.id});if(r)toast("✓ "+r.text)}}else if(k==="cleanup"){if(await ask(t("swCleanQ"))){await act("swarm_cleanup",{run:SW.id})}}pollSwarm();return}
const ag=e.target.closest("[data-ag]");if(ag&&SW)openAgent(SW,SW.agents.find(a=>a.id===ag.dataset.ag))});
function openAgent(R,a){let last=0;const o=modal(`<h3>${esc(a.id)} · ${esc(a.title)} ${sgp(a.status)}</h3><div class="tip">${a.files.map(f=>`<span class="gp">${esc(f)}</span>`).join("")}</div><details open><summary class="tip">${t("swTask")}</summary><div class="pth" style="direction:auto;text-align:start;white-space:pre-wrap">${esc(a.prompt)}</div></details>
${a.note?`<div class="err">${esc(a.note)}</div>`:""}${a.violations.length?`<div class="err">! ${esc(a.violations.join(", "))}</div>`:""}${a.changed.length?`<div class="tip">· ${a.changed.map(esc).join(", ")}</div>`:""}${a.verify_out?`<details><summary class="tip">✓ check</summary><pre class="mono" style="white-space:pre-wrap;font-size:12px">${esc(a.verify_out)}</pre></details>`:""}
<div id="agl" class="mono" style="background:#05070e;color:#cfd6f3;border-radius:10px;padding:8px 10px;max-height:240px;overflow:auto;font-size:12px;margin-top:8px"></div><div class="rowb"><button class="btn" data-x>${t("close")}</button></div>`,"big",false);
const tm=setInterval(async()=>{try{const r=await api(`swarm_log?run=${R.id}&agent=${a.id}&since=${last}`);r.lines.forEach(l=>{const d=document.createElement("div");d.textContent=l;$("#agl",o).append(d)});last=r.last;if(r.lines.length)$("#agl",o).scrollTop=1e9}catch{}},1000);
o.onclick=e=>{if(e.target.closest("[data-x]")){clearInterval(tm);o.close()}}}
/* ---------- boot ---------- */
const toggleMobileNav=()=>{const app=$("#app"),shade=$("#navshade");if(!app)return;const on=app.classList.toggle("navopen");if(shade)shade.hidden=!on};
$("#mobileNav").onclick=toggleMobileNav;$("#navshade").onclick=toggleMobileNav;
document.addEventListener("keydown",e=>{if(e.key==="Escape"){$("#app")?.classList.remove("navopen");$("#navshade")?.setAttribute("hidden","")}});
$("#bth").onclick=()=>{localStorage.dsb_theme=(localStorage.dsb_theme||"dark")==="dark"?"light":"dark";applyTheme()};$("#blang").onclick=()=>{L=L==="fa"?"en":"fa";localStorage.dsb_lang=L;applyLang()};
$("#bpal").onclick=openPalette;$$(".nb[data-go]").forEach(b=>b.onclick=()=>go(b.dataset.go));
function hashPage(){const h=location.hash;const r=(h.match(/#\/(\w+)/)||h.match(/[#&]p=(\w+)/)||[])[1];return PAGES.includes(r)?r:null}
window.addEventListener("hashchange",()=>{const r=hashPage();if(r&&r!==page)go(r)});
window.addEventListener("popstate",()=>{const r=hashPage();if(r&&r!==page)go(r)});
applyTheme();applyUiPerformance();connectDashStream();renderClaudeMirror();{const r=(location.hash.match(/#\/(\w+)/)||location.hash.match(/[#&]p=(\w+)/)||[])[1];page=PAGES.includes(r)?r:"dash"}applyLang();loadInfo().catch(()=>{});if(localStorage.dsb_dock==="1")setDock(true);tick();
</script></body></html>
"""



# ============================================================================
# HTTP API
# ============================================================================


class ClientGone(Exception):
    pass


MODELS = ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-web",
          "claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-20250514",
          "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-5-opus-20241022"]


class APIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 600          # a client that stalls mid-request can no longer pin a thread forever

    def log_message(self, fmt, *args) -> None:
        pass

    def setup(self) -> None:
        super().setup()
        state = getattr(self.server, "runtime_state", None)
        self._runtime_token = _CURRENT_STATE.set(state) if state is not None else None

    def finish(self) -> None:
        try:
            super().finish()
        finally:
            token = getattr(self, "_runtime_token", None)
            if token is not None:
                try:
                    _CURRENT_STATE.reset(token)
                except Exception:
                    pass
                self._runtime_token = None

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionError, BrokenPipeError, socket.timeout):
            pass
        except OSError as exc:
            if getattr(exc, "errno", None) not in (10053, 10054, 104, 32):
                raise

    # ---- low level -----------------------------------------------------------

    def _w(self, s: str) -> None:
        self.wfile.write(s.encode("utf-8"))
        self.wfile.flush()

    def _send_json(self, code: int, obj: Dict[str, Any]) -> None:
        body = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionError, BrokenPipeError):
            pass

    def _err(self, code: int, etype: str, msg: str) -> None:
        self._send_json(code, {"type": "error", "error": {"type": etype, "message": msg}})

    def _open_sse(self) -> None:
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        self.wfile.flush()

    def _client_gone(self) -> bool:
        try:
            r, _, _ = select.select([self.connection], [], [], 0)
            if r:
                return self.connection.recv(1, socket.MSG_PEEK) == b""
        except Exception:
            return True
        return False

    def _check_hook_auth(self) -> bool:
        supplied=self.headers.get("Authorization","").strip()
        supplied=supplied[7:].strip() if supplied.lower().startswith("bearer ") else supplied
        if not supplied: supplied=self.headers.get("x-ds-bridge-hook-key","").strip()
        expected=str((getattr(_state().BRIDGE,"cfg",{}) or {}).get("hook_key") or "")
        if not expected or not supplied: return False
        return secrets.compare_digest(supplied.encode("utf-8","ignore"),expected.encode("utf-8"))

    def _check_auth(self) -> bool:
        auth = self.headers.get("Authorization", "").strip()
        supplied = auth[7:].strip() if auth.lower().startswith("bearer ") else auth
        if not supplied:
            supplied = self.headers.get("x-api-key", "").strip()
        if not supplied:
            supplied = self.headers.get("anthropic-api-key", "").strip()
        if not supplied and self.path.startswith("/dash/api/stream"):
            try:
                supplied = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("key", [""])[0]
            except Exception:
                supplied = ""
        if not _state().API_KEY:
            return False
        return secrets.compare_digest(supplied.encode("utf-8", "ignore"), _state().API_KEY.encode("utf-8"))

    def _read_body(self) -> bytes:
        te = self.headers.get("Transfer-Encoding", "").lower()
        if "chunked" in te:
            chunks, total = [], 0
            while True:
                raw = self.rfile.readline(65537)
                if not raw:      # EOF: readline() returns b"" forever, so never `continue` on it
                    raise ConnectionError("connection closed inside a chunked request body")
                line = raw.strip()
                if not line:
                    continue
                size = int(line.split(b";")[0], 16)
                if size < 0:
                    raise ValueError("invalid chunk size")
                if size == 0:
                    while True:                       # optional trailers, ends with an empty line / EOF
                        if not self.rfile.readline(65537).strip():
                            break
                    break
                total += size
                if total > _state().MAX_HTTP_BODY_BYTES:
                    raise ValueError(f"request body too large (> {_state().MAX_HTTP_BODY_BYTES:,} bytes)")
                data = self.rfile.read(size)
                if len(data) != size:
                    raise ConnectionError("truncated chunk in request body")
                chunks.append(data)
                self.rfile.readline()
            return b"".join(chunks)
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            raise ValueError("invalid Content-Length header")
        if n < 0:
            raise ValueError("invalid Content-Length header")
        if n > _state().MAX_HTTP_BODY_BYTES:
            raise ValueError(f"request body too large ({n:,} bytes)")
        if n == 0:
            return b""
        data = self.rfile.read(n)
        if len(data) != n:
            raise ConnectionError("request body ended early")
        return data

    # ---- routes ----------------------------------------------------------------

    def do_OPTIONS(self) -> None:
        try:
            origin=self.headers.get("Origin","").strip()
            allow=""
            if origin and (urllib.parse.urlsplit(origin).hostname or "").lower() in ("127.0.0.1","localhost","::1"):
                allow=origin
            self.send_response(204)
            if allow:
                self.send_header("Access-Control-Allow-Origin",allow)
                self.send_header("Vary","Origin")
                self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type, X-Api-Key, X-Ds-Bridge-Hook-Key, anthropic-api-key")
                self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
            self.send_header("Content-Length","0")
            self.end_headers()
        except Exception:
            pass

    def do_GET(self) -> None:
        path = self._route_path()
        if path in ("/dash", "/dash/"):
            if self._dash_host_ok():
                self._send_html(DASH_HTML)
        elif path == "/dash/api/stream":
            if self._dash_host_ok():
                if not self._check_auth():
                    self._err(401, "authentication_error", "invalid api key")
                else:
                    self._dash_stream()
        elif path.startswith("/dash/api/"):
            if self._dash_host_ok():
                if not self._check_auth():
                    self._err(401, "authentication_error", "invalid api key")
                else:
                    try:
                        from urllib.parse import parse_qs, urlsplit
                        self._send_json(200, dash_get(_state().BRIDGE, path[len("/dash/api/"):],
                                                      parse_qs(urlsplit(self.path).query)))
                    except ValueError as exc:
                        self._err(400, "invalid_request_error", str(exc))
        elif path == "/":
            state = _state()
            self._send_json(200, {"ok": True, "service": "deepseek-local-bridge", "version": VERSION,
                                  "accounts": len(getattr(state.BRIDGE, "accounts", []) or [])})
        elif path == "/health":
            state = _state()
            bound_port = int(getattr(self.server, "server_address", ("127.0.0.1", state.RESOLVED_PORT))[1])
            self._send_json(200, {
                "ok": True, "service": "deepseek-local-bridge", "version": VERSION,
                "accounts": len(getattr(state.BRIDGE, "accounts", []) or []),
                "script": str(state.paths.script),
                "instance_name": state.instance_name,
                "instance_home": str(state.paths.home),
                "config": str(state.CONFIG_PATH),
                "pid": state.PID,
                "start_time": state.START_TIME,
                "port": bound_port,
            })
        elif path == "/v1/models":
            self._send_json(200, {"object": "list", "data": [
                {"id": m, "object": "model", "type": "model", "display_name": m, "owned_by": "local"} for m in MODELS]})
        else:
            self._err(404, "not_found_error", f"unknown path: {path}")

    def do_POST(self) -> None:
        path = self._route_path()
        is_hook = path == "/dash/api/claude-hook"
        if is_hook:
            if not self._dash_host_ok():
                return
            if not self._check_hook_auth():
                log("[claude-hook] authentication failed", C.red, event="hook_auth_failed")
                self._err(401, "authentication_error", "invalid hook key")
                return
        elif not self._check_auth():
            log("[http] authentication failed", C.red)
            self._err(401, "authentication_error", "invalid api key")
            return
        try:
            body = self._read_body()
        except (socket.timeout, TimeoutError):
            self.close_connection = True
            self._err(408, "invalid_request_error", "timed out while reading the request body")
            return
        except Exception as exc:                 # incl. truncated bodies: answer if the peer can still read
            self.close_connection = True
            self._err(400, "invalid_request_error", str(exc))
            return
        if path == "/dash/api/claude-hook":
            try:
                data = json.loads(body) if body else {}
                if not isinstance(data, dict):
                    raise ValueError("hook body must be a JSON object")
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                ingest_claude_hook(_state().BRIDGE, data)
            except Exception as exc:
                log(f"[claude-hook] ignored malformed hook event: {exc}", C.yellow)
            return
        if path == "/dash/api/swarm_attachment":
            if not self._dash_host_ok():
                return
            name = urllib.parse.unquote(self.headers.get("X-Filename", "attachment"))
            mime = self.headers.get("X-Mime", "application/octet-stream")
            try:
                meta = store_swarm_attachment(name, mime, body)
                self._send_json(200, {"ok": True, "attachment": {k: meta[k] for k in ("id", "name", "mime", "size")}})
            except ValueError as exc:
                self._err(400, "invalid_request_error", str(exc))
            return
        if not body.strip():
            self._err(400, "invalid_request_error", "empty request body")
            return
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError("request JSON must be an object")
        except Exception as exc:
            self._err(400, "invalid_request_error", f"invalid JSON: {exc}")
            return
        try:
            if path == "/v1/messages":
                self._chat(normalize_anthropic(data, "anthropic", "toolu_"))
            elif path == "/v1/chat/completions":
                req = normalize_anthropic(openai_to_anthropic(data), "openai", "call_")
                self._chat(req)
            elif path.startswith("/dash/api/"):
                if self._dash_host_ok():
                    try:
                        self._send_json(200, dash_action(_state().BRIDGE, path[len("/dash/api/"):], data))
                    except ValueError as exc:
                        self._err(400, "invalid_request_error", str(exc))
            elif path == "/v1/messages/count_tokens":
                self._send_json(200, {"input_tokens": estimate_tokens(
                    [data.get("system"), data.get("messages"), data.get("tools")])})
            else:
                self._err(404, "not_found_error", f"unknown path: {path}")
        except (ClientGone, ConnectionError, BrokenPipeError):
            pass
        except Exception as exc:
            traceback.print_exc()
            try:
                self._err(500, "api_error", str(exc))
            except Exception:
                pass

    # ---- dashboard helpers -----------------------------------------------------

    def _route_path(self) -> str:
        """Parse optional /a/<account> and /s/<agent-tag> prefixes in either order."""
        path = self.path.split("?", 1)[0]
        self._pin = self._tag = None
        from urllib.parse import unquote
        # Allow /a/<account>/s/<tag>/v1/... so Swarm can pin both dimensions at once.
        for _ in range(2):
            mt = re.match(r"^/a/([^/]+)(/.*)$", path)
            if mt and self._pin is None:
                self._pin, path = unquote(mt.group(1)), mt.group(2)
                continue
            mt = re.match(r"^/s/([^/]+)(/.*)$", path)
            if mt and self._tag is None:
                self._tag, path = unquote(mt.group(1)), mt.group(2)
                continue
            break
        return path

    def _dash_host_ok(self) -> bool:
        """DNS-rebinding / cross-site protection: only local Host and Origin values are accepted."""
        from urllib.parse import urlparse
        local = ("127.0.0.1", "localhost", "::1")
        host = (self.headers.get("Host", "") or "").rsplit(":", 1)[0].strip("[]").lower()
        origin = self.headers.get("Origin")
        bad = host not in local
        if origin and not bad:
            try:
                bad = (urlparse(origin).hostname or "").lower() not in local
            except Exception:
                bad = True
        if bad:
            self._err(403, "permission_error", "dashboard is only available from localhost")
        return not bad

    def _dash_stream(self) -> None:
        """Low-overhead dashboard event stream; sends only deltas and never blocks the producer."""
        q: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=256)
        add_dash_subscription(q)
        try:
            self.close_connection = True
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            # Backlog is intentionally bounded so a reconnect is cheap.
            for event in list(_state().CLAUDE_MIRROR)[-120:]:
                payload = json.dumps(event.get("data", {}), ensure_ascii=False, separators=(",", ":"))
                self.wfile.write(f"id: {int(event.get('id', 0))}\nevent: {event.get('kind', 'event')}\ndata: {payload}\n\n".encode("utf-8"))
            self.wfile.flush()
            last_ping = time.time()
            while True:
                try:
                    event = q.get(timeout=15)
                    payload = json.dumps(event.get("data", {}), ensure_ascii=False, separators=(",", ":"))
                    self.wfile.write(f"id: {int(event.get('id', 0))}\nevent: {event.get('kind', 'event')}\ndata: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    last_ping = time.time()
                except (BrokenPipeError, ConnectionError, OSError):
                    break
                if self._client_gone():
                    break
                if time.time() - last_ping > 30:
                    try:
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
                        last_ping = time.time()
                    except (BrokenPipeError, ConnectionError, OSError):
                        break
        finally:
            remove_dash_subscription(q)

    def _send_html(self, html: str) -> None:
        html = html.replace("__INSTANCE_NAME__", _state().instance_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        body = html.encode("utf-8")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionError, BrokenPipeError):
            pass

    def _reply_local(self, req: NormReq, text: str, in_tokens: int) -> None:
        outcome = Outcome(text=text, calls=[])
        if req.stream:
            self._open_sse()
            em = self._emitter(req, in_tokens)
            em.start()
            self._deliver(req, outcome, em, "", in_tokens)
        else:
            self._deliver(req, outcome, None, "", in_tokens)

    # ---- chat ------------------------------------------------------------------

    def _emitter(self, req: NormReq, in_tokens: int):
        model = req.model or "deepseek-v4-pro"
        cls = AnthropicSSE if req.fmt == "anthropic" else OpenAISSE
        return cls(self._w, model, in_tokens)

    def _deliver(self, req: NormReq, outcome: Outcome, emitter, sent_text: str, in_tokens: int) -> None:
        model = req.model or "deepseek-v4-pro"
        if emitter is None:
            if req.fmt == "anthropic":
                self._send_json(200, anthropic_message(outcome, model, in_tokens))
            else:
                self._send_json(200, openai_completion(outcome, model, in_tokens))
            return
        rest, diverged = reconcile_stream(outcome.text, sent_text)
        if diverged:
            log("[stream] final reply differs from the text already streamed; "
                "the difference was not resent (a stream cannot be retracted)", C.yellow)
        if rest.strip():
            emitter.text(rest)
        for c in outcome.calls:
            emitter.tool(c)
        emitter.finish(outcome.stop_reason)

    def _chat(self, req: NormReq) -> None:
        req.pin = getattr(self, "_pin", None)
        req.tag = getattr(self, "_tag", None)
        sw = getattr(_state().BRIDGE, "swarm", None)
        if req.tag and sw is not None:
            req.role = sw.role_of(req.tag)
        t_req = time.time()
        if req.pin and hasattr(_state().BRIDGE, "get") and _state().BRIDGE.get(req.pin) is None:
            self._err(404, "not_found_error", f"unknown account '{req.pin}'")
            return
        in_tokens = estimate_tokens([req.system_text, req.messages, list(req.tools)])
        log(f"[http] {req.fmt} model={req.model} stream={req.stream} msgs={len(req.messages)} "
            f"tools={len(req.tools)} tool_choice={req.tool_choice.get('type', 'auto')}"
            f"{' side' if req.side else ''}", C.dim)
        emit_dash_event("request", {"tag": req.tag or "", "role": req.role or "", "model": req.model,
                                     "stream": bool(req.stream), "messages": len(req.messages),
                                     "tools": len(req.tools), "side": bool(req.side)})

        # Quota / connectivity probes never touch the browser.
        if req.max_tokens is not None and req.max_tokens <= 1 and not req.tools:
            self._reply_local(req, "ok", in_tokens)
            return

        # /ds slash command typed in Claude Code: answered here, instantly, without any model call.
        if not req.side and hasattr(_state().BRIDGE, "run_command"):
            cmd = extract_bridge_command(req)
            if cmd is not None:
                self._reply_local(req, _state().BRIDGE.run_command(cmd, ctx={"cwd": claude_cwd(req)}), in_tokens)
                return

        if _state().BRIDGE is None or not _state().BRIDGE.ok:
            self._err(529, "overloaded_error", "bridge is not ready")
            return

        cancel = threading.Event()
        evq: "queue.Queue[str]" = queue.Queue()
        streamer = SafeTextStream(evq.put)
        prio = _state().PRIORITY_SIDE if req.side else _state().PRIORITY_MAIN
        on_part = streamer.update if req.stream else None
        if hasattr(_state().BRIDGE, "dispatch"):
            fut = _state().BRIDGE.dispatch(req, cancel, on_part, lambda: bool(streamer.sent_text), prio)
        else:
            fut = _state().BRIDGE.submit(lambda eng: eng.process(req, cancel, on_part), priority=prio, cancel=cancel)
        emitter = None
        # Generous: a request may legitimately wait behind other long jobs.
        deadline = time.time() + _state().MAX_REPLY_SECONDS * 3 + 300
        try:
            if req.stream:
                self._open_sse()
                emitter = self._emitter(req, in_tokens)
                emitter.start()
            last_write = time.time()
            while True:
                try:
                    delta = evq.get(timeout=0.4)
                    if emitter:
                        emitter.text(delta)
                        last_write = time.time()
                    continue
                except queue.Empty:
                    pass
                if fut.done() and evq.empty():
                    break
                if not fut.done():
                    if not _state().BRIDGE.alive():
                        raise BridgeError("the selected AI worker thread stopped unexpectedly", "upstream")
                    if time.time() > deadline:
                        raise BridgeError("the request exceeded the overall time limit", "timeout")
                if self._client_gone():
                    raise ClientGone()
                if emitter and time.time() - last_write > 8:
                    emitter.ping()
                    last_write = time.time()
            outcome = fut.result()
            record_activity(req, outcome, time.time() - t_req, in_tokens)
            self._deliver(req, outcome, emitter, streamer.sent_text, in_tokens)
        except (ClientGone, ConnectionError, BrokenPipeError):
            cancel.set()
            log("[http] client disconnected; cancelling generation", C.yellow)
        except BridgeCancelled:
            pass
        except Exception as exc:
            cancel.set()                      # a queued / running job must not outlive its request
            code, etype = error_status(exc)
            record_activity(req, None, time.time() - t_req, in_tokens, err=str(exc))
            log(f"[http] request failed ({code} {etype}): {exc}", C.red)
            if emitter is not None:
                try:
                    emitter.error(etype, str(exc))
                except Exception:
                    pass
            else:
                self._err(code, etype, str(exc))


# ============================================================================
# Server
# ============================================================================

def start_server(port: int, state: Optional[RuntimeState] = None) -> ThreadingHTTPServer:
    state = state or _state()
    server = ThreadingHTTPServer(("127.0.0.1", int(port)), APIHandler)
    server.runtime_state = state
    server.daemon_threads = True
    state_thread(target=server.serve_forever, daemon=True, name="DeepSeekHTTP").start()
    return server


def stop_server(server: Optional[ThreadingHTTPServer]) -> None:
    if not server:
        return
    for fn in (server.shutdown, server.server_close):
        try:
            fn()
        except Exception:
            pass


# ============================================================================
# CLI
# ============================================================================

def print_banner(cfg: Dict[str, Any], url: str, mode: str = DEFAULT_MODE, mode_src: str = "default") -> None:
    key = cfg["api_key"]
    print()
    print(C.bold("=" * 70))
    print(C.bold(f"  DeepSeek Local Bridge V{VERSION}"))
    print(C.bold("=" * 70))
    print()
    print(C.green("  API Key:"))
    print(f"    {C.bold(key)}")
    print()
    print(C.green("  Endpoints:"))
    print(f"    Anthropic / OpenAI : {C.cyan(url + '/v1')}")
    print(f"    Health             : {C.cyan(url + '/health')}")
    print(f"    Dashboard          : {C.cyan(url + '/dash#k=' + key)}")
    print()
    print(C.green("  Claude Code (PowerShell):"))
    for line in (f'$env:ANTHROPIC_BASE_URL="{url}"', f'$env:ANTHROPIC_API_KEY="{key}"',
                 '$env:ANTHROPIC_MODEL="claude-sonnet-4-20250514"',
                 '$env:ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-haiku-4-20250514"',
                 '$env:CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000"',
                 '$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"',
                 f'$env:API_TIMEOUT_MS="{CLIENT_API_TIMEOUT_MS}"',
                 f'$env:BASH_DEFAULT_TIMEOUT_MS="{CLIENT_BASH_DEFAULT_TIMEOUT_MS}"',
                 f'$env:BASH_MAX_TIMEOUT_MS="{CLIENT_BASH_MAX_TIMEOUT_MS}"'):
        print("    " + line)
    print()
    print(C.green("  Claude Code (cmd.exe):"))
    for line in (f"set ANTHROPIC_BASE_URL={url}", f"set ANTHROPIC_API_KEY={key}",
                 "set ANTHROPIC_MODEL=claude-sonnet-4-20250514",
                 "set ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-haiku-4-20250514",
                 "set CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000",
                 "set CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
                 f"set API_TIMEOUT_MS={CLIENT_API_TIMEOUT_MS}",
                 f"set BASH_DEFAULT_TIMEOUT_MS={CLIENT_BASH_DEFAULT_TIMEOUT_MS}",
                 f"set BASH_MAX_TIMEOUT_MS={CLIENT_BASH_MAX_TIMEOUT_MS}"):
        print("    " + line)
    print()
    print(C.green("  Claude Code (bash / zsh):"))
    for line in (f'export ANTHROPIC_BASE_URL="{url}"', f'export ANTHROPIC_API_KEY="{key}"',
                 'export ANTHROPIC_MODEL="claude-sonnet-4-20250514"',
                 'export ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-haiku-4-20250514"',
                 'export CLAUDE_CODE_MAX_CONTEXT_TOKENS="1000000"',
                 'export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"',
                 f'export API_TIMEOUT_MS="{CLIENT_API_TIMEOUT_MS}"',
                 f'export BASH_DEFAULT_TIMEOUT_MS="{CLIENT_BASH_DEFAULT_TIMEOUT_MS}"',
                 f'export BASH_MAX_TIMEOUT_MS="{CLIENT_BASH_MAX_TIMEOUT_MS}"'):
        print("    " + line)
    print()
    print(C.green("  Tuning:"))
    print(f"    history budget / new chat : {_state().HISTORY_BUDGET_CHARS:,} chars  (~{int(_state().HISTORY_BUDGET_CHARS / _state().CHARS_PER_TOKEN):,} tokens)")
    print(f"    hard prompt ceiling       : {_state().MAX_PROMPT_CHARS:,} chars  (DS_BRIDGE_MAX_PROMPT_CHARS)")
    print(f"    max block in follow-ups   : {_state().DELTA_BLOCK_LIMIT:,} chars  (DS_BRIDGE_DELTA_BLOCK_LIMIT)")
    print(f"    chat rotation             : {_state().ROTATE_CHARS:,} chars")
    print(f"    max live tabs             : {_state().MAX_TABS}  (older conversations hibernate, chats are kept; up to {_state().MAX_KEPT_CONVS})")
    print(f"    stall / max reply         : {_state().STALL_TIMEOUT}s / {_state().MAX_REPLY_SECONDS}s   retries: {_state().MAX_RETRIES} (backoff up to {_state().RETRY_BACKOFF_MAX}s)")
    print(f"    delete old bridge chats   : {_state().DELETE_OLD_CHATS}")
    print(f"    Claude Code mode          : {mode}  [{mode_src}]  (--mode safe|ask|auto, --set-mode to save)")
    print(f"    debug dir                 : {_state().DEBUG_DIR or '(off)'}")
    print(f"    config file               : {_state().CONFIG_PATH}")
    print()
    print(C.dim("  Type /help for terminal commands."))
    print()


def print_help() -> None:
    print(C.bold("\nCommands:"))
    for c, d in [("/help", "this help"), ("/key", "show API key"), ("/url", "show base URL"),
                 ("/status", "accounts, usage + live conversations"),
                 ("/acc <cmd>", "account command: next | prev | use N | auto | add NAME | ..."),
                 ("/new", "new terminal chat"), ("/reset", "forget all Claude Code conversations"),
                 ("/purge", "delete every chat this bridge created"), ("/exit", "quit"),
                 ("<text>", "chat directly with DeepSeek (keeps context)")]:
        print(f"  {C.cyan(c):<22} {d}")
    print()


def terminal_loop(cfg: Dict[str, Any], url: str) -> None:
    def run(fn):
        return _state().BRIDGE.submit(fn, _state().PRIORITY_MAIN).result(timeout=300)

    while True:
        try:
            line = input(C.green("You> ")).strip()
        except EOFError:
            print(C.dim("[stdin closed] running as a background service; press Ctrl+C to stop."))
            try:
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                return
        except KeyboardInterrupt:
            print("\nbye.")
            return
        if not line:
            continue
        try:
            if line.startswith("/"):
                cmd = line.split()[0].lower()
                if cmd in ("/exit", "/quit"):
                    return
                if cmd == "/help":
                    print_help()
                elif cmd == "/key":
                    print(cfg["api_key"])
                elif cmd == "/url":
                    print(url)
                elif cmd == "/status":
                    print(f"  server : {url}")
                    print(_state().BRIDGE.status_text())
                    convs = _state().BRIDGE.describe_all()
                    print("  conversations:" if convs else "  conversations: (none)")
                    for c in convs:
                        print("    " + c)
                elif cmd in ("/acc", "/accounts"):
                    print(_state().BRIDGE.run_command(line[len(cmd):].strip() or "status"))
                elif cmd == "/new":
                    run(lambda e: e.terminal_reset())
                    print(C.green("[new terminal chat]"))
                elif cmd == "/reset":
                    print(C.green(f"[dropped {run(lambda e: e.reset_all())} conversation(s)]"))
                elif cmd == "/purge":
                    print(C.green(f"[deleted {run(lambda e: e.purge_all())} chat(s)]"))
                else:
                    print(C.red(f"[unknown command] {cmd}"))
                continue
            print(C.cyan("DeepSeek> "), end="", flush=True)
            print(run(lambda e: e.terminal(line)))
        except KeyboardInterrupt:
            print("\nbye.")
            return
        except Exception as exc:
            print(C.red(f"\n[error] {exc}"))


# ============================================================================
# Self-tests (no browser needed)
# ============================================================================


def _selftest_v63_new_features() -> None:
    """V6.3: attachment storage, worktree exclusion, prompt improve, live events."""
    import tempfile
    old_cfg = _state().CONFIG_PATH
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _state().CONFIG_PATH = root / "cfg.json"
        # Attachment round-trip, arbitrary bytes (including NULs), and safe filename handling.
        old_attach = _state().SWARM_ATTACH_DIR
        _state().SWARM_ATTACH_DIR = root / "attachments"
        payload = bytes(range(256)) * 4
        meta = store_swarm_attachment("photo<>name.zip", "application/zip", payload)
        got = get_swarm_attachment(meta["id"])
        assert got["size"] == len(payload)
        assert (Path(got["path"]).read_bytes() == payload)

        # Prompt improver action must preserve original/current/custom channels.
        class _PromptPool:
            def __init__(self): self.cfg = {"settings": {}}; self.calls = []
            def ask(self, prompt, **kw): self.calls.append(prompt); return "IMPROVED: preserve intent"
            def event(self, *args): pass
            def snapshot(self): return {}
            def get(self, *args): return None
        pp = _PromptPool()
        r = dash_action(pp, "swarm_prompt_improve", {"prompt": "Build an API", "current": "Build a REST API", "custom": "Add tests"})
        assert r["improved"] == "IMPROVED: preserve intent" and "CURRENT AI-IMPROVED VERSION" in pp.calls[0] and "Add tests" in pp.calls[0]

        # Real git worktree attachment test: attachment input must remain untracked.
        if shutil.which("git"):
            proj = root / "repo"
            proj.mkdir()
            git(["init", "-q"], proj)
            (proj / "base.txt").write_text("base\n", encoding="utf-8")
            git(["add", "base.txt"], proj)
            git(["-c", "user.email=test@example.invalid", "-c", "user.name=Test", "commit", "-q", "-m", "base"], proj)
            wt = root / "wt"
            git(["worktree", "add", "-q", "-b", "v63-test", str(wt), "HEAD"], proj)
            try:
                class _A:
                    def __init__(self): self.id="a1"; self.log=[]; self.activity=""
                    def add_log(self, msg): self.log.append(msg)
                class _R:
                    def __init__(self): self.opts={"attachments":[meta["id"]]}; self.agents=[]
                fake = object.__new__(Swarm)
                fake.pool = None
                paths = fake._materialize_attachments(_R(), _A(), wt)
                assert len(paths) == 1 and Path(paths[0]).is_file()
                status = git(["status", "--porcelain"], wt, check=False).stdout.strip()
                assert ".dsb-agent-input" not in status, status
            finally:
                git(["worktree", "remove", "--force", str(wt)], proj, check=False)
                git(["branch", "-D", "v63-test"], proj, check=False)
        _state().SWARM_ATTACH_DIR = old_attach
    _state().CONFIG_PATH = old_cfg

def _selftest_multiauth() -> None:
    """Offline regression tests for multi web providers, thinking setting, and project affinity."""
    assert {x["id"] for x in PROVIDERS if x.get("kind")=="web"} >= {"deepseek_web","chatgpt_web","grok_web"}
    assert WEB_RECIPES["chatgpt_web"]["login_url"].startswith("https://chatgpt.com/auth/login")
    assert WEB_RECIPES["grok_web"]["url"].startswith("https://grok.com")
    assert any(s[0]=="THINK_MODE" and s[1]=="bool" and s[7]=="live" for s in SETTINGS_SCHEMA)
    assert any(s[0]=="PARALLEL_MODE" and s[1]=="choice" and s[7]=="live" for s in SETTINGS_SCHEMA)
    assert any(s[0]=="UI_MODE" and s[1]=="choice" and s[7]=="live" for s in SETTINGS_SCHEMA)
    assert 'account_ids' in DASH_HTML and 'add_web' in DASH_HTML and 'swAccounts' in DASH_HTML
    class P:
        def __init__(self):
            self.project_accounts={}; self.accounts=[]; self.lock=threading.RLock(); self.cfg={"accounts":[]}
            self.routing={"strategy":"balanced","smart_routing":False,"auto_failover":True,"rotate_requests":0,"rotate_minutes":0}
        def _project_key(self,p): return Pool._project_key(p)
        def project_accounts_for(self,p): return Pool.project_accounts_for(self,p)
        def get(self,x): return next((a for a in self.accounts if a.id==x),None)
        def get_by_id(self,x): return self.get(x)
        def _save(self): pass
        def event(self,*a): pass
    with tempfile.TemporaryDirectory() as td:
        p=P(); proj=str(Path(td).resolve())
        a1=Account({"id":"deep","name":"Deep","enabled":True,"kind":"web","provider":"deepseek_web"}); a2=Account({"id":"gpt","name":"GPT","enabled":True,"kind":"web","provider":"chatgpt_web"})
        class W:
            ok=True
            engine=None
        for a in (a1,a2): a.worker=W(); a.status="ready"
        p.accounts=[a1,a2]
        Pool.set_project_accounts(p,proj,["gpt"])
        assert p.project_accounts_for(proj)==["gpt"]
        Pool.set_project_accounts(p,proj,["deep","gpt"])
        assert p.project_accounts_for(proj)==["deep","gpt"]
        class Req:
            system_text=f"Primary working directory: {proj}"
            headers={}
        picked, why = Pool.pick(p, Req())
        assert picked in (a1,a2) and why == "balanced", (picked, why)
        # Swarm must distribute independent tasks round-robin across every selected account.
        sw=Swarm(p)
        run=SwarmRun("sw-test","parallel",Path(proj),"base","main",{"agents":2,"tasks_text":"task one\ntask two\ntask three","account_ids":["deep","gpt"]})
        sw._plan(run)
        assert [a.account_id for a in run.agents] == ["deep","gpt","deep"]
    # Generic web prompt injection must never use clipboard/paste (ChatGPT turns >10k pastes into attachments).
    class _Loc:
        def __init__(self): self.value=None
        def fill(self, text, timeout=0): self.value=text
    class _Page:
        def __init__(self): self.loc=_Loc(); self.eval_calls=[]
        def evaluate(self, script, arg=None): self.eval_calls.append((script,arg)); return {"ok":False,"len":0}
        def locator(self, sel):
            class _L:
                def __init__(self, loc): self.loc=loc
                @property
                def first(self): return self.loc
            return _L(self.loc)
    fp=_Page(); dt=DeepSeekWeb(profile_dir=Path(tempfile.gettempdir())/"dsb-test", provider="chatgpt_web")
    long_text="X"*25000
    assert dt._inject_generic(fp, "textarea", long_text)==25000 and fp.loc.value==long_text
    assert "clipboard" not in str(fp.eval_calls[0][0]).lower() and "insert_text" not in str(fp.eval_calls[0][0]).lower()
    d=dt
    assert d.provider=="chatgpt_web" and d.recipe["name"]=="ChatGPT" and d.think_pref==bool(_state().THINK_MODE)
    # Native API reasoning fields are added only when the live setting is enabled.
    old_think=_state().THINK_MODE
    try:
        _state().THINK_MODE=True
        class A: provider="deepseek_api"; model="deepseek-chat"
        body=apply_think_mode({"messages":[]},A())
        assert body["thinking"]=={"type":"enabled"}
        class B: provider="openai"; model="gpt-5.2"
        body2=apply_think_mode({"messages":[]},B())
        assert body2["reasoning_effort"]=="high"
        _state().THINK_MODE=False
        body3=apply_think_mode({"messages":[]},A())
        body4=apply_think_mode({"messages":[]},B())
        assert body3["thinking"]=={"type":"disabled"}
        assert body4["reasoning_effort"]=="low"
        tool_body=apply_think_mode({"messages":[],"tools":[{"type":"function"}],"tool_choice":"required"},A())
        assert tool_body["thinking"]=={"type":"disabled"} and tool_body["tool_choice"]=="required"
        _state().THINK_MODE=True
        tool_body=apply_think_mode({"messages":[],"tools":[{"type":"function"}],"tool_choice":"required"},A())
        assert tool_body["thinking"]=={"type":"enabled"} and tool_body["tool_choice"]=="auto"
    finally:
        _state().THINK_MODE=old_think



def _selftest_master_hardening() -> None:
    """Focused regression tests for the implementation gates added in V6.4."""
    import inspect
    import types

    # Browser lifecycle is explicit and rejects arbitrary state jumps.
    d = DeepSeekWeb(profile_dir=Path(tempfile.gettempdir()) / "dsb-lifecycle-test", provider="deepseek_web")
    assert d.lifecycle_state == "CREATED"
    d._transition("STARTING", "test")
    d._transition("READY", "test")
    d._transition("BUSY", "test")
    d._transition("WAITING_RESPONSE", "test")
    d._transition("READY", "test")
    try:
        d._transition("LOGIN_REQUIRED", "illegal test transition")
        raise AssertionError("invalid browser lifecycle transition was accepted")
    except RuntimeError:
        pass

    # Hook authentication is intentionally separate from the public API key.
    cfg = {"api_key": "api-secret", "hook_key": "hook-secret", "port": 8788}
    env = claude_env(cfg, "http://127.0.0.1:8788")
    assert env["DS_BRIDGE_HOOK_KEY"] == "hook-secret" and env["DS_BRIDGE_HOOK_KEY"] != cfg["api_key"]

    old_env_events = os.environ.get("DS_BRIDGE_CLAUDE_HOOK_EVENTS")
    try:
        os.environ["DS_BRIDGE_CLAUDE_HOOK_EVENTS"] = "MessageDisplay,DefinitelyNotAClaudeHook"
        events = _claude_hook_events()
        assert "MessageDisplay" in events and "DefinitelyNotAClaudeHook" not in events
    finally:
        if old_env_events is None:
            os.environ.pop("DS_BRIDGE_CLAUDE_HOOK_EVENTS", None)
        else:
            os.environ["DS_BRIDGE_CLAUDE_HOOK_EVENTS"] = old_env_events

    # A localhost-only, non-wildcard CORS policy is part of the dashboard boundary.
    opts_src = inspect.getsource(APIHandler.do_OPTIONS)
    assert 'Access-Control-Allow-Origin", "*"' not in opts_src and "allow-origin: *" not in opts_src.lower()

    # The hook endpoint uses the dedicated hook key.
    class _HookHandler:
        headers = {"Authorization": "Bearer hook-secret"}
    old_bridge = _state().BRIDGE
    try:
        class _HookPool:
            cfg = {"hook_key": "hook-secret"}
        _state().BRIDGE = _HookPool()
        assert APIHandler._check_hook_auth(_HookHandler()) is True
        _HookHandler.headers = {"Authorization": "Bearer wrong"}
        assert APIHandler._check_hook_auth(_HookHandler()) is False
    finally:
        _state().BRIDGE = old_bridge

    # An explicit empty account list must remain empty; it must not resurrect the legacy
    # DeepSeek profile or crash while assigning the pinned account.
    empty_cfg = {"accounts": [], "routing": {}}
    empty_pool = Pool(empty_cfg, autostart=False)
    assert empty_pool.accounts == [] and empty_pool.routing.get("pinned") is None
    assert startup_prepare_accounts(empty_pool, {"mode": "multi", "full": False}) == []

    # Deleted accounts remain permanent deletions; the compatibility API must fail clearly.
    restore_pool = Pool({"api_key": "k", "hook_key": "h", "accounts": [], "routing": {}}, autostart=False)
    deleted = Account({"id": "r1", "name": "Deleted", "enabled": False, "deleted": True,
                       "kind": "api", "provider": "custom_openai", "api_key": "x",
                       "base_url": "http://127.0.0.1", "model": "m"})
    try:
        restore_pool.restore_account(deleted, start=True)
        raise AssertionError("deleted account unexpectedly restorable")
    except ValueError as exc:
        assert "cannot be restored" in str(exc)

    # Deterministic lane ownership is stable and independent of request IDs.
    eg = Engine.__new__(Engine)
    eg.ds = types.SimpleNamespace(provider="chatgpt_web", name="ChatGPT 1")
    eg.acct = types.SimpleNamespace(id="chatgpt-1")
    eg._lane_locks = {}
    req1 = types.SimpleNamespace(side=False, tag="agent-17", system_text="Primary working directory: C:/Project")
    req2 = types.SimpleNamespace(side=False, tag="agent-17", system_text="Primary working directory: C:/Project")
    req3 = types.SimpleNamespace(side=False, tag="agent-18", system_text="Primary working directory: C:/Project")
    assert eg._lane_lock_key(req1) == eg._lane_lock_key(req2)
    assert eg._lane_lock_key(req1) != eg._lane_lock_key(req3)

    # Dashboard-only / selection-driven startup must not auto-start saved browser accounts.
    with tempfile.TemporaryDirectory() as td:
        old_accounts_dir = _state().ACCOUNTS_DIR
        try:
            cfg_path = Path(td) / "cfg.json"
            cfg_local = {"api_key":"k", "hook_key":"h", "accounts":[{"id":"saved","name":"Saved",
                          "enabled":True,"kind":"web","provider":"deepseek_web","profile":str(Path(td)/"saved")}],
                          "routing":{}, "settings":{}}
            pp = Pool(cfg_local, autostart=False)
            assert pp.get_by_id("saved") is not None and pp.get_by_id("saved").worker is None
            pp.stop()
        finally:
            if old_accounts_dir is not None:
                _state().ACCOUNTS_DIR = old_accounts_dir

    # Scheduler modes are deterministic and resource-aware.
    class _Gov:
        def snapshot(self, pool): return {"recommended": 2}
    p = types.SimpleNamespace(accounts=[], governor=_Gov(), capacity=lambda: 6)
    for provider, aid, mp in (("chatgpt_web", "g1", 2), ("deepseek_web", "d1", 1), ("grok_web", "x1", 3)):
        a = types.SimpleNamespace(id=aid, provider=provider, enabled=True, deleted=False, status="ready",
                                 cooldown_until=0, budget=0.0, max_parallel=mp, worker=object(),
                                 inflight=0)
        a.over_budget=lambda: False
        p.accounts.append(a)
    assert Pool.parallel_capacity(p, None, "serial") == 1
    assert Pool.parallel_capacity(p, None, "light") == 3
    assert Pool.parallel_capacity(p, None, "full") == 6
    assert Pool.parallel_capacity(p, None, "auto") == 2

    # Generated hook settings contain only an absolute localhost URL and no secret query string.
    hs = claude_mirror_settings()
    assert hs.get("hooks")
    for groups in hs["hooks"].values():
        hook = groups[0]["hooks"][0]
        assert hook["url"].startswith("http://127.0.0.1:") and "?" not in hook["url"]
        assert hook["headers"]["Authorization"] == "Bearer $DS_BRIDGE_HOOK_KEY"

    log("Authorization: Bearer super-secret", C.dim, provider="chatgpt_web", account="g1",
        lane="lane-test", project="C:/Project", request_id="req-test", event="test.redaction")
    assert "super-secret" not in _state().LOG_RING[-1][3] and "[REDACTED]" in _state().LOG_RING[-1][3]

    # UI invariants guarding the initialization race and lightweight mobile behavior.
    assert 'var CC_SESSION=window.CC_SESSION={cwd:"",model:"",tool:"",text:"",event:"",status:"idle"}' in DASH_HTML
    assert 'const localStorage=(()=>{try{return window.localStorage}' in DASH_HTML
    assert 'prefers-reduced-motion' in DASH_HTML and 'width:min(82vw,280px)' in DASH_HTML
    assert 'background-image:none!important' in DASH_HTML

    # The dashboard performs authenticated write actions in-browser; make it impossible to embed/clickjack.
    html_src = inspect.getsource(APIHandler._send_html)
    assert 'X-Frame-Options", "DENY"' in html_src
    assert "Content-Security-Policy\", \"frame-ancestors 'none'" in html_src


def _selftest_startup_menu() -> None:
    items = _startup_provider_items({"accounts": []})
    assert len(items) == 6 and items[0][0] == "ChatGPT" and items[1][0] == "DeepSeek" and items[2][0] == "Grok"
    assert _startup_menu_index(0, "down", 6) == 1
    assert _startup_menu_index(5, "down", 6) == 0
    assert _startup_menu_index(0, "up", 6) == 5
    assert _startup_menu_index(0, "enter:2", 6) == 2
    assert _startup_menu_index(0, "enter:99", 6) == 5
    assert {"chatgpt": "chatgpt_web", "deepseek": "deepseek_web", "grok": "grok_web"}["chatgpt"] == "chatgpt_web"
    with tempfile.TemporaryDirectory() as td:
        cfg = {"accounts": [{"id": "g1", "name": "GPT 1", "enabled": True, "kind": "web", "provider": "chatgpt_web"},
                            {"id": "g2", "name": "GPT 2", "enabled": True, "kind": "web", "provider": "chatgpt_web"},
                            {"id": "d1", "name": "DS 1", "enabled": True, "kind": "web", "provider": "deepseek_web"}],
               "routing": {"pinned": "g2"}}
        assert _startup_count_text(cfg, "chatgpt_web") == "2 accounts"
        assert _startup_count_text(cfg, "grok_web") == "not configured"
        class FakePool:
            def __init__(self):
                self.cfg = cfg
                self.accounts = [Account(x) for x in cfg["accounts"]]
                self.routing = cfg["routing"]
            def get_by_id(self, aid): return next((a for a in self.accounts if a.id == aid), None)
            def add_web_account(self, provider, name="", headed=True, start=False):
                a = Account({"id": f"{provider}-new", "name": name, "enabled": True, "kind": "web", "provider": provider})
                self.accounts.append(a); return a
        f = FakePool()
        ids = startup_prepare_accounts(f, {"mode": "multi", "full": False})
        assert ids == ["g2", "d1"], ids
        assert len(f.accounts) == 3, "multi mode must not create surprise provider profiles"
        f2 = FakePool()
        ids2 = startup_prepare_accounts(f2, {"mode": "multi", "full": True})
        assert ids2 == ["g1", "g2", "d1"], ids2
        assert len(f2.accounts) == 3


def self_test() -> None:
    _selftest_master_hardening()
    _selftest_startup_menu()
    # 1. Original failure: malformed <tool_call> JSON + DSML residue.
    malformed = (
        '<tool_call>{"name": "Write", "arguments": {'
        '"file_path": "C:\\Users\\Pc\\Desktop\\claude_test\\hello.py", '
        '"content": "print("hello world")\\n"'
        '}}</｜｜DSML｜｜ parameter>\n</｜｜DSML｜｜ invoke>\n</｜｜DSML｜｜ calls>')
    clean, calls, probs = parse_tool_calls(malformed)
    assert len(calls) == 1 and calls[0]["name"] == "Write", (calls, probs)
    assert calls[0]["arguments"]["file_path"] == r"C:\Users\Pc\Desktop\claude_test\hello.py"
    assert calls[0]["arguments"]["content"] == 'print("hello world")\n'
    assert "DSML" not in clean, clean

    # 1b. V5.10 regressions captured from a real unattended run (garbled DeepSeek markup).
    _wt = {"Write": {"input_schema": {"type": "object", "required": ["file_path", "content"],
                                      "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}}}},
           "Edit": {"input_schema": {"type": "object", "required": ["file_path", "old_string", "new_string"],
                                     "properties": {"file_path": {"type": "string"}, "old_string": {"type": "string"},
                                                    "new_string": {"type": "string"}}}}}
    _pp, _pc = "</｜DSML｜parameter>", "<｜DSML｜parameter name="
    dup = ('<｜DSML｜tool_calls>\n<｜DSML｜invoke name="Write">\n' + _pc + '"file_path" string="true">a.txt' + _pp + "\n"
           + _pc + '"content" string="true">hello\n' + _pp + "\n" + _pp + "\n</｜DSML｜invoke>\n</｜DSML｜tool_calls>")
    _, c1b, p1b = parse_tool_calls(dup, _wt)
    assert not p1b and c1b[0]["arguments"]["content"] == "hello\n", (c1b, p1b)          # doubled close tag
    noinv = ('<｜DSML｜tool_calls>\n<｜DSML｜invoke name="Write">\n' + _pc + '"file_path" string="true">a' + _pp + "\n"
             + _pc + '"content" string="true">A' + _pp + "\n</｜DSML｜invoke>\n"
             + _pc + '"file_path" string="true">b' + _pp + "\n" + _pc + '"content" string="true">B\n' + _pp + "\n" + _pp
             + "\n</｜DSML｜tool_calls>\n</｜DSML｜tool_calls>")
    _, c1c, p1c = parse_tool_calls(noinv, _wt)
    assert not p1c and [(c["name"], c["arguments"]["file_path"], c["arguments"]["content"]) for c in c1c] == \
        [("Write", "a", "A"), ("Write", "b", "B\n")], (c1c, p1c)                           # missing <invoke>
    allmissing = ('<｜DSML｜tool_calls>\n<｜｜DSML｜｜ calls>\n' + _pc + '"file_path" string="true">z' + _pp + "\n"
                  + _pc + '"content" string="true">Z' + _pp + "\n</｜DSML｜tool_calls>")
    _, c1d, p1d = parse_tool_calls(allmissing, _wt)
    assert not p1d and c1d and c1d[0]["name"] == "Write", (c1d, p1d)                     # no invoke at all
    _, c1e, p1e = parse_tool_calls('<｜DSML｜tool_calls>\n' + _pc + '"zzz" string="true">1' + _pp + "\n</｜DSML｜tool_calls>", _wt)
    assert not c1e and p1e, (c1e, p1e)                    # unreadable markup is reported => repair round-trip
    _, c1f, p1f = parse_tool_calls("Use it like this:\n```\n<｜DSML｜tool_calls>\n```\nDone.", _wt)
    assert not c1f and not p1f, p1f                       # examples inside a fence are not errors
    print("  [ok] garbled DSML (double close, missing invoke, unreadable markup)")

    # 2. Native DSML + multi calls (identical calls are NOT merged).
    multi = canonical_dsml_calls([
        {"name": "Write", "arguments": {"file_path": r"C:\tmp\x.py", "content": 'print("hi")\n'}},
        {"name": "Bash", "arguments": {"command": "ls"}},
        {"name": "Bash", "arguments": {"command": "ls"}}])
    _, c3, p3 = parse_tool_calls("Sure.\n" + multi)
    assert [c["name"] for c in c3] == ["Write", "Bash", "Bash"] and not p3, (c3, p3)
    assert c3[0]["arguments"]["content"] == 'print("hi")\n'

    # 3. Closing tag INSIDE a parameter value.
    tricky = ('<｜DSML｜tool_calls>\n<｜DSML｜invoke name="Write">\n'
              '<｜DSML｜parameter name="content" string="true">x = "</｜DSML｜parameter>"; y = 1\n</｜DSML｜parameter>\n'
              '</｜DSML｜invoke>\n</｜DSML｜tool_calls>')
    _, c4, _ = parse_tool_calls(tricky)
    assert c4[0]["arguments"]["content"] == 'x = "</｜DSML｜parameter>"; y = 1\n', c4

    # 4. Fences: an example inside a fence is NOT executed; a fully fenced reply is.
    example = "Here is the format:\n```\n" + canonical_dsml_calls(
        [{"name": "Bash", "arguments": {"command": "rm -rf x"}}]) + "\n```\nDone."
    _, c5, _ = parse_tool_calls(example)
    assert c5 == [], c5
    wrapped = "```xml\n" + canonical_dsml_calls([{"name": "Bash", "arguments": {"command": "ls"}}]) + "\n```"
    _, c6, _ = parse_tool_calls(wrapped)
    assert len(c6) == 1, c6

    # 5. Schema aware coercion + validation.
    tools = {
        "Read": {"name": "Read", "input_schema": {"type": "object", "required": ["file_path"], "properties": {
            "file_path": {"type": "string"}, "offset": {"type": "integer"}, "flag": {"type": "boolean"}}}},
        "Echo": {"name": "Echo", "input_schema": {"type": "object", "required": ["content"],
                                                    "properties": {"content": {"type": "string"}}}},
    }
    src = ('<｜DSML｜tool_calls><｜DSML｜invoke name="read">'
           '<｜DSML｜parameter name="file_path" string="true">/a</｜DSML｜parameter>'
           '<｜DSML｜parameter name="offset">10</｜DSML｜parameter>'
           '<｜DSML｜parameter name="flag" string="false">true</｜DSML｜parameter>'
           '<｜DSML｜parameter name="bogus" string="true">z</｜DSML｜parameter>'
           '</｜DSML｜invoke>'
           '<｜DSML｜invoke name="Echo"><｜DSML｜parameter name="content">123</｜DSML｜parameter></｜DSML｜invoke>'
           '</｜DSML｜tool_calls>')
    _, c7, p7 = parse_tool_calls(src, tools)
    assert not p7, p7
    assert c7[0] == {"name": "Read", "arguments": {"file_path": "/a", "offset": 10, "flag": True}}, c7[0]
    assert c7[1]["arguments"]["content"] == "123" and isinstance(c7[1]["arguments"]["content"], str)
    _, c8, p8 = parse_tool_calls('<｜DSML｜invoke name="Nope"></｜DSML｜invoke>', tools)
    assert not c8 and "unknown tool" in p8[0]
    _, c9, p9 = parse_tool_calls('<｜DSML｜invoke name="Read"></｜DSML｜invoke>', tools)
    assert not c9 and "missing required" in p9[0]

    # 6. Truncated call is reported, not executed.
    cut = '<｜DSML｜invoke name="Echo"><｜DSML｜parameter name="content" string="true">half a fi'
    _, c10, p10 = parse_tool_calls(cut, tools)
    assert not c10 and p10, (c10, p10)

    # 7. Reply sanitising.
    assert sanitize_reply("[ASSISTANT]\nhello [citation:1]\n[USER]\nfake") == "hello "

    # 8. Signatures / continuation matching.
    def um(t): return {"role": "user", "content": t}
    def am(ids, t="ok"):
        return {"role": "assistant", "content": [{"type": "text", "text": t}] +
                [{"type": "tool_use", "id": i, "name": "Bash", "input": {}} for i in ids]}
    def tr(i, t): return {"role": "user", "content": [{"type": "tool_result", "tool_use_id": i, "content": t}]}
    m1 = [um("task <system-reminder>a</system-reminder>")]
    s1 = [msg_signature(m) for m in m1]
    reply_ids = ["toolu_1"]
    m2 = [um("task <system-reminder>CHANGED</system-reminder>"), am(reply_ids, "different text"), tr("toolu_1", "out")]
    s2 = [msg_signature(m) for m in m2]
    assert match_continuation(s1, 1, reply_ids, m2, s2)
    assert not match_continuation(s1, 1, ["toolu_X"], m2, s2)
    m3 = [um("EDITED task"), am(reply_ids), tr("toolu_1", "out")]
    assert not match_continuation(s1, 1, reply_ids, m3, [msg_signature(m) for m in m3])
    assert not match_continuation(s1, 1, reply_ids, m1, s1)   # identical retry => not a continuation
    m4 = [um("task"), am(reply_ids), tr("toolu_1", "[Old tool result content cleared]")]
    assert match_continuation([msg_signature(um("task"))], 1, reply_ids, m4, [msg_signature(m) for m in m4])

    # 9. Compaction: fits the budget, keeps first + last, cuts nothing mid-message.
    hist = [um("THE-TASK " + "t" * 500)]
    for i in range(60):
        hist.append(am([f"toolu_{i}"], "thinking " * 50))
        hist.append(tr(f"toolu_{i}", "R" * 30_000))
    hist.append(um("LAST-QUESTION"))
    for budget in (300_000, 100_000, 30_000, 8_000):
        out = compact_history(hist, budget)
        assert len(out) <= budget * 1.05 + 2000, (budget, len(out))
        assert "THE-TASK" in out and "LAST-QUESTION" in out, budget
    small = compact_history(hist[:3], 500_000)
    assert small == render_messages(hist[:3])

    # 10. Streaming filter never leaks DSML.
    got: List[str] = []
    st = SafeTextStream(got.append)
    full = "Let me check.\n" + multi
    for i in range(1, len(full) + 1, 7):
        st.update(full[:i])
    st.update(full)
    assert "".join(got) == "Let me check.\n" and "DSML" not in "".join(got)

    # 11. Schema minifier.
    ms = minify_schema({"$schema": "x", "additionalProperties": False, "type": "object",
                        "properties": {"a": {"type": "string", "description": "d" * 5000}}})
    assert "$schema" not in ms and len(ms["properties"]["a"]["description"]) < 1000

    # 12. OpenAI -> Anthropic conversion round trip.
    oa = openai_to_anthropic({"messages": [
        {"role": "system", "content": "S"}, {"role": "user", "content": "hi"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_1", "type": "function", "function": {"name": "Bash", "arguments": '{"command":"ls"}'}}]},
        {"role": "tool", "tool_call_id": "call_1", "content": "out"}],
        "tools": [{"type": "function", "function": {"name": "Bash", "parameters": {"type": "object"}}}]})
    assert oa["system"] == "S" and oa["messages"][1]["content"][0]["type"] == "tool_use"
    assert oa["messages"][2]["content"][0]["type"] == "tool_result" and oa["tools"][0]["name"] == "Bash"

    # 13. Integer schemas reject 1.5 / NaN, numbers accept them; Persian digits still work.
    assert _from_text("1.5", {"integer"}) == (None, False)
    assert _from_text("1.5", {"number"}) == (1.5, True)
    assert _from_text("7", {"integer"}) == (7, True)
    assert _from_text("3.0", {"integer"}) == (3, True)
    assert _from_text("1.5", {"integer", "string"}) == ("1.5", True)
    assert _from_text("NaN", {"number"}) == (None, False)
    assert _from_text("۱۲۳", {"integer"}) == (123, True)

    # 14. Fence rules: 4-backtick outer fence may contain 3-backtick examples;
    #     same-length nesting is ambiguous => NOT whole (an example is never executed).
    inner = canonical_dsml_calls([{"name": "Bash", "arguments": {"command": "ls"}}])
    assert _whole_fenced("```xml\n" + inner + "\n```")
    assert _whole_fenced("````xml\nexample:\n```python\nprint(1)\n```\n" + inner + "\n````")
    assert not _whole_fenced("```xml\nexample:\n```python\nprint(1)\n```\n" + inner + "\n```")
    assert not _whole_fenced("text first\n```\n" + inner + "\n```")
    _, c11, _ = parse_tool_calls("````xml\nexample:\n```python\nprint(1)\n```\n" + inner + "\n````")
    assert len(c11) == 1, c11

    # 15. Streamed text == sanitized final text, at any chunking (no citation / role-header leaks).
    for text in ("Answer [citation:1] is 42 [citation:23]. Done.",
                 "hello\n[USER]\nfake continuation",
                 "[ASSISTANT]\nhi there, arr[0] and [x] stay.",
                 "Plain text with < and > signs, a<b> ok."):
        for step in (1, 2, 3, 7):
            got2: List[str] = []
            s2 = SafeTextStream(got2.append)
            for i in range(step, len(text) + 1, step):
                s2.update(text[:i])
                assert sanitize_reply(text[:i]).startswith("".join(got2)) or not "".join(got2), (text, i, got2)
            s2.update(text)
            assert "".join(got2) == sanitize_reply(text), (text, step, got2)
    assert reconcile_stream("Hello world", "Hello\n") == (" world", False)
    assert reconcile_stream("Hello", "\n\nHello \n") == ("", False)
    assert reconcile_stream("Hello", "") == ("Hello", False)
    assert reconcile_stream("abc", "xyz") == ("", True)

    # 16. Real HTTP server against a fake worker: truncated chunked body, dead worker, clean streaming.
    old_bridge, old_key = _state().BRIDGE, _state().API_KEY

    class _FakeEngine:
        def process(self, req, cancel, on_partial):
            raw = ("Sure [citation:1] thing.\n" +
                   canonical_dsml_calls([{"name": "Bash", "arguments": {"command": "ls"}}]) + "\nafter text")
            for i in range(1, len(raw) + 1, 5):
                if on_partial:
                    on_partial(raw[:i])
            if on_partial:
                on_partial(raw)
            clean, calls, _ = parse_tool_calls(raw)
            for c in calls:
                c["id"] = make_id()
            return Outcome(text=clean, calls=calls, stop_reason="tool_use")

    class _FakeBridge:
        ok = True

        def __init__(self, dead: bool = False):
            self.dead = dead

        def alive(self) -> bool:
            return not self.dead

        def submit(self, fn, priority=0, cancel=None):
            fut: concurrent.futures.Future = concurrent.futures.Future()
            if not self.dead:
                def run():
                    try:
                        fut.set_result(fn(_FakeEngine()))
                    except BaseException as exc:
                        fut.set_exception(exc)
                state_thread(target=run, daemon=True).start()
            return fut

    def http(port: int, payload: bytes, half_close: bool = False, timeout: float = 8.0) -> bytes:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        try:
            s.sendall(payload)
            if half_close:
                s.shutdown(socket.SHUT_WR)
            buf = b""
            while True:
                try:
                    d = s.recv(65536)
                except socket.timeout:
                    break
                if not d:
                    break
                buf += d
            return buf
        finally:
            s.close()

    _state().API_KEY = "testkey"
    server = start_server(0)
    port = server.server_address[1]
    try:
        head = (b"POST /v1/messages HTTP/1.1\r\nHost: x\r\nx-api-key: testkey\r\n"
                b"Content-Type: application/json\r\nConnection: close\r\n")
        # 16a. chunked body cut off mid-chunk => prompt 400, not an endless loop
        t0 = time.time()
        r = http(port, head + b"Transfer-Encoding: chunked\r\n\r\n5\r\nab", half_close=True)
        assert r.startswith(b"HTTP/1.1 400"), r[:80]
        assert time.time() - t0 < 5, "chunked EOF took too long"
        # 16b. negative Content-Length is rejected explicitly
        r = http(port, head + b"Content-Length: -5\r\n\r\n")
        assert r.startswith(b"HTTP/1.1 400"), r[:80]
        # 16c. worker dead => 529 within seconds instead of hanging
        _state().BRIDGE = _FakeBridge(dead=True)
        body = json.dumps({"model": "m", "max_tokens": 50,
                           "messages": [{"role": "user", "content": "hi"}]}).encode()
        t0 = time.time()
        r = http(port, head + b"Content-Length: %d\r\n\r\n" % len(body) + body)
        assert r.startswith(b"HTTP/1.1 529"), r[:80]
        assert time.time() - t0 < 5, "dead worker request hung"
        # 16d. streaming: no citation leak, text reconstructs exactly, tool call delivered
        _state().BRIDGE = _FakeBridge()
        body = json.dumps({"model": "m", "max_tokens": 50, "stream": True,
                           "messages": [{"role": "user", "content": "hi"}]}).encode()
        r = http(port, head + b"Content-Length: %d\r\n\r\n" % len(body) + body, timeout=10).decode("utf-8", "replace")
        payloads = [json.loads(ln[6:]) for blk in r.split("\n\n") for ln in blk.splitlines()
                    if ln.startswith("data: ")]
        text = "".join(p["delta"]["text"] for p in payloads
                       if p.get("type") == "content_block_delta" and p["delta"].get("type") == "text_delta")
        expected = parse_tool_calls("Sure [citation:1] thing.\n" + inner + "\nafter text")[0]
        assert "citation" not in r and "DSML" not in r, r[:400]
        assert text.strip() == expected.strip() and text.startswith("Sure  thing."), (text, expected)
        assert any(p.get("type") == "content_block_start" and p["content_block"].get("type") == "tool_use"
                   for p in payloads), "tool_use block missing"
        assert payloads[-1]["type"] == "message_stop"
        # 16e. a client that goes silent mid-body gets 408 (not a raw 400) once the read timeout hits
        old_to, APIHandler.timeout = APIHandler.timeout, 1
        try:
            t0 = time.time()
            r = http(port, head + b"Content-Length: 100\r\n\r\n{\"a\":", timeout=6)
            assert r.startswith(b"HTTP/1.1 408"), r[:80]
            assert time.time() - t0 < 5
        finally:
            APIHandler.timeout = old_to
    finally:
        stop_server(server)
        _state().BRIDGE, _state().API_KEY = old_bridge, old_key

    # 17. Worker resilience: a job that dies with BaseException still resolves its future.
    bw = Bridge.__new__(Bridge)
    bw._q = queue.PriorityQueue()
    bw._seq = itertools.count()
    bw.ok = True
    bw.engine = type("E", (), {"idle": lambda self: None})()
    fut_bad: concurrent.futures.Future = concurrent.futures.Future()
    fut_after: concurrent.futures.Future = concurrent.futures.Future()

    def _boom(_e):
        raise KeyboardInterrupt()
    bw._q.put((0, next(bw._seq), Job(_boom, fut_bad, None)))
    bw._q.put((0, next(bw._seq), Job(lambda e: "still alive", fut_after, None)))
    bw._q.put((0, next(bw._seq), None))
    import contextlib, io
    with contextlib.redirect_stderr(io.StringIO()):      # the simulated crash prints a traceback
        bw._serve()
    assert isinstance(fut_bad.exception(timeout=1), BridgeError) and fut_after.result(timeout=1) == "still alive"
    fut_q: concurrent.futures.Future = concurrent.futures.Future()
    bw._q.put((0, next(bw._seq), Job(lambda e: 1, fut_q, None)))
    bw._fail_pending()
    assert isinstance(fut_q.exception(timeout=1), BridgeError)

    # 18. Fence consistency: _inside_fence follows the same fence-length rules as _whole_fenced.
    assert _inside_fence("````\nexample\n```py\nx\n```\n", 10**6)          # 3-tick lines do not close a 4-tick fence
    assert not _inside_fence("````\nexample\n```py\nx\n```\n````\n", 10**6)
    assert not _inside_fence("use ```inline``` code\nthen text", 10**6)
    tricky = "intro\n````xml\nexample\n```\n" + inner + "\n````\noutro"
    assert parse_tool_calls(tricky)[1] == [], "an example inside a 4-backtick fence must never run"
    assert len(parse_tool_calls("intro\n" + inner)[1]) == 1

    # 19. Partial valid calls are repaired AND merged (valid ones are never lost).
    rq = normalize_anthropic({"model": "m", "messages": [{"role": "user", "content": "go"}], "tools": [
        {"name": "Bash", "input_schema": {"type": "object", "properties": {"command": {"type": "string"}},
                                          "required": ["command"]}},
        {"name": "Read", "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}},
                                          "required": ["file_path"]}}]})
    bad = ('<｜DSML｜tool_calls><｜DSML｜invoke name="Bash"><｜DSML｜parameter name="command" string="true">ls'
           '</｜DSML｜parameter></｜DSML｜invoke><｜DSML｜invoke name="Read"></｜DSML｜invoke></｜DSML｜tool_calls>')
    fixed = canonical_dsml_calls([{"name": "Read", "arguments": {"file_path": "a.txt"}}])
    asked: List[str] = []

    class _FakeDS:
        def exchange(self, page, prompt, cancel=None, on_partial=None):
            asked.append(prompt)
            return Exchange(text=fixed, session_id=None, seconds=0.0)

    eng = Engine.__new__(Engine)
    eng.ds = _FakeDS()
    _, fcalls, _ = eng._finalize(rq, None, bad, None, None)
    assert [c["name"] for c in fcalls] == ["Bash", "Read"], fcalls
    assert "Bash" in asked[0] and "Do NOT repeat" in asked[0], asked[0]
    both = canonical_dsml_calls([{"name": "Bash", "arguments": {"command": "ls"}},
                                 {"name": "Read", "arguments": {"file_path": "a.txt"}}])
    assert [c["name"] for c in merge_repaired([{"name": "Bash", "arguments": {"command": "ls"}}],
                                              parse_tool_calls(both)[1])] == ["Bash", "Read"]

    # 20. Follow-up prompts cap a single giant block; submit() cannot strand a job.
    big = [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "a" * 500_000}]}]
    old_dbl = _state().DELTA_BLOCK_LIMIT
    try:
        _state().DELTA_BLOCK_LIMIT = 150_000                 # independent of the user's environment
        assert len(build_delta_prompt(rq, big, False)) < 150_000 + 5_000
        _state().DELTA_BLOCK_LIMIT = 0                       # 0 = "no cap" must really mean no cap
        assert len(build_delta_prompt(rq, big, False)) > 400_000
    finally:
        _state().DELTA_BLOCK_LIMIT = old_dbl
    bq = Bridge.__new__(Bridge)

    class _DyingQueue(queue.PriorityQueue):
        def put(self, item, *a, **k):
            super().put(item, *a, **k)
            bq.ok = False                 # the worker dies right after the enqueue

    bq._q, bq._seq, bq.ok = _DyingQueue(), itertools.count(), True
    assert isinstance(bq.submit(lambda e: 1).exception(timeout=1), BridgeError)

    # 21. Launcher: modes, permission-flag detection, settings files, project folder choice.
    import tempfile
    old_cfg_path = _state().CONFIG_PATH
    old_env_mode = os.environ.pop("DS_BRIDGE_MODE", None)
    with tempfile.TemporaryDirectory() as td:
        _state().CONFIG_PATH = Path(td) / "cfg.json"
        try:
            # mode resolution: --mode > env > saved > default; junk is ignored, aliases work
            assert resolve_mode(None, {}) == ("safe", "default")
            assert resolve_mode(None, {"permission_mode": "auto"}) == ("auto", "saved setting")
            assert resolve_mode("ask", {"permission_mode": "auto"}) == ("ask", "--mode")
            assert resolve_mode("autonomous", {}) == ("auto", "--mode")
            assert resolve_mode(None, {"permission_mode": "bogus"})[0] == "safe"
            os.environ["DS_BRIDGE_MODE"] = "ask"
            assert resolve_mode(None, {"permission_mode": "auto"}) == ("ask", "DS_BRIDGE_MODE")
            assert resolve_mode("auto", {}) == ("auto", "--mode")
            os.environ.pop("DS_BRIDGE_MODE")
            # safe: settings file with acceptEdits, NO blanket Write/Edit/Read allow, sudo denied
            a_safe = permission_args("safe", ["--continue"])
            assert a_safe[0] == "--settings"
            cfg_safe = json.loads(Path(a_safe[1]).read_text())["permissions"]
            assert cfg_safe["defaultMode"] == "acceptEdits"
            assert not {"Write", "Edit", "Read", "Bash"} & set(cfg_safe["allow"]), cfg_safe["allow"]
            assert "Bash(git commit:*)" in cfg_safe["allow"] and "Bash(sudo:*)" in cfg_safe["deny"]
            assert not set(cfg_safe["allow"]) & set(cfg_safe["deny"])
            # Claude Code rejects a rule that mixes '*' with the ':*' suffix.
            assert not [r for r in cfg_safe["allow"] + cfg_safe["deny"] if "*" in r and ":*" in r and r.count("*") > 1]
            assert not [r for r in cfg_safe["allow"] + cfg_safe["deny"] if "|" in r]
            assert len(set(cfg_safe["allow"])) == len(cfg_safe["allow"])
            assert permission_args("safe", ["--settings", "mine.json"]) == []      # user's file wins, untouched
            assert "your own --settings" in permission_mode_text("safe", "x", ["--settings", "mine.json"])
            assert "unrestricted" in permission_mode_text("safe", "default", [])
            assert "Bash(git init)" in cfg_safe["allow"] and "Bash(git init:*)" not in cfg_safe["allow"]
            assert not {"Bash(env:*)", "Bash(cat:*)", "Bash(cp:*)", "Bash(mv:*)", "Bash(grep:*)"} & set(cfg_safe["allow"])
            assert "Bash(env:*)" in cfg_safe["deny"] and "Bash(git log*--output*)" in cfg_safe["deny"]
            assert _mode_arg("Autonomous") == "auto" and _mode_arg("folder") == "safe"
            try:
                _mode_arg("bogus")
                raise AssertionError("bogus mode accepted")
            except argparse.ArgumentTypeError:
                pass
            # ask: mirror hooks are added through a generated settings file; URL must be concrete
            # because Claude Code validates HTTP hook URLs before starting the session.
            ask_args = permission_args("ask", [])
            assert ask_args[:1] == ["--settings"] and Path(ask_args[1]).is_file()
            ask_cfg = json.loads(Path(ask_args[1]).read_text())
            assert "hooks" in ask_cfg
            assert set(ask_cfg["hooks"]) == set(_CLAUDE_MIRROR_EVENTS)
            hook = ask_cfg["hooks"]["UserPromptSubmit"][0]["hooks"][0]
            assert re.match(r"^http://127\.0\.0\.1:\d+/dash/api/claude-hook$", hook["url"])
            assert hook["headers"]["Authorization"] == "Bearer $DS_BRIDGE_HOOK_KEY"
            assert hook["allowedEnvVars"] == ["DS_BRIDGE_HOOK_KEY"]
            assert "MessageDisplay" not in ask_cfg["hooks"] and "PostModelSwitch" not in ask_cfg["hooks"]
            # auto: skip-permissions (+ warning pre-accepted) or, as root, a tool allow-list
            a_auto = permission_args("auto", [])
            if running_as_root():
                assert a_auto[0].startswith("--allowedTools=") and "Bash" in a_auto[0], a_auto
            else:
                assert a_auto[0] == "--dangerously-skip-permissions" and a_auto[1] == "--settings"
                assert json.loads(Path(a_auto[2]).read_text())["skipDangerousModePermissionPrompt"] is True
                assert "--settings" not in permission_args("auto", ["--settings", "mine.json"])
            # the user's own permission flag always wins, in every mode
            for m in MODES:
                for own in (["--permission-mode", "plan"], ["--permission-mode=plan"],
                            ["--dangerously-skip-permissions"], ["--allowedTools", "Bash"]):
                    assert permission_args(m, own) == [], (m, own)
            assert claude_env({"api_key": "k"}, "http://x")["ANTHROPIC_API_KEY"] == "k"
            assert "your own" in permission_mode_text("safe", "x", ["--permission-mode", "plan"])
            # project folder
            cfg_t: Dict[str, Any] = {}
            assert pick_project_dir(cfg_t, None, False, here=True) == SCRIPT_DIR
            assert pick_project_dir(cfg_t, td, False) == Path(td).resolve()
            assert pick_project_dir(cfg_t, "/definitely/not/here", False, here=True) == SCRIPT_DIR
            if not (sys.stdin and sys.stdin.isatty()):
                assert _ask_project_dir(cfg_t) == SCRIPT_DIR and cfg_t["project_dir"] == str(SCRIPT_DIR)

            # Active project context must be shared by the launcher, dashboard and swarm.
            project_cfg = {"project_dir": str(SCRIPT_DIR), "recent_projects": [str(SCRIPT_DIR), str(Path(td))]}
            remembered = remember_project(project_cfg, td, persist=False)
            assert remembered == Path(td).resolve()
            assert project_cfg["project_dir"] == str(Path(td).resolve())
            assert project_cfg["recent_projects"][0] == str(Path(td).resolve())
            assert project_cfg["recent_projects"].count(str(Path(td).resolve())) == 1

            class _ProjectPool:
                def __init__(self, cfg):
                    self.cfg = cfg
                    self.events = []
                def snapshot(self):
                    return {}
                def event(self, level, msg):
                    self.events.append((level, msg))

            pp = _ProjectPool({"project_dir": str(SCRIPT_DIR), "recent_projects": []})
            rctx = set_project_context(pp, td)
            assert rctx["project"] == str(Path(td).resolve())
            assert pp.cfg["project_dir"] == str(Path(td).resolve())
            assert pp.events and str(Path(td).resolve()) in pp.events[-1][1]

            # Regression guard for the dashboard's Team Agent project selector:
            # the live bridge project must beat stale localStorage from an older launch.
            assert 'const project=I.project||LS.project||""' in DASH_HTML
            assert 'window.CC_SESSION={cwd:"",model:"",tool:"",text:"",event:"",status:"idle"}' in DASH_HTML
            assert 'async function enterSwarm(){try{await loadInfo(true);S=await api("state")}' in DASH_HTML
        finally:
            _state().CONFIG_PATH = old_cfg_path
            if old_env_mode is not None:
                os.environ["DS_BRIDGE_MODE"] = old_env_mode

    _selftest_multiauth()
    _selftest_v63_new_features()
    _selftest_multi()
    _selftest_v61()
    _selftest_api()
    _selftest_swarm()
    print(C.green("[self-test] all tests passed."))



def _selftest_multi() -> None:
    """V6: classification, stats, routing, cooldown, fail-over, /ds commands, dashboard API (no browser)."""
    import http.client
    import tempfile
    import types

    # ---- classification
    assert classify_error("DeepSeek: HTTP 401: x") == "login"
    assert classify_error('hint: {"content":"Messages too frequently"}') == "rate_limit"
    assert classify_error("HTTP 503: upstream") == "rate_limit"
    assert classify_error("hint: context_length_exceeded") == "chat_full"
    assert classify_error("stream error: boom") == "upstream"
    assert site_notice_kind("The server is busy. Please try again later.") == "rate_limit"
    assert site_notice_kind("服务器繁忙，请稍后再试。") == "rate_limit"
    assert site_notice_kind("Sure, I will try again later.") is None
    assert site_notice_kind("word " * 100 + " server is busy") is None
    assert site_notice_kind("This conversation has reached its length limit.") == "chat_full"
    assert fmt_tok(1234) == "1.2k" and fmt_dur(3725) == "1h 02m"

    # ---- /ds command extraction (only the LAST plain user message counts)
    def rq(messages):
        return normalize_anthropic({"model": "m", "messages": messages})
    assert extract_bridge_command(rq([{"role": "user", "content": "DS-BRIDGE-CMD use 2"}])) == "use 2"
    assert extract_bridge_command(rq([{"role": "user", "content": [
        {"type": "text", "text": "<command-name>/ds</command-name>"},
        {"type": "text", "text": "<system-reminder>x</system-reminder>DS-BRIDGE-CMD next\nmore"}]}])) == "next"
    assert extract_bridge_command(rq([{"role": "user", "content": "DS-BRIDGE-CMD next"},
                                      {"role": "assistant", "content": "done"},
                                      {"role": "user", "content": "thanks"}])) is None
    assert extract_bridge_command(rq([{"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t", "content": "DS-BRIDGE-CMD next"}]}])) is None

    # ---- stats
    st = AcctStats()
    st.record_exchange(40_000, 4_000, 2.0)
    st.record_exchange(8_000, 400, 1.0)
    sn = st.snapshot(time.time())
    assert sn["in_tok"] == 12_000 and sn["out_tok"] == 1_100 and sn["req"] == 2 and sn["streak_live"]
    assert sn["today_in"] == 12_000 and sum(sn["spark"]) == 13_100 and len(sn["spark"]) == 60
    st2 = AcctStats()
    st2.load(st.to_json())
    assert st2.in_tok == 12_000 and st2.req == 2

    # ---- engine: owns() + quick hand-over when another account exists + chat_full recovery
    um = lambda t: {"role": "user", "content": t}
    am = lambda ids: {"role": "assistant", "content": [{"type": "text", "text": "ok"}] +
                      [{"type": "tool_use", "id": i, "name": "Bash", "input": {}} for i in ids]}
    tr = lambda i: {"role": "user", "content": [{"type": "tool_result", "tool_use_id": i, "content": "o"}]}

    class _FDS:
        epoch = 0
        headless = True
        scratch = None

        def __init__(self, script):
            self.script = list(script)

        def new_page(self): return types.SimpleNamespace(is_closed=lambda: False)
        def open_chat(self, p): pass
        def close_page(self, p): pass
        def session_of(self, p): return None

        def exchange(self, page, prompt, cancel=None, on_partial=None, files=None):
            r = self.script.pop(0)
            if isinstance(r, Exception):
                raise r
            return Exchange(text=r, session_id=None, seconds=0.0)

    acc_t = Account({"id": "t", "name": "T"})
    pool_t = types.SimpleNamespace(has_alternative=lambda a: True)
    e1 = Engine(_FDS([BridgeError("busy", "rate_limit")]), acc_t, pool_t)
    r1 = rq([um("hi")])
    t0 = time.time()
    try:
        e1.process(r1, None, None)
        raise AssertionError("expected BridgeError")
    except BridgeError as exc:
        assert exc.kind == "rate_limit" and time.time() - t0 < 2      # no 6x backoff: handed to the pool
    assert acc_t.stats.err == 1 and acc_t.stats.rate_limits == 1
    e2 = Engine(_FDS([BridgeError("full", "chat_full"), "hello"]), acc_t, types.SimpleNamespace(has_alternative=lambda a: False))
    t0 = time.time()
    assert e2.process(r1, None, None).text == "hello" and time.time() - t0 < 2   # new chat, same account
    assert acc_t.stats.ok == 1
    m1 = [um("task")]
    e3 = Engine(_FDS(["r1"]), None, None)
    out = e3.process(normalize_anthropic({"model": "m", "messages": m1}), None, None)
    m2 = m1 + [{"role": "assistant", "content": "r1"}, um("next question")]
    assert e3.owns(normalize_anthropic({"model": "m", "messages": m2})) == 1
    assert e3.owns(normalize_anthropic({"model": "m", "messages": [um("other")]})) == -1
    e3.ds.epoch = 5
    assert e3.owns(normalize_anthropic({"model": "m", "messages": m2})) == -1   # browser restarted => chats gone

    # ---- generic web regression: ChatGPT/Grok reuse ONE existing browser tab/chat even
    # when Claude Code rewrites metadata enough to defeat the strict continuation matcher.
    class _GenericPage:
        def __init__(self): self.closed = False
        def is_closed(self): return self.closed
        def evaluate(self, js, *args):
            if js == JS_GENERIC_NEW_CHAT:
                return True
            return None

    class _GenericDS(_FDS):
        def __init__(self):
            self.provider = "chatgpt_web"
            self.recipe = {"name": "ChatGPT", "url": "https://chatgpt.com/", "supports_think": True}
            self.epoch = 0
            self.headless = True
            self.page = _GenericPage()
            self.scratch = self.page
            self.pages = [self.page]
            self.new_pages = 0
            self.opens = 0
            self.prompts = []
            self.script = ["first answer", "second answer", "agent one", "agent two", "side one", "side two"]
        def ensure_alive(self):
            self.scratch = self.page
        def new_page(self):
            self.new_pages += 1
            p = _GenericPage()
            self.pages.append(p)
            return p
        def open_chat(self, p):
            self.opens += 1
        def close_page(self, p):
            p.closed = True
        def session_of(self, page):
            return "https://chatgpt.com/c/test-chat"
        def _provider_name(self):
            return "ChatGPT"
        def exchange(self, page, prompt, cancel=None, on_partial=None, files=None):
            self.prompts.append(prompt)
            return Exchange(text=self.script.pop(0), session_id=self.session_of(page), seconds=0.0)
    gds = _GenericDS()
    ge = Engine(gds, None, None)
    gm1 = [{"role": "user", "content": "first"}]
    gm2 = gm1 + [{"role": "assistant", "content": "first answer"}, {"role": "user", "content": "second topic"}]
    ge.process(rq(gm1), None, None)
    ge.process(rq(gm2), None, None)
    assert gds.new_pages == 0 and gds.opens == 0 and len(gds.prompts) == 2, (gds.new_pages, gds.opens, len(gds.prompts))
    assert gds.prompts[0].startswith("You are the ASSISTANT")
    assert gds.prompts[1].startswith("[NEW ITEMS SINCE YOUR LAST TURN]") and len(gds.prompts[1]) < len(gds.prompts[0])
    assert ge.sticky_conv is not None and ge.sticky_conv.page is gds.scratch and ge.sticky_conv.turns == 2
    assert ge._find_conv(normalize_anthropic({"model": "m", "messages": gm2 + [{"role": "assistant", "content": "unrelated"}, {"role": "user", "content": "third"}]})) is ge.sticky_conv
    assert ge.owns(normalize_anthropic({"model": "m", "messages": [{"role": "user", "content": "rewritten metadata"}]})) == len(gm2)

    # Explicit reset keeps the browser tab alive and requests a new web conversation.
    assert ge.reset_all() == 1 and ge.sticky_conv is not None and gds.new_pages == 0 and ge.sticky_conv.n == 0

    # Different logical lanes (for example Swarm agents) get their own persistent chat tab,
    # but repeated requests within the same lane reuse that tab instead of creating a chat.
    ra1 = normalize_anthropic({"model": "m", "messages": [{"role": "user", "content": "agent task"}]})
    ra1.tag = "sw1.a1"
    ra2 = normalize_anthropic({"model": "m", "messages": [{"role": "user", "content": "agent task"},
                                                   {"role": "assistant", "content": "agent one"},
                                                   {"role": "user", "content": "agent next"}]})
    ra2.tag = "sw1.a1"
    before_pages = gds.new_pages
    ge.process(ra1, None, None); ge.process(ra2, None, None)
    assert gds.new_pages == before_pages + 1
    agent_page = ge.generic_lanes["tag:sw1.a1"].page
    assert agent_page is not ge.sticky_conv.page

    # Generic side work must not navigate the main ChatGPT tab; one dedicated side tab is reused.
    rs = normalize_anthropic({"model": "haiku", "messages": [{"role": "user", "content": "side"}]})
    before_pages = gds.new_pages
    ge.process(rs, None, None); ge.process(rs, None, None)
    assert gds.new_pages == before_pages + 1 and ge.generic_side_page is not ge.sticky_conv.page

    # ---- pool: routing with fake workers
    class _FE:
        def __init__(self, behave, own=-1):
            self.behave, self.own, self.convs = behave, own, []

        def owns(self, req): return self.own
        def process(self, req, cancel, on_partial): return self.behave()
        def reset_all(self): return 0
        def ping(self): return {"seconds": 0.1, "reply": "OK"}

    class _FW:
        def __init__(self, behave, own=-1):
            self.ok, self.stopping = True, False
            self._thread = threading.current_thread()
            self.engine = _FE(behave, own)

        def submit(self, fn, priority=0, cancel=None):
            fut: concurrent.futures.Future = concurrent.futures.Future()
            try:
                fut.set_result(fn(self.engine))
            except BaseException as exc:
                fut.set_exception(exc)
            return fut

        def stop(self): pass

    old_cfg, old_wait = _state().CONFIG_PATH, _state().ACCOUNT_WAIT_SECONDS
    _state().ACCOUNT_WAIT_SECONDS = 0
    with tempfile.TemporaryDirectory() as td:
        _state().CONFIG_PATH = Path(td) / "cfg.json"
        cfg = {"port": 0, "api_key": "k", "accounts": [{"id": i, "name": n, "enabled": True, "logged_in": True,
                                                        "profile": str(Path(td) / i)} for i, n in (("a", "A"), ("b", "B"), ("c", "C"))]}
        pool = Pool(cfg, autostart=False)
        ok_out = lambda who: (lambda: Outcome(text="from " + who, calls=[]))
        for a in pool.accounts:
            a.worker = _FW(ok_out(a.name))
            a.set_status("ready")
        A, B, Cc = pool.accounts
        R = types.SimpleNamespace(side=False)

        pool.routing.update(strategy="failover")
        assert pool.pick(R)[0] is A
        A.cooldown_until = time.time() + 60
        assert pool.pick(R)[0] is B and not A.usable()
        A.cooldown_until = 0
        pool.routing.update(strategy="balanced")
        A.stats.record_exchange(400_000, 0, 1)
        B.stats.record_exchange(100_000, 0, 1)
        assert pool.pick(R)[0] is Cc                                   # least used
        Cc.inflight = 1
        assert pool.pick(R)[0] is B                                    # busy account is avoided
        Cc.inflight = 0
        B.worker.engine.own = 4
        assert pool.pick(R) == (B, "continuation")                     # a running chat stays put ...
        pool.routing.update(rotate_requests=2)
        B.stint_reqs = 2
        a2, why = pool.pick(R)
        assert why == "rotation" and a2 is not B                       # ... until it is rotated
        B.stint_reqs, B.worker.engine.own = 0, -1
        pool.routing.update(strategy="round_robin", rotate_requests=0)
        seq = [pool.pick(R)[0].id for _ in range(4)]
        assert seq == ["a", "b", "c", "a"], seq
        pool.routing.update(strategy="pinned", pinned="c", auto_failover=False)
        assert pool.pick(R)[0] is Cc
        Cc.cooldown_until = time.time() + 60
        assert pool.pick(R)[0] is None
        pool.routing.update(auto_failover=True)
        assert pool.pick(R)[0] is A                                    # pinned account resting => fail-over
        Cc.cooldown_until = 0
        for x in (B, Cc):
            x.enabled = False
        A.cooldown_until = time.time() + 99
        assert pool.pick(R) == (A, "only account")                     # a lone account is never locked out
        for x in (B, Cc):
            x.enabled = True
        A.cooldown_until = 0
        pool.routing.update(strategy="failover")

        # fail-over: A is busy => same request is served by B, A rests
        def boom():
            raise BridgeError("The server is busy", "rate_limit")
        A.worker.engine.behave = boom
        res = pool.dispatch(R, None, None, lambda: False).result(timeout=5)
        assert res.text == "from B" and A.cooldown_until > time.time() and A.rl_streak == 1
        assert any("moved from 'A' to 'B'" in e["msg"] for e in pool.events), list(pool.events)
        # once text reached the client there is no silent switch
        A.cooldown_until = 0
        try:
            pool.dispatch(R, None, None, lambda: True).result(timeout=5)
            raise AssertionError("must not fail over after streaming started")
        except BridgeError as exc:
            assert exc.kind == "rate_limit"
        # everybody failing => error, not a hang
        for x in pool.accounts:
            x.cooldown_until = 0
            x.worker.engine.behave = boom
        try:
            pool.dispatch(R, None, None, lambda: False).result(timeout=10)
            raise AssertionError("expected failure")
        except BridgeError:
            pass
        # expired login => account leaves the rotation until Login is clicked
        for x in pool.accounts:
            x.cooldown_until = 0
            x.worker.engine.behave = ok_out(x.name)
        A.worker.engine.behave = lambda: (_ for _ in ()).throw(BridgeError("login expired", "login"))
        assert pool.dispatch(R, None, None, lambda: False).result(timeout=5).text == "from B"
        assert A.status == "login_needed" and not A.usable()
        A.set_status("ready")

        # commands
        assert "A" in pool.run_command("status") and "strategy" in pool.run_command("")
        assert "Switched to 'B'" in pool.run_command("use 2") and pool.routing["pinned"] == "b"
        assert pool.run_command("next").startswith("Switched to 'C'")
        assert pool.run_command("prev").startswith("Switched to 'B'")
        assert pool.run_command("use nosuch").startswith("Unknown account")
        assert pool.run_command("auto").startswith("Load balancing") and pool.routing["strategy"] == "balanced"
        assert "Unknown command" in pool.run_command("zzz")
        snap = pool.snapshot()
        assert len(snap["accounts"]) == 3 and snap["accounts"][0]["state"] in ("ready", "cooldown") and snap["events"]

        # persistence
        saved = json.loads(_state().CONFIG_PATH.read_text())
        assert [d["id"] for d in saved["accounts"]] == ["a", "b", "c"] and saved["routing"]["strategy"] == "balanced"
        pool.save_usage()
        pool2 = Pool(json.loads(_state().CONFIG_PATH.read_text()), autostart=False)
        assert pool2.get("a").stats.in_tok == 100_000 and pool2.get("2").id == "b"
        na = pool.add_account("Work #2!", start=False)
        assert na.id.startswith("work-2") and len(pool.accounts) == 4
        pool.move(na, -1)
        assert pool.accounts[2] is na
        deleted_profile = na.profile
        deleted_id = na.id
        pool.remove_account(na, purge=False)
        assert len(pool.accounts) == 3 and pool.get("Work") is None
        assert not deleted_profile.exists()
        saved_after_delete = json.loads(_state().CONFIG_PATH.read_text())
        assert all(d["id"] != deleted_id for d in saved_after_delete["accounts"])
        try:
            pool.restore_account(na, start=False)
            raise AssertionError("deleted accounts must not be restorable")
        except ValueError as exc:
            assert "permanent" in str(exc).lower()

        # ---- permanent deletion cleans config, usage, routing, project mappings, and profile
        extra = pool.add_account("Delete Me", start=False)
        extra_profile = extra.profile
        extra_profile.mkdir(parents=True, exist_ok=True)
        usage_path = pool._usage_path()
        usage_path.write_text(json.dumps({"version": 1, "accounts": {extra.id: {"req": 7}, "a": {"req": 2}}}), encoding="utf-8")
        project_mapping = str(Path(usage_path).parent / "project-test")
        pool.set_project_accounts(project_mapping, [extra.id, "a"])
        pool.routing["pinned"] = extra.id
        pool.current = extra.id
        pool._last_route = extra.id
        pool.remove_account(extra)
        assert pool.get_by_id(extra.id) is None
        assert extra.id not in pool.routing.get("pinned", "")
        assert pool.current != extra.id and pool._last_route is None
        assert extra.id not in sum(pool.project_accounts.values(), [])
        assert not extra_profile.exists()
        saved = json.loads(_state().CONFIG_PATH.read_text())
        assert extra.id not in {d["id"] for d in saved.get("accounts", [])}
        usage = json.loads(usage_path.read_text(encoding="utf-8"))
        assert extra.id not in usage.get("accounts", {}) and usage.get("accounts", {}).get("a", {}).get("req") == 2

        # ---- dashboard over real HTTP (auth, host / origin guard, actions, /ds interception)
        old_b, old_k = _state().BRIDGE, _state().API_KEY
        _state().BRIDGE, _state().API_KEY = pool, "k"
        server = start_server(0)
        port = server.server_address[1]

        def call(method, path, body=None, headers=None):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            h = {"Authorization": "Bearer k", "Content-Type": "application/json"}
            h.update(headers or {})
            c.request(method, path, body=json.dumps(body) if body is not None else None, headers=h)
            r = c.getresponse()
            data = r.read()
            c.close()
            return r.status, data
        try:
            s, d = call("GET", "/dash", headers={"Authorization": ""})
            assert s == 200 and b"DeepSeek Bridge" in d and b"/dash/api/" in d and b'api("state")' in d
            assert call("GET", "/dash/api/state", headers={"Authorization": "Bearer nope"})[0] == 401
            s, d = call("GET", "/dash/api/state")
            assert s == 200 and len(json.loads(d)["accounts"]) == 3
            assert call("GET", "/dash/api/state", headers={"Host": "evil.example"})[0] == 403
            assert call("POST", "/dash/api/use", {"id": "c"}, {"Origin": "http://evil.example"})[0] == 403
            assert call("POST", "/dash/api/use", {"id": "c"})[0] == 200 and pool.routing["pinned"] == "c"
            assert call("POST", "/dash/api/use", {"id": "zzz"})[0] == 400
            assert call("POST", "/dash/api/settings", {"strategy": "failover", "rotate_requests": 7,
                                                        "auto_failover": False})[0] == 200
            assert pool.routing["strategy"] == "failover" and pool.routing["rotate_requests"] == 7
            assert call("POST", "/dash/api/rename", {"id": "a", "name": "Main"})[0] == 200 and pool.get("a").name == "Main"
            s, d = call("POST", "/dash/api/test", {"id": "b"})
            assert json.loads(d)["ok"] is True
            assert call("POST", "/dash/api/bogus", {})[0] == 400
            s, d = call("POST", "/v1/messages", {"model": "m", "max_tokens": 50, "messages": [
                {"role": "user", "content": "<command-message>ds</command-message>\nDS-BRIDGE-CMD use 1"}]})
            assert s == 200 and b"Switched to" in d and pool.routing["pinned"] == "a"
            s, d = call("POST", "/v1/messages", {"model": "m", "max_tokens": 50, "stream": True, "messages": [
                {"role": "user", "content": "DS-BRIDGE-CMD status"}]})
            assert s == 200 and b"message_stop" in d and b"strategy" in d
            pool.routing.update(strategy="failover")
            s, d = call("POST", "/v1/messages", {"model": "m", "max_tokens": 50, "messages": [
                {"role": "user", "content": "hello"}]})
            assert s == 200 and b"from " in d                          # a normal chat is routed through the pool
        finally:
            stop_server(server)
            _state().BRIDGE, _state().API_KEY = old_b, old_k
    _state().CONFIG_PATH, _state().ACCOUNT_WAIT_SECONDS = old_cfg, old_wait

    # ---- slash command files are installed once and never overwrite a user's own command
    with tempfile.TemporaryDirectory() as td:
        old_env = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = td
        try:
            install_claude_commands()
            assert "DS-BRIDGE-CMD $ARGUMENTS" in (Path(td) / "commands" / "ds.md").read_text()
            (Path(td) / "commands" / "ds-next.md").write_text("my own command")
            install_claude_commands()
            assert (Path(td) / "commands" / "ds-next.md").read_text() == "my own command"
        finally:
            if old_env is None:
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
            else:
                os.environ["CLAUDE_CONFIG_DIR"] = old_env

    # ---- worker lifecycle with a fake browser: start, login wait, abort, enable / disable, stop
    global DeepSeekWeb
    real_web, seen = DeepSeekWeb, []

    class _FakeWeb:
        def __init__(self, profile_dir=None, name="", headed=False, on_state=None, on_exchange=None, provider="deepseek_web"):
            self.name, self.provider, self.on_state, self.abort, self.epoch = name, provider, on_state, False, 0

        def start(self, known_login=True):
            seen.append((self.name, known_login))
            if not known_login:
                self.on_state("login")
                end = time.time() + 1.0
                while time.time() < end and not self.abort:
                    time.sleep(0.05)
                return not self.abort
            return True

        def stop(self): pass
    DeepSeekWeb = _FakeWeb                                   # type: ignore[misc,assignment]
    with tempfile.TemporaryDirectory() as td:
        old_cfg = _state().CONFIG_PATH
        _state().CONFIG_PATH = Path(td) / "c.json"
        try:
            lp = Pool({"port": 0, "api_key": "k", "accounts": [
                {"id": "a", "name": "A", "logged_in": True, "profile": td + "/a"},
                {"id": "b", "name": "B", "logged_in": False, "profile": td + "/b"}]}, autostart=False)
            lp.start_all()
            time.sleep(0.3)
            la, lb = lp.accounts
            assert la.status == "ready" and lb.status == "login" and lp.wait_any_ready(5)
            # Regression: the real browser maps LOGIN_REQUIRED -> login_needed;
            # startup must continue waiting instead of closing the login window.
            la.set_status("login_needed")
            lb.set_status("login_needed")
            def _finish_interactive_login():
                time.sleep(0.25)
                la.set_status("ready")
            state_thread(target=_finish_interactive_login, daemon=True).start()
            assert lp.wait_selected_ready([la.id], 1.5) is True
            lb.set_status("login")
            time.sleep(1.2)
            assert lb.status == "ready" and lb.logged_in                      # login detected, saved
            lp.login(la)
            time.sleep(0.4)
            assert la.status == "login" and ("A", False) in seen
            lp.restart_account(la)                                            # aborts the login wait
            time.sleep(0.8)
            assert la.status == "ready"
            lp.set_enabled(lb, False)
            time.sleep(0.5)
            assert lb.status == "disabled" and not lb.usable()
            lp.set_enabled(lb, True)
            time.sleep(0.5)
            assert lb.status == "ready"
            lp.stop()
        finally:
            _state().CONFIG_PATH = old_cfg
            DeepSeekWeb = real_web                           # type: ignore[misc,assignment]
    print("  [ok] multi-account: routing, cooldown, fail-over, /ds commands, dashboard API")


def _selftest_v61() -> None:
    """V6.1: files / images, per-account endpoints, settings, launcher, folder browser, console log, panel API."""
    import http.client
    import types
    PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 40
    b64 = lambda raw: base64.b64encode(raw).decode()
    img = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64(PNG)}}
    pdf = {"type": "document", "title": "../r e p.pdf", "source": {"type": "base64", "media_type": "application/pdf", "data": b64(b"%PDF-1.4 hi")}}

    # ---- extraction + temp files (names are sanitised, nested tool_result images found, limit honoured)
    msgs = [{"role": "user", "content": [{"type": "text", "text": "a"}, img]},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t", "content": [img]}, pdf]}]
    found = extract_attachments(msgs, 0)
    assert [f[0] for f in found] == ["image", "image", "document"] and len(extract_attachments(msgs, 2)) == 2
    assert len(extract_attachments(msgs, 0, 2)) == 2
    d = tempfile.mkdtemp()
    paths = write_attachments(found, d)
    assert [os.path.basename(p) for p in paths] == ["image-1.png", "image-2.png", "r e p.pdf"], paths
    assert open(paths[0], "rb").read() == PNG
    cleanup_dir(d)
    assert not os.path.exists(d)
    assert write_attachments([("image", "", "image/png", "!!notbase64!!")], tempfile.mkdtemp()) == []

    # ---- OpenAI-style parts become the same blocks
    oa = openai_to_anthropic({"model": "m", "messages": [{"role": "user", "content": [
        {"type": "text", "text": "look"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64(PNG)}},
        {"type": "file", "file": {"filename": "a.pdf", "file_data": "data:application/pdf;base64," + b64(b"%PDF")}}]}]})
    kinds = [b["type"] for b in oa["messages"][0]["content"]]
    assert kinds == ["text", "image", "document"], kinds

    # ---- engine uploads exactly the files of THIS turn and never pastes base64 into the prompt
    class _CapDS:
        epoch, headless, scratch = 0, True, None

        def __init__(self): self.calls = []
        def new_page(self): return types.SimpleNamespace(is_closed=lambda: False)
        def open_chat(self, p): pass
        def close_page(self, p): pass
        def session_of(self, p): return None

        def exchange(self, page, prompt, cancel=None, on_partial=None, files=None):
            self.calls.append((prompt, list(files or []), [open(f, "rb").read() for f in (files or [])]))
            return Exchange(text="ok", session_id=None, seconds=0.0)
    cds = _CapDS()
    eng = Engine(cds, None, None)
    m1 = [{"role": "user", "content": [{"type": "text", "text": "what is this?"}, img]}]
    eng.process(normalize_anthropic({"model": "m", "messages": m1}), None, None)
    p1, f1, raw1 = cds.calls[0]
    assert len(f1) == 1 and raw1[0] == PNG and "[image attached]" in p1 and b64(PNG) not in p1
    assert not os.path.exists(f1[0]), "temp upload files must be removed"
    m2 = m1 + [{"role": "assistant", "content": "a picture"}, {"role": "user", "content": [{"type": "text", "text": "and this"}, pdf]}]
    eng.process(normalize_anthropic({"model": "m", "messages": m2}), None, None)
    p2, f2, raw2 = cds.calls[1]
    assert [os.path.basename(x) for x in f2] == ["r e p.pdf"] and raw2[0] == b"%PDF-1.4 hi" and "[file attached: ../r e p.pdf]" in p2, (f2, p2[-200:])

    # ---- _attach waits for the upload, fails loudly, times out
    class _FP:
        def __init__(self, states):
            self.states, self.set = list(states), None

        def evaluate(self, js, *a):
            if js == JS_UP_STATE:
                return self.states.pop(0) if len(self.states) > 1 else self.states[0]
            return None

        def locator(self, sel):
            return types.SimpleNamespace(count=lambda: 1, first=types.SimpleNamespace(
                set_input_files=lambda files, timeout=0: setattr(self, "set", files)))
    web = DeepSeekWeb(Path(tempfile.mkdtemp()), "t")
    fp = _FP([{"n": 0, "open": 0, "seen": False}, {"n": 0, "open": 1, "seen": True},
              {"n": 1, "open": 0, "seen": True, "parsing": True}, {"n": 1, "open": 0, "seen": True, "parsing": False}])
    t0 = time.time()
    web._attach(fp, ["/x/a.png"], None)
    assert fp.set == ["/x/a.png"] and 2.4 < time.time() - t0 < 12
    try:
        web._attach(_FP([{"n": 0, "open": 0, "seen": True}, {"n": 0, "open": 0, "seen": True, "err": "upload HTTP 500"}]), ["/x/a"], None)
        raise AssertionError("expected an upload error")
    except BridgeError as exc:
        assert "upload HTTP 500" in str(exc)
    old_to, _state().UPLOAD_TIMEOUT = _state().UPLOAD_TIMEOUT, 1
    try:
        web._attach(_FP([{"n": 0, "open": 0, "seen": True}, {"n": 0, "open": 1, "seen": True}]), ["/x/a"], None)
        raise AssertionError("expected a timeout")
    except BridgeError as exc:
        assert exc.kind == "timeout"
    finally:
        _state().UPLOAD_TIMEOUT = old_to

    # ---- panel API, account endpoints, settings, launcher
    class _FE:
        def __init__(self, who): self.who, self.convs = who, []
        def owns(self, req): return -1
        def process(self, req, cancel, on_partial): return Outcome(text="from " + self.who, calls=[])
        def reset_all(self): return 0
        def ping(self): return {"seconds": 0.1, "reply": "OK"}

    class _FW:
        def __init__(self, who):
            self.ok, self.stopping, self._thread, self.engine = True, False, threading.current_thread(), _FE(who)

        def submit(self, fn, priority=0, cancel=None):
            f: concurrent.futures.Future = concurrent.futures.Future()
            f.set_result(fn(self.engine))
            return f

        def stop(self): pass
    old_cfg, old_b, old_k, old_tabs = _state().CONFIG_PATH, _state().BRIDGE, _state().API_KEY, _state().MAX_TABS
    real_which = shutil.which
    with tempfile.TemporaryDirectory() as td:
        _state().CONFIG_PATH = Path(td) / "cfg.json"
        cfg = {"port": 8788, "api_key": "k", "accounts": [{"id": i, "name": i.upper(), "logged_in": True, "profile": td + "/" + i} for i in "ab"]}
        init_settings(cfg)
        pool = Pool(cfg, autostart=False)
        for a in pool.accounts:
            a.set_status("ready")
            a.worker = _FW(a.id.upper())
        pool.routing.update(strategy="failover")
        (Path(td) / "sub").mkdir()
        _state().BRIDGE, _state().API_KEY = pool, "k"
        server = start_server(0)
        port = server.server_address[1]

        def call(method, path, body=None, headers=None):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            h = {"Authorization": "Bearer k", "Content-Type": "application/json"}
            h.update(headers or {})
            c.request(method, path, body=json.dumps(body) if body is not None else None, headers=h)
            r = c.getresponse()
            data = r.read()
            c.close()
            return r.status, data
        chat = {"model": "m", "max_tokens": 50, "messages": [{"role": "user", "content": "hello"}]}
        try:
            assert b"from A" in call("POST", "/v1/messages", chat)[1]                  # normal routing: first account
            assert b"from B" in call("POST", "/a/b/v1/messages", chat)[1]              # account endpoint: exactly B
            assert call("POST", "/a/zzz/v1/messages", chat)[0] == 404
            assert call("GET", "/a/b/v1/models")[0] == 200
            pool.accounts[1].set_status("starting")
            old_wait, _state().ACCOUNT_WAIT_SECONDS = _state().ACCOUNT_WAIT_SECONDS, 0
            try:
                s, d = call("POST", "/a/b/v1/messages", chat)
            finally:
                _state().ACCOUNT_WAIT_SECONDS = old_wait
            assert s >= 500 and b"not ready" in d                                       # never silently another account
            pool.accounts[1].set_status("ready")
            log("[v61-marker] hello console", C.yellow)
            s, d = call("GET", "/dash/api/info")
            info = json.loads(d)
            assert s == 200 and info["base"].endswith(":8788") and info["key"] == "k" and info["accounts"][1]["url"].endswith("/a/b")
            assert len(info["settings"]) >= 20 and info["limits"]["files"] == _state().ATTACH_MAX_FILES
            s, d = call("GET", "/dash/api/logs?since=0")
            lg = json.loads(d)
            assert any("v61-marker" in x["m"] and x["l"] == "warn" for x in lg["lines"]) and lg["last"] >= 1
            assert json.loads(call("GET", f"/dash/api/logs?since={lg['last']}")[1])["lines"] == []
            s, d = call("POST", "/dash/api/fs", {"path": td})
            assert "sub" in json.loads(d)["dirs"]
            assert call("POST", "/dash/api/mkdir", {"path": td, "name": "new"})[0] == 200 and (Path(td) / "new").is_dir()
            assert call("POST", "/dash/api/mkdir", {"path": td, "name": ".."})[0] == 400
            shutil.which = lambda n, *a, **k: "/usr/bin/claude" if n == "claude" else real_which(n, *a, **k)
            s, d = call("POST", "/dash/api/launch", {"project": td, "mode": "ask", "dry": True, "continue": True,
                                                     "extra": "--model sonnet", "prompt": "do it"})
            pv = json.loads(d)
            assert s == 200 and set(pv["preview"]) == {"powershell", "cmd", "bash"} and "ANTHROPIC_BASE_URL" in pv["preview"]["bash"]
            assert "--continue" in pv["preview"]["bash"] and "--model" in pv["preview"]["cmd"] and "AUTONOMOUS_PROMPT.md" in pv["preview"]["powershell"]
            assert not (Path(td) / "AUTONOMOUS_PROMPT.md").exists(), "a dry run must not write files"
            assert call("POST", "/dash/api/launch", {"project": td + "/nope", "dry": True})[0] == 400
            shutil.which = lambda n, *a, **k: None if n == "claude" else real_which(n, *a, **k)
            s, d = call("POST", "/dash/api/launch", {"project": td, "dry": True})
            assert s == 400 and b"not installed" in d
            shutil.which = real_which
            # settings: validated as a whole, applied live, saved, resettable
            assert call("POST", "/dash/api/settings_set", {"values": {"MAX_TABS": 9, "KEEP_GOING": False}})[0] == 200 and _state().MAX_TABS == 9
            assert json.loads(_state().CONFIG_PATH.read_text())["settings"]["MAX_TABS"] == 9
            s, d = call("POST", "/dash/api/settings_set", {"values": {"MAX_TABS": 11, "STALL_TIMEOUT": 1}})
            assert s == 400 and _state().MAX_TABS == 9, "an invalid value must not apply anything"
            assert call("POST", "/dash/api/settings_set", {"values": {"nope": 1}})[0] == 400
            s, d = call("POST", "/dash/api/settings_set", {"values": {"port": 9001, "permission_mode": "auto"}})
            assert json.loads(d)["restart"] == ["port"] and pool.cfg["port"] == 9001 and pool.cfg["permission_mode"] == "auto"
            call("POST", "/dash/api/settings_set", {"reset": ["port", "permission_mode", "MAX_TABS", "KEEP_GOING"]})
            assert _state().MAX_TABS == old_tabs and pool.cfg["port"] == DEFAULT_PORT and "permission_mode" not in pool.cfg
            assert "MAX_TABS" not in json.loads(_state().CONFIG_PATH.read_text())["settings"]
            pool.accounts[0].stats.record_exchange(4000, 400, 1)
            assert call("POST", "/dash/api/reset_usage", {})[0] == 200 and pool.accounts[0].stats.in_tok == 0
            assert call("POST", "/dash/api/bridge", {"action": "stop"})[0] == 400       # inside Claude Code: refused, not killed
            assert call("POST", "/dash/api/task", {"name": "rm -rf"})[0] == 400
            assert pool.run_command("key").startswith("The API key is not shown") and pool.run_command("key", secret=True) == "k"
            assert "usage" in pool.run_command("help") and pool.run_command("usage-reset").startswith("Usage")
            assert pool.run_command("test A").startswith("A: ") and pool.run_command("reset").count("\n") == 1
        finally:
            shutil.which = real_which
            stop_server(server)
            _state().CONFIG_PATH, _state().BRIDGE, _state().API_KEY = old_cfg, old_b, old_k
    print("  [ok] v6.1: files + vision upload, account endpoints, settings, launcher, folder browser, console log")


def _selftest_api() -> None:
    """V6.2: API accounts (OpenAI-compatible + Anthropic), tiers, budget, parallel requests."""
    import types
    from http.server import BaseHTTPRequestHandler as _H, ThreadingHTTPServer as _S
    state: Dict[str, Any] = {"hits": [], "delay": 0.0}

    class Up(_H):
        def log_message(self, *a): pass

        def _json(self, code, obj, headers=None):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            if self.path.endswith("/models"):
                k = self.headers.get("Authorization", "").replace("Bearer ", "") or self.headers.get("x-api-key", "")
                if k != "sk-test":
                    return self._json(401, {"error": {"message": "bad key"}})
                return self._json(200, {"data": [{"id": "m-b"}, {"id": "m-a"}]})
            self._json(404, {})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            state["hits"].append((self.path, {k.lower(): v for k, v in self.headers.items()}, body))
            if state["delay"]:
                time.sleep(state["delay"])
            model = body.get("model")
            oai = self.path.endswith("/chat/completions")
            key = self.headers.get("Authorization", "").replace("Bearer ", "") if oai else self.headers.get("x-api-key", "")
            if key != "sk-test":
                return self._json(401, {"error": {"message": "bad key"}})
            if model == "ratelimited":
                return self._json(429, {"error": {"message": "slow down"}})
            if model == "toolong" and body.get("max_tokens", 0) > 1000:
                return self._json(400, {"error": {"message": "max_tokens is too large: %d. This model supports at most 1000 completion tokens" % body["max_tokens"]}})
            want_tool = "weather" in json.dumps(body.get("messages")) and body.get("tools")
            if oai:
                msg = {"role": "assistant", "content": "pong"}
                if want_tool:
                    msg = {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function",
                           "function": {"name": "Weather", "arguments": json.dumps({"city": "Paris"})}}]}
                return self._json(200, {"choices": [{"message": msg, "finish_reason": "tool_calls" if want_tool else "stop"}],
                                        "usage": {"prompt_tokens": 1000, "completion_tokens": 200}})
            content = [{"type": "tool_use", "id": "tu_1", "name": "Weather", "input": {"city": "Paris"}}] if want_tool else [{"type": "text", "text": "pong"}]
            self._json(200, {"content": content, "stop_reason": "tool_use" if want_tool else "end_turn",
                             "usage": {"input_tokens": 1000, "output_tokens": 200}})
    up = _S(("127.0.0.1", 0), Up)
    up.daemon_threads = True
    state_thread(target=up.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{up.server_address[1]}"

    # ---- request conversion Anthropic -> OpenAI
    raw = {"system": "be brief", "messages": [
        {"role": "user", "content": [{"type": "text", "text": "hi"}, {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAA"}}]},
        {"role": "assistant", "content": [{"type": "text", "text": "ok"}, {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "a.txt"}, {"type": "text", "text": "next"}]}],
        "tools": [{"name": "Bash", "description": "run", "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}}}],
        "tool_choice": {"type": "any"}}
    oa = anthropic_to_openai(raw, "m", 100, "max_tokens")
    roles = [m["role"] for m in oa["messages"]]
    assert roles == ["system", "user", "assistant", "tool", "user"], roles
    assert oa["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert oa["messages"][2]["tool_calls"][0]["function"]["arguments"] == '{"command":"ls"}' and oa["messages"][3]["tool_call_id"] == "t1"
    assert oa["tools"][0]["function"]["name"] == "Bash" and oa["tool_choice"] == "required" and oa["max_tokens"] == 100
    assert guess_tier("claude-opus-4") == 5 and guess_tier("gpt-4o-mini") == 2 and guess_tier("grok-3") == 4 and guess_tier("deepseek-chat") == 3
    assert api_base("https://x.ai") == "https://x.ai/v1" and api_base("https://x.ai/v1/") == "https://x.ai/v1"

    old_cfg, old_wait = _state().CONFIG_PATH, _state().ACCOUNT_WAIT_SECONDS
    _state().ACCOUNT_WAIT_SECONDS = 0
    with tempfile.TemporaryDirectory() as td:
        _state().CONFIG_PATH = Path(td) / "c.json"
        pool = Pool({"port": 1, "api_key": "k", "accounts": [{"id": "w", "name": "Web", "logged_in": True, "profile": td + "/w"}]}, autostart=False)
        web = pool.accounts[0]
        web.set_status("ready")
        web.worker = types.SimpleNamespace(ok=True, stopping=False, _thread=threading.current_thread(),
                                           engine=types.SimpleNamespace(owns=lambda r: -1, convs=[]),
                                           submit=lambda fn, p=0, c=None: (lambda f: (f.set_result(Outcome(text="from web", calls=[])), f)[1])(concurrent.futures.Future()),
                                           stop=lambda: None)
        g = pool.add_api_account("custom_openai", "Grok-ish", base, "sk-test", "grok-x", tier=4, max_parallel=3, price_in=3.0, price_out=15.0)
        c = pool.add_api_account("custom_anthropic", "Claude-ish", base, "sk-test", "claude-opus-x", price_in=15.0, price_out=75.0, budget=0.05)
        for _ in range(50):
            if g.status == "ready" and c.status == "ready":
                break
            time.sleep(0.05)
        assert g.status == "ready" and c.status == "ready" and c.tier == 5 and g.tier == 4 and g.max_parallel == 3
        mk = lambda **kw: normalize_anthropic({"model": kw.pop("model", "claude-sonnet-4"), "max_tokens": 5000, **kw,
                                               "messages": kw.pop("messages", [{"role": "user", "content": "ping"}])})
        # exact usage, cost and the right wire format for each kind
        pool.routing.update(strategy="pinned", pinned=g.id, smart_routing=False)
        out = pool.dispatch(mk(), None, None, None).result(timeout=10)
        assert out.text == "pong" and out.usage == (1000, 200) and out.account == "Grok-ish" and out.tier == 4
        assert g.stats.in_tok == 1000 and g.stats.out_tok == 200 and abs(g.cost() - (0.003 + 0.003)) < 1e-9
        path, hdr, body = state["hits"][-1]
        assert path == "/v1/chat/completions" and hdr["authorization"] == "Bearer sk-test" and body["model"] == "grok-x" and body["max_tokens"] == 5000
        pool.routing.update(pinned=c.id)
        out = pool.dispatch(mk(thinking={"type": "enabled"}, metadata={"u": 1}), None, None, None).result(timeout=10)
        path, hdr, body = state["hits"][-1]
        assert path == "/v1/messages" and hdr["x-api-key"] == "sk-test" and hdr["anthropic-version"] and body["model"] == "claude-opus-x"
        assert "thinking" not in body and "metadata" not in body
        # native tool calls come back as bridge tool calls (both kinds)
        tools = [{"name": "Weather", "description": "w", "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}}}]
        for acc in (g, c):
            pool.routing.update(pinned=acc.id)
            o = pool.dispatch(mk(tools=tools, messages=[{"role": "user", "content": "weather in Paris?"}]), None, None, None).result(timeout=10)
            assert o.stop_reason == "tool_use" and o.calls[0]["name"] == "Weather" and o.calls[0]["arguments"] == {"city": "Paris"}, o
        # a provider's output-token limit is learnt, not fatal
        g.model = "toolong"
        pool.routing.update(pinned=g.id)
        assert pool.dispatch(mk(), None, None, None).result(timeout=10).text == "pong" and g.max_out == 1000
        g.model = "grok-x"
        # model list for the "Fetch models" button
        assert dash_action(pool, "models_probe", {"kind": "openai", "base_url": base, "api_key": "sk-test"})["models"] == ["m-a", "m-b"]
        try:
            dash_action(pool, "models_probe", {"kind": "openai", "base_url": base, "api_key": "wrong"})
            raise AssertionError("bad key must fail")
        except ValueError as exc:
            assert "401" in str(exc)
        # budget: the Claude-ish account was configured with $0.05 and has spent more => it leaves the rotation
        for _ in range(3):
            pool.dispatch(mk(), None, None, None).result(timeout=10)
        assert c.over_budget() and c.state(time.time()) == "budget" and not c.usable()
        c.budget = 0.0
        assert c.usable()
        # secrets never reach the dashboard
        snap = json.dumps(pool.snapshot(), ensure_ascii=False) + json.dumps(panel_info(pool), ensure_ascii=False)
        assert "sk-test" not in snap and "••••test" in snap
        # login problems and rate limits move the request on
        g.model = "ratelimited"
        pool.routing.update(strategy="failover", smart_routing=False)
        pool.accounts.sort(key=lambda a: 0 if a is g else 1)
        o = pool.dispatch(mk(), None, None, None).result(timeout=10)
        assert o.account in ("Web", "Claude-ish") and g.cooldown_until > time.time()
        g.model, g.cooldown_until = "grok-x", 0.0
        g.api_key = "bad"
        o = pool.dispatch(mk(), None, None, None).result(timeout=10)
        assert g.status == "login_needed" and o.account != "Grok-ish"
        g.api_key = "sk-test"
        g.set_status("ready")
        # several requests really run at the same time on one API account
        state["delay"] = 0.6
        pool.routing.update(strategy="pinned", pinned=g.id)
        t0 = time.time()
        futs = [pool.dispatch(mk(), None, None, None) for _ in range(3)]
        assert all(f.result(timeout=10).text == "pong" for f in futs) and time.time() - t0 < 1.4, time.time() - t0
        state["delay"] = 0.0
        # quality tiers: strong -> best account, balanced -> cheapest adequate, fast -> cheapest
        low = pool.add_api_account("custom_openai", "Cheap", base, "sk-test", "tiny-mini", price_in=0.1, price_out=0.4)
        for _ in range(50):
            if low.status == "ready":
                break
            time.sleep(0.05)
        for x in pool.accounts:
            x.cooldown_until, x.budget = 0.0, 0.0
        assert (web.tier, low.tier, g.tier, c.tier) == (3, 2, 4, 5)
        pool.routing.update(strategy="balanced", smart_routing=True)
        pick = lambda **kw: pool.pick(types.SimpleNamespace(side=kw.get("side", False), pin=None, role=kw.get("role"), model=kw.get("model", "claude-sonnet-4")))[0]
        assert pick(model="claude-opus-4") is c and pick(role="planner") is c and pick(role="reviewer") is c
        assert pick() is web and pick(model="claude-3-5-haiku") is low and pick(side=True) is low
        c.cooldown_until = time.time() + 60
        assert pick(model="claude-opus-4") is g                       # best AVAILABLE account
        c.cooldown_until = 0
        pool.routing.update(tier_balanced=4)
        assert pick() is g                                            # raise the bar for normal work
        pool.routing.update(smart_routing=False, tier_balanced=3)
        assert pick(model="claude-opus-4") is not None                # tiers ignored: plain strategy
        # edit an account from the panel
        dash_action(pool, "update_account", {"id": low.id, "tier": 3, "name": "Cheap2", "model": "tiny-2"})
        assert low.tier == 3 and low.name == "Cheap2" and low.model == "tiny-2"
        try:
            dash_action(pool, "login", {"id": g.id})
            raise AssertionError("login is for website accounts only")
        except ValueError:
            pass
        # settings / tiers from the console; API keys are refused inside a chat
        old_tabs = _state().MAX_TABS
        assert pool.run_command("set MAX_TABS 12") == "MAX_TABS = 12" and _state().MAX_TABS == 12 and "MAX_TABS = 12   (default" in pool.run_command("settings")
        assert pool.run_command("set MAX_TABS 0").startswith("Error") and _state().MAX_TABS == 12 and pool.run_command("set nope 1").startswith("Usage")
        assert "after a restart" in pool.run_command("set port 9000") and pool.run_command("tier Cheap2 5").startswith("'Cheap2' is now tier 5")
        settings_set(pool.cfg, {}, ["port", "MAX_TABS"])
        assert _state().MAX_TABS == old_tabs and "Never type an API key" in pool.run_command("add-api grok sk-secret")
        added = pool.run_command("add-api grok sk-secret grok-4", secret=True)
        assert added.startswith("Added") and any(x.api_key == "sk-secret" and x.provider == "grok" and x.tier == 5 for x in pool.accounts)
        pool.stop()
    up.shutdown()
    _state().CONFIG_PATH, _state().ACCOUNT_WAIT_SECONDS = old_cfg, old_wait
    print("  [ok] v6.2: API accounts (OpenAI + Anthropic wire formats), tool calls, tiers, budget, parallel, secrets")


FAKE_CLAUDE = '''#!{py}
import json, os, re, sys, time, urllib.request
prompt = sys.stdin.read()
base, key = os.environ.get("ANTHROPIC_BASE_URL", ""), os.environ.get("ANTHROPIC_API_KEY", "")
try:    # talk to the bridge exactly like the real Claude Code would (tag route => agent label + role)
    rq = urllib.request.Request(base + "/v1/messages", headers={{"content-type": "application/json", "x-api-key": key}},
        data=json.dumps({{"model": "claude-sonnet-4", "max_tokens": 50, "messages": [{{"role": "user", "content": "work"}}]}}).encode())
    urllib.request.build_opener(urllib.request.ProxyHandler({{}})).open(rq, timeout=20).read()
except Exception:
    pass
def emit(o): print(json.dumps(o), flush=True)
def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w").write(text.replace("\\\\n", "\\n") + "\\n")
    emit({{"type": "assistant", "message": {{"content": [{{"type": "tool_use", "name": "Write", "input": {{"file_path": path}}}}]}}}})
m = re.search(r"^SLEEP (\\d+)", prompt, re.M)
if m: time.sleep(int(m.group(1)))
time.sleep(0.4)
if "has CONFLICTS" in prompt:
    for f in re.findall(r"^- (.+)$", prompt.split("CONFLICTED FILES:")[1], re.M):
        t = re.sub(r"^(<<<<<<<|=======|>>>>>>>).*\\n", "", open(f.strip()).read(), flags=re.M)
        write(f.strip(), t.rstrip("\\n"))
elif "You are the reviewer" in prompt:
    write("reviewed-" + base.rsplit("/", 1)[-1].split(".")[-1] + ".txt", "reviewed")
else:
    pat = "FIX" if "Verification command" in prompt else "WRITE"
    for p, c in re.findall(r"^" + pat + r" (\\S+) :: (.*)$", prompt, re.M):
        write(p, c)
    if "FAILHARD" in prompt:
        sys.exit(3)
emit({{"type": "result", "result": "done: all good", "is_error": False}})
'''


def _selftest_swarm() -> None:
    """V6.2: activity feed, /panel + /swarm commands, quality plan parsing, and the parallel swarm itself."""
    import http.client
    import types

    # ---- pure helpers
    assert in_scope("api/x/y.py", ["api/**"]) and in_scope("api.py", ["api.py"]) and in_scope("a/b.txt", ["a/"])
    assert not in_scope("ui/x.py", ["api/**", "tests/test_api.py"]) and in_scope("anything", [])
    assert in_scope("src/a/b.js", ["src/**/*.js"]) and not in_scope("src/a/b.ts", ["src/**/*.js"])
    plan = parse_plan('Sure!\n```json\n{"summary":"s","contracts":"c","tasks":[{"id":"a b","title":"T","prompt":"p","files":["x/**"],"depends_on":["zzz","a1"]},'
                      '{"id":"a1","prompt":"q"},{"id":"a1","prompt":"dup"},{"title":"empty prompt"}]}\n```')
    assert [t["id"] for t in plan["tasks"]] == ["ab", "a1", "a1-3"] and plan["tasks"][0]["deps"] == ["a1"]
    for bad in ("no json here", '{"tasks": []}', "{broken"):
        try:
            parse_plan(bad)
            raise AssertionError("must reject: " + bad)
        except ValueError:
            pass
    with tempfile.TemporaryDirectory() as d0:
        (Path(d0) / "package.json").write_text('{"scripts":{"test":"echo \\"Error: no test specified\\" && exit 1"}}')
        assert detect_verify(d0) == ""
        (Path(d0) / "package.json").write_text('{"scripts":{"test":"jest"}}')
        assert detect_verify(d0) == "npm test --silent"
    assert fmt_tok(0) == "0"
    mk = lambda msgs, **kw: normalize_anthropic({"model": "claude-sonnet-4", "max_tokens": 50, "messages": msgs, **kw})
    r = mk([{"role": "user", "content": "go"}, {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls -la"}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "a.txt\nb.txt"}]}],
           system="Primary working directory: " + tempfile.gettempdir())
    assert summarize_last(r) == "↩ Bash: a.txt b.txt" and claude_cwd(r) == tempfile.gettempdir()
    assert _brief_call({"name": "Bash", "arguments": {"description": "d", "command": "git  status"}}) == "Bash: git status"

    if os.name == "nt" or not shutil.which("git"):
        print("  [skip] swarm integration test (needs git and a POSIX shell)")
        return

    # ---- environment: a git project, a fake `claude` on PATH, a pool whose model returns a plan for the planner
    old_cfg, old_b, old_k, old_path, old_fix = _state().CONFIG_PATH, _state().BRIDGE, _state().API_KEY, os.environ.get("PATH", ""), _state().SWARM_FIX_ROUNDS
    real_open = globals()["open_dashboard"]
    opened: List[Any] = []
    globals()["open_dashboard"] = lambda url, key, page="": opened.append(page)
    plans: Dict[str, Any] = {}

    class _FE:
        convs: List[Any] = []
        def owns(self, req): return -1
        def process(self, req, cancel, on_partial):
            if req.role == "planner":
                return Outcome(text=json.dumps(plans["next"]) if plans.get("next") else "not json at all", calls=[])
            return Outcome(text="ok", calls=[])
        def reset_all(self): return 0

    class _FW:
        def __init__(self): self.ok, self.stopping, self._thread, self.engine = True, False, threading.current_thread(), _FE()
        def submit(self, fn, priority=0, cancel=None):
            f: concurrent.futures.Future = concurrent.futures.Future()
            f.set_result(fn(self.engine))
            return f
        def stop(self): pass

    with tempfile.TemporaryDirectory() as td:
        _state().CONFIG_PATH = Path(td) / "cfg.json"
        binp = Path(td) / "bin"
        binp.mkdir()
        (binp / "claude").write_text(FAKE_CLAUDE.format(py=sys.executable))
        os.chmod(binp / "claude", 0o755)
        os.environ["PATH"] = str(binp) + os.pathsep + old_path
        proj = Path(td) / "proj"
        proj.mkdir()
        (proj / "README.md").write_text("hello\n")
        (proj / "check.py").write_text('import os, sys\nsys.path.insert(0, ".")\nif os.path.exists("calc.py"):\n    import calc\n    assert calc.add(1, 2) == 3, "add is wrong"\n')
        git(["init", "-q", "-b", "main"], proj)
        git(["add", "-A"], proj)
        git(["commit", "-q", "-m", "init"], proj)
        pool = Pool({"port": 0, "api_key": "k", "accounts": [{"id": "a", "name": "A", "logged_in": True, "profile": td + "/a"}]}, autostart=False)
        pool.accounts[0].set_status("ready")
        pool.accounts[0].worker = _FW()
        _state().BRIDGE, _state().API_KEY = pool, "k"
        server = start_server(0)
        pool.cfg["port"] = server.server_address[1]
        port = pool.cfg["port"]

        def call(method, path, body=None):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
            c.request(method, path, body=json.dumps(body) if body is not None else None,
                      headers={"Authorization": "Bearer k", "Content-Type": "application/json"})
            r2 = c.getresponse()
            d = r2.read()
            c.close()
            return r2.status, d

        def wait(run, states, timeout=90):
            end = time.time() + timeout
            while time.time() < end and run.status not in states:
                time.sleep(0.2)
            assert run.status in states, (run.status, run.summary, [(a.id, a.status, a.note) for a in run.agents], list(run.events)[-4:])

        def show(rev, path): return git(["show", f"{rev}:{path}"], proj, check=False)
        try:
            # ---- project context regression: dashboard must follow the project selected by the launcher.
            other = Path(td) / "other-project"
            other.mkdir()
            s, d = call("POST", "/dash/api/project_context", {"project": str(other)})
            assert s == 200 and json.loads(d)["project"] == str(other.resolve())
            s, d = call("GET", "/dash/api/info")
            assert s == 200 and json.loads(d)["project"] == str(other.resolve())
            s, d = call("POST", "/dash/api/project_context", {"project": str(proj)})
            assert s == 200 and json.loads(d)["project"] == str(proj.resolve())

            # ---- activity feed + commands
            n0 = len(_state().ACTIVITY)
            s, d = call("POST", "/s/swX.a9/v1/messages", {"model": "claude-sonnet-4", "max_tokens": 50, "messages": [{"role": "user", "content": "hello feed"}]})
            assert s == 200
            last = _state().ACTIVITY[-1]
            assert len(_state().ACTIVITY) == n0 + 1 and last["tag"] == "swX.a9" and last["kind"] == "agent" and last["account"] == "A" and "hello feed" in last["user"]
            s, d = call("GET", "/dash/api/activity?since=0")
            assert any(x["tag"] == "swX.a9" for x in json.loads(d)["items"])
            assert json.loads(call("GET", f"/dash/api/activity?since={_state().ACTIVITY[-1]['n']}")[1])["items"] == []
            assert "Panel opened" in pool.run_command("panel swarm") and opened[-1] == "swarm"
            pool.run_command("panel nonsense")
            assert opened[-1] == ""
            assert "No swarm runs" in pool.run_command("swarm status")
            s, d = call("GET", "/dash/api/swarm")
            sj = json.loads(d)
            assert s == 200 and sj["git"] and sj["claude"] and sj["capacity"] >= 1

            # ---- run 1: parallel agents, a dependency, concurrency cap, live resize, live feed labels, apply + cleanup
            plans["next"] = {"summary": "three parts", "contracts": "A is 1, B is 2", "tasks": [
                {"id": "a1", "title": "API", "prompt": "WRITE api/a.py :: A = 1", "files": ["api/**"], "depends_on": []},
                {"id": "a2", "title": "UI", "prompt": "WRITE ui/b.py :: B = 2", "files": ["ui/**"], "depends_on": []},
                {"id": "a3", "title": "Docs", "prompt": "WRITE docs/c.md :: docs", "files": ["docs/**"], "depends_on": ["a1"]}]}
            run = pool.swarm.start("build three parts", str(proj), agents=2, verify="off", review="off", mode="ask")
            peak, seen = 0, set()
            end = time.time() + 90
            while time.time() < end and run.status in ("planning", "running", "verifying"):
                peak = max(peak, sum(1 for a in run.agents if a.status in SW_ACTIVE))
                seen |= {a.status for a in run.agents}
                time.sleep(0.05)
            wait(run, ("done",))
            assert peak == 2, f"two agents must overlap but never exceed the cap (peak {peak})"
            assert [a.status for a in run.agents] == ["merged"] * 3, [(a.id, a.status, a.note) for a in run.agents]
            tree = git(["ls-tree", "-r", "--name-only", run.merged_branch], proj).stdout.split()
            assert {"api/a.py", "ui/b.py", "docs/c.md", "README.md"} <= set(tree), tree
            a3 = run.get("a3")
            assert "api/a.py" in git(["ls-tree", "-r", "--name-only", a3.base], proj).stdout, "a dependent task must start from the merged work"
            assert all(not a.violations for a in run.agents) and "3/3 agents merged" in run.summary
            tags = {x["tag"] for x in _state().ACTIVITY if x["tag"].startswith(run.id)}
            assert {f"{run.id}.a1", f"{run.id}.a2", f"{run.id}.a3"} <= tags and all(x["role"] == "coder" for x in _state().ACTIVITY if x["tag"].startswith(run.id + ".a"))
            assert git(["status", "--porcelain"], proj).stdout.strip() == "", "the swarm must not dirty the user's folder"
            assert "Merged into main" in pool.swarm.apply(run) and (proj / "api" / "a.py").read_text().strip() == "A = 1"
            try:
                pool.swarm.apply(run)
                raise AssertionError("second apply must fail")
            except ValueError:
                pass
            pool.swarm.cleanup(run)
            assert not (proj / SWARM_DIR_NAME / run.id).exists() and "swarm/" not in git(["branch"], proj).stdout.replace("swarm/" + run.id + "/merged", "")
            assert git(["status", "--porcelain"], proj).stdout.strip() == ""

            # ---- run 2: failing check -> automatic fix round, scope violation, merge conflict resolved automatically, reviewer role
            plans["next"] = {"summary": "quality", "contracts": "", "tasks": [
                {"id": "b1", "title": "calc", "prompt": "WRITE calc.py :: def add(a, b): return a - b\nFIX calc.py :: def add(a, b): return a + b", "files": ["calc.py"]},
                {"id": "b2", "title": "notes", "prompt": "WRITE shared.txt :: B2 version\nWRITE notes/n.txt :: n", "files": ["notes/**"]},
                {"id": "b3", "title": "other", "prompt": "WRITE shared.txt :: B3 version", "files": ["other/**"]}]}
            run = pool.swarm.start("quality run", str(proj), agents=3, verify=f'"{sys.executable}" check.py', review="on", mode="ask")
            wait(run, ("done", "done_with_issues"))
            b1, b2, b3 = run.get("b1"), run.get("b2"), run.get("b3")
            assert b1.attempts == 2 and b1.verify_ok is True and b1.status == "merged", (b1.status, b1.note, b1.verify_out)
            assert "shared.txt" in (b2.violations + b3.violations) and "shared.txt" in b2.violations
            resolved = [a for a in (b2, b3) if a.note.startswith("conflict auto-resolved")]
            assert len(resolved) == 1 and b2.status == b3.status == "merged", [(a.id, a.status, a.note) for a in run.agents]
            shared = show(run.merged_branch, "shared.txt").stdout
            assert "B2 version" in shared and "B3 version" in shared and "<<<<" not in shared
            assert run.final_verify["ok"] is True and run.status == "done", (run.status, run.summary, run.final_verify)
            assert show(run.merged_branch, "calc.py").stdout.strip().endswith("a + b")
            assert show(run.merged_branch, "reviewed-b1r.txt").returncode == 0, "the reviewer agent must run and its fixes merge"
            assert pool.swarm.role_of(f"{run.id}.b1r") == "reviewer" and pool.swarm.role_of(f"{run.id}.b1") == "coder"
            pool.swarm.cleanup(run)

            # ---- run 3: strict scope, a failing agent, its dependent skipped, issues reported; /swarm command from Claude Code
            plans["next"] = {"summary": "mixed", "contracts": "", "tasks": [
                {"id": "c1", "title": "crash", "prompt": "FAILHARD", "files": ["c1/**"]},
                {"id": "c2", "title": "needs c1", "prompt": "WRITE c2/x.txt :: x", "files": ["c2/**"], "depends_on": ["c1"]},
                {"id": "c3", "title": "strict", "prompt": "WRITE x/ok.txt :: ok\nWRITE y/bad.txt :: bad", "files": ["x/**"]}]}
            out = pool.run_command("swarm strict mixed run", ctx={"cwd": str(proj)})
            assert "started on" in out and opened[-1] == "swarm"
            run = pool.swarm.latest()
            run.opts["strict"] = True
            wait(run, ("done_with_issues", "done"))
            assert (run.get("c1").status, run.get("c2").status, run.get("c3").status) == ("failed", "skipped", "merged"), [(a.id, a.status, a.note) for a in run.agents]
            tree = git(["ls-tree", "-r", "--name-only", run.merged_branch], proj).stdout.split()
            assert "x/ok.txt" in tree and "y/bad.txt" not in tree and run.status == "done_with_issues" and "c1 failed" in run.summary
            assert "run" in pool.run_command("swarm status") or run.id in pool.run_command("swarm status")
            pool.swarm.cleanup(run)

            # ---- run 4: unusable planner output -> one agent does everything; stop kills the process
            plans["next"] = None
            run = pool.swarm.start("SLEEP 30\nWRITE slow.txt :: s", str(proj), agents="auto", verify="off", review="off", mode="ask")
            end = time.time() + 30
            while time.time() < end and not any(a.status == "running" for a in run.agents):
                time.sleep(0.1)
            assert len(run.agents) == 1 and run.agents[0].status == "running" and "single agent" in run.summary_plan
            proc = run.agents[0].proc
            assert pool.run_command("swarm agents 3").endswith("3 agents at the same time.") and run.max_agents == 3
            t0 = time.time()
            pool.swarm.stop(run)
            assert run.status == "stopped" and run.agents[0].status == "stopped"
            time.sleep(0.5)
            assert proc is not None and proc.poll() is not None and time.time() - t0 < 10, "the agent process must be killed"
            pool.swarm.cleanup(run)
            # ---- errors are readable
            for bad_start, msg in ((("", str(proj)), "describe"), (("x", td + "/nope"), "not a folder")):
                try:
                    pool.swarm.start(*bad_start)
                    raise AssertionError("expected an error")
                except ValueError as exc:
                    assert msg in str(exc)
            s, d = call("POST", "/dash/api/swarm_start", {"goal": "", "project": str(proj)})
            assert s == 400
        finally:
            for r_ in list(pool.swarm.runs.values()):
                pool.swarm.stop(r_)
            stop_server(server)
            globals()["open_dashboard"] = real_open
            os.environ["PATH"] = old_path
            _state().CONFIG_PATH, _state().BRIDGE, _state().API_KEY, _state().SWARM_FIX_ROUNDS = old_cfg, old_b, old_k, old_fix
    print("  [ok] v6.2: live feed, /panel + /swarm, parallel git-worktree swarm (deps, cap, verify-fix, conflicts, strict scope, stop, apply)")


# ============================================================================
# Claude Code launcher (single-window mode)
# ============================================================================

def _ask_project_dir(cfg: Dict[str, Any]) -> Path:
    """
    Nothing decided the folder yet (double-click, or --choose-project).
    Enter = folder picker (the classic behaviour); 1 = the folder that holds
    this .py file; anything else = a typed / pasted path.
    Without a real terminal (service, pipe) the script's own folder is used.
    """
    interactive = False
    try:
        interactive = bool(sys.stdin and sys.stdin.isatty())
    except Exception:
        pass
    if not interactive:
        chosen_path = SCRIPT_DIR
    else:
        print()
        print(C.bold("Where should Claude Code work?"))
        print(f"  {C.cyan('Enter')}  open a folder picker")
        print(f"  {C.cyan('1')}      this script's folder  ({SCRIPT_DIR})")
        print("  or type / paste a folder path")
        answer = input(C.green("> ")).strip().strip('"').strip("'")
        if answer.lower() in ("1", "here", "h", "script"):
            chosen_path = SCRIPT_DIR
        elif answer:
            chosen_path = Path(answer).expanduser().resolve()
        else:
            chosen = ""
            try:
                import tkinter
                from tkinter import filedialog
                root = tkinter.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                chosen = filedialog.askdirectory(title="Choose the project folder for Claude Code")
                root.destroy()
            except Exception:
                pass
            if not chosen:
                chosen = input("Project folder (Enter = this script's folder): ").strip().strip('"') \
                         or str(SCRIPT_DIR)
            chosen_path = Path(chosen).expanduser().resolve()
    if not chosen_path.is_dir():
        raise SystemExit(f"Not a folder: {chosen_path}")
    cfg["project_dir"] = str(chosen_path)
    save_config(cfg)
    return chosen_path


def pick_project_dir(cfg: Dict[str, Any], explicit: Optional[str], force_choose: bool,
                     here: bool = False) -> Path:
    """
    Explicit arg > --here (folder of this .py file) > terminal cwd > saved choice
    > interactive choice (picker / script folder / typed path).
    """
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if p.is_dir():
            return p
        print(C.red(f"[project] not a folder: {p}"))
    if here:
        return SCRIPT_DIR
    cwd = Path.cwd().resolve()
    if not force_choose and cwd != SCRIPT_DIR:
        return cwd                     # started from a terminal inside a project
    saved = cfg.get("project_dir")
    if not force_choose and saved and Path(saved).is_dir():
        return Path(saved)
    return _ask_project_dir(cfg)


# Flags that already decide how Claude Code handles permissions: when the user
# passes one of these we never add our own.
_PERMISSION_FLAGS = ("--dangerously-skip-permissions", "--allow-dangerously-skip-permissions",
                     "--permission-mode", "--allowedTools", "--allowed-tools",
                     "--disallowedTools", "--disallowed-tools", "--permission-prompt-tool")


def has_permission_flag(extra: List[str]) -> bool:
    return any(a.split("=", 1)[0] in _PERMISSION_FLAGS for a in extra)


def _norm_mode(value: Any) -> Optional[str]:
    v = str(value or "").strip().lower()
    aliases = {"safe": "safe", "folder": "safe", "project": "safe", "ask": "ask", "normal": "ask",
               "auto": "auto", "autonomous": "auto", "yolo": "auto"}
    return aliases.get(v)


def _mode_arg(value: str) -> str:
    m = _norm_mode(value)
    if not m:
        raise argparse.ArgumentTypeError(
            f"invalid mode {value!r} (use safe, ask or auto; also accepted: folder, normal, autonomous)")
    return m


def resolve_mode(cli_mode: Optional[str], cfg: Dict[str, Any]) -> Tuple[str, str]:
    """(mode, where it came from). --mode > DS_BRIDGE_MODE > saved config > safe."""
    for where, raw in (("--mode", cli_mode), ("DS_BRIDGE_MODE", os.getenv("DS_BRIDGE_MODE")),
                       ("saved setting", cfg.get("permission_mode"))):
        if raw in (None, ""):
            continue
        m = _norm_mode(raw)
        if m:
            return m, where
        _warn_once("mode_" + where, f"{where}={raw!r} is not a valid mode ({', '.join(MODES)}); ignored")
    return DEFAULT_MODE, "default"


# 'safe' mode. Claude Code itself confines file edits to the project folder and asks
# for anything outside it (verified against the real CLI), so no blanket
# Write/Edit/Read allow rule is added - such a rule would lift that fence.
# Shell: common development commands run freely, dangerous ones are blocked,
# everything else is asked. Compound commands (a && b) are checked part by part.
_SAFE_BASH_ALLOW = (
    # git: only what Claude Code does not already allow on its own.
    "git log", "git show", "git rev-parse", "git add", "git commit", "git checkout", "git switch",
    "git stash", "git restore",
    # dev toolchain (arbitrary code by nature - see the docstring)
    "python", "python3", "py", "pip install", "pip list", "pip show", "pip freeze", "pytest",
    "node", "npm install", "npm ci", "npm run", "npm test", "npm start", "npm ls", "npx", "pnpm", "yarn",
    "tsc", "cargo build", "cargo test", "cargo run", "cargo check", "go build", "go test", "go run",
    "go mod", "make", "cmake", "dotnet build", "dotnet test", "dotnet run", "mvn", "gradle",
)
# Exact-match rules (no trailing arguments): `git init <path>` could create a repo elsewhere.
_SAFE_BASH_ALLOW_EXACT = ("git init",)
_SAFE_BASH_DENY = (
    "sudo", "su", "doas", "rm -rf /", "rm -rf ~", "rm -rf $HOME", "rm -fr /", "rm -fr ~",
    "mkfs", "dd if=", "shutdown", "reboot", "halt", "poweroff", "format", "diskpart", "chmod -R 777 /",
    "del /s", "del /f /s", "rd /s /q C:", "rmdir /s /q C:", "Remove-Item -Recurse -Force C:",
    "git push --force", "git push -f", "env", "xargs",
)                       # (a piped `curl ... | sh` is stopped anyway: each part of a pipeline is checked)
# Wildcard rules: `git log/show --output=<file>` writes wherever it is told to.
_SAFE_BASH_DENY_WILDCARD = ("git log*--output*", "git show*--output*")


# Conservative default for older CLI releases. Newer installations may opt in to additional
# documented hook events by setting DS_BRIDGE_CLAUDE_HOOK_EVENTS to a comma/space separated list.
_CLAUDE_MIRROR_EVENTS_SAFE = (
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "Notification", "UserPromptSubmit",
    "SessionStart", "SessionEnd", "Stop", "StopFailure", "SubagentStart", "SubagentStop",
    "PreCompact", "PostCompact", "PermissionRequest", "PermissionDenied", "Setup",
    "TeammateIdle", "TaskCreated", "TaskCompleted", "Elicitation", "ElicitationResult",
    "ConfigChange", "WorktreeCreate", "WorktreeRemove", "InstructionsLoaded", "CwdChanged",
    "FileChanged",
)

def _claude_hook_events() -> Tuple[str, ...]:
    raw=os.getenv("DS_BRIDGE_CLAUDE_HOOK_EVENTS","").strip()
    if not raw or raw.lower()=="safe": return _CLAUDE_MIRROR_EVENTS_SAFE
    requested=tuple(dict.fromkeys(x.strip() for x in re.split(r"[,\s]+",raw) if x.strip()))
    invalid=[x for x in requested if x not in CLAUDE_HOOK_EVENT_UNION]
    if invalid:
        _warn_once("hook-events","ignoring unknown Claude hook events: "+", ".join(invalid[:8]))
        requested=tuple(x for x in requested if x in CLAUDE_HOOK_EVENT_UNION)
    return requested or _CLAUDE_MIRROR_EVENTS_SAFE

_CLAUDE_MIRROR_EVENTS = _claude_hook_events()


def _claude_hook_url(port: Optional[int] = None) -> str:
    """Return a concrete localhost URL matching the port of this runtime instance."""
    resolved = int(port if port is not None else _state().RESOLVED_PORT)
    return f"http://127.0.0.1:{resolved}/dash/api/claude-hook"


def claude_mirror_settings() -> Dict[str, Any]:
    """Non-blocking semantic event bridge from Claude Code into the dashboard.

    The default event set is conservative for old Claude Code clients. The optional event override
    is validated against CLAUDE_HOOK_EVENT_UNION before it is emitted. The hook never returns a decision
    and therefore cannot block Claude.
    """
    url = _claude_hook_url(int(_state().cfg.get("port", DEFAULT_PORT)))
    groups: Dict[str, Any] = {}
    for event in _CLAUDE_MIRROR_EVENTS:
        groups[event] = [{"hooks": [{
            "type": "http", "url": url, "timeout": 3,
            "headers": {"Authorization": "Bearer $DS_BRIDGE_HOOK_KEY"},
            "allowedEnvVars": ["DS_BRIDGE_HOOK_KEY"]
        }]}]
    return {"hooks": groups}


def _merge_claude_hook_settings(base: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    hooks = dict(out.get("hooks") or {})
    mirror = claude_mirror_settings().get("hooks", {})
    for event, groups in mirror.items():
        hooks[event] = list(hooks.get(event) or []) + groups
    out["hooks"] = hooks
    return out


def _sanitize_claude_hook_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """Turn Claude Code hook input into a compact, safe dashboard event payload."""
    event = str(data.get("hook_event_name") or "unknown")[:64]
    payload: Dict[str, Any] = {"event": event}
    for key in ("session_id", "cwd", "tool_name", "model", "permission_mode", "source", "reason"):
        if key in data and data.get(key) is not None:
            value = str(data.get(key))
            payload[key] = value[:260]
    if event == "UserPromptSubmit":
        payload["text"] = str(data.get("prompt") or "")[:1200]
    elif event == "MessageDisplay":
        payload["text"] = str(data.get("delta") or "")[:1200]
        payload["final"] = bool(data.get("final"))
        payload["index"] = int(data.get("index") or 0)
    elif event in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        ti = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
        interesting = {k: ti[k] for k in ("command", "file_path", "path", "pattern", "query") if k in ti}
        if interesting:
            payload["input"] = {k: str(v)[:500] for k, v in interesting.items()}
        if event != "PreToolUse":
            payload["duration_ms"] = int(data.get("duration_ms") or 0)
    elif event == "Notification":
        payload["text"] = str(data.get("message") or data.get("notification") or "")[:600]
    return payload


def ingest_claude_hook(pool: Any, data: Dict[str, Any]) -> Dict[str, Any]:
    payload = _sanitize_claude_hook_event(data)
    payload["project"] = str((data.get("cwd") or pool.cfg.get("project_dir") or SCRIPT_DIR))
    emit_dash_event("claude", payload)
    return {"ok": True}


def safe_settings() -> Dict[str, Any]:
    base = {"permissions": {
        "defaultMode": "acceptEdits",
        "allow": [f"Bash({c}:*)" for c in _SAFE_BASH_ALLOW] + [f"Bash({c})" for c in _SAFE_BASH_ALLOW_EXACT],
        "deny": [f"Bash({c}:*)" for c in _SAFE_BASH_DENY] + [f"Bash({c})" for c in _SAFE_BASH_DENY_WILDCARD],
    }}
    return _merge_claude_hook_settings(base)


def _write_json_once(path: Path, obj: Dict[str, Any]) -> Optional[str]:
    try:
        text = json.dumps(obj, indent=2)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)
        return str(path)
    except Exception as exc:
        _warn_once("settings_" + path.name, f"could not write {path} ({exc})")
        return None



_KEEP_GOING_SCRIPT = r'''# Written by DeepSeek Local Bridge: Claude Code "Stop" hook for unattended projects.
# It only acts when <project>/PROGRESS.md exists and does not yet start with FINAL BUILD COMPLETE.
import json, os, sys, tempfile
MARK = "FINAL BUILD COMPLETE"
LIMIT = int(os.environ.get("DS_BRIDGE_KEEP_GOING_MAX", "__MAX__"))
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
cwd = d.get("cwd") or os.getcwd()
prog = os.path.join(cwd, "PROGRESS.md")
if not os.path.isfile(prog):
    sys.exit(0)
try:
    head = open(prog, encoding="utf-8", errors="replace").read()[:3000]
except Exception:
    sys.exit(0)
if MARK in head:
    sys.exit(0)
sid = "".join(ch for ch in str(d.get("session_id") or "x") if ch.isalnum() or ch in "-_")[:60]
cf = os.path.join(tempfile.gettempdir(), "ds_bridge_keepgoing_" + sid + ".count")
try:
    n = int(open(cf).read().strip())
except Exception:
    n = 0
n += 1
try:
    open(cf, "w").write(str(n))
except Exception:
    pass
if n > LIMIT:
    sys.exit(0)                      # safety valve: never loop forever
sys.stderr.write(
    "AUTONOMOUS MODE - you are NOT finished: PROGRESS.md does not start with '" + MARK + "'. "
    "Do not stop and do not ask questions. Re-read PROGRESS.md, then continue with the NEXT step "
    "using tool calls right now. If your last tool call failed to run, send it again. "
    "Only when `npm run verify` passes and every acceptance criterion is done, write '" + MARK +
    "' at the top of PROGRESS.md.\n")
sys.exit(2)
'''


def keep_going_settings() -> Dict[str, Any]:
    """Hooks block that stops Claude Code from ending its turn before the project is finished."""
    script = _settings_path("keepgoing").with_suffix(".py")
    try:
        script.parent.mkdir(parents=True, exist_ok=True)
        text = _KEEP_GOING_SCRIPT.replace("__MAX__", str(_state().KEEP_GOING_MAX))
        if not script.exists() or script.read_text(encoding="utf-8") != text:
            script.write_text(text, encoding="utf-8")
    except Exception as exc:
        _warn_once("keepgoing", f"could not write the keep-going hook ({exc})")
        return {}
    cmd = f'"{Path(sys.executable).as_posix()}" "{script.as_posix()}"'
    return _merge_claude_hook_settings({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": cmd, "timeout": 30}]}]}})


def _settings_path(name: str) -> Path:
    return _state().CONFIG_PATH.with_name(f".deepseek_bridge_claude_{name}.json")


_ROOT_ALLOWED_TOOLS = ("Bash,Read,Write,Edit,MultiEdit,NotebookEdit,Glob,Grep,LS,WebFetch,WebSearch,"
                       "TodoWrite,Task")


def running_as_root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


def permission_args(mode: str, extra: List[str]) -> List[str]:
    """Extra Claude Code arguments for `mode` (nothing when the user set their own flag)."""
    if has_permission_flag(extra):
        return []
    has_settings = any(a.split("=", 1)[0] == "--settings" for a in extra)
    if mode == "ask":
        sf = _write_json_once(_settings_path("mirror"), claude_mirror_settings())
        return ["--settings", sf] if sf else []
    if mode == "safe":
        if has_settings:
            return []                # the user's own --settings decides; we never override it
        sf = _write_json_once(_settings_path("safe"), safe_settings())
        return ["--settings", sf] if sf else ["--permission-mode", "acceptEdits"]
    # auto
    if running_as_root():
        # Claude Code refuses --dangerously-skip-permissions for root, so pre-approve
        # every built-in tool instead (single '=' token: a variadic flag must not
        # swallow a prompt that follows it).
        _warn_once("root_auto", "running as root: Claude Code forbids --dangerously-skip-permissions, "
                                "so all built-in tools are pre-approved instead")
        args = [f"--allowedTools={_ROOT_ALLOWED_TOOLS}", "--permission-mode", "acceptEdits"]
        if not has_settings:
            conf = keep_going_settings() if _state().KEEP_GOING else claude_mirror_settings()
            sf = _write_json_once(_settings_path("auto"), conf)
            if sf:
                args += ["--settings", sf]
        return args
    args = ["--dangerously-skip-permissions"]
    if not has_settings:
        # Pre-accepts Claude Code's one-time "bypass permissions" warning screen.
        conf: Dict[str, Any] = _merge_claude_hook_settings({"skipDangerousModePermissionPrompt": True})
        if _state().KEEP_GOING:
            conf.update(keep_going_settings())
        sf = _write_json_once(_settings_path("auto"), conf)
        if sf:
            args += ["--settings", sf]
    return args


def claude_env(cfg: Dict[str, Any], url: str) -> Dict[str, str]:
    env = dict(os.environ)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)
    env.update({
        "ANTHROPIC_BASE_URL": url,
        "ANTHROPIC_API_KEY": cfg["api_key"],
        "ANTHROPIC_MODEL": "claude-sonnet-4-20250514",
        "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-20250514",
        "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-4-20250514",
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-20250514",
        "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "1000000",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DS_BRIDGE_HOOK_URL": f"http://127.0.0.1:{cfg.get('port', DEFAULT_PORT)}/dash/api/claude-hook",
        "DS_BRIDGE_HOOK_KEY": cfg.get("hook_key") or cfg["api_key"],
    })
    for k, v in (("API_TIMEOUT_MS", CLIENT_API_TIMEOUT_MS),
                 ("BASH_DEFAULT_TIMEOUT_MS", CLIENT_BASH_DEFAULT_TIMEOUT_MS),
                 ("BASH_MAX_TIMEOUT_MS", CLIENT_BASH_MAX_TIMEOUT_MS)):
        env.setdefault(k, v)             # a value you set yourself always wins
    return env


def launch_claude(cfg: Dict[str, Any], url: str, project: Path, extra: List[str],
                  mode: str = DEFAULT_MODE) -> int:
    exe = shutil.which("claude")
    if not exe:
        print(C.red("[error] 'claude' was not found in PATH."))
        print("Install it with:  npm install -g @anthropic-ai/claude-code")
        return 127
    install_claude_commands(getattr(_state(), "CLAUDE_COMMANDS_DIR", None), getattr(_state(), "FORCE_CLAUDE_COMMANDS", False))
    cmd = [exe, *permission_args(mode, extra), *extra]
    old = signal.signal(signal.SIGINT, signal.SIG_IGN)   # Ctrl+C belongs to Claude Code
    try:
        return subprocess.call(cmd, cwd=str(project), env=claude_env(cfg, url))
    finally:
        signal.signal(signal.SIGINT, old)


def permission_mode_text(mode: str, source: str, extra: List[str]) -> str:
    if has_permission_flag(extra):
        return "your own Claude Code permission flag is used"
    if mode == "safe" and any(a.split("=", 1)[0] == "--settings" for a in extra):
        return "SAFE requested, but your own --settings file decides the permissions (the bridge adds nothing)"
    if mode == "safe":
        desc = ("SAFE - free inside the project folder; python / node / npm / pip run unrestricted; "
                "everything else asks")
    elif mode == "ask":
        desc = "ASK - Claude Code's normal approval prompts"
    else:
        desc = "AUTO - fully autonomous, no prompts at all"
        if running_as_root():
            desc += " (root: every built-in tool incl. Bash is pre-approved)"
    return f"{desc}  [{source}]"


def verify_safe() -> int:
    """Public entry: runs the check and ALWAYS removes every temporary folder it made."""
    made: List[Path] = []
    try:
        return _verify_safe(made)
    finally:
        for d in made:
            shutil.rmtree(d, ignore_errors=True)


def _verify_safe(made: List[Path]) -> int:
    """
    Runs the real Claude Code (`claude -p`) in SAFE mode against a scripted fake model
    and reports, per command, whether it ran or was stopped for approval.
    Exit code 0 = every expectation held.
    """
    import tempfile
    exe = shutil.which("claude")
    if not exe:
        print(C.red("[verify-safe] 'claude' was not found in PATH (npm install -g @anthropic-ai/claude-code)."))
        return 127
    try:
        ver = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=90).stdout.strip()
    except Exception:
        ver = "?"
    has_git = bool(shutil.which("git"))
    proj = Path(tempfile.mkdtemp(prefix="dsb_verify_proj_"))
    made.append(proj)
    out = Path(tempfile.mkdtemp(prefix="dsb_verify_outside_"))
    made.append(out)
    (proj / "in.txt").write_text("hello", encoding="utf-8")
    (out / "secret.txt").write_text("secret", encoding="utf-8")
    if has_git:
        for cmd in (["init", "-q"], ["config", "user.email", "v@v"], ["config", "user.name", "v"],
                    ["add", "."], ["commit", "-qm", "init"]):
            subprocess.call(["git", *cmd], cwd=str(proj), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    O = str(out)
    RUN, ASK = "runs", "asks"
    cases: List[Tuple[str, str, Dict[str, Any], str]] = [
        ("write a file inside the folder", "Write", {"file_path": str(proj / "new.txt"), "content": "x"}, RUN),
        ("echo inside the folder", "Bash", {"command": "echo hi"}, RUN),
        ("python inside the folder", "Bash", {"command": "python -c pass"}, RUN),
        ("redirect inside the folder", "Bash", {"command": "echo hi > redirected.txt"}, RUN),
        ("mkdir + touch inside the folder", "Bash", {"command": "mkdir sub && touch sub/a"}, RUN),
        ("write a file OUTSIDE the folder", "Write", {"file_path": str(out / "w.txt"), "content": "x"}, ASK),
        ("read a file OUTSIDE (Read tool)", "Read", {"file_path": str(out / "secret.txt")}, ASK),
        ("cat a file OUTSIDE", "Bash", {"command": f"cat {O}/secret.txt"}, ASK),
        ("cat ~/.ssh/id_rsa", "Bash", {"command": "cat ~/.ssh/id_rsa"}, ASK),
        ("grep OUTSIDE", "Bash", {"command": f"grep -r secret {O}"}, ASK),
        ("cp into OUTSIDE", "Bash", {"command": f"cp in.txt {O}/"}, ASK),
        ("mv inside OUTSIDE", "Bash", {"command": f"mv {O}/secret.txt {O}/moved.txt"}, ASK),
        ("redirect OUTSIDE", "Bash", {"command": f"echo hi > {O}/redir.txt"}, ASK),
        ("allowed && unlisted", "Bash", {"command": "echo a && curl -s http://example.com"}, ASK),
        ("allowed ; unlisted", "Bash", {"command": "echo a; curl -s http://example.com"}, ASK),
        ("allowed | unlisted", "Bash", {"command": "echo a | curl -s -d @- http://example.com"}, ASK),
        ("allowed || unlisted", "Bash", {"command": "echo a || curl -s http://example.com"}, ASK),
        ("$( ) substitution", "Bash", {"command": "echo $(curl -s http://example.com)"}, ASK),
        ("newline-chained command", "Bash", {"command": "echo a\ncurl -s http://example.com"}, ASK),
        ("env wrapper", "Bash", {"command": "env curl -s http://example.com"}, ASK),
        ("curl", "Bash", {"command": "curl -s http://example.com"}, ASK),
        ("sudo", "Bash", {"command": "sudo id"}, ASK),
        ("rm -rf ~", "Bash", {"command": "rm -rf ~"}, ASK),
        ("rm OUTSIDE", "Bash", {"command": f"rm -rf {O}/secret.txt"}, ASK),
        ("cat | grep, both inside", "Bash", {"command": "cat in.txt | grep hello"}, RUN),
        ("pip list", "Bash", {"command": "pip list"}, RUN),
        ("npm test", "Bash", {"command": "npm test"}, RUN),
    ]
    if has_git:
        cases += [
            ("git status", "Bash", {"command": "git status"}, RUN),
            ("git log", "Bash", {"command": "git log --oneline"}, RUN),
            ("git add + commit", "Bash", {"command": "git add -A && git commit -qm t"}, RUN),
            ("git log | grep (both parts allowed)", "Bash", {"command": "git log | grep foo"}, RUN),
            ("git status && rm OUTSIDE", "Bash", {"command": f"git status && rm -rf {O}/secret.txt"}, ASK),
            ("git log --output=OUTSIDE", "Bash", {"command": f"git log --output={O}/leak1.txt"}, ASK),
            ("git log --oneline --output=OUTSIDE", "Bash", {"command": f"git log --oneline --output={O}/leak2.txt"}, ASK),
            ("git show HEAD --output=OUTSIDE", "Bash", {"command": f"git show HEAD --output={O}/leak3.txt"}, ASK),
            ("git diff --output=OUTSIDE", "Bash", {"command": f"git diff --output={O}/leak4.txt"}, ASK),
            ("git init OUTSIDE", "Bash", {"command": f"git init {O}/repo"}, ASK),
            ("git push", "Bash", {"command": "git push origin HEAD"}, ASK),
            ("git push --force", "Bash", {"command": "git push --force origin HEAD"}, ASK),
        ]
    # Claude Code's real stop messages (captured from the CLI): a stop STARTS with one of these
    # phrases, or says a path "needs approval" / "was blocked". Anchored on purpose - an ordinary
    # error such as the OS's own "Permission denied" must never count as Claude Code stopping.
    # If a future Claude Code words these differently, ASK rows turn BAD (loud, never silently OK).
    denied_re = re.compile(
        r"^\s*(Claude requested permissions|Permission to use|This (Bash )?command (requires approval|"
        r"contains multiple operations)|Contains command_substitution)|(needs approval|was blocked)\.",
        re.I)
    results: Dict[str, Tuple[bool, str]] = {}        # tool_use id -> (is_error, text)
    ids: List[str] = []
    lock = threading.Lock()
    state = {"i": 0}

    class _Engine:
        def process(self, req, cancel, on_partial):
            if getattr(req, "side", False) or not req.tools:
                return Outcome(text="ok", calls=[])
            last = req.messages[-1]
            content = last.get("content")
            if isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        results[str(blk.get("tool_use_id"))] = (bool(blk.get("is_error")), str(blk.get("content")))
            with lock:
                if state["i"] >= len(cases):
                    return Outcome(text="finished", calls=[])
                _, name, args, _ = cases[state["i"]]
                state["i"] += 1
                cid = make_id()
                ids.append(cid)
            return Outcome(text="", calls=[{"name": name, "arguments": args, "id": cid}],
                           stop_reason="tool_use")

    class _Bridge:
        ok = True

        def alive(self) -> bool:
            return True

        def submit(self, fn, priority=0, cancel=None):
            fut: concurrent.futures.Future = concurrent.futures.Future()

            def run() -> None:
                try:
                    fut.set_result(fn(_Engine()))
                except BaseException as exc:
                    fut.set_exception(exc)
            state_thread(target=run, daemon=True).start()
            return fut

    old_bridge, old_key = _state().BRIDGE, _state().API_KEY
    _state().BRIDGE, _state().API_KEY = _Bridge(), "verify-key"           # type: ignore[assignment]
    server = start_server(0)
    print(C.bold(f"[verify-safe] {ver or 'claude'}  |  {len(cases)} scenarios  |  this takes about a minute"))
    try:
        # Clean-room environment: no stray CLAUDE_* / ANTHROPIC_* variables and a throw-away home, so
        # the person's own ~/.claude settings cannot change the result. (An organisation's managed
        # policy settings, if any, still apply - that is what Claude Code enforces on this machine.)
        home = tempfile.mkdtemp(prefix="dsb_verify_home_")
        made.append(Path(home))
        ours = claude_env({"api_key": _state().API_KEY}, f"http://127.0.0.1:{server.server_address[1]}")
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("CLAUDE", "ANTHROPIC"))}
        env.update({k: v for k, v in ours.items() if k.startswith(("CLAUDE", "ANTHROPIC"))})
        env.update({"HOME": home, "USERPROFILE": home, "CLAUDE_CONFIG_DIR": str(Path(home) / ".claude")})
        cmd = [exe, *permission_args("safe", []), "-p", "go", "--max-turns", str(len(cases) + 3)]
        subprocess.call(cmd, cwd=str(proj), env=env, stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    except subprocess.TimeoutExpired:
        print(C.red("[verify-safe] Claude Code did not finish in time."))
    except OSError as exc:
        print(C.red(f"[verify-safe] could not run Claude Code: {exc}"))
    finally:
        stop_server(server)
        _state().BRIDGE, _state().API_KEY = old_bridge, old_key

    bad = 0
    ran_n = 0
    for idx, (label, _, _, want) in enumerate(cases):
        if idx >= len(ids) or ids[idx] not in results:
            continue
        ran_n += 1
        is_err, text = results[ids[idx]]
        # a stop is an error result carrying an approval / permission message - a command that
        # merely prints the word "permission" is not counted
        stopped = is_err and bool(denied_re.search(text[:400]))
        ok = stopped if want == ASK else not stopped
        bad += 0 if ok else 1
        print(f"  {C.green('OK ') if ok else C.red('BAD')} {label:38} expected {want:4} -> "
              f"{'asked / blocked' if stopped else 'ran'}")
    missing = len(cases) - ran_n
    if missing:
        bad += missing
        print(C.red(f"  {missing} scenario(s) produced no result (Claude Code stopped early)."))
    try:
        leaked = sorted(f for f in os.listdir(out) if f != "secret.txt")
        secret_ok = (out / "secret.txt").exists()
    except OSError:
        leaked, secret_ok = [], False
    if leaked or not secret_ok:
        bad += 1
        print(C.red(f"  BAD side effects outside the folder: {leaked or 'secret.txt was removed'}"))
    else:
        print(C.green("  OK  nothing was created, changed or removed outside the project folder"))
    print(C.green("[verify-safe] every check held - safe mode behaves as documented.") if not bad else
          C.red(f"[verify-safe] {bad} check(s) FAILED - do not rely on safe mode with this Claude Code version."))
    return 0 if not bad else 1


# ============================================================================
# First-run setup + "already running" detection
# ============================================================================

def find_system_chrome() -> bool:
    cands: List[str] = []
    if os.name == "nt":
        for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            base = os.environ.get(var)
            if base:
                cands.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
    elif sys.platform == "darwin":
        cands.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    else:
        return any(shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chrome"))
    return any(os.path.exists(c) for c in cands)


def _run(cmd: List[str]) -> bool:
    try:
        return subprocess.call(cmd) == 0
    except Exception as exc:
        print(C.red(f"[setup] {exc}"))
        return False


def ensure_dependencies(cfg: Dict[str, Any], need_claude: bool) -> bool:
    """Install only dependencies required by an already-selected workflow.

    The startup menu must remain cheap: this helper is intentionally called only
    after the user has selected a mode/account that actually needs a browser or
    Claude Code. A system Chromium/Chrome binary is accepted before attempting a
    network-backed Playwright browser download.
    """
    import importlib
    try:
        importlib.import_module("playwright")
    except ImportError:
        print(C.yellow("[setup] installing the 'playwright' package (first run only)..."), flush=True)
        if not _run([sys.executable, "-m", "pip", "install", "playwright", "--disable-pip-version-check"]):
            print(C.red("[setup] could not install playwright."))
            return False
        importlib.invalidate_caches()

    if not find_system_chrome():
        system_browser = (shutil.which("chromium") or shutil.which("chromium-browser") or
                          shutil.which("google-chrome") or shutil.which("chrome"))
        if system_browser:
            _state().BROWSER_CHANNEL = ""
        else:
            _state().BROWSER_CHANNEL = ""                      # use Playwright's own Chromium
            if not cfg.get("chromium_installed"):
                print(C.yellow("[setup] no supported system browser found; installing Playwright Chromium..."), flush=True)
                if not _run([sys.executable, "-m", "playwright", "install", "chromium"]):
                    print(C.red("[setup] could not install a browser. Install Chrome/Chromium and retry."))
                    return False
                cfg["chromium_installed"] = True
                save_config(cfg)
    if need_claude and not shutil.which("claude"):
        npm = shutil.which("npm")
        if not npm:
            print(C.red("[setup] Claude Code is missing and npm was not found."))
            print("        Install Node.js from https://nodejs.org/ and run this file again.")
            return False
        print(C.yellow("[setup] installing Claude Code (first run only)..."), flush=True)
        if not _run([npm, "install", "-g", "@anthropic-ai/claude-code"]) or not shutil.which("claude"):
            print(C.red("[setup] Claude Code installation failed."))
            return False
    return True


class BridgeInstanceConflict(RuntimeError):
    pass


def _health_identity(port: int, timeout: float = 1.2) -> Optional[Dict[str, Any]]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{int(port)}/health", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        return data if isinstance(data, dict) and data.get("ok") and data.get("service") == "deepseek-local-bridge" else None
    except Exception:
        return None


def _port_occupied(port: int) -> bool:
    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sck.settimeout(0.4)
        return sck.connect_ex(("127.0.0.1", int(port))) == 0
    except Exception:
        return False
    finally:
        sck.close()


def find_running_instances(start_port: int, end_port: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for port in range(int(start_port), int(end_port) + 1):
        ident = _health_identity(port)
        if ident is not None:
            item = dict(ident)
            item["port"] = int(item.get("port") or port)
            out.append(item)
    return out


def bridge_already_running(port: int, state: Optional[RuntimeState] = None) -> Optional[Dict[str, Any]]:
    ident = _health_identity(port)
    if ident is None:
        if _port_occupied(port):
            raise BridgeInstanceConflict(
                f"TCP port {port} is already in use by another process, but it is not a DeepSeek Local Bridge; "
                f"pick a different --port."
            )
        return None
    state = state or _state()
    same_config = str(Path(str(ident.get("config", ""))).resolve(strict=False)) == str(state.CONFIG_PATH.resolve(strict=False))
    same_script = str(Path(str(ident.get("script", ""))).resolve(strict=False)) == str(SCRIPT_PATH.resolve(strict=False))
    same_home = str(Path(str(ident.get("instance_home", ""))).resolve(strict=False)) == str(state.paths.home.resolve(strict=False))
    if same_config and same_script and same_home:
        return ident
    raise BridgeInstanceConflict(
        "port conflict: another bridge instance is already listening here.\n"
        f"  port: {port}\n"
        f"  name: {ident.get('instance_name', '?')}\n"
        f"  pid: {ident.get('pid', '?')}\n"
        f"  script: {ident.get('script', '?')}\n"
        f"  instance home: {ident.get('instance_home', '?')}\n"
        f"  config: {ident.get('config', '?')}\n"
        "Pick a different --port for this instance."
    )


# ============================================================================
# Startup AI chooser: keep browser startup explicit and keyboard-driven.
# ============================================================================

STARTUP_WEB_PROVIDERS: Tuple[str, ...] = ("chatgpt_web", "deepseek_web", "grok_web")


def _startup_provider_name(provider: str) -> str:
    return str((_PROVIDER.get(provider) or WEB_RECIPES.get(provider) or {}).get("name") or provider)


def _startup_accounts_from_cfg(cfg: Dict[str, Any], provider: str) -> List[Dict[str, Any]]:
    raw = cfg.get("accounts")
    items = [d for d in raw if isinstance(d, dict) and d.get("id")] if isinstance(raw, list) else []
    if not items and provider == "deepseek_web":
        try:
            had = _state().PROFILE_DIR.exists() and any(_state().PROFILE_DIR.iterdir())
        except Exception:
            had = False
        items = [{"id": "main", "name": "Account 1", "enabled": True, "logged_in": had,
                  "kind": "web", "provider": "deepseek_web"}]
    out: List[Dict[str, Any]] = []
    for d in items:
        pv = str(d.get("provider") or ("deepseek_web" if str(d.get("kind") or "web") == "web" else ""))
        if pv != provider:
            continue
        out.append(d)
    return out


def _startup_count_text(cfg: Dict[str, Any], provider: str) -> str:
    accts = _startup_accounts_from_cfg(cfg, provider)
    enabled = sum(1 for a in accts if a.get("enabled", True))
    if not accts:
        return "not configured"
    return f"{enabled} account{'s' if enabled != 1 else ''}"


def _startup_clear() -> None:
    if not sys.stdout.isatty():
        return
    try:
        if os.name == "nt":
            os.system("cls")
        else:
            print("\x1b[2J\x1b[H", end="")
    except Exception:
        pass


def _startup_key() -> str:
    """Read one lightweight terminal key; Windows is the primary target, line input is the CI fallback."""
    if not sys.stdin.isatty():
        value = input("Select [1-6]: ").strip().lower()
        return {"1": "enter:0", "2": "enter:1", "3": "enter:2", "4": "enter:3", "5": "enter:4", "6": "enter:5"}.get(value, "esc")
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(ch2, "")
        return {"\r": "enter", "\n": "enter", "\x1b": "esc", "q": "esc", "Q": "esc", " ": "space"}.get(ch, "")
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = ""
            try:
                ready, _, _ = select.select([fd], [], [], 0.06)
                if ready: seq = sys.stdin.read(2)
            except Exception:
                seq = ""
            if seq == "[A": return "up"
            if seq == "[B": return "down"
            if seq == "[C": return "right"
            if seq == "[D": return "left"
            return "esc"
        if ch in ("\r", "\n"): return "enter"
        if ch in ("q", "Q"): return "esc"
        if ch == " ": return "space"
        return ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _startup_menu_index(index: int, key: str, count: int) -> int:
    if count <= 0:
        return 0
    if key == "up":
        return (index - 1) % count
    if key == "down":
        return (index + 1) % count
    if key.startswith("enter:"):
        try:
            n = int(key.split(":", 1)[1])
            return max(0, min(count - 1, n))
        except (TypeError, ValueError):
            return index
    return index


def _startup_menu(title: str, items: List[Tuple[str, str]], selected: int = 0,
                  allow_space: bool = False) -> Optional[int]:
    if not items:
        return None
    idx = max(0, min(len(items) - 1, selected))
    while True:
        _startup_clear()
        print(C.green("AI Bridge"))
        print(C.dim(title))
        print()
        for i, (name, sub) in enumerate(items):
            marker = ">" if i == idx else " "
            compact_sub = f"  • {sub}" if sub else ""
            print(f" {marker} {i + 1}. {name}{C.dim(compact_sub)}")
        print()
        hint = "↑↓ انتخاب  •  Enter تأیید"
        if allow_space:
            hint += "  •  Space انتخاب/لغو"
        print(C.dim(hint + "  •  Esc خروج"))
        key = _startup_key()
        if key in ("up", "down"):
            idx = _startup_menu_index(idx, key, len(items))
            continue
        if key == "enter":
            return idx
        if key.startswith("enter:"):
            return _startup_menu_index(idx, key, len(items))
        if key == "esc":
            return None
        # Space is intentionally ignored by the single-select menu.


def _startup_provider_items(cfg: Dict[str, Any]) -> List[Tuple[str, str]]:
    return [("ChatGPT", _startup_count_text(cfg, "chatgpt_web")),
            ("DeepSeek", _startup_count_text(cfg, "deepseek_web")),
            ("Grok", _startup_count_text(cfg, "grok_web")),
            ("Multi-AI / Parallel", "one account per AI (light); full parallel is available next"),
            ("Dashboard only", "start Bridge without starting any AI browser"),
            ("Exit", "close without starting Bridge")]


def startup_ai_menu(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Interactive chooser; non-interactive callers must get deterministic startup behavior."""
    if not sys.stdin.isatty():
        raw = cfg.get("accounts")
        accounts = [d for d in raw if isinstance(d, dict) and d.get("id") and d.get("enabled", True) and not d.get("deleted", False)] if isinstance(raw, list) else []
        if not accounts:
            try:
                had = _state().PROFILE_DIR.exists() and any(_state().PROFILE_DIR.iterdir())
            except Exception:
                had = False
            if had:
                accounts = [{"id": "main", "name": "Account 1", "enabled": True, "logged_in": True, "kind": "web", "provider": "deepseek_web"}]
        pinned = str((cfg.get("routing") or {}).get("pinned") or "")
        if pinned and any(str(a.get("id")) == pinned for a in accounts):
            chosen = next(a for a in accounts if str(a.get("id")) == pinned)
        elif accounts:
            chosen = accounts[0]
        else:
            print(C.red("[startup] non-interactive launch requires --ai <provider> or at least one enabled pre-configured web account."), flush=True)
            print(C.dim("         Example: python bridge.py --instance B --port 8789 --ai deepseek --panel"), flush=True)
            return {"mode": "error", "code": 2}
        provider = str(chosen.get("provider") or ("deepseek_web" if chosen.get("kind") == "web" else ""))
        if provider in STARTUP_WEB_PROVIDERS:
            return {"mode": "provider", "provider": provider}
        print(C.red(f"[startup] pre-configured account provider '{provider}' cannot be started by the web startup selector."), flush=True)
        return {"mode": "error", "code": 2}
    items = _startup_provider_items(cfg)
    picked = _startup_menu("What should start now?", items)
    if picked is None or picked == 5:
        return {"mode": "exit"}
    if picked == 4:
        return {"mode": "dashboard"}
    if picked == 3:
        sub = [("Light parallel", "ChatGPT + DeepSeek + Grok: one account from each AI"),
               ("Full parallel", "start every enabled web account (uses more RAM/CPU)"),
               ("Back", "return to the previous menu")]
        mode = _startup_menu("Parallel mode", sub)
        if mode is None or mode == 2:
            return startup_ai_menu(cfg)
        return {"mode": "multi", "full": bool(mode == 1)}
    return {"mode": "provider", "provider": STARTUP_WEB_PROVIDERS[picked]}


def startup_choose_account(cfg: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """Choose one account or all enabled accounts for a single provider."""
    accounts = [d for d in _startup_accounts_from_cfg(cfg, provider) if d.get("enabled", True)]
    if len(accounts) <= 1:
        return {"mode": "one", "ids": [str(accounts[0]["id"])] if accounts else []}
    items = [(str(d.get("name") or d.get("id")),
              "logged in" if d.get("logged_in") else "login needed") for d in accounts]
    items.append((f"All enabled {_startup_provider_name(provider)} accounts", f"start all {len(accounts)} accounts"))
    picked = _startup_menu(f"Choose {_startup_provider_name(provider)} account", items)
    if picked is None:
        return {"mode": "cancel", "ids": []}
    if picked == len(accounts):
        return {"mode": "all", "ids": [str(d["id"]) for d in accounts]}
    return {"mode": "one", "ids": [str(accounts[picked]["id"])]}


def startup_prepare_accounts(pool: "Pool", choice: Dict[str, Any], headed: bool = False) -> List[str]:
    """Ensure selected providers have accounts, then return the exact account IDs to start."""
    mode = choice.get("mode")
    if mode == "dashboard":
        return []
    if mode == "provider":
        provider = str(choice.get("provider") or "")
        if provider not in STARTUP_WEB_PROVIDERS:
            return []
        candidates = [a for a in pool.accounts if a.enabled and a.kind == "web" and a.provider == provider]
        if not candidates:
            a = pool.add_web_account(provider, name=f"{_startup_provider_name(provider)} 1", headed=headed, start=False)
            return [a.id]
        if len(candidates) == 1:
            return [candidates[0].id]
        # Re-use the keyboard chooser, but when the console is non-interactive start the first enabled one.
        picked = startup_choose_account(pool.cfg, provider)
        return [x for x in picked.get("ids", []) if pool.get_by_id(x)]
    if mode == "multi":
        providers = list(STARTUP_WEB_PROVIDERS)
        selected: List[str] = []
        for provider in providers:
            candidates = [a for a in pool.accounts if a.enabled and not a.deleted and a.kind == "web" and a.provider == provider]
            # Multi-AI is explicit: it never creates a surprise browser profile.
            if not candidates:
                continue
            if choice.get("full"):
                selected.extend(a.id for a in candidates)
            else:
                pinned = pool.get_by_id(pool.routing.get("pinned"))
                primary = pinned if pinned and pinned.provider == provider and pinned.enabled else candidates[0]
                selected.append(primary.id)
        return list(dict.fromkeys(selected))
    return []

# ============================================================================
# Main
# ============================================================================

def _parse_port_range(spec: str) -> Tuple[int, int]:
    raw = str(spec or "8700-8800").strip()
    if "-" not in raw:
        n = int(raw)
        return n, n
    a, b = raw.split("-", 1)
    start, end = int(a), int(b)
    if not (1 <= start <= 65535 and 1 <= end <= 65535 and start <= end):
        raise ValueError("port range must be between 1 and 65535")
    return start, end


def _print_instances(items: List[Dict[str, Any]]) -> None:
    for x in items:
        print(f"name={x.get('instance_name','?')} pid={x.get('pid','?')} port={x.get('port','?')} "
              f"script={x.get('script','?')} instance_home={x.get('instance_home','?')} config={x.get('config','?')}")


def _resolve_run_port(args: argparse.Namespace, cfg: Dict[str, Any]) -> Tuple[int, str]:
    if getattr(args, "port", None) is not None:
        return int(args.port), "--port"
    env = os.getenv("DS_BRIDGE_PORT")
    if env is not None:
        try:
            return int(env), "DS_BRIDGE_PORT"
        except ValueError:
            print(C.red(f"[port] DS_BRIDGE_PORT={env!r} is invalid; using config/default"), flush=True)
    try:
        return int(cfg.get("port", DEFAULT_PORT)), "config"
    except Exception:
        return DEFAULT_PORT, "default"


def _validate_port(port: int) -> None:
    if not (1 <= int(port) <= 65535):
        raise ValueError("port must be between 1 and 65535")


def main() -> int:
    ap = argparse.ArgumentParser(description="DeepSeek V6.4 bridge. One process owns one instance home, config, browser profile set and TCP port.")
    ap.add_argument("project", nargs="?", help="project folder for Claude Code (drag a folder onto this file)")
    ap.add_argument("--terminal", action="store_true", help="bridge only, with the interactive terminal (no Claude Code)")
    ap.add_argument("--choose-project", action="store_true", help="pick the project folder again")
    ap.add_argument("--here", action="store_true", help="use the folder that contains this .py file as the project folder")
    ap.add_argument("--mode", type=_mode_arg, metavar="{safe,ask,auto}", help="Claude Code permission mode for this run")
    ap.add_argument("--safe", dest="mode", action="store_const", const="safe", help="same as --mode safe")
    ap.add_argument("--ask", dest="mode", action="store_const", const="ask", help="same as --mode ask")
    ap.add_argument("--auto", "--autonomous", dest="mode", action="store_const", const="auto", help="same as --mode auto")
    ap.add_argument("--set-mode", type=_mode_arg, metavar="{safe,ask,auto}", help="save the default permission mode in the config file and continue")
    ap.add_argument("--prompt-file", metavar="FILE", help="copy a long task prompt into the project as AUTONOMOUS_PROMPT.md")
    ap.add_argument("--port", type=int, help="local HTTP port for this run (not saved unless --save-port)")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="run offline regression tests and exit")
    ap.add_argument("--verify-safe", action="store_true", help="run the real Claude Code safe-mode verification")
    ap.add_argument("--headed", action="store_true", help="always use a visible browser window")
    ap.add_argument("--ai", choices=("chatgpt", "deepseek", "grok", "multi", "dashboard"), help="which AI account/provider to start")
    ap.add_argument("--debug-dir", help="dump every prompt / raw reply into this directory")
    ap.add_argument("--add-account", action="append", metavar="NAME", help="add an account before startup")
    ap.add_argument("--list-accounts", action="store_true", help="show the saved accounts and exit")
    ap.add_argument("--ctl", nargs="*", metavar="COMMAND", help="control an already running bridge")
    ap.add_argument("--panel", action="store_true", help="stay in foreground as a dashboard service; combines with --ai")
    ap.add_argument("--no-open", action="store_true", help="do not open the dashboard in your browser")
    ap.add_argument("--instance", "--instance-home", dest="instance", metavar="PATH", help="instance home; defaults to the folder containing bridge.py")
    ap.add_argument("--instance-name", metavar="NAME", help="human-readable instance name (default: home folder name)")
    ap.add_argument("--list-instances", nargs="?", const="8700-8800", metavar="START-END", help="scan a port range and list live bridge instances")
    ap.add_argument("--save-port", action="store_true", help="persist --port into this instance's config")
    ap.add_argument("--print-paths", action="store_true", help="print resolved instance paths and exit")
    ap.add_argument("--force-claude-commands", action="store_true", help="overwrite Claude command files generated by another bridge instance")
    ap.add_argument("--install-commands-into", metavar="DIR", help="Claude config directory to receive generated commands")
    ap.add_argument("--version", action="version", version=f"deepseek-local-bridge {VERSION}")
    args = ap.parse_args()

    state = make_runtime_state(Path(args.instance).expanduser() if args.instance else SCRIPT_DIR, args.instance_name)
    if args.no_color:
        state.COLOR_ENABLED = False
    state.CLAUDE_COMMANDS_DIR = Path(args.install_commands_into).expanduser().resolve() if args.install_commands_into else None
    state.FORCE_CLAUDE_COMMANDS = bool(args.force_claude_commands)
    token = _CURRENT_STATE.set(state)
    try:
        # Read/list-only modes must have no config/browser side effects.
        if args.list_instances is not None:
            try:
                a, b = _parse_port_range(args.list_instances)
                _print_instances(find_running_instances(a, b))
                return 0
            except Exception as exc:
                print(C.red(f"[list-instances] {exc}"), flush=True)
                return 2
        if args.print_paths:
            p = state.paths
            print(f"instance_name={state.instance_name}")
            print(f"instance_home={p.home}")
            print(f"script={p.script}")
            print(f"config={p.config}")
            print(f"usage={p.usage}")
            print(f"profile={p.profile}")
            print(f"accounts={p.accounts}")
            print(f"log={p.log}")
            print(f"swarm_attachments={p.swarm_attachments}")
            print(f"claude_settings_safe={p.claude_settings('safe')}")
            print(f"claude_settings_ask={p.claude_settings('mirror')}")
            print(f"claude_settings_auto={p.claude_settings('auto')}")
            print(f"claude_settings_keepgoing={p.claude_settings('keepgoing')}")
            print(f"keep_going_hook={p.keep_going_hook()}")
            return 0

        if args.self_test:
            return self_test()
        if args.verify_safe:
            return verify_safe()

        cfg = load_config()
        init_settings(cfg)
        if args.debug_dir:
            state.DEBUG_DIR = args.debug_dir
        if args.headed:
            state.HEADLESS_MODE = "0"
        state.cfg = cfg

        resolved_port, port_src = _resolve_run_port(args, cfg)
        _validate_port(resolved_port)
        state.PERSISTED_PORT = int(cfg.get("port", DEFAULT_PORT))
        state.RESOLVED_PORT = int(resolved_port)
        state.PORT_SOURCE = port_src
        state.PORT_PERSIST_ALLOWED = bool(args.save_port and args.port is not None)
        cfg["port"] = resolved_port
        state.API_KEY = cfg.get("api_key")
        # Agents parse these exact first five stdout lines before browser startup begins.
        print(VERSION)
        print(state.instance_name)
        print(state.paths.home)
        print(state.CONFIG_PATH)
        print(resolved_port)
        if args.save_port and args.port is not None:
            save_config(cfg)
        elif args.save_port and args.port is None:
            print(C.yellow("[port] --save-port has no effect without --port"), flush=True)

        if args.set_mode:
            cfg["permission_mode"] = args.set_mode
            save_config(cfg)
            print(C.green(f"[mode] default permission mode saved: {args.set_mode}  ({state.CONFIG_PATH})"))
        mode, mode_src = resolve_mode(args.mode or args.set_mode, cfg)
        if args.set_mode and not args.mode:
            mode_src = "--set-mode"

        if args.ctl is not None:
            return ctl_client(cfg, " ".join(args.ctl) or "status")
        if args.list_accounts:
            return 0 if not print(Pool(cfg, autostart=False).status_text()) else 0

        # Resolve port ownership before starting a browser. This is the key race-safety rule.
        try:
            existing = bridge_already_running(resolved_port, state)
        except BridgeInstanceConflict as exc:
            print(C.red(f"[port conflict] {exc}"), flush=True)
            return 2

        if existing is not None and not args.terminal:
            project = pick_project_dir(cfg, args.project, args.choose_project, args.here)
            if project is not None:
                ctl_project(cfg, project)
            for nm in args.add_account or []:
                ctl_client(cfg, "add " + nm)
            print(C.green(f"Bridge already running for instance {state.instance_name} on port {resolved_port}; starting another Claude Code."))
            print(C.dim(f"Project: {project}\nPermissions: {permission_mode_text(mode, mode_src, [])}"))
            if args.panel:
                return 0
            return launch_claude(cfg, f"http://127.0.0.1:{resolved_port}", project, [], mode)

        if os.name == "nt":
            os.system(f"title DeepSeek Bridge - {state.instance_name}")

        # Explicit CLI startup modes. --panel means service mode, not dashboard-only when --ai is also present.
        if args.panel:
            state.PANEL_ONLY = True
            state.RUN_MODE = "panel"
            if args.ai in (None, "dashboard"):
                startup_choice = {"mode": "dashboard"}
            elif args.ai == "multi":
                startup_choice = {"mode": "multi", "full": False}
            else:
                startup_choice = {"mode": "provider", "provider": args.ai + "_web"}
        elif args.ai:
            state.RUN_MODE = "claude"
            startup_choice = {"mode": "dashboard" if args.ai == "dashboard" else "multi" if args.ai == "multi" else "provider",
                              **({} if args.ai in ("dashboard", "multi") else {"provider": args.ai + "_web"}),
                              **({"full": False} if args.ai == "multi" else {})}
        elif args.terminal:
            state.RUN_MODE = "terminal"
            startup_choice = {"mode": "provider", "provider": "deepseek_web"}
        else:
            state.RUN_MODE = "claude"
            startup_choice = startup_ai_menu(cfg)
        if startup_choice.get("mode") in ("exit", "error"):
            if startup_choice.get("mode") == "error":
                return int(startup_choice.get("code", 2))
            print(C.dim("[startup] cancelled."), flush=True)
            return 0

        claude_extra: List[str] = []
        project = None
        if not args.terminal and not args.panel:
            project = pick_project_dir(cfg, args.project, args.choose_project, args.here)
        if args.prompt_file and project is not None:
            try:
                src_text = Path(args.prompt_file).expanduser().read_text(encoding="utf-8-sig")
                target = Path(project) / "AUTONOMOUS_PROMPT.md"
                if not target.exists() or target.read_text(encoding="utf-8") != src_text:
                    target.write_text(src_text, encoding="utf-8")
                claude_extra.append("Read AUTONOMOUS_PROMPT.md completely (it is the full specification) and execute it now, fully autonomously. Never ask me anything. Keep PROGRESS.md up to date; if you are ever unsure where you are, re-read AUTONOMOUS_PROMPT.md and PROGRESS.md.")
                print(C.green(f"[prompt] {len(src_text):,} chars -> {target}"))
            except Exception as exc:
                print(C.red(f"[prompt] cannot use --prompt-file: {exc}"))
                return 1

        if project is not None:
            remember_project(cfg, project, persist=True)
        state.BRIDGE = Pool(cfg, autostart=False)
        for nm in args.add_account or []:
            state.BRIDGE.add_account(nm, start=False)
        selected_ids = startup_prepare_accounts(state.BRIDGE, startup_choice, headed=bool(args.headed))
        if args.headed:
            for aid in selected_ids:
                account = state.BRIDGE.get_by_id(aid)
                if account is not None and account.kind == "web":
                    account.headed = True
            state.BRIDGE._save()

        selected_accounts = [state.BRIDGE.get_by_id(aid) for aid in selected_ids]
        selected_web = any(a is not None and getattr(a, "kind", "") == "web" for a in selected_accounts)
        need_claude = not args.terminal and not args.panel and startup_choice.get("mode") != "dashboard"
        if (selected_web or (need_claude and bool(selected_ids))) and not ensure_dependencies(cfg, need_claude=need_claude):
            state.BRIDGE.stop()
            return 1
        if startup_choice.get("mode") != "dashboard" and not selected_ids:
            log("[startup] the selected mode has no ready/configured account; nothing was started", C.yellow)
            state.BRIDGE.stop()
            return 1
        if startup_choice.get("mode") == "dashboard":
            state.PANEL_ONLY = True
            state.RUN_MODE = "panel"
            log("[main] starting Bridge without starting an AI browser (Dashboard only).", C.dim)
        else:
            names = [state.BRIDGE.get_by_id(aid).name for aid in selected_ids if state.BRIDGE.get_by_id(aid)]
            log(f"[main] starting selected AI account(s): {', '.join(names) or 'none'}", C.dim)
            state.BRIDGE.start_selected(selected_ids)
            if not state.BRIDGE.wait_selected_ready(selected_ids, state.LOGIN_WAIT_SECONDS + 120):
                log("[error] no selected AI account could be started / logged in.", C.red)
                state.BRIDGE.stop()
                return 1

        try:
            server = start_server(resolved_port, state)
            state.SERVER = server
        except OSError as exc:
            ident = _health_identity(resolved_port)
            if ident:
                print(C.red("[server error] requested port is already occupied by:\n"
                            f"  instance={ident.get('instance_name')} pid={ident.get('pid')}\n"
                            f"  home={ident.get('instance_home')}\n  config={ident.get('config')}\n"
                            f"Use --port <different-port>."), flush=True)
            else:
                print(C.red(f"[server error] cannot listen on 127.0.0.1:{resolved_port} ({exc}). Use --port <different-port>."), flush=True)
            state.BRIDGE.stop()
            return 1
        except Exception as exc:
            log(f"[server error] {exc}", C.red)
            state.BRIDGE.stop()
            return 1

        url = f"http://127.0.0.1:{resolved_port}"
        if state.DASH_AUTOOPEN and not args.no_open:
            open_dashboard(url, cfg["api_key"])
        try:
            if args.terminal or args.panel:
                print_banner(cfg, url, mode, mode_src)
                if state.PANEL_ONLY:
                    print(C.green("\nPanel mode: control everything from the dashboard. Press Ctrl+C here to stop the bridge."))
                    try:
                        while True:
                            time.sleep(3600)
                    except KeyboardInterrupt:
                        pass
                else:
                    terminal_loop(cfg, url)
                return 0

            logpath = state.paths.log
            print(C.green(f"Bridge ready on {url}"))
            print(C.dim(f"Dashboard: {url}/dash   |   in Claude Code: /panel  /swarm <goal>  /ds next  /ds use 2  /ds auto"))
            print(C.dim(f"Project: {project}\nPermissions: {permission_mode_text(mode, mode_src, claude_extra)}\nBridge log: {logpath}\nStarting Claude Code..."))
            try:
                if logpath.exists() and logpath.stat().st_size > 5 * 1024 * 1024:
                    os.replace(logpath, logpath.with_suffix(".log.1"))
            except OSError:
                pass
            state.LOG_FILE = open(logpath, "a", encoding="utf-8", errors="replace")
            old_stderr = sys.stderr
            sys.stderr = state.LOG_FILE
            try:
                code = launch_claude(cfg, url, project, claude_extra, mode)
            finally:
                sys.stderr = old_stderr
                lf, state.LOG_FILE = state.LOG_FILE, None
                try:
                    lf.close()
                except Exception:
                    pass
            return code
        finally:
            stop_server(server)
            state.BRIDGE.stop()
    finally:
        _CURRENT_STATE.reset(token)


if __name__ == "__main__":
    rc = 1
    try:
        rc = main()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        rc = 0
    except Exception:
        traceback.print_exc()
    if rc not in (0, None) and sys.__stdin__ is not None and sys.__stdin__.isatty():
        try:
            input("\nPress Enter to close this window...")   # keep errors visible after a double-click
        except Exception:
            pass
    sys.exit(rc or 0)
