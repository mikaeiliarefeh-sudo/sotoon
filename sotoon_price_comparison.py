"""Compare Sotoon's model prices with OpenRouter and the original providers.

Usage: python3 sotoon_price_comparison.py <sotoon-prices.xlsx> [output.xlsx]

Sotoon's price list is the base. For each row, the OpenRouter price (from its
models API) and the official provider price (OpenAI, Anthropic, DeepSeek,
Cohere pricing pages, collected by openrouter_prices.py) are added next to it,
together with Sotoon's markup over each.
"""
import re
import sys
from datetime import date

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import openrouter_prices as op

SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "sotoon_price_comparison.xlsx"

or_prices = {m["id"]: m.get("pricing", {}) for m in op.models}


def openrouter_id(model_name, provider, underlying):
    """Best-guess OpenRouter model ID for a Sotoon row."""
    if provider == "openrouter":
        return underlying.removeprefix("openrouter/")
    if provider == "hosted_vllm":
        return None  # self-hosted; no OpenRouter equivalent to compare
    name = model_name if "/" in model_name else f"{provider}/{model_name}"
    if provider == "anthropic":
        name = re.sub(r"(\d)-(\d)", r"\1.\2", name)  # claude-haiku-4-5 -> 4.5
    return name


def official_price(or_id):
    """(model, input, cached, cache write, output, note) from the provider's page."""
    if not or_id or "/" not in or_id:
        return None
    provider, rest = or_id.lstrip("~").split("/", 1)
    prices = op.official.get(provider)
    if prices is None:
        return None
    base, _, variant = rest.partition(":")
    tier = "Batch" if variant == "batch" else "Standard"
    name = op.ALIASES.get(base, base)
    o = prices.get((name, tier))
    return (name,) + o if o else None


def markup(ours, theirs):
    if ours is None or not theirs:
        return None
    return ours / theirs - 1


wb_in = load_workbook(SRC, read_only=True)
src_rows = list(wb_in.worksheets[0].iter_rows(values_only=True))
src_head, src_rows = list(src_rows[0]), [r for r in src_rows[1:] if r and r[0]]
col = {h: i for i, h in enumerate(src_head)}

headers = [
    # Sotoon (base)
    "Model", "Provider", "Underlying model", "Mode",
    "Sotoon Input $/1M", "Sotoon Output $/1M", "Sotoon Cache read $/1M", "Sotoon Cache write $/1M",
    # OpenRouter
    "OpenRouter ID", "OpenRouter Input $/1M", "OpenRouter Output $/1M",
    "OpenRouter Cache read $/1M", "OpenRouter Cache write $/1M",
    # Official provider
    "Official model", "Official Input $/1M", "Official Output $/1M",
    "Official Cache read $/1M", "Official Cache write $/1M", "Official note",
    # Markups
    "Markup vs OpenRouter (input)", "Markup vs OpenRouter (output)",
    "Markup vs Official (input)", "Markup vs Official (output)",
]
GROUPS = [(1, 8, "305496"), (9, 13, "7030A0"), (14, 19, "548235"), (20, 23, "C65911")]
widths = [40, 12, 42, 11, 12, 12, 13, 13, 40, 12, 12, 13, 13, 24, 12, 12, 13, 13, 40, 14, 14, 14, 14]

out_rows = []
for r in src_rows:
    name, provider, underlying = r[col["model_name"]], r[col["provider"]], r[col["underlying_model"]] or ""
    ours = [r[col[k]] for k in ("input $/1M", "output $/1M", "cache_read $/1M", "cache_write $/1M")]
    or_id = openrouter_id(name, provider, underlying)
    p = or_prices.get(or_id) if or_id else None
    if p:
        theirs = [op.per_million(p.get(k)) for k in
                  ("prompt", "completion", "input_cache_read", "input_cache_write")]
    else:
        theirs = [None] * 4
    off = official_price(or_id)
    if off:
        o_name, o_in, o_cached, o_write, o_out, o_note = off
        official = [o_name, o_in, o_out, o_cached, o_write, o_note or None]
    else:
        official = [None] * 6
    out_rows.append(
        [name, provider, underlying, r[col["mode"]]] + ours
        + [or_id if p else None] + theirs
        + official
        + [markup(ours[0], theirs[0]), markup(ours[1], theirs[1]),
           markup(ours[0], official[1]), markup(ours[1], official[2])]
    )

wb = Workbook()
ws = wb.active
ws.title = "Comparison"
ws.append(headers)
for row in out_rows:
    ws.append(row)
for c in ws[1]:
    fill = next(f for a, b, f in GROUPS if a <= c.column <= b)
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=fill)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws.row_dimensions[1].height = 45
ws.freeze_panes = "B2"
ws.auto_filter.ref = ws.dimensions
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
BELOW_COST = PatternFill("solid", fgColor="FFC7CE")
for row in ws.iter_rows(min_row=2):
    for c in row[4:8] + row[9:13] + row[14:18]:
        c.number_format = "$#,##0.00##"
    for c in row[19:23]:
        c.number_format = "0.0%"
        if isinstance(c.value, (int, float)) and c.value < -1e-9:
            c.fill = BELOW_COST
ws.append([])
ws.append([f"Base: Sotoon price list ({SRC.rsplit('/', 1)[-1]}). "
           f"OpenRouter: {op.URL}, fetched {date.today().isoformat()}."])
for pv, url in op.OFFICIAL_URLS.items():
    ws.append([f"Official ({op.PROVIDER_TITLES[pv]}): {url}"])
ws.append(["Markup = Sotoon price / other price - 1. Red = Sotoon is cheaper than that source."])

wb.save(OUT)
n_or = sum(1 for r in out_rows if r[8])
n_off = sum(1 for r in out_rows if r[13])
print(f"{len(out_rows)} Sotoon rows; {n_or} with OpenRouter price, {n_off} with official price -> {OUT}")
