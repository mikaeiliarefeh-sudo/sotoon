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

# ------------------------------------------------------------ Summary sheet
# Row indexes into out_rows: 0 model, 1 provider, 4/5 Sotoon in/out,
# 8 OpenRouter ID, 9/10 OpenRouter in/out, 13 official model, 14/15 official
# in/out, 19-22 markups (OpenRouter in/out, official in/out).

EPS = 0.001
TYPICAL = {"openrouter": 0.15, "anthropic": 0.15, "openai": 0.3225}  # 1.15, 1.15 x 1.15

sm = wb.create_sheet("خلاصه", 0)
sm.sheet_view.rightToLeft = True
TITLE_FONT = Font(bold=True, size=13, color="1F3864")
HEAD_FILL = PatternFill("solid", fgColor="305496")


def section(title, note, head, data, pct_cols=(), money_cols=()):
    sm.append([title])
    sm.cell(sm.max_row, 1).font = TITLE_FONT
    if note:
        sm.append([note])
        sm.cell(sm.max_row, 1).font = Font(italic=True, color="595959")
    sm.append(head)
    for c in sm[sm.max_row]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    if not data:
        sm.append(["—  موردی پیدا نشد"])
    for d in data:
        sm.append(list(d))
        row = sm[sm.max_row]
        for i in pct_cols:
            row[i].number_format = "0.0%"
            if isinstance(row[i].value, (int, float)) and row[i].value < -EPS:
                row[i].fill = BELOW_COST
        for i in money_cols:
            row[i].number_format = "$#,##0.00##"
    sm.append([])
    sm.append([])


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return (xs[n // 2] + xs[(n - 1) // 2]) / 2 if n else None


# 1. Markup pattern per source.
pattern = []
for pv in sorted({r[1] for r in out_rows}):
    rs = [r for r in out_rows if r[1] == pv]
    mk_or = [r[19] for r in rs if r[19] is not None]
    mk_off = [r[21] for r in rs if r[21] is not None]
    pattern.append([pv, len(rs), len(mk_or), median(mk_or),
                    min(mk_or) if mk_or else None, max(mk_or) if mk_or else None,
                    len(mk_off), median(mk_off)])
section("۱. الگوی مارک‌آپ بر اساس منبع تأمین",
        "مارک‌آپ ورودی. میانه = مقدار معمول.",
        ["منبع (provider)", "تعداد مدل", "با قیمت OpenRouter", "میانه‌ی مارک‌آپ نسبت به OpenRouter",
         "کمترین", "بیشترین", "با قیمت رسمی", "میانه‌ی مارک‌آپ نسبت به قیمت رسمی"],
        pattern, pct_cols=(3, 4, 5, 7))

# 2. Priced below a source.
below = []
for r in out_rows:
    if r[19] is not None and (r[19] < -EPS or r[20] < -EPS):
        below.append([r[0], r[1], "OpenRouter", r[4], r[5], r[9], r[10], r[19], r[20]])
    if r[21] is not None and (r[21] < -EPS or (r[22] is not None and r[22] < -EPS)):
        below.append([r[0], r[1], "رسمی", r[4], r[5], r[14], r[15], r[21], r[22]])
section("۲. مدل‌هایی که قیمت ما پایین‌تر از منبع است",
        "برای DeepSeek، قیمت رسمی نرخ ساعت شلوغ (peak) است.",
        ["مدل", "منبع تأمین", "مقایسه با", "ورودی ما", "خروجی ما", "ورودی منبع", "خروجی منبع",
         "مارک‌آپ ورودی", "مارک‌آپ خروجی"],
        below, pct_cols=(7, 8), money_cols=(3, 4, 5, 6))

# 3. Sold at cost (no markup).
zero = []
for r in out_rows:
    for label, a, b in (("OpenRouter", 19, 20), ("رسمی", 21, 22)):
        if r[a] is not None and abs(r[a]) < EPS and (r[b] is None or abs(r[b]) < EPS):
            zero.append([r[0], r[1], label, r[4], r[5]])
            break
section("۳. مدل‌هایی که بدون مارک‌آپ فروخته می‌شوند",
        None, ["مدل", "منبع تأمین", "برابر با قیمت", "ورودی", "خروجی"],
        zero, money_cols=(3, 4))

# 4. "latest" aliases whose markup is off the usual rate.
stale = []
for r in out_rows:
    if r[0].startswith("~") and r[19] is not None:
        usual = TYPICAL.get(r[1], 0.15)
        if abs(r[19] - usual) > 0.01 or abs(r[20] - usual) > 0.01:
            stale.append([r[0], r[4], r[5], r[9], r[10], r[19], r[20]])
section("۴. مدل‌های «latest» با مارک‌آپ غیرعادی (احتمالاً قیمت کهنه)",
        "این شناسه‌ها همیشه به جدیدترین نسخه اشاره می‌کنند؛ اگر نسخه عوض شده، قیمت ما به‌روز نشده است.",
        ["مدل", "ورودی ما", "خروجی ما", "ورودی OpenRouter", "خروجی OpenRouter",
         "مارک‌آپ ورودی", "مارک‌آپ خروجی"],
        stale, pct_cols=(5, 6), money_cols=(1, 2, 3, 4))

# 5. Other rows off the usual markup (not aliases, not below cost, not zero).
flagged = {r[0] for r in below} | {r[0] for r in zero} | {r[0] for r in stale}
odd = []
for r in out_rows:
    if r[0] in flagged or r[19] is None:
        continue
    usual = TYPICAL.get(r[1])
    if usual is not None and (abs(r[19] - usual) > 0.01 or abs(r[20] - usual) > 0.01):
        odd.append([r[0], r[1], r[4], r[5], r[9], r[10], r[19], r[20]])
section("۵. سایر مدل‌ها با مارک‌آپ متفاوت از الگوی معمول",
        "الگوی معمول: ۱۵٪ برای OpenRouter و Anthropic، ۳۲٫۲٪ برای OpenAI.",
        ["مدل", "منبع تأمین", "ورودی ما", "خروجی ما", "ورودی OpenRouter", "خروجی OpenRouter",
         "مارک‌آپ ورودی", "مارک‌آپ خروجی"],
        odd, pct_cols=(6, 7), money_cols=(2, 3, 4, 5))

# 6. Duplicates and rows with no OpenRouter match.
counts = {}
for r in out_rows:
    counts[r[0]] = counts.get(r[0], 0) + 1
section("۶. ردیف‌های تکراری در لیست ما", None, ["مدل", "تعداد تکرار"],
        [[m, n] for m, n in counts.items() if n > 1])


def no_match_reason(r):
    if r[1] == "hosted_vllm":
        return "میزبانی خودمان (hosted_vllm)"
    if r[13]:
        return "در OpenRouter نیست، ولی قیمت رسمی دارد"
    return "در فهرست مدل‌های OpenRouter پیدا نشد"


section("۷. مدل‌هایی که در OpenRouter پیدا نشدند", None, ["مدل", "منبع تأمین", "توضیح"],
        [[r[0], r[1], no_match_reason(r)] for r in out_rows if not r[8]])

for i, w in enumerate([42, 16, 16, 16, 16, 16, 16, 16, 16], 1):
    sm.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT)
n_or = sum(1 for r in out_rows if r[8])
n_off = sum(1 for r in out_rows if r[13])
print(f"{len(out_rows)} Sotoon rows; {n_or} with OpenRouter price, {n_off} with official price -> {OUT}")
