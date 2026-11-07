"""
prototype/core/llm_service.py — Grounded Gemini generation for the AI Sustainability Research Assistant.

Design (hybrid / retrieval-grounded):
  1. Deterministic handlers in copilot_service retrieve the relevant platform data
     (CSV tables, metrics, evidence records).
  2. That data is numbered [E1], [E2], ... and passed to Gemini as the ONLY allowed source.
  3. Gemini writes a free-form answer that cites the evidence IDs.
  4. On any failure (no key, no network, quota, bad model), generate() returns None and the
     caller falls back to the deterministic answer, so the demo can never break.

API key resolution order: explicit argument -> GEMINI_API_KEY / GOOGLE_API_KEY env var ->
Streamlit secrets. Keys are never written to disk by this module.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

MODEL_CANDIDATES_DEFAULT = ["gemini-flash-latest", "gemini-2.5-flash"]
REQUEST_TIMEOUT_MS = 30_000

SYSTEM_INSTRUCTION = """You are the AI Sustainability Research Assistant inside the Apetit Climate & Nature Navigator,
a decision platform for a Nordic food company (frozen vegetables, contract farming in Finland and Sweden).

STRICT GROUNDING RULES:
- Answer ONLY from the DATA CONTEXT provided in the prompt. Never use outside facts, numbers or company knowledge.
- Every number you state must appear in the data context. Do not compute new figures unless it is a simple,
  clearly shown difference or ratio of numbers in the context.
- Cite evidence inline using the evidence IDs given, e.g. [E1] or [E2, E3].
- If the data context does not contain enough information to answer, say so plainly and state which data
  would be needed. Do not guess.
- The platform runs on a calibrated synthetic (fictional) demonstration dataset. Do not present it as real
  Apetit confidential data.

ANSWER FORMAT (Markdown, concise, executive-friendly, max ~220 words):
1. A direct 1–2 sentence answer first.
2. "**Why?**" followed by 2–4 short bullet points, each with a citation.
3. If relevant, one "**Trade-off to watch:**" line (interconnected effects on water, energy, cost, biodiversity, growers).
4. One "**Recommended next step:**" line.
Do not use headings larger than bold text. Do not use the dollar sign; write EUR or € for currency."""


def _resolve_api_key(explicit: Optional[str] = None) -> Optional[str]:
    if explicit and explicit.strip():
        return explicit.strip()
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(var)
        if val and val.strip():
            return val.strip()
    try:
        import streamlit as st  # local import: service must work outside Streamlit too

        for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            if var in st.secrets and str(st.secrets[var]).strip():
                return str(st.secrets[var]).strip()
    except Exception:
        pass
    return None


def _compact(value: Any, max_chars: int = 6000) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= max_chars else text[:max_chars] + " …[truncated]"


class LLMService:
    """Thin, failure-tolerant wrapper around the google-genai SDK."""

    _client_cache: Dict[str, Any] = {}
    _working_model: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = _resolve_api_key(api_key)
        env_model = os.environ.get("GEMINI_MODEL", "").strip()
        self.model_candidates: List[str] = ([env_model] if env_model else []) + [
            m for m in MODEL_CANDIDATES_DEFAULT if m != env_model
        ]
        self.last_error: Optional[str] = None
        self.last_model: Optional[str] = None

    # ── Availability ─────────────────────────────────────────────────────────
    @staticmethod
    def sdk_installed() -> bool:
        try:
            import google.genai  # noqa: F401

            return True
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        return bool(self.api_key) and self.sdk_installed()

    def _client(self):
        from google import genai
        from google.genai import types

        if self.api_key not in self._client_cache:
            self._client_cache[self.api_key] = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
            )
        return self._client_cache[self.api_key]

    # ── Prompt construction ──────────────────────────────────────────────────
    @staticmethod
    def build_context(res: Dict[str, Any]) -> str:
        """Serialise a deterministic research result into a numbered evidence context."""
        parts: List[str] = []
        parts.append(f"RESEARCH CATEGORY: {res.get('category', 'General')}")

        evidence = res.get("evidence", []) or []
        for i, ev in enumerate(evidence, start=1):
            parts.append(
                f"[E{i}] {ev.get('dataset_name')} — file {ev.get('file_path')} "
                f"({ev.get('records_analyzed')} records). Basis: {ev.get('formula')}. "
                f"Standard: {ev.get('standard_ref')}. Extract: {ev.get('sample_snippet')}"
            )

        if res.get("metrics"):
            parts.append("KEY METRICS (computed from the evidence above): " + _compact(res["metrics"], 1500))
        if res.get("why"):
            parts.append("ANALYST FINDINGS (deterministic, from the evidence above):\n- " + "\n- ".join(map(str, res["why"])))
        if res.get("table_data"):
            parts.append("DATA TABLE ROWS: " + _compact(res["table_data"][:40], 7000))
        if res.get("extra_context"):
            parts.append("ADDITIONAL PLATFORM DATA:\n" + str(res["extra_context"]))
        return "\n\n".join(parts)

    @staticmethod
    def _history_block(history: Optional[List[Dict[str, str]]]) -> str:
        if not history:
            return ""
        lines = []
        for turn in history[-6:]:
            role = "User" if turn.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {str(turn.get('content', ''))[:600]}")
        return "RECENT CONVERSATION (for follow-up context only, not a data source):\n" + "\n".join(lines) + "\n\n"

    # ── Generation ───────────────────────────────────────────────────────────
    def generate(
        self,
        query: str,
        res: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        """Return a grounded Markdown answer, or None if Gemini is unavailable/failed."""
        self.last_error = None
        if not self.is_available:
            self.last_error = "No Gemini API key configured" if self.sdk_installed() else "google-genai not installed"
            return None

        from google.genai import errors, types

        prompt = (
            self._history_block(history)
            + "DATA CONTEXT:\n"
            + self.build_context(res)
            + f"\n\nUSER QUESTION: {query}\n\nWrite the answer now, following the grounding rules and format."
        )
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
            max_output_tokens=1200,
        )

        candidates = ([LLMService._working_model] if LLMService._working_model else []) + [
            m for m in self.model_candidates if m != LLMService._working_model
        ]
        for model in candidates:
            try:
                resp = self._client().models.generate_content(model=model, contents=prompt, config=config)
                text = (resp.text or "").strip()
                if not text:
                    self.last_error = f"Empty response from {model}"
                    continue
                LLMService._working_model = model
                self.last_model = model
                return text
            except errors.ClientError as exc:
                self.last_error = f"{model}: {getattr(exc, 'code', '')} {getattr(exc, 'message', exc)}"
                # 404 = model name not available for this key -> try next candidate; anything else is fatal
                if getattr(exc, "code", None) == 404:
                    continue
                return None
            except Exception as exc:  # network, timeout, server errors
                self.last_error = f"{model}: {type(exc).__name__}: {exc}"
                return None
        return None

