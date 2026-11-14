"""Root entry point for HealthTriage application.

Usage:
    python -m streamlit run app.py
"""

import importlib
import sys
from pathlib import Path

# Ensure root directory is on sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Reload UI modules to ensure fresh code execution
import src.ui.styles
importlib.reload(src.ui.styles)

import src.ui.components.patient_form
importlib.reload(src.ui.components.patient_form)

import src.ui.components.triage_display
importlib.reload(src.ui.components.triage_display)

import src.ui.components.audit_trace
importlib.reload(src.ui.components.audit_trace)

import src.ui.components.hypothesis_view
importlib.reload(src.ui.components.hypothesis_view)

import src.ui.components.knowledge_viewer
importlib.reload(src.ui.components.knowledge_viewer)

import src.ui.app
importlib.reload(src.ui.app)

# Execute main application directly
src.ui.app.main()
