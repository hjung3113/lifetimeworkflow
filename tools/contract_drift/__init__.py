"""Contract-drift gate (CONTRACT-04, D-07): manifest-vs-baseline diff + breaking classification.

Recomputes the live JCS SHA-256 manifest via ``tools.contract_hash``, diffs it against the
committed baseline ``contracts/.hashes/manifest.json``, and classifies each drifted schema
breaking vs non-breaking. Because the manifest covers ``format-conventions.schema.json``, a §4-5
convention flip trips this gate exactly like a column reorder (PITFALLS P14).
"""
