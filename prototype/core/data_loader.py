"""
core/data_loader.py — Cached data loader wrapping ccn_tools.io
All raw tables are loaded once and cached for the Streamlit session.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


def _ensure_tools(root: Path) -> None:
    tools = root / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))


@st.cache_resource(show_spinner="Loading dataset …")
def load_raw(root: Path) -> dict:
    """Load all raw tables via ccn_tools.io.load_raw()."""
    _ensure_tools(root)
    from ccn_tools import io as IO  # noqa: PLC0415
    IO.DEFAULT_ROOT = root  # point to the actual dataset root
    return IO.load_raw()


@st.cache_resource(show_spinner="Building canonical tables …")
def load_canonical(root: Path) -> dict:
    """Return naive-canonical tables (pre-correction) for quick inspection."""
    _ensure_tools(root)
    from ccn_tools import io as IO  # noqa: PLC0415
    IO.DEFAULT_ROOT = root
    raw = load_raw(root)
    return IO.naive_canonical(raw)

