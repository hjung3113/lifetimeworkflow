using System.Globalization;
using System.Text;
using Normalize;

namespace ToyConverter;

/// <summary>
/// Fixture-grade converter (D-02): reads a seed TSV via <c>--in</c>, normalizes each cell through
/// the SHARED §4-5 <see cref="Normalizer"/> core (no real parse/correction logic), and writes the
/// result to <c>--out</c> as no-BOM / LF. This is the "new" producer of the A-model boundary —
/// the Python golden-runner spawns it via <c>subprocess.run([...], shell=False)</c> and diffs the
/// normalized <c>--out</c> file against the approved <c>golden/</c> baseline.
///
/// Exit-code contract (integration_contracts §4.5):
///   0 = success, 2 = bad args, 3 = path traversal / confinement violation, 4 = IO/parse failure.
/// </summary>
internal static class Program
{
    private static readonly UTF8Encoding Utf8NoBom = new(encoderShouldEmitUTF8Identifier: false);

    private static int Main(string[] args)
    {
        string? inPath = null;
        string? outPath = null;

        // Minimal --in/--out arg parse (fixture-grade; no arg library).
        for (var i = 0; i < args.Length - 1; i++)
        {
            switch (args[i])
            {
                case "--in":
                    inPath = args[++i];
                    break;
                case "--out":
                    outPath = args[++i];
                    break;
            }
        }

        if (string.IsNullOrEmpty(inPath) || string.IsNullOrEmpty(outPath))
        {
            Console.Error.WriteLine("usage: toy-converter --in <seed.tsv> --out <output.tsv>");
            return 2;
        }

        // T-06-02 — resolve + confine both paths to the workspace or the system temp area; reject
        // traversal that escapes (e.g. ../../etc/passwd). The runner writes --out under pytest's
        // tmp dir, so the temp root is an allowed sink alongside the repo working directory.
        string fullIn, fullOut;
        try
        {
            fullIn = Path.GetFullPath(inPath);
            fullOut = Path.GetFullPath(outPath);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"invalid path: {ex.Message}");
            return 3;
        }

        if (!IsConfined(fullIn) || !IsConfined(fullOut))
        {
            Console.Error.WriteLine("path confinement violation: --in/--out must stay within the workspace or temp area");
            return 3;
        }

        try
        {
            var raw = File.ReadAllBytes(fullIn);
            var normalized = Convert(raw);
            var outDir = Path.GetDirectoryName(fullOut);
            if (!string.IsNullOrEmpty(outDir))
            {
                Directory.CreateDirectory(outDir);
            }

            // no-BOM + explicit LF (Convert already joins on "\n"); write raw bytes to avoid any
            // platform newline/encoding surprise.
            File.WriteAllBytes(fullOut, Utf8NoBom.GetBytes(normalized));
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"conversion failed: {ex.Message}");
            return 4;
        }
    }

    /// <summary>
    /// Parse the seed TSV, normalize each data cell by its column kind via the shared core, and
    /// re-emit rows in input order (the runner sorts rows during its own normalization). The
    /// header row passes through unchanged; its names drive the per-column kind map.
    /// </summary>
    private static string Convert(byte[] raw)
    {
        // R1 (BOM strip) + R2 (LF) via the shared core, then split into logical rows.
        var canonicalText = StripBomAndLf(raw);
        var lines = canonicalText.Split('\n');

        // Drop a single trailing empty line produced by a final newline.
        var end = lines.Length;
        if (end > 0 && lines[end - 1].Length == 0)
        {
            end--;
        }

        if (end == 0)
        {
            return string.Empty;
        }

        var header = lines[0].Split('\t');
        var kinds = new string[header.Length];
        for (var c = 0; c < header.Length; c++)
        {
            kinds[c] = KindFor(header[c]);
        }

        var outRows = new List<string>(end) { lines[0] }; // header verbatim
        for (var r = 1; r < end; r++)
        {
            var cells = lines[r].Split('\t');
            for (var c = 0; c < cells.Length; c++)
            {
                var kind = c < kinds.Length ? kinds[c] : "string";
                cells[c] = Normalizer.NormalizeCell(cells[c], kind);
            }

            outRows.Add(string.Join('\t', cells));
        }

        return string.Join('\n', outRows) + '\n';
    }

    /// <summary>
    /// Map a standard-log column name to a §4-5 cell kind. Fixture-grade: keyed to the seeded
    /// standard-log spec (timestamp=datetime, param_value=decimal, everything else=string). Real
    /// column typing comes from the contract schema in a later phase — out of scope here (D-02).
    /// </summary>
    private static string KindFor(string columnName) => columnName switch
    {
        "timestamp" => "datetime",
        "param_value" => "decimal",
        _ => "string",
    };

    private static string StripBomAndLf(byte[] raw)
    {
        var offset = 0;
        if (raw.Length >= 3 && raw[0] == 0xEF && raw[1] == 0xBB && raw[2] == 0xBF)
        {
            offset = 3;
        }

        var text = Utf8NoBom.GetString(raw, offset, raw.Length - offset);
        return text.Replace("\r\n", "\n").Replace("\r", "\n");
    }

    /// <summary>
    /// True when <paramref name="fullPath"/> resolves under the current working directory
    /// (the repo/workspace root the runner spawns from) or the system temp area.
    ///
    /// Both sides are reduced to their REAL path first, so the decision is made on the canonical
    /// path rather than on a spelling of it. On macOS <c>/var</c> is a symlink to
    /// <c>/private/var</c>, so pytest's tmp dir and <see cref="Path.GetTempPath"/> are two
    /// spellings of one directory and a raw comparison falsely trips. Canonicalizing does not
    /// relax the guard — the comparison stays Ordinal, and a genuine escape (e.g. ../../etc/passwd)
    /// still lands outside every root and is refused.
    /// </summary>
    private static bool IsConfined(string fullPath)
    {
        var realPath = RealPath(fullPath);
        var roots = new[]
        {
            RealPath(Directory.GetCurrentDirectory()),
            RealPath(Path.GetTempPath()),
        };

        foreach (var root in roots)
        {
            var normalizedRoot = root.EndsWith(Path.DirectorySeparatorChar)
                ? root
                : root + Path.DirectorySeparatorChar;
            if (realPath.Equals(root, StringComparison.Ordinal) ||
                realPath.StartsWith(normalizedRoot, StringComparison.Ordinal))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Resolve <paramref name="path"/> to its real path by following any symlinked component,
    /// walking root → leaf. Components that do not exist yet (the <c>--out</c> file, its parent)
    /// are simply appended — a not-yet-created path still gets its existing ancestors canonicalized.
    /// Any failure degrades to the plain full path, which is the strict (never more permissive)
    /// answer.
    /// </summary>
    private static string RealPath(string path)
    {
        var full = Path.GetFullPath(path);
        try
        {
            var root = Path.GetPathRoot(full);
            if (string.IsNullOrEmpty(root))
            {
                return full;
            }

            var current = root;
            var segments = full[root.Length..]
                .Split(Path.DirectorySeparatorChar, StringSplitOptions.RemoveEmptyEntries);

            foreach (var segment in segments)
            {
                current = Path.Combine(current, segment);

                // returnFinalTarget: true collapses a symlink chain in one call; null = not a link.
                var target = Directory.Exists(current)
                    ? Directory.ResolveLinkTarget(current, returnFinalTarget: true)
                    : File.Exists(current)
                        ? File.ResolveLinkTarget(current, returnFinalTarget: true)
                        : null;

                if (target is not null)
                {
                    // A link target may be relative to the link's own directory.
                    current = Path.IsPathRooted(target.FullName)
                        ? target.FullName
                        : Path.GetFullPath(
                            Path.Combine(Path.GetDirectoryName(current) ?? root, target.FullName));
                }
            }

            return Path.GetFullPath(current);
        }
        catch (Exception)
        {
            return full;
        }
    }
}
