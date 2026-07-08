"""Python-only JCS (RFC 8785) canonicalize + SHA-256 contract-schema hasher (CONTRACT-04, D-07).

This is the FIRST of two canonicalizers and is entirely separate from the §4-5 TSV comparator
(RESEARCH Pattern 1 / Pitfall 1): JCS runs on JSON *contract text*, is Python-only (``rfc8785``),
and needs zero .NET code. The manifest it produces covers ``format-conventions.schema.json`` so a
§4-5 convention flip (e.g. ``bom`` false→true) bumps the drift hash exactly like a column reorder
(PITFALLS P14).
"""
