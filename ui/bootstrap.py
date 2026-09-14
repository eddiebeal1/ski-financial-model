"""Shared Streamlit bootstrap: page config + SessionStore access.

Imported by ``app.py`` and every page under ``pages/`` so setup logic lives in one
place instead of being duplicated per page.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow `import skimodel` without a package install (src/ layout).
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from skimodel.persistence.store import SessionStore  # noqa: E402


def configure_page(title: str, icon: str = "🎿") -> None:
    st.set_page_config(page_title=f"{title} | Ski Resort Capital Planner", page_icon=icon, layout="wide")


def get_store() -> SessionStore:
    """Return the singleton SessionStore for this browser session."""

    return SessionStore(st.session_state)
