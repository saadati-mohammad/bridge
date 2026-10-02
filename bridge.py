#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Local Bridge V5.8
==========================

Anthropic/OpenAI-compatible local gateway for Claude Code, backed by a real
chat.deepseek.com browser session (Playwright).

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
import concurrent.futures
import hashlib
import itertools
import json
import math
import os
import queue
import re
import secrets
import select
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
import uuid
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
# Configuration
# ============================================================================

_WARNED: set = set()


def _warn_once(key: str, msg: str) -> None:
    if key in _WARNED:
        return
    _WARNED.add(key)
    try:
        print(f"[warning] {msg}", file=sys.stderr, flush=True)
    except Exception:
        pass


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except Exception:
        _warn_once(name, f"{name}={raw!r} is not an integer; using {default}")
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        _warn_once(name, f"{name}={raw!r} is not a number; using {default}")
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


VERSION = "5.10"
SCRIPT_DIR = Path(__file__).resolve().parent
CHAT_URL = os.getenv("DS_BRIDGE_CHAT_URL", "https://chat.deepseek.com/")
# Absolute + anchored to the script so the login survives different cwd's.
PROFILE_DIR = Path(os.getenv("DS_BRIDGE_PROFILE_DIR", str(SCRIPT_DIR / "ds_profile"))).expanduser().resolve()
CONFIG_PATH = Path(os.getenv("DS_BRIDGE_CONFIG", str(Path.home() / ".deepseek_bridge.json")))
DEBUG_DIR = os.getenv("DS_BRIDGE_DEBUG_DIR", "")
BROWSER_CHANNEL = os.getenv("DS_BRIDGE_CHANNEL", "chrome")
# auto = try real headless first, fall back to a visible window; 1 = force
# headless; 0 = always visible window.
HEADLESS_MODE = os.getenv("DS_BRIDGE_HEADLESS", "auto").strip().lower()

DEFAULT_PORT = _env_int("DS_BRIDGE_PORT", 8788)
LOGIN_WAIT_SECONDS = _env_int("DS_BRIDGE_LOGIN_WAIT", 600)
HEADLESS_READY_TIMEOUT = _env_int("DS_BRIDGE_READY_TIMEOUT", 20)

# Prompt budgets (characters).
MAX_PROMPT_CHARS = _env_int("DS_BRIDGE_MAX_PROMPT_CHARS", 800_000)
# Budget for the *history* part of a brand new chat. System prompt and tool
# schemas are budgeted separately, so a huge tool schema never wipes history.
HISTORY_BUDGET_CHARS = _env_int("DS_BRIDGE_HISTORY_BUDGET_CHARS", 300_000)
# When one DeepSeek chat has received this many characters, rotate to a fresh
# chat (with a compacted history) instead of growing forever.
ROTATE_CHARS = _env_int("DS_BRIDGE_ROTATE_CHARS", 700_000)
KEEP_RECENT_MESSAGES_FULL = _env_int("DS_BRIDGE_KEEP_RECENT_MESSAGES", 12)
BASE_BLOCK_LIMIT = _env_int("DS_BRIDGE_OLD_BLOCK_LIMIT", 6000)
TOOL_DESC_LIMIT = _env_int("DS_BRIDGE_TOOL_DESC_LIMIT", 1800)
PARAM_DESC_LIMIT = _env_int("DS_BRIDGE_PARAM_DESC_LIMIT", 300)

# A single tool result / message block inside a *follow-up* (delta) prompt is
# head+tail trimmed above this size, so one giant file dump can never push a
# whole chat over the site's context window.
DELTA_BLOCK_LIMIT = _env_int("DS_BRIDGE_DELTA_BLOCK_LIMIT", 150_000)
# Claude Code permission mode: safe (default) | ask | auto  (see the module docstring).
MODES = ("safe", "ask", "auto")
DEFAULT_MODE = "safe"

MAX_HTTP_BODY_BYTES = _env_int("DS_BRIDGE_MAX_HTTP_BODY_BYTES", 32 * 1024 * 1024)

# Reply handling.
STALL_TIMEOUT = _env_int("DS_BRIDGE_STALL_TIMEOUT", 900)      # no progress at all (long thinking is fine)
MAX_REPLY_SECONDS = _env_int("DS_BRIDGE_MAX_REPLY_SECONDS", 10800)
SUBMIT_TIMEOUT = _env_int("DS_BRIDGE_SUBMIT_TIMEOUT", 25)
POLL_SECONDS = _env_float("DS_BRIDGE_POLL_SECONDS", 0.1)
MAX_CONTINUES = _env_int("DS_BRIDGE_MAX_CONTINUES", 8)
MAX_REPAIRS = _env_int("DS_BRIDGE_MAX_REPAIRS", 4)
REQUEST_GAP_SECONDS = _env_float("DS_BRIDGE_REQUEST_GAP", 0.05)

MAX_TABS = _env_int("DS_BRIDGE_MAX_TABS", 8)            # live browser tabs; older ones hibernate
MAX_KEPT_CONVS = _env_int("DS_BRIDGE_MAX_KEPT_CONVS", 40)  # hibernated (tab closed, chat kept) conversations
# V5.9: chats are KEPT by default (DeepSeek is free, nothing is gained by deleting them, and a
# deleted chat can never be resumed).  Use /purge in the terminal, or set this to 1, to delete.
DELETE_OLD_CHATS = _env_bool("DS_BRIDGE_DELETE_OLD_CHATS", False)
# Transient failures (server busy, stall, empty reply) are retried this many times with backoff.
MAX_RETRIES = _env_int("DS_BRIDGE_MAX_RETRIES", 6)
RETRY_BACKOFF_MAX = _env_int("DS_BRIDGE_RETRY_BACKOFF_MAX", 60)
# Passed to Claude Code so that very long tasks are not aborted client-side.
CLIENT_API_TIMEOUT_MS = "7200000"
CLIENT_BASH_DEFAULT_TIMEOUT_MS = "1800000"
CLIENT_BASH_MAX_TIMEOUT_MS = "7200000"
CHARS_PER_TOKEN = _env_float("DS_BRIDGE_CHARS_PER_TOKEN", 4.0)

PRIORITY_MAIN = 0
PRIORITY_SIDE = 5


# ============================================================================
# ANSI colours + logging
# ============================================================================

class C:
    _on = True

    @classmethod
    def enable(cls, value: bool) -> None:
        cls._on = bool(value)

    @classmethod
    def _w(cls, code: str, text: Any) -> str:
        s = str(text)
        return f"\033[{code}m{s}\033[0m" if cls._on else s

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


LOG_FILE = None  # set in Claude mode so bridge logs never corrupt Claude's TUI


def log(msg: str, color: Optional[Callable[[Any], str]] = None) -> None:
    if LOG_FILE is not None:
        try:
            LOG_FILE.write(time.strftime("%H:%M:%S ") + msg + "\n")
            LOG_FILE.flush()
        except Exception:
            pass
        return
    print(color(msg) if color else msg, flush=True)


_dump_counter = itertools.count(1)


def dump_debug(kind: str, text: str) -> None:
    if not DEBUG_DIR:
        return
    try:
        d = Path(DEBUG_DIR)
        d.mkdir(parents=True, exist_ok=True)
        name = f"{time.strftime('%H%M%S')}-{next(_dump_counter):04d}-{kind}.txt"
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


# ============================================================================
# Config file
# ============================================================================

def save_config(cfg: Dict[str, Any]) -> None:
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp, CONFIG_PATH)
    except Exception as exc:
        _warn_once("save_config", f"could not write {CONFIG_PATH} ({exc}); "
                                  "a new API key will be generated on every start")


def load_config() -> Dict[str, Any]:
    cfg: Dict[str, Any] = {"port": DEFAULT_PORT, "api_key": None}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                cfg.update(loaded)
        except Exception:
            pass
    if not cfg.get("api_key"):
        cfg["api_key"] = "sk-ds-local-" + secrets.token_hex(24)
        save_config(cfg)
    try:
        cfg["port"] = int(cfg.get("port", DEFAULT_PORT))
    except Exception:
        cfg["port"] = DEFAULT_PORT
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
    return max(1, int(n / CHARS_PER_TOKEN))


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

def minify_schema(node: Any, desc_limit: int = PARAM_DESC_LIMIT, _depth: int = 0) -> Any:
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
        desc = trim_text_boundary(str(tool.get("description", "") or ""), TOOL_DESC_LIMIT)
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
    tail_start = max(1, n - KEEP_RECENT_MESSAGES_FULL)

    def build(scale: float, tail_scale: Optional[float], drop: int) -> str:
        parts: List[str] = []
        omitted = 0
        for idx, m in enumerate(messages):
            if 1 <= idx < 1 + drop and idx < tail_start:
                omitted += 1
                continue
            if idx == 0:
                parts.append(render_message(m, int(BASE_BLOCK_LIMIT * 3 * scale)) if scale < 1 else full[0])
            elif idx >= tail_start:
                if tail_scale is None:
                    parts.append(full[idx])
                else:
                    parts.append(render_message(m, max(400, int(BASE_BLOCK_LIMIT * tail_scale))))
            else:
                parts.append(render_message(m, max(300, int(BASE_BLOCK_LIMIT * scale))))
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
    budget = max(20_000, min(history_budget, MAX_PROMPT_CHARS - overhead))
    parts.append("[TRANSCRIPT]\n" + compact_history(req.messages, budget))
    parts.append(TAIL)
    return "\n\n".join(parts)


def build_delta_prompt(req: "NormReq", delta: List[Dict[str, Any]], tools_changed: bool) -> str:
    parts = ["[NEW ITEMS SINCE YOUR LAST TURN]\n" + render_messages(delta, limit=DELTA_BLOCK_LIMIT or None)]
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
                        blocks.append({"type": "text", "text": "[image attached]"})
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
        "usage": {"input_tokens": in_tokens, "output_tokens": estimate_tokens([o.text, o.calls]),
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
    out_t = estimate_tokens([o.text, o.calls])
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
                                    "usage": {"output_tokens": max(1, int(self.out_chars / CHARS_PER_TOKEN))}})
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
  const B = { seq: 0, cur: null };
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
    let resp;
    try { resp = await origFetch.apply(this, arguments); }
    catch (e) { if (c) { c.error = 'fetch failed: ' + e; c.done = true; } throw e; }
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


class DeepSeekWeb:
    """Owned and used by ONE thread only (sync Playwright requirement)."""

    def __init__(self) -> None:
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

    # ---- launch -----------------------------------------------------------

    def _launch(self, headless: bool):
        args = ["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
        if sys.platform.startswith("linux"):
            args.append("--no-sandbox")
        if not headless and not sys.platform.startswith("linux"):
            args.append("--start-minimized")     # most Linux window managers mishandle it
        kwargs = dict(user_data_dir=str(PROFILE_DIR), headless=headless, args=args,
                      viewport={"width": 1280, "height": 900}, locale="en-US",
                      ignore_default_args=["--enable-automation"])
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        if BROWSER_CHANNEL:
            try:
                return self.pw.chromium.launch_persistent_context(channel=BROWSER_CHANNEL, **kwargs)
            except Exception as exc:
                log(f"[browser] channel '{BROWSER_CHANNEL}' failed ({exc}); using bundled chromium", C.yellow)
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

    @staticmethod
    def _has_token(page) -> bool:
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

    def _find_textarea(self, page) -> Optional[str]:
        if self._sel:
            try:
                if page.evaluate("(s) => !!document.querySelector(s)", self._sel):
                    return self._sel
            except Exception:
                pass
            self._sel = None
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
        return self._has_token(page) and self._find_textarea(page) is not None

    def _goto_chat(self, page) -> None:
        try:
            page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            log(f"[browser] navigation warning: {exc}", C.yellow)
        self._wait_textarea(page, 8)

    def _boot(self, headless: bool, login_wait: int, announce: bool = False) -> bool:
        try:
            self.ctx = self._launch(headless)
            self.ctx.add_init_script(HOOK_JS)
            page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
            self._setup_page(page)
            self._goto_chat(page)
            self.scratch = page
            self.headless = headless
            if self._logged_in(page):
                return True
            if announce:
                print()
                print(C.bold("=" * 66))
                print(C.bold("  Please log in to DeepSeek in the opened Chrome window."))
                print(C.bold(f"  Waiting up to {login_wait // 60} minutes..."))
                print(C.bold("=" * 66))
            end = time.time() + login_wait
            last_report = 0.0
            while time.time() < end:
                try:
                    if self._logged_in(page):
                        self._did_login = self._did_login or announce
                        if announce:
                            log("[login] detected; session saved in the persistent profile.", C.green)
                            time.sleep(1.5)
                        return True
                except Exception:
                    pass
                if announce and time.time() - last_report > 15:
                    last_report = time.time()
                    log(f"  ...still waiting ({int(login_wait - (end - time.time()))}s)", C.dim)
                time.sleep(1.0)
            return False
        except Exception as exc:
            log(f"[startup] launch failed ({'headless' if headless else 'headed'}): {exc}", C.yellow)
            return False

    def start(self) -> bool:
        from playwright.sync_api import sync_playwright  # lazy: self-test needs no browser
        self.pw = sync_playwright().start()
        ok = False
        if HEADLESS_MODE != "0":
            log("[startup] trying real headless...", C.dim)
            ok = self._boot(True, HEADLESS_READY_TIMEOUT)
            if ok:
                log("[startup] headless session ready.", C.green)
        if not ok:
            self._close()
            log("[startup] opening a visible browser window...", C.dim)
            ok = self._boot(False, LOGIN_WAIT_SECONDS, announce=True)
            if ok and HEADLESS_MODE == "auto" and self._did_login:
                log("[startup] login saved; trying headless again...", C.dim)
                self._close()
                if self._boot(True, HEADLESS_READY_TIMEOUT):
                    log("[startup] headless session ready.", C.green)
                else:
                    self._close()
                    ok = self._boot(False, LOGIN_WAIT_SECONDS)
                    log("[startup] headless is not accepted by the site; keeping a visible window.", C.yellow)
            elif ok:
                log("[startup] session ready (visible window).", C.green)
        return ok

    def stop(self) -> None:
        self._close()
        try:
            if self.pw:
                self.pw.stop()
        except Exception:
            pass
        self.pw = None

    def restart(self) -> None:
        log("[browser] restarting browser session...", C.yellow)
        self._close()
        self.epoch += 1
        if not self._boot(self.headless, HEADLESS_READY_TIMEOUT):
            self._close()
            if not self._boot(False, HEADLESS_READY_TIMEOUT):
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
            raise BridgeError("DeepSeek login expired. Restart the bridge and log in again.", "login")
        if not self._find_textarea(page):
            raise BridgeError("chat input box not found (site layout changed or blocked)", "upstream")

    def open_session(self, page, sid: Optional[str]) -> bool:
        """Open an existing DeepSeek chat (by session id) in `page`."""
        if not sid:
            return False
        url = CHAT_URL.rstrip("/") + "/a/chat/s/" + sid
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            log(f"[browser] navigation warning: {exc}", C.yellow)
        if not self._wait_textarea(page, 12) or not self._has_token(page):
            return False
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
            return m.group(1) if m else None
        except Exception:
            return None

    def delete_chat(self, sid: str) -> bool:
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

    def _submit(self, page, sel: str, seq0: int, cancel) -> None:
        page.keyboard.press("Enter")
        t0 = time.time()
        pressed, clicked = 1, False
        while time.time() - t0 < SUBMIT_TIMEOUT:
            if cancel is not None and cancel.is_set():
                raise BridgeCancelled()
            if self._seq(page) > seq0:
                return
            el = time.time() - t0
            try:
                remaining = page.evaluate(JS_TA_LEN, sel)
            except Exception:
                remaining = -1
            if remaining == 0 and el < SUBMIT_TIMEOUT - 3:
                time.sleep(0.15)   # box already emptied: the site is submitting
                continue
            if el > 4 and pressed < 2:
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
                    kind = "login" if re.search(r"HTTP 40[13]", err) else "upstream"
                    raise BridgeError("DeepSeek: " + err, kind)
                if st.get("done"):
                    return {"text": text, "incomplete": bool(st.get("incomplete")), "seq": st["id"],
                            "sessionId": st.get("sessionId"), "status": st.get("status")}
            elif now - t_start > need_start:
                raise NotStarted("no generation started", "upstream")
            if now - last_progress > STALL_TIMEOUT:
                self._stop_generation(page)
                raise BridgeError(f"DeepSeek stalled for {STALL_TIMEOUT}s", "timeout")
            if now - t_start > MAX_REPLY_SECONDS:
                self._stop_generation(page)
                raise BridgeError("reply exceeded the maximum duration", "timeout")
            # While the model is silent (thinking) every poll is a wasted CDP round-trip.
            time.sleep(POLL_SECONDS if now - last_progress < 3 else max(POLL_SECONDS, 0.3))

    def _collect_dom(self, page, before: int, cancel, on_partial) -> str:
        """Fallback when the network hook is unavailable."""
        end = time.time() + MAX_REPLY_SECONDS
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
            time.sleep(POLL_SECONDS)
        raise BridgeError("timeout waiting for the reply (DOM mode)", "timeout")

    def exchange(self, page, prompt: str, cancel=None, on_partial=None) -> Exchange:
        if len(prompt) > MAX_PROMPT_CHARS + 20_000:
            raise BridgeError(f"prompt too large ({len(prompt):,} chars)", "bad_request")
        self.ensure_alive()
        if page.is_closed():
            raise BridgeError("the browser tab was closed", "upstream")
        if not self._has_token(page):
            raise BridgeError("DeepSeek login expired. Restart the bridge and log in again.", "login")
        gap = REQUEST_GAP_SECONDS - (time.time() - self._last_finished)
        if gap > 0:
            time.sleep(gap)
        t0 = time.perf_counter()
        sel = self._wait_textarea(page, 8)
        if not sel:
            raise BridgeError("chat input box not found", "upstream")
        dump_debug("prompt", prompt)
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
            self._submit(page, sel, seq0, cancel)
        else:
            page.keyboard.press("Enter")
        log(f"[send] {n:,} chars injected in {inj:.2f}s ({'hook' if hook else 'DOM fallback'})", C.dim)

        session_id: Optional[str] = None
        if hook:
            acc, seq_after = "", seq0
            for i in range(MAX_CONTINUES + 1):
                try:
                    r = self._run_wait(page, seq_after, cancel, on_partial, acc,
                                       need_start=SUBMIT_TIMEOUT if i == 0 else 15)
                except NotStarted:
                    if i == 0:
                        raise BridgeError("the message was sent but no reply started", "upstream")
                    break
                acc += r["text"]
                session_id = r["sessionId"] or session_id
                seq_after = r["seq"]
                if not (r["incomplete"] and acc.strip()) or i == MAX_CONTINUES:
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
        self.last_timings = {"prompt_chars": float(len(prompt)), "inject_s": inj,
                             "total_s": total, "reply_chars": float(len(text))}
        log(f"[reply] {len(text):,} chars in {total:.2f}s", C.green)
        return Exchange(text=text, session_id=session_id, seconds=total)


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
    def __init__(self, ds: DeepSeekWeb):
        self.ds = ds
        self.convs: List[Conversation] = []
        self.epoch = ds.epoch
        self.created_sessions: set = set()
        self.pending_delete: List[str] = []
        self.term_page = None
        self.term_ready = False

    # ---- housekeeping -----------------------------------------------------

    def _sync_epoch(self) -> None:
        if self.ds.epoch != self.epoch:
            self.convs.clear()
            self.term_page, self.term_ready = None, False
            self.epoch = self.ds.epoch

    def _schedule_delete(self, sid: Optional[str], force: bool = False) -> None:
        if sid and (DELETE_OLD_CHATS or force) and sid in self.created_sessions:
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
        sid = conv.session_id or (self.ds.session_of(conv.page) if conv.page is not None else None)
        if conv.page is not None:
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
        while len(hib) > MAX_KEPT_CONVS:
            oldest = min(hib, key=lambda c: c.last_used)
            hib.remove(oldest)
            self._drop(oldest)

    def _make_room(self, exclude: Optional[Conversation] = None) -> None:
        while True:
            live = [c for c in self.convs if c.page is not None and c is not exclude]
            if len(live) < MAX_TABS:
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

    def _new_conv(self) -> Conversation:
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

    def reset_all(self) -> int:
        n = len(self.convs)
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
        while problems and repairs < MAX_REPAIRS:
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

    # ---- main entry ---------------------------------------------------------

    def process(self, req: NormReq, cancel, on_partial) -> Outcome:
        self._sync_epoch()
        if req.side:
            return self._process_side(req, cancel, on_partial)
        conv = self._find_conv(req)
        budget = HISTORY_BUDGET_CHARS
        attempt = 0
        while True:
            if conv is not None and conv.page is None and not self._wake(conv):
                self._drop(conv)
                conv = None
            cont = conv is not None
            if cont:
                delta = req.messages[conv.n + 1:]
                prompt = build_delta_prompt(req, delta, tools_changed=(req.tools_sig != conv.tools_sig))
                if conv.chars_sent + len(prompt) > ROTATE_CHARS:
                    log(f"[conv {conv.cid}] chat is getting long; rotating to a fresh chat", C.yellow)
                    self._drop(conv)
                    conv, cont = None, False
            if not cont:
                conv = self._new_conv()
                prompt = build_full_prompt(req, budget)
            log(f"[conv {conv.cid}] {'CONTINUE +' + str(len(req.messages) - conv.n - 1) + ' msg' if cont else 'NEW chat, ' + str(len(req.messages)) + ' msg'}"
                f" -> prompt {len(prompt):,} chars", C.cyan)
            try:
                ex = self.ds.exchange(conv.page, prompt, cancel, on_partial if attempt == 0 else None)
                if not ex.text.strip():
                    raise BridgeError("DeepSeek returned an empty reply", "empty")
                break
            except BridgeCancelled:
                self._drop(conv)
                raise
            except BridgeError as exc:
                log(f"[conv {conv.cid}] {exc.kind}: {exc}", C.red)
                self._drop(conv)
                conv = None
                attempt += 1
                if exc.kind in ("login", "bad_request") or attempt > MAX_RETRIES:
                    raise
                if not cont and attempt <= 2:
                    budget = max(40_000, budget // 2)
                wait = min(RETRY_BACKOFF_MAX, 2 ** attempt * 2) if attempt > 1 else 0.5
                log(f"[retry {attempt}/{MAX_RETRIES}] waiting {wait:.0f}s before trying again", C.yellow)
                t_end = time.time() + wait
                while time.time() < t_end:
                    if cancel is not None and cancel.is_set():
                        raise BridgeCancelled()
                    time.sleep(0.5)
        if ex.session_id:
            conv.session_id = ex.session_id
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
        return Outcome(text=clean, calls=calls, stop_reason="tool_use" if calls else "end_turn")

    def _process_side(self, req: NormReq, cancel, on_partial) -> Outcome:
        self.ds.ensure_alive()
        page = self.ds.scratch
        self.ds.open_chat(page)
        prompt = build_full_prompt(req, HISTORY_BUDGET_CHARS)
        log(f"[side] scratch chat, prompt {len(prompt):,} chars", C.cyan)
        ex = self.ds.exchange(page, prompt, cancel, on_partial)
        if ex.session_id:
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
        if ex.session_id:
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
    def __init__(self) -> None:
        self._q: "queue.PriorityQueue" = queue.PriorityQueue()
        self._seq = itertools.count()
        self._ready = threading.Event()
        self.ok = False
        self.ds: Optional[DeepSeekWeb] = None
        self.engine: Optional[Engine] = None
        self._thread = threading.Thread(target=self._run, daemon=True, name="DeepSeekWorker")
        self._thread.start()
        self._ready.wait(timeout=LOGIN_WAIT_SECONDS + 120)

    def alive(self) -> bool:
        return self.ok and self._thread.is_alive()

    def _run(self) -> None:
        try:
            self.ds = DeepSeekWeb()
            self.ok = self.ds.start()
            if self.ok:
                self.engine = Engine(self.ds)
        except Exception as exc:
            log(f"[worker] initialization error: {exc}", C.red)
            traceback.print_exc()
            self.ok = False
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
        self._q.put((-1, next(self._seq), None))
        self._thread.join(timeout=20)


# ============================================================================
# HTTP API
# ============================================================================

BRIDGE: Optional[Bridge] = None
API_KEY: Optional[str] = None


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

    def _check_auth(self) -> bool:
        auth = self.headers.get("Authorization", "").strip()
        supplied = auth[7:].strip() if auth.lower().startswith("bearer ") else auth
        if not supplied:
            supplied = self.headers.get("x-api-key", "").strip()
        if not supplied:
            supplied = self.headers.get("anthropic-api-key", "").strip()
        if not API_KEY:
            return False
        return secrets.compare_digest(supplied.encode("utf-8", "ignore"), API_KEY.encode("utf-8"))

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
                if total > MAX_HTTP_BODY_BYTES:
                    raise ValueError(f"request body too large (> {MAX_HTTP_BODY_BYTES:,} bytes)")
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
        if n > MAX_HTTP_BODY_BYTES:
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
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Content-Length", "0")
            self.end_headers()
        except Exception:
            pass

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/health"):
            self._send_json(200, {"ok": True, "service": "deepseek-local-bridge", "version": VERSION})
        elif path == "/v1/models":
            self._send_json(200, {"object": "list", "data": [
                {"id": m, "object": "model", "type": "model", "display_name": m, "owned_by": "local"} for m in MODELS]})
        else:
            self._err(404, "not_found_error", f"unknown path: {path}")

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if not self._check_auth():
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
        in_tokens = estimate_tokens([req.system_text, req.messages, list(req.tools)])
        log(f"[http] {req.fmt} model={req.model} stream={req.stream} msgs={len(req.messages)} "
            f"tools={len(req.tools)} tool_choice={req.tool_choice.get('type', 'auto')}"
            f"{' side' if req.side else ''}", C.dim)

        # Quota / connectivity probes never touch the browser.
        if req.max_tokens is not None and req.max_tokens <= 1 and not req.tools:
            outcome = Outcome(text="ok", calls=[])
            if req.stream:
                self._open_sse()
                em = self._emitter(req, in_tokens)
                em.start()
                self._deliver(req, outcome, em, "", in_tokens)
            else:
                self._deliver(req, outcome, None, "", in_tokens)
            return

        if BRIDGE is None or not BRIDGE.ok:
            self._err(529, "overloaded_error", "bridge is not ready")
            return

        cancel = threading.Event()
        evq: "queue.Queue[str]" = queue.Queue()
        streamer = SafeTextStream(evq.put)
        fut = BRIDGE.submit(
            lambda eng: eng.process(req, cancel, streamer.update if req.stream else None),
            priority=PRIORITY_SIDE if req.side else PRIORITY_MAIN, cancel=cancel)
        emitter = None
        # Generous: a request may legitimately wait behind other long jobs.
        deadline = time.time() + MAX_REPLY_SECONDS * 3 + 300
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
                    if not BRIDGE.alive():
                        raise BridgeError("the DeepSeek worker thread stopped unexpectedly", "upstream")
                    if time.time() > deadline:
                        raise BridgeError("the request exceeded the overall time limit", "timeout")
                if self._client_gone():
                    raise ClientGone()
                if emitter and time.time() - last_write > 8:
                    emitter.ping()
                    last_write = time.time()
            outcome = fut.result()
            self._deliver(req, outcome, emitter, streamer.sent_text, in_tokens)
        except (ClientGone, ConnectionError, BrokenPipeError):
            cancel.set()
            log("[http] client disconnected; cancelling generation", C.yellow)
        except BridgeCancelled:
            pass
        except Exception as exc:
            cancel.set()                      # a queued / running job must not outlive its request
            code, etype = error_status(exc)
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

def start_server(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", int(port)), APIHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True, name="DeepSeekHTTP").start()
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
    print(f"    history budget / new chat : {HISTORY_BUDGET_CHARS:,} chars  (~{int(HISTORY_BUDGET_CHARS / CHARS_PER_TOKEN):,} tokens)")
    print(f"    hard prompt ceiling       : {MAX_PROMPT_CHARS:,} chars  (DS_BRIDGE_MAX_PROMPT_CHARS)")
    print(f"    max block in follow-ups   : {DELTA_BLOCK_LIMIT:,} chars  (DS_BRIDGE_DELTA_BLOCK_LIMIT)")
    print(f"    chat rotation             : {ROTATE_CHARS:,} chars")
    print(f"    max live tabs             : {MAX_TABS}  (older conversations hibernate, chats are kept; up to {MAX_KEPT_CONVS})")
    print(f"    stall / max reply         : {STALL_TIMEOUT}s / {MAX_REPLY_SECONDS}s   retries: {MAX_RETRIES} (backoff up to {RETRY_BACKOFF_MAX}s)")
    print(f"    delete old bridge chats   : {DELETE_OLD_CHATS}")
    print(f"    Claude Code mode          : {mode}  [{mode_src}]  (--mode safe|ask|auto, --set-mode to save)")
    print(f"    debug dir                 : {DEBUG_DIR or '(off)'}")
    print(f"    config file               : {CONFIG_PATH}")
    print()
    print(C.dim("  Type /help for terminal commands."))
    print()


def print_help() -> None:
    print(C.bold("\nCommands:"))
    for c, d in [("/help", "this help"), ("/key", "show API key"), ("/url", "show base URL"),
                 ("/status", "bridge status + live conversations"),
                 ("/new", "new terminal chat"), ("/reset", "forget all Claude Code conversations"),
                 ("/purge", "delete every chat this bridge created"), ("/exit", "quit"),
                 ("<text>", "chat directly with DeepSeek (keeps context)")]:
        print(f"  {C.cyan(c):<22} {d}")
    print()


def terminal_loop(cfg: Dict[str, Any], url: str) -> None:
    def run(fn):
        return BRIDGE.submit(fn, PRIORITY_MAIN).result(timeout=300)

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
                    print(f"  server : {url}\n  mode   : {'headless' if BRIDGE.ds.headless else 'visible window'}")
                    print(f"  timing : {BRIDGE.ds.last_timings}")
                    convs = run(lambda e: e.describe())
                    print("  conversations:" if convs else "  conversations: (none)")
                    for c in convs:
                        print("    " + c)
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

def self_test() -> None:
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
    global BRIDGE, API_KEY
    old_bridge, old_key = BRIDGE, API_KEY

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
                threading.Thread(target=run, daemon=True).start()
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

    API_KEY = "testkey"
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
        BRIDGE = _FakeBridge(dead=True)
        body = json.dumps({"model": "m", "max_tokens": 50,
                           "messages": [{"role": "user", "content": "hi"}]}).encode()
        t0 = time.time()
        r = http(port, head + b"Content-Length: %d\r\n\r\n" % len(body) + body)
        assert r.startswith(b"HTTP/1.1 529"), r[:80]
        assert time.time() - t0 < 5, "dead worker request hung"
        # 16d. streaming: no citation leak, text reconstructs exactly, tool call delivered
        BRIDGE = _FakeBridge()
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
        BRIDGE, API_KEY = old_bridge, old_key

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
    global DELTA_BLOCK_LIMIT
    old_dbl = DELTA_BLOCK_LIMIT
    try:
        DELTA_BLOCK_LIMIT = 150_000                 # independent of the user's environment
        assert len(build_delta_prompt(rq, big, False)) < 150_000 + 5_000
        DELTA_BLOCK_LIMIT = 0                       # 0 = "no cap" must really mean no cap
        assert len(build_delta_prompt(rq, big, False)) > 400_000
    finally:
        DELTA_BLOCK_LIMIT = old_dbl
    bq = Bridge.__new__(Bridge)

    class _DyingQueue(queue.PriorityQueue):
        def put(self, item, *a, **k):
            super().put(item, *a, **k)
            bq.ok = False                 # the worker dies right after the enqueue

    bq._q, bq._seq, bq.ok = _DyingQueue(), itertools.count(), True
    assert isinstance(bq.submit(lambda e: 1).exception(timeout=1), BridgeError)

    # 21. Launcher: modes, permission-flag detection, settings files, project folder choice.
    global CONFIG_PATH
    import tempfile
    old_cfg_path = CONFIG_PATH
    old_env_mode = os.environ.pop("DS_BRIDGE_MODE", None)
    with tempfile.TemporaryDirectory() as td:
        CONFIG_PATH = Path(td) / "cfg.json"
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
            # ask: nothing added
            assert permission_args("ask", []) == []
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
        finally:
            CONFIG_PATH = old_cfg_path
            if old_env_mode is not None:
                os.environ["DS_BRIDGE_MODE"] = old_env_mode

    print(C.green("[self-test] all tests passed."))



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


def safe_settings() -> Dict[str, Any]:
    return {"permissions": {
        "defaultMode": "acceptEdits",
        "allow": [f"Bash({c}:*)" for c in _SAFE_BASH_ALLOW] + [f"Bash({c})" for c in _SAFE_BASH_ALLOW_EXACT],
        "deny": [f"Bash({c}:*)" for c in _SAFE_BASH_DENY] + [f"Bash({c})" for c in _SAFE_BASH_DENY_WILDCARD],
    }}


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


KEEP_GOING = _env_bool("DS_BRIDGE_KEEP_GOING", True)
KEEP_GOING_MAX = _env_int("DS_BRIDGE_KEEP_GOING_MAX", 400)

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
        text = _KEEP_GOING_SCRIPT.replace("__MAX__", str(KEEP_GOING_MAX))
        if not script.exists() or script.read_text(encoding="utf-8") != text:
            script.write_text(text, encoding="utf-8")
    except Exception as exc:
        _warn_once("keepgoing", f"could not write the keep-going hook ({exc})")
        return {}
    cmd = f'"{Path(sys.executable).as_posix()}" "{script.as_posix()}"'
    return {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": cmd, "timeout": 30}]}]}}


def _settings_path(name: str) -> Path:
    return CONFIG_PATH.with_name(f".deepseek_bridge_claude_{name}.json")


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
        return []
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
        if KEEP_GOING and not has_settings:
            sf = _write_json_once(_settings_path("auto"), keep_going_settings())
            if sf:
                args += ["--settings", sf]
        return args
    args = ["--dangerously-skip-permissions"]
    if not has_settings:
        # Pre-accepts Claude Code's one-time "bypass permissions" warning screen.
        conf: Dict[str, Any] = {"skipDangerousModePermissionPrompt": True}
        if KEEP_GOING:
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
    global BRIDGE, API_KEY
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
            threading.Thread(target=run, daemon=True).start()
            return fut

    old_bridge, old_key = BRIDGE, API_KEY
    BRIDGE, API_KEY = _Bridge(), "verify-key"           # type: ignore[assignment]
    server = start_server(0)
    print(C.bold(f"[verify-safe] {ver or 'claude'}  |  {len(cases)} scenarios  |  this takes about a minute"))
    try:
        # Clean-room environment: no stray CLAUDE_* / ANTHROPIC_* variables and a throw-away home, so
        # the person's own ~/.claude settings cannot change the result. (An organisation's managed
        # policy settings, if any, still apply - that is what Claude Code enforces on this machine.)
        home = tempfile.mkdtemp(prefix="dsb_verify_home_")
        made.append(Path(home))
        ours = claude_env({"api_key": API_KEY}, f"http://127.0.0.1:{server.server_address[1]}")
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
        BRIDGE, API_KEY = old_bridge, old_key

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
    """Everything the old .bat did, but only when something is really missing."""
    global BROWSER_CHANNEL
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
        BROWSER_CHANNEL = ""                      # no Chrome: use Playwright's own Chromium
        if not cfg.get("chromium_installed"):
            print(C.yellow("[setup] Google Chrome not found; installing Playwright Chromium..."), flush=True)
            if not _run([sys.executable, "-m", "playwright", "install", "chromium"]):
                print(C.red("[setup] could not install a browser. Install Google Chrome and retry."))
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


def bridge_already_running(port: int) -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1.5) as r:
            return bool(json.loads(r.read().decode("utf-8", "replace")).get("ok"))
    except Exception:
        return False


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    global BRIDGE, API_KEY, DEBUG_DIR, HEADLESS_MODE, LOG_FILE
    ap = argparse.ArgumentParser(
        description=f"DeepSeek V{VERSION} bridge. By default it starts the bridge AND Claude Code in this window.",
        epilog="Unknown arguments are passed to Claude Code (e.g. --continue, --resume).")
    ap.add_argument("project", nargs="?", help="project folder for Claude Code (drag a folder onto this file)")
    ap.add_argument("--terminal", action="store_true", help="bridge only, with the interactive terminal (no Claude Code)")
    ap.add_argument("--choose-project", action="store_true", help="pick the project folder again")
    ap.add_argument("--here", action="store_true",
                    help="use the folder that contains this .py file as the project folder")
    ap.add_argument("--mode", type=_mode_arg, metavar="{safe,ask,auto}",
                    help="Claude Code permission mode for this run: safe = free inside the project folder "
                         "(default), ask = normal prompts, auto = fully autonomous")
    ap.add_argument("--safe", dest="mode", action="store_const", const="safe", help="same as --mode safe")
    ap.add_argument("--ask", dest="mode", action="store_const", const="ask", help="same as --mode ask")
    ap.add_argument("--auto", "--autonomous", dest="mode", action="store_const", const="auto",
                    help="same as --mode auto")
    ap.add_argument("--set-mode", type=_mode_arg, metavar="{safe,ask,auto}",
                    help="save the default permission mode in the config file and continue")
    ap.add_argument("--prompt-file", metavar="FILE",
                    help="a long task prompt: copied into the project as AUTONOMOUS_PROMPT.md and Claude Code is "
                         "started with a short instruction to read and execute it (terminals truncate big pastes)")
    ap.add_argument("--port", type=int, help="local HTTP port")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="run offline regression tests and exit")
    ap.add_argument("--verify-safe", action="store_true",
                    help="run the real Claude Code against a fake model and check that safe mode holds, then exit")
    ap.add_argument("--headed", action="store_true", help="always use a visible browser window")
    ap.add_argument("--debug-dir", help="dump every prompt / raw reply into this directory")
    ap.add_argument("--version", action="version", version=f"deepseek-local-bridge {VERSION}")
    args, claude_extra = ap.parse_known_args()
    if args.port is not None and not (1 <= args.port <= 65535):
        ap.error("--port must be between 1 and 65535")

    if args.no_color:
        C.enable(False)
    if args.self_test:
        self_test()
        return 0
    if args.verify_safe:
        return verify_safe()
    if args.headed:
        HEADLESS_MODE = "0"
    if args.debug_dir:
        DEBUG_DIR = args.debug_dir

    cfg = load_config()
    if args.port:
        cfg["port"] = args.port
        save_config(cfg)
    if args.set_mode:
        cfg["permission_mode"] = args.set_mode
        save_config(cfg)
        print(C.green(f"[mode] default permission mode saved: {args.set_mode}  ({CONFIG_PATH})"))
    mode, mode_src = resolve_mode(args.mode or args.set_mode, cfg)
    if args.set_mode and not args.mode:
        mode_src = "--set-mode"
    API_KEY = cfg["api_key"]

    if os.name == "nt":
        os.system("title DeepSeek Bridge + Claude Code")
    project = None
    if not args.terminal:
        project = pick_project_dir(cfg, args.project, args.choose_project, args.here)
    if args.prompt_file and project is not None:
        try:
            src_text = Path(args.prompt_file).expanduser().read_text(encoding="utf-8-sig")
            target = Path(project) / "AUTONOMOUS_PROMPT.md"
            if not target.exists() or target.read_text(encoding="utf-8") != src_text:
                target.write_text(src_text, encoding="utf-8")
            claude_extra.append("Read AUTONOMOUS_PROMPT.md completely (it is the full specification) and execute it "
                                "now, fully autonomously. Never ask me anything. Keep PROGRESS.md up to date; if you "
                                "are ever unsure where you are, re-read AUTONOMOUS_PROMPT.md and PROGRESS.md.")
            print(C.green(f"[prompt] {len(src_text):,} chars -> {target}"))
        except Exception as exc:
            print(C.red(f"[prompt] cannot use --prompt-file: {exc}"))
            return 1
    if not ensure_dependencies(cfg, need_claude=not args.terminal):
        return 1
    if not args.terminal and bridge_already_running(int(cfg["port"])):
        # A second double-click: reuse the running bridge, just open another Claude Code.
        print(C.green(f"Bridge already running on port {cfg['port']}; starting another Claude Code."))
        print(C.dim(f"Project: {project}\nPermissions: {permission_mode_text(mode, mode_src, claude_extra)}"))
        return launch_claude(cfg, f"http://127.0.0.1:{cfg['port']}", project, claude_extra, mode)

    log("[main] starting DeepSeek worker (a browser may open for login)...", C.dim)
    BRIDGE = Bridge()
    if not BRIDGE.ok:
        log("[error] could not start the DeepSeek browser session / login.", C.red)
        return 1

    try:
        server = start_server(cfg["port"])
    except OSError as exc:
        log(f"[server error] cannot listen on 127.0.0.1:{cfg['port']} ({exc}). "
            f"Another bridge may already be running - close it or use --port <other>.", C.red)
        BRIDGE.stop()
        return 1
    except Exception as exc:
        log(f"[server error] {exc}", C.red)
        BRIDGE.stop()
        return 1

    url = f"http://127.0.0.1:{cfg['port']}"
    try:
        if args.terminal:
            print_banner(cfg, url, mode, mode_src)
            terminal_loop(cfg, url)
            return 0
        logpath = SCRIPT_DIR / "bridge.log"
        print(C.green(f"Bridge ready on {url}"))
        print(C.dim(f"Project: {project}\nPermissions: {permission_mode_text(mode, mode_src, claude_extra)}\n"
                    f"Bridge log: {logpath}\nStarting Claude Code..."))
        try:                                        # simple rotation: bridge.log -> bridge.log.1 above 5 MB
            if logpath.exists() and logpath.stat().st_size > 5 * 1024 * 1024:
                os.replace(logpath, logpath.with_suffix(".log.1"))
        except OSError:
            pass
        LOG_FILE = open(logpath, "a", encoding="utf-8", errors="replace")
        old_stderr = sys.stderr
        sys.stderr = LOG_FILE                       # tracebacks must not paint over Claude's UI
        try:
            code = launch_claude(cfg, url, project, claude_extra, mode)
        finally:
            sys.stderr = old_stderr
            lf, LOG_FILE = LOG_FILE, None
            try:
                lf.close()
            except Exception:
                pass
        return code
    finally:
        stop_server(server)
        BRIDGE.stop()


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
