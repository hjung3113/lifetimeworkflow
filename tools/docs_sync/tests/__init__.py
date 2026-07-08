"""Tests for the docs_sync member (DOCS-03). `tools` is a namespace package (no tools/__init__.py);
pytest's prepend import mode inserts the repo root, so `import tools.docs_sync...` resolves."""
