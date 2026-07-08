# Recorded converter outputs (.NET-free comparison proof)

These files are **recorded** stand-ins for the byte-exact output the .NET toy converter emits for
each golden case's `input/seed.tsv` (no-BOM / LF, cells normalized per §4-5). They exist so the
golden-runner's **normalize + diff + `.received`** comparison path (`runner.compare`) is proven
green in pure Python even while the live `dotnet` spawn is DEFERRED in this container (.NET 10
egress-blocked — see `01-06-SUMMARY.md`).

Because the .NET and Python §4-5 cores implement the SAME rules and are cross-validated by
`libs/normalize-fixtures/` (D-04), these recorded outputs equal what a live `dotnet run` produces.
When .NET 10 is available, `test_repr_only.py` / `test_value_regression.py` exercise the identical
comparison via a real spawn — the recorded path stays as a fast, runtime-free regression guard.

- `repr-only.converter-output.tsv` — equals the approved baseline → `compare` returns PASS.
- `value-regression.converter-output.tsv` — param_value 9.99 (baseline 1.5) → `compare` returns FAIL.
