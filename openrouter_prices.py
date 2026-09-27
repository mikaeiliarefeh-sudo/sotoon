"""Fetch OpenRouter model prices for selected providers and write them to Excel.

OpenRouter prices come from its models API (USD per token, converted to USD
per 1M tokens). For each provider, the official prices from its own pricing
page are added in extra columns next to each row; models that OpenRouter
does not list are added as new rows.
"""
import html
import json
import re
import sys
import urllib.request
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

PROVIDERS = ["openai", "anthropic", "deepseek", "cohere"]
URL = "https://openrouter.ai/api/v1/models"
OPENAI_URL = "https://developers.openai.com/api/docs/pricing"
ANTHROPIC_URL = "https://platform.claude.com/docs/en/about-claude/pricing"
DEEPSEEK_URL = "https://api-docs.deepseek.com/quick_start/pricing"
COHERE_URL = "https://cohere.com/pricing"
OFFICIAL_URLS = {"openai": OPENAI_URL, "anthropic": ANTHROPIC_URL,
                 "deepseek": DEEPSEEK_URL, "cohere": COHERE_URL}
PROVIDER_TITLES = {"openai": "OpenAI", "anthropic": "Anthropic",
                   "deepseek": "DeepSeek", "cohere": "Cohere"}
OUT = sys.argv[1] if len(sys.argv) > 1 else "openrouter_prices.xlsx"

# OpenRouter model name -> OpenAI pricing page name, where they differ.
ALIASES = {
    "gpt-4": "gpt-4-0613",
    "gpt-4-turbo": "gpt-4-turbo-2024-04-09",
    "gpt-chat-latest": "chat-latest",
    "o3-mini-high": "o3-mini",
    "o4-mini-high": "o4-mini",
    # DeepSeek: legacy names are served and billed as V4.1 Flash.
    "deepseek-v4-flash": "deepseek-v4.1-flash",
    "deepseek-v4-flash-vision-exp": "deepseek-v4.1-flash",
    # Cohere's pricing page uses short names for these versions.
    "command-r-08-2024": "command-r",
    "command-r7b-12-2024": "command-r7b",
}


def per_million(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return round(v * 1_000_000, 4) if v >= 0 else None  # -1 means "variable"


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


# ---------------------------------------------------------------- OpenRouter

models = json.loads(fetch(URL))["data"]
rows = []
for m in models:
    provider = m["id"].split("/")[0]
    if provider not in PROVIDERS:
        continue
    p = m.get("pricing", {})
    rows.append([
        provider,
        m["id"],
        m.get("name"),
        m.get("context_length"),
        per_million(p.get("prompt")),
        per_million(p.get("completion")),
        per_million(p.get("input_cache_read")),
        per_million(p.get("input_cache_write")),
        per_million(p.get("internal_reasoning")),
        float(p["request"]) if p.get("request") not in (None, "") else None,
        float(p["image"]) if p.get("image") not in (None, "") else None,
        float(p["web_search"]) if p.get("web_search") not in (None, "") else None,
    ])
rows.sort(key=lambda r: (PROVIDERS.index(r[0]), r[1]))

# -------------------------------------------------------------------- OpenAI
# The pricing page embeds each table's data as Astro component props,
# serialized as [0, value] / [1, [items]] pairs.


def astro_decode(v):
    if isinstance(v, list) and len(v) == 2 and v[0] in (0, 1):
        tag, x = v
        if tag == 1:
            return [astro_decode(i) for i in x]
        return {k: astro_decode(w) for k, w in x.items()} if isinstance(x, dict) else x
    if isinstance(v, list) and len(v) == 1:
        return None
    return v


page = fetch(OPENAI_URL)
tables = []
for attrs in re.findall(r"<astro-island([^>]*)>", page):
    comp = re.search(r'component-export="([^"]*)"', attrs)
    props = re.search(r'props="([^"]*)"', attrs)
    if comp and props:
        p = json.loads(html.unescape(props.group(1)))
        tables.append((comp.group(1), {k: astro_decode(v) for k, v in p.items()}))

# official[provider][(name, tier)] = (input, cached input, cache write, output, note)
official = {pv: {} for pv in OFFICIAL_URLS}


def add(name, tier, inp, cached, write, out, note="", provider="openai"):
    official[provider].setdefault((name, tier), (num(inp), num(cached), num(write), num(out), note))


for comp, p in tables:
    if comp == "TextTokenPricingTables" and p["tier"] in ("standard", "batch"):
        tier = p["tier"].capitalize()
        for r in p["rows"]:
            name = re.sub(r"\s*\(.*", "", r[0])
            note = "Short context (<272K) price" if "272K" in r[0] else ""
            if len(r) == 5:
                add(name, tier, r[1], r[2], r[3], r[4], note)
            else:
                add(name, tier, r[1], r[2], None, r[3], note)
    elif comp == "GroupedPricingTable":
        heads = [h if isinstance(h, str) else "" for h in p["headings"]]
        for g in p["groups"]:
            model, grows = g["model"], g["rows"]
            if heads[:2] == ["Model", "Short context input"]:  # cyber models
                r = grows[0]
                add(model, "Standard", r[0], r[1], r[2], r[3], "Short context price")
            elif heads[:2] == ["Category", "Model"]:  # specialized models
                for r in grows:
                    note = g["model"] if num(r[1]) is not None or r[1] == "-" else f"{g['model']}; {r[1]}"
                    add(r[0], "Standard", r[1], r[2], None, r[3], note)
            elif len(heads) > 1 and heads[1] == "" and "Input" in heads:  # image models
                by_mod = {r[0]: r for r in grows}
                img = by_mod.get("Image")
                text = by_mod.get("Text")
                note = "Image tokens; text: in {} / cached {} / out {}".format(*text[1:4]) if text else ""
                add(model, "Standard", img[1], img[2], None, img[3], note)
            elif heads[1:2] == ["Modality"]:  # realtime / audio / TTS
                by_mod = {r[0]: r for r in grows}
                text = by_mod.get("Text")
                others = "; ".join(f"{k}: in {v[1]} / cached {v[2]} / out {v[3]}"
                                   for k, v in by_mod.items() if k != "Text")
                if text and num(text[1]) is not None:
                    add(model, "Standard", text[1], text[2], None, text[3],
                        "Text tokens" + (f"; {others}" if others else ""))
                elif text:
                    add(model, "Standard", None, None, None, None, f"Text: {text[1]}")
                else:
                    add(model, "Standard", None, None, None, None, others)
            elif heads[1:2] == ["Use case"]:  # transcription
                r = grows[0]
                add(model, "Standard", r[1], None, None, r[2], f"{r[0]}; est. {r[3]}")

# ----------------------------------------------------------------- Anthropic
# The docs page is also served as Markdown; prices look like "$2.50 / MTok".


def mtok(cell):
    m = re.search(r"\$([\d.,]+)\s*/\s*MTok", cell)
    return float(m.group(1).replace(",", "")) if m else None


def md_tables(md):
    """Yield (header cells, body rows) for each Markdown table."""
    lines = md.splitlines() + [""]
    block = []
    for line in lines:
        if line.startswith("|"):
            block.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif block:
            if len(block) > 2:
                yield block[0], block[2:]
            block = []


def claude_name(cell):
    """'Claude Opus 4.1 ([retired, ...](...))' -> ('claude-opus-4.1', 'retired, ...')."""
    status = re.search(r"\(\[([^\]]+)\]", cell)
    name = re.sub(r"\s*\(.*", "", cell).strip()
    return name.lower().replace(" ", "-"), status.group(1) if status else ""


ant_md = fetch(ANTHROPIC_URL + ".md")
for head, body in md_tables(ant_md):
    if head[:2] == ["Model", "Base input tokens"]:
        for r in body:
            name, status = claude_name(r[0])
            note = f"1h cache write: ${mtok(r[3]):g}" + (f"; {status}" if status else "")
            add(name, "Standard", mtok(r[1]), mtok(r[4]), mtok(r[2]), mtok(r[5]), note, "anthropic")
    elif head[:2] == ["Model", "Batch input"]:
        for r in body:
            name, status = claude_name(r[0])
            add(name, "Batch", mtok(r[1]), None, None, mtok(r[2]), status, "anthropic")

# ------------------------------------------------------------------ DeepSeek
# One table: a MODEL VERSION row, then cache-hit / cache-miss / output rows,
# each split into off-peak and peak prices, one column per model.


def html_lines(page):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    t = re.sub(r"<(tr|h[1-6]|p|div|li|br)[^>]*>", "\n", t)
    t = re.sub(r"<t[dh][^>]*>", " | ", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return [re.sub(r"\s+", " ", ln).strip() for ln in t.splitlines() if ln.strip()]


ds_lines = html_lines(fetch(DEEPSEEK_URL))
versions = next(ln for ln in ds_lines if ln.startswith("| MODEL VERSION |"))
versions = [c.strip() for c in versions.split("|")[2:] if c.strip()]
price_lines = [ln for ln in ds_lines if "PEAK" in ln and "$" in ln]
prices = [[float(x) for x in re.findall(r"\$([\d.]+)", ln)] for ln in price_lines]
# prices rows: hit off, hit peak, miss off, miss peak, output off, output peak
for i, version in enumerate(versions):
    hit_off, hit_peak, miss_off, miss_peak, out_off, out_peak = (row[i] for row in prices)
    note = (f"Peak-hour price; off-peak (half): in {miss_off:g} / cached {hit_off:g} "
            f"/ out {out_off:g}")
    add(version.lower(), "Standard", miss_peak, hit_peak, None, out_peak, note, "deepseek")

# -------------------------------------------------------------------- Cohere
# The page's model cards are embedded as JSON (modelName, per, pricings);
# older models are only mentioned in the FAQ text.


def cohere_name(name):
    return name.lower().replace("+", "-plus").replace(" ", "-")


co_page = fetch(COHERE_URL).replace('\\"', '"')
cards = list(re.finditer(r'"modelName":"([^"]*)","per":"([^"]*)"', co_page))
for i, m in enumerate(cards):
    end = cards[i + 1].start() if i + 1 < len(cards) else m.end() + 20000
    seg = co_page[m.end():end]
    name, per = m.group(1), m.group(2)
    pr = re.search(r'"pricings":(\[.*?\])(?=,"primaryCta")', seg)
    if not pr:
        text = re.findall(r'"text":"([^"]*\$[^"]*)"', seg)
        if text:
            add(cohere_name(name), "Standard", None, None, None, None,
                text[0].replace("$$", "$"), "cohere")
        continue
    p = json.loads(pr.group(1))[0]
    inp, out = p.get("inputPrice"), p.get("outputPrice")
    if per == "Free":
        add(cohere_name(name), "Standard", 0, None, None, 0,
            "Free (open-weights model)", "cohere")
    elif p.get("overridePer"):
        add(cohere_name(name), "Standard", None, None, None, None,
            f"${inp:g} / {p['overridePer']}", "cohere")
    elif p.get("outputLabel") == "Output":
        add(cohere_name(name), "Standard", inp, None, None, out, "", "cohere")
    else:
        add(cohere_name(name), "Standard", inp, None, None, None,
            f"{p['outputLabel']}: ${out:g} / 1M tokens", "cohere")

co_text = " ".join(html_lines(co_page))
for name, inp, out in re.findall(
        r"([\w+.\- ]+?) pricing is \$([\d.]+)/1M tokens for input and \$([\d.]+)/1M tokens for output",
        co_text):
    add(cohere_name(name.strip()), "Standard", float(inp), None, None, float(out),
        "Listed in Cohere pricing FAQ", "cohere")
aya = re.search(r"Aya Expanse models \(([\dB]+) and ([\dB]+)\).*?\$([\d.]+)/1M tokens for input "
                r"and \$([\d.]+)/1M tokens for output", co_text)
if aya:
    for size in aya.group(1, 2):
        add(f"aya-expanse-{size.lower()}", "Standard", float(aya.group(3)), None, None,
            float(aya.group(4)), "Listed in Cohere pricing FAQ", "cohere")

# ------------------------------------------------------------------- Compare

matched = {pv: set() for pv in OFFICIAL_URLS}
OAI_HEADERS = ["Official model", "Official tier", "Official Input $/1M",
               "Official Cached input $/1M", "Official Cache write $/1M",
               "Official Output $/1M", "Compare", "Official note"]


def same(a, b):
    return a is None or b is None or abs(a - b) < 1e-6


for r in rows:
    pv = r[0]
    if pv not in official:
        r.extend([None] * len(OAI_HEADERS))
        continue
    base, _, variant = r[1].split("/", 1)[1].partition(":")
    tier = "Batch" if variant == "batch" else "Standard"
    name = ALIASES.get(base, base)
    o = official[pv].get((name, tier))
    if not o:
        r.extend([None] * 6 + [f"Not on {PROVIDER_TITLES[pv]} page", None])
        continue
    matched[pv].add((name, tier))
    inp, cached, write, out, note = o
    if name != base:
        note = f"Matched as '{name}'" + (f"; {note}" if note else "")
    if inp is None and out is None:
        cmp = f"Not per-token on {PROVIDER_TITLES[pv]}"
    elif same(r[4], inp) and same(r[5], out) and same(r[6], cached):
        cmp = "Same"
    else:
        cmp = "Different"
    r.extend([name, tier, inp, cached, write, out, cmp, note or None])

new_rows = []
for pv, prices in official.items():
    for (name, tier), (inp, cached, write, out, note) in prices.items():
        if (name, tier) in matched[pv]:
            continue
        new_rows.append([pv, None, None, None] + [None] * 8
                        + [name, tier, inp, cached, write, out,
                           f"Only on {PROVIDER_TITLES[pv]}", note or None])
new_rows.sort(key=lambda r: (PROVIDERS.index(r[0]), r[13] != "Standard", r[12]))

# --------------------------------------------------------------------- Excel

headers = [
    "Provider", "Model ID", "Name", "Context (tokens)",
    "Input $/1M", "Output $/1M", "Cache read $/1M", "Cache write $/1M",
    "Reasoning $/1M", "Per request $", "Per image $", "Web search $",
] + OAI_HEADERS
widths = [11, 42, 42, 14, 12, 12, 14, 14, 14, 13, 12, 12, 26, 11, 12, 14, 14, 12, 22, 50]
NEW_FILL = PatternFill("solid", fgColor="FFF2CC")
CMP_FILLS = {"Same": "C6EFCE", "Different": "FFC7CE"}
all_rows = rows + new_rows

wb = Workbook()
sheets = [("All", all_rows)] + [
    (pv, [r for r in all_rows if r[0] == pv]) for pv in PROVIDERS
]
titles = {"All": "All", "openai": "OpenAI", "anthropic": "Anthropic",
          "deepseek": "DeepSeek", "cohere": "Cohere"}
for i, (key, data) in enumerate(sheets):
    ws = wb.active if i == 0 else wb.create_sheet()
    ws.title = titles[key]
    with_oai = key == "All" or key in OFFICIAL_URLS
    ncols = len(headers) if with_oai else 12
    ws.append(headers[:ncols])
    for r in data:
        ws.append(r[:ncols])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        fill = "548235" if c.column > 12 else "305496"
        c.fill = PatternFill("solid", fgColor=fill)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    for col, w in enumerate(widths[:ncols], 1):
        ws.column_dimensions[get_column_letter(col)].width = w
    for row in ws.iter_rows(min_row=2):
        row[3].number_format = "#,##0"
        for c in row[4:12]:
            c.number_format = "$#,##0.00##"
        if with_oai:
            for c in row[14:18]:
                c.number_format = "$#,##0.00##"
            status = row[18].value
            if status and status.startswith("Only on "):
                for c in row:
                    c.fill = NEW_FILL
            elif status in CMP_FILLS:
                row[18].fill = PatternFill("solid", fgColor=CMP_FILLS[status])
    ws.append([])
    ws.append([f"Source: {URL} — fetched {date.today().isoformat()}. Empty = not applicable."])
    if with_oai:
        for pv, url in OFFICIAL_URLS.items():
            if key in ("All", pv):
                ws.append([f"Green columns ({PROVIDER_TITLES[pv]}): official prices from {url}"])
        ws.append(["Standard tier, or Batch tier for ':batch' models. "
                   "Yellow rows: models OpenRouter does not list."])

wb.save(OUT)
print(f"{len(rows)} OpenRouter models + {len(new_rows)} official-only rows -> {OUT}")
