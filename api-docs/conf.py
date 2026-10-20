"""Sphinx configuration for entra-id-auth-example documentation."""

import sys
from pathlib import Path

# Add src to path for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Project information
project = "entra-id-auth-example"
copyright = "2024"  # noqa: A001
author = ""

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML output options
html_theme = "sphinx_rtd_theme"

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_class_signature = "separated"
typehints_use_signature = True
typehints_use_signature_return = True

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
# Attributes セクションを :ivar: で出力し、dataclass のフィールドとの重複定義を避ける
napoleon_use_ivar = True

# Suppress warnings
suppress_warnings = ["ref.python", "autodoc"]
