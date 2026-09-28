"""Compare Sotoon's model prices with OpenRouter and the original providers.

Usage: python3 sotoon_price_comparison.py <sotoon-prices.xlsx> [output.xlsx]

Sotoon's price list is the base. For each row, the OpenRouter price (from its
models API) and the official provider price are added next to it, together
with Sotoon's markup over each. Official prices come from two places:
openrouter_prices.py scrapes OpenAI, Anthropic, DeepSeek and Cohere live, and
official_prices_extra.csv holds the other makers' prices, each row with the
page it was read from.
"""
import csv
import os
import re
import sys
from datetime import date

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import openrouter_prices as op

SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "sotoon_price_comparison.xlsx"

EXTRA_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "official_prices_extra.csv")



def availability(or_id, provider, or_source, off):
    """(status labels, deprecated) for a Sotoon row; deprecated is "بله" (confirmed:
    removed or scheduled for removal on OpenRouter, or retired by the maker), "شاید"
    (not on the maker's pricing page, which can also mean it was never sold there)
    or None."""
    if provider == "hosted_vllm":
        return "میزبانی خودمان", None
    labels, level = [], None
    bought_direct = provider in ("openai", "anthropic") and off and off[0] is not None
    if or_id and or_source is None and not bought_direct:
        labels.append("حذف‌شده از OpenRouter")
        level = "بله"
    elif or_source == "api":
        labels.append("قیمت در صفحه‌ی OpenRouter نیامده؛ قیمت API استفاده شد")
    expires = op.api_models.get(or_id, {}).get("expiration_date") if or_id else None
    if expires:
        labels.append(f"حذف از OpenRouter در {expires}")
        level = "بله"
    note = (off[5] if off else None) or ""
    if re.search(r"retired|deprecated", note, re.I):
        labels.append("بازنشسته/منسوخ نزد پرووایدر اصلی")
        level = "بله"
    elif (not off or off[0] is None) and note.startswith("Not listed on"):
        labels.append("در صفحه‌ی قیمت پرووایدر اصلی نیست")
        level = level or "شاید"
    return " | ".join(labels) or None, level



def num_or_none(v):
    return float(v) if v not in (None, "") else None


# extra[maker] = [(model pattern, official model, input, cached, output, note, source)]
extra = {}
with open(EXTRA_CSV, newline="") as f:
    for r in csv.DictReader(f):
        extra.setdefault(r["maker"], []).append((
            r["model"], r["official_model"] or None, num_or_none(r["input_per_1m"]),
            num_or_none(r["cached_input_per_1m"]), num_or_none(r["output_per_1m"]),
            r["note"] or None, r["source"] or None))


HOSTED_ALIASES = {"google/gemma3-27b": "google/gemma-3-27b-it"}


def openrouter_id(model_name, provider, underlying):
    """Best-guess OpenRouter model ID for a Sotoon row."""
    if provider == "openrouter":
        return underlying.removeprefix("openrouter/")
    if provider == "hosted_vllm":
        # Self-hosted; compare with the same model on OpenRouter where there is one.
        name = model_name.lower()
        for candidate in (HOSTED_ALIASES.get(name), name, name.removesuffix("-fp8")):
            if candidate in op.api_models:
                return candidate
        return None
    name = model_name if "/" in model_name else f"{provider}/{model_name}"
    if provider == "anthropic":
        name = re.sub(r"(\d)-(\d)", r"\1.\2", name)  # claude-haiku-4-5 -> 4.5
    return name


def official_price(or_id, model_name, provider):
    """(model, input, cached, cache write, output, note, source) from the maker's page.

    When no price is found, the model fields are None and the note says why.
    """
    key = or_id or model_name.lower()
    if "/" not in key:
        return None
    maker, rest = key.lstrip("~").split("/", 1)
    base, _, variant = rest.partition(":")
    tier = "Batch" if variant == "batch" else "Standard"
    prices = op.official.get(maker)
    if prices is not None:
        name = op.ALIASES.get(base, base)
        o = prices.get((name, tier))
        if o:
            return (name,) + o + (op.OFFICIAL_URLS[maker],)
    for pattern, name, inp, cached, out, note, source in extra.get(maker, []):
        exact = pattern == base
        prefix = pattern.endswith("*") and base.startswith(pattern[:-1])
        if tier == "Standard" and (exact or prefix):
            return (name, inp, cached, None, out, note, source)
    if provider == "hosted_vllm":
        reason = "Self-hosted by Sotoon"
    elif key.startswith("~"):
        reason = "Alias to the latest model; no fixed official price"
    elif prices is not None or maker in extra:
        reason = f"Not listed on {op.PROVIDER_TITLES.get(maker, maker)}'s official pricing page"
    else:
        reason = "No official per-token price page found"
    return (None, None, None, None, None, reason, None)


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
    "Official source", "وضعیت در دسترس بودن", "منسوخ/حذف‌شده؟", "تاریخ حذف از OpenRouter",
]
GROUPS = [(1, 8, "305496"), (9, 13, "7030A0"), (14, 19, "548235"), (20, 23, "C65911"), (24, 24, "548235"), (25, 27, "7F7F7F")]
widths = [40, 12, 42, 11, 12, 12, 13, 13, 40, 12, 12, 13, 13, 24, 12, 12, 13, 13, 50, 14, 14, 14, 14, 50, 45, 12, 14]

op.prefetch_pages([openrouter_id(r[col["model_name"]], r[col["provider"]],
                                r[col["underlying_model"]] or "") for r in src_rows])

out_rows = []
for r in src_rows:
    name, provider, underlying = r[col["model_name"]], r[col["provider"]], r[col["underlying_model"]] or ""
    ours = [r[col[k]] for k in ("input $/1M", "output $/1M", "cache_read $/1M", "cache_write $/1M")]
    or_id = openrouter_id(name, provider, underlying)
    p, or_source = op.effective_pricing(or_id) if or_id else (None, None)
    if p:
        theirs = [op.per_million(p.get(k)) for k in
                  ("prompt", "completion", "input_cache_read", "input_cache_write")]
    else:
        theirs = [None] * 4
    off = official_price(or_id, name, provider)
    if off:
        o_name, o_in, o_cached, o_write, o_out, o_note, o_source = off
        official = [o_name, o_in, o_out, o_cached, o_write, o_note or None]
    else:
        official, o_source = [None] * 6, None
    out_rows.append(
        [name, provider, underlying, r[col["mode"]]] + ours
        + [or_id if p else None] + theirs
        + official
        + [markup(ours[0], theirs[0]), markup(ours[1], theirs[1]),
           markup(ours[0], official[1]), markup(ours[1], official[2])]
        + [o_source]
        + list(availability(or_id, provider, or_source, off))
        + [op.api_models.get(or_id, {}).get("expiration_date") if or_id else None]
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
DEPRECATED = PatternFill("solid", fgColor="BFBFBF")
MAYBE_DEPRECATED = PatternFill("solid", fgColor="EDEDED")
for row in ws.iter_rows(min_row=2):
    for c in row[4:8] + row[9:13] + row[14:18]:
        c.number_format = "$#,##0.00##"
    for c in row[19:23]:
        c.number_format = "0.0%"
        if isinstance(c.value, (int, float)) and c.value < -1e-9:
            c.fill = BELOW_COST
    if len(row) > 25 and row[25].value in ("بله", "شاید"):
        for c in (row[0], row[24], row[25]):
            c.fill = DEPRECATED if row[25].value == "بله" else MAYBE_DEPRECATED
ws.append([])
ws.append([f"Base: Sotoon price list ({SRC.rsplit('/', 1)[-1]}). "
           f"OpenRouter: price on each model's page on openrouter.ai, fetched {date.today().isoformat()}."])
for pv, url in op.OFFICIAL_URLS.items():
    ws.append([f"Official ({op.PROVIDER_TITLES[pv]}): {url}"])
ws.append(["Other makers: official_prices_extra.csv (read 2026-09-27); "
           "each row's page is in the 'Official source' column."])
ws.append(["Markup = Sotoon price / other price - 1. Red = Sotoon is cheaper than that source."])
ws.append(["منسوخ/حذف‌شده: «بله» (خاکستری تیره) = از OpenRouter حذف شده یا حذفش زمان‌بندی شده، یا پرووایدر "
           "اصلی بازنشسته‌اش کرده. «شاید» (خاکستری روشن) = در صفحه‌ی قیمت پرووایدر اصلی نیست."])

# ------------------------------------------------------------ Summary sheet
# Row indexes into out_rows: 0 model, 1 provider, 4/5 Sotoon in/out,
# 8 OpenRouter ID, 9/10 OpenRouter in/out, 13 official model, 14/15 official
# in/out, 19-22 markups (OpenRouter in/out, official in/out).

EPS = 0.001
TYPICAL = {"openrouter": 0.15, "anthropic": 0.15, "openai": 0.3225}  # 1.15, 1.15 x 1.15

sm = wb.create_sheet("خلاصه")
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

coverage = {}
for r in out_rows:
    status = "قیمت رسمی دارد" if (r[14] is not None or r[15] is not None) else (r[18] or "—")
    coverage[status] = coverage.get(status, 0) + 1
section("۸. پوشش قیمت رسمی", "برای مدل‌هایی که قیمت رسمی ندارند، علت آمده است.",
        ["وضعیت", "تعداد مدل"], sorted(coverage.items(), key=lambda kv: -kv[1]))

for i, w in enumerate([42, 16, 16, 16, 16, 16, 16, 16, 16], 1):
    sm.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT)
n_or = sum(1 for r in out_rows if r[8])
n_off = sum(1 for r in out_rows if r[13])
print(f"{len(out_rows)} Sotoon rows; {n_or} with OpenRouter price, {n_off} with official price -> {OUT}")
