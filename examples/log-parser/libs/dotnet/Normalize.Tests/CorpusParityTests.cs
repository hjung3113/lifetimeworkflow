using System.Text.Json;
using Xunit;

namespace Normalize.Tests;

/// <summary>
/// Corpus parity test — .NET core vs the SAME shared (raw, canonical) fixture corpus the Python
/// pytest suite loads (D-04). Every entry in <c>libs/normalize-fixtures/*.json</c> is asserted;
/// identical canonical output across both languages proves cross-language parity. Any per-language
/// drift fails here.
/// </summary>
public class CorpusParityTests
{
    /// <summary>
    /// Walk up from the test binary to the repo root and resolve the shared corpus directory.
    /// The corpus is language-neutral and lives at <c>libs/normalize-fixtures</c>.
    /// </summary>
    private static string FixturesDir()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir is not null)
        {
            var candidate = Path.Combine(dir.FullName, "libs", "normalize-fixtures");
            if (Directory.Exists(candidate))
            {
                return candidate;
            }

            dir = dir.Parent;
        }

        throw new DirectoryNotFoundException(
            "Could not locate libs/normalize-fixtures walking up from " + AppContext.BaseDirectory);
    }

    public static IEnumerable<object[]> Corpus()
    {
        var dir = FixturesDir();
        var files = Directory.GetFiles(dir, "*.json");
        Array.Sort(files, StringComparer.Ordinal);
        Assert.NotEmpty(files);

        foreach (var file in files)
        {
            using var doc = JsonDocument.Parse(File.ReadAllBytes(file));
            var stem = Path.GetFileNameWithoutExtension(file);
            foreach (var entry in doc.RootElement.EnumerateArray())
            {
                var name = entry.GetProperty("name").GetString()!;
                var kind = entry.GetProperty("kind").GetString()!;
                var canonical = entry.GetProperty("canonical").GetString()!;
                var raw = entry.TryGetProperty("raw", out var r) ? r.GetString() : null;
                var rawB64 = entry.TryGetProperty("raw_b64", out var b) ? b.GetString() : null;
                yield return new object[] { $"{stem}::{name}", kind, raw!, rawB64!, canonical };
            }
        }
    }

    [Theory]
    [MemberData(nameof(Corpus))]
    public void DotnetCoreReproducesCanonical(
        string caseId, string kind, string raw, string rawB64, string canonical)
    {
        string actual;
        if (kind == "tsv")
        {
            actual = Normalizer.NormalizeTsv(Convert.FromBase64String(rawB64));
        }
        else
        {
            actual = Normalizer.NormalizeCell(raw, kind);
        }

        Assert.True(
            actual == canonical,
            $"{caseId}: got {actual}, expected {canonical}");
    }
}
