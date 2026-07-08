"""RED stub — implementation lands in the GREEN commit."""

from __future__ import annotations


def load_matrix(path: str = "harness/permission-matrix.json") -> dict:
    raise NotImplementedError


def resolve_bash(rules: dict, command: str, default: str = "ask") -> str:
    raise NotImplementedError


def resolve_path(deny_globs: list, path: str) -> str:
    raise NotImplementedError
