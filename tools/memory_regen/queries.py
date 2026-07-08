"""Per-language tree-sitter tags queries + the parse layer (MEM-03, Task 1, RESEARCH Pattern 1).

This module owns the FIRST stage of the repo-map: turn a source file into ``def``/``ref`` symbol
names. It deliberately uses the tree-sitter **0.25** API — ``tree_sitter.Query(lang, s)`` +
``tree_sitter.QueryCursor(query).captures(root)`` — and NEVER the removed 0.24-era
``Language.query(s).captures(node)`` chain (Pitfall 3 / RESEARCH §State of the Art: that path throws
``AttributeError`` on 0.25). Grammars load from the pinned individual wheels (``tree_sitter_python``,
``tree_sitter_c_sharp``, ``tree_sitter_bash``) — NOT ``tree-sitter-language-pack`` (which downloads
parser binaries at runtime, breaking determinism + offline/ephemeral operation; T-02-SC).

``LANGUAGES`` maps a language name → (grammar module, file extensions, tags query). ``parse_symbols``
runs the query for one file and returns ``{"def": [...names], "ref": [...names]}``. The repo-map
(``repo_map.py``) walks the tree, resolves each file's language via :func:`lang_for_path`, and builds
a def/ref graph from these captures.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tree_sitter as ts
import tree_sitter_bash
import tree_sitter_c_sharp
import tree_sitter_python


@dataclass(frozen=True)
class LangSpec:
    """A language's grammar module, file extensions, and def/ref tags query."""

    module: object
    extensions: tuple[str, ...]
    query: str


# Per-language tags queries. Each captures @def (definitions that name a file's symbols) and @ref
# (references to symbols defined elsewhere) — the two edges the PageRank graph is built from. Kept
# minimal + robust: over-broad queries are noisier but never crash; missing a construct only weakens
# ranking, never breaks determinism.
_PYTHON_QUERY = (
    "(function_definition name: (identifier) @def)\n"
    "(class_definition name: (identifier) @def)\n"
    "(call function: (identifier) @ref)\n"
    "(call function: (attribute attribute: (identifier) @ref))"
)

_C_SHARP_QUERY = (
    "(method_declaration name: (identifier) @def)\n"
    "(class_declaration name: (identifier) @def)\n"
    "(interface_declaration name: (identifier) @def)\n"
    "(invocation_expression function: (identifier) @ref)\n"
    "(invocation_expression function: (member_access_expression name: (identifier) @ref))"
)

_BASH_QUERY = (
    "(function_definition name: (word) @def)\n"
    "(command name: (command_name (word) @ref))"
)


LANGUAGES: dict[str, LangSpec] = {
    "python": LangSpec(tree_sitter_python, (".py",), _PYTHON_QUERY),
    "c_sharp": LangSpec(tree_sitter_c_sharp, (".cs",), _C_SHARP_QUERY),
    "bash": LangSpec(tree_sitter_bash, (".sh",), _BASH_QUERY),
}

# Extension → language-name lookup (lower-cased suffix), built once from LANGUAGES.
_EXT_TO_LANG: dict[str, str] = {
    ext: name for name, spec in LANGUAGES.items() for ext in spec.extensions
}


def lang_for_path(path: str | Path) -> str | None:
    """Resolve a file path to a language name via its extension, or ``None`` if unmapped."""
    return _EXT_TO_LANG.get(Path(path).suffix.lower())


def parse_symbols(path: str | Path, lang_name: str) -> dict[str, list[str]]:
    """Parse one source file → ``{"def": [...names], "ref": [...names]}`` (0.25 QueryCursor API).

    Loads the grammar from its pinned wheel, parses the file's bytes, and runs the language's tags
    query through ``tree_sitter.QueryCursor(query).captures(root)`` — the tree-sitter 0.25 seam
    (Pattern 1). Capture node text is decoded via ``node.text.decode()``. Always returns both keys
    (empty lists when a language exposes no refs), so callers never key-check.
    """
    spec = LANGUAGES[lang_name]
    lang = ts.Language(spec.module.language())
    parser = ts.Parser(lang)
    src_bytes = Path(path).read_bytes()
    tree = parser.parse(src_bytes)
    query = ts.Query(lang, spec.query)
    captures = ts.QueryCursor(query).captures(tree.root_node)
    return {
        "def": [n.text.decode("utf-8", "replace") for n in captures.get("def", [])],
        "ref": [n.text.decode("utf-8", "replace") for n in captures.get("ref", [])],
    }
