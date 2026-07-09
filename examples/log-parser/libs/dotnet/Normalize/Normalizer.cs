using System.Globalization;
using System.Text;

namespace Normalize;

/// <summary>
/// §4.3–4.6 canonicalization core — .NET thin implementation (CONTRACT-02, D-04/D-05).
///
/// The RULE is canonical (see <c>libs/normalize-spec.md</c>); this class is one thin
/// implementation of it. The Python core (<c>libs/python/normalize</c>) implements the same
/// rules and both are cross-validated by the shared <c>libs/normalize-fixtures/*.json</c> corpus.
/// Identical output across both languages proves parity (D-04).
///
/// Uses <see cref="CultureInfo.InvariantCulture"/> for decimals, UTC-adjusted
/// <see cref="DateTimeOffset"/> for datetimes, and <c>new UTF8Encoding(false)</c> for BOM-free
/// decoding — never hand-rolled number formatting or BOM detection (RESEARCH §Don't Hand-Roll).
///
/// This is the TSV data comparator ONLY. It contains none of the contract-text JSON-canonicalizer
/// (that hasher lives Python-side in Plan 05) — a deliberately separate canonicalizer.
/// </summary>
public static class Normalizer
{
    /// <summary>R6 — the agreed null token (format-conventions.schema.json <c>null_token</c>).</summary>
    public const string DefaultNullToken = "\\N";

    /// <summary>R6 — distinct sentinel a null cell canonicalizes to ("" != null, §4.3).</summary>
    public const string NullSentinel = "<NULL>";

    private static readonly UTF8Encoding Utf8NoBom = new(encoderShouldEmitUTF8Identifier: false);

    /// <summary>
    /// R3 — InvariantCulture decimal, '.' separator, no thousands, trailing zeros stripped.
    /// A locale ',' decimal separator is remapped to '.' before parsing (thousands separators are
    /// forbidden by §4.6, so the remap is unambiguous). Uses <see cref="decimal"/> — never a
    /// double round-trip — to avoid last-digit representation diffs.
    /// </summary>
    public static string NormalizeDecimal(string value)
    {
        var remapped = value.Replace(",", ".");
        var d = decimal.Parse(remapped, NumberStyles.Number, CultureInfo.InvariantCulture);
        // "0.############" emits '.' only and drops trailing zeros: 1.50 -> 1.5, 100 -> 100.
        return d.ToString("0.############", CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// R5 — convert to UTC and emit the fixed ISO-8601 string <c>yyyy-MM-ddTHH:mm:ssZ</c>.
    /// A value with an explicit offset is adjusted to UTC; a naive value is assumed UTC.
    /// </summary>
    public static string NormalizeDateTime(string value)
    {
        var dto = DateTimeOffset.Parse(
            value,
            CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
        return dto.UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Canonicalize a single cell per its <paramref name="kind"/>
    /// (<c>decimal</c> | <c>datetime</c> | <c>string</c>). The null-token check (R6) runs first so
    /// a null is never mis-parsed as a decimal/datetime.
    /// </summary>
    public static string NormalizeCell(string value, string kind, string nullToken = DefaultNullToken)
    {
        if (value == nullToken)
        {
            return NullSentinel;
        }

        return kind switch
        {
            "decimal" => NormalizeDecimal(value),
            "datetime" => NormalizeDateTime(value),
            // string / any other kind: pass through (R6 empty-string stays empty).
            _ => value,
        };
    }

    /// <summary>
    /// Canonicalize a whole TSV blob: R1 (BOM strip) + R2 (LF) + R8 (deterministic row sort).
    /// Decoding drops a leading UTF-8 BOM if present; rows are ordinal-sorted so an unordered set
    /// never causes a false diff (matches Python <c>sorted()</c> code-point order on ASCII/BMP).
    /// </summary>
    public static string NormalizeTsv(byte[] raw)
    {
        // R1 — strip a leading UTF-8 BOM (EF BB BF) if present, then decode BOM-free.
        int offset = 0;
        if (raw.Length >= 3 && raw[0] == 0xEF && raw[1] == 0xBB && raw[2] == 0xBF)
        {
            offset = 3;
        }

        var text = Utf8NoBom.GetString(raw, offset, raw.Length - offset);

        // R2 — force LF.
        text = text.Replace("\r\n", "\n").Replace("\r", "\n");

        var lines = new List<string>(text.Split('\n'));
        if (lines.Count > 0 && lines[^1].Length == 0)
        {
            lines.RemoveAt(lines.Count - 1); // drop trailing empty from a final newline
        }

        // R8 — deterministic ordinal order before diff.
        lines.Sort(StringComparer.Ordinal);
        return string.Join("\n", lines);
    }
}
