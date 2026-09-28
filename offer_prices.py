"""Build the minimum offer price list from the Sotoon price comparison.

Usage: python3 offer_prices.py [sotoon_price_comparison.xlsx] [output.xlsx]

Our cost is what we pay the source we buy from: OpenAI's own price for OpenAI
models (and Anthropic's for models bought directly from Anthropic), and the
OpenRouter price for everything else. On top of every purchase we pay the
exchanger a 5% fee, so the lowest price we can offer without a loss is
cost x 1.05.

  Min price 1 = purchase source price x 1.05
  Min price 2 = original provider's (official) price x 1.05, filled only when
                it differs from the purchase source price
"""
import sys
from datetime import date

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

SRC = sys.argv[1] if len(sys.argv) > 1 else "sotoon_price_comparison.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "sotoon_offer_prices.xlsx"
FEE = 0.05
EPS = 1e-6
DIRECT = {"openai", "anthropic"}  # Sotoon "provider" values bought from the maker itself
CUSTOMER_MAKERS = ("openai", "anthropic")

src = load_workbook(SRC, read_only=True)["Comparison"]
rows = [r for r in src.iter_rows(min_row=2, values_only=True) if r[1]]
# Comparison columns: 0 model, 1 provider, 4-7 Sotoon in/out/cache read/cache write,
# 8 OpenRouter ID, 9-12 OpenRouter in/out/cache read/cache write,
# 13 official model, 14 in, 15 out, 16 cache read, 17 cache write, 18 note, 23 source.


def with_fee(prices):
    return [None if p is None else round(p * (1 + FEE), 6) for p in prices]


def same(a, b):
    """Same price list, ignoring parts that one side does not publish."""
    return all(x is None or y is None or abs(x - y) < EPS for x, y in zip(a, b))


def maker_of(model):
    return model.lstrip("~").split("/")[0].lower() if "/" in model else None


PARTS = ("ورودی", "خروجی", "خواندن کش", "نوشتن کش")
out_rows = []
dropped = []
for r in rows:
    model, provider = r[0], r[1]
    maker = maker_of(model) or provider
    ours = list(r[4:8])
    openrouter = list(r[9:13])
    official = list(r[14:18])
    has_or = any(p is not None for p in openrouter[:2])
    has_off = any(p is not None for p in official[:2])
    notes = []

    # Reference cost: the source we buy from; if OpenRouter doesn't offer the
    # model, the original provider's price; if neither does, drop the model.
    if provider in DIRECT and has_off:
        source, cost = f"{provider} (direct)", official
    elif has_or:
        source, cost = "OpenRouter", openrouter
        if provider == "hosted_vllm":
            source = "OpenRouter (مرجع؛ میزبانی خودمان)"
        if provider in DIRECT:
            notes.append(f"No official {provider} price; OpenRouter price used")
    elif has_off:
        source, cost = "پرووایدر اصلی (در OpenRouter نیست)", official
    else:
        reason = ("Self-hosted by Sotoon" if provider == "hosted_vllm"
                  else "Neither OpenRouter nor the original provider offers it")
        dropped.append([model, maker, provider] + ours + [reason, r[24], r[25]])
        continue

    min1 = with_fee(cost)
    min2 = [None] * 4
    if has_off and cost is not official and not same(cost, official):
        min2 = with_fee(official)
    if not has_off:
        notes.append(r[18] or "No official price")

    # How far Min price 1 is below the customer's reference (official) price.
    gap_in = min1[0] / official[0] - 1 if min1[0] is not None and official[0] else None
    gap_out = min1[1] / official[1] - 1 if min1[1] is not None and official[1] else None

    # Components where buying via OpenRouter costs more than the original provider's price.
    pricier = []
    if source.startswith("OpenRouter") and any(p is not None for p in min2):
        pricier = [PARTS[i] for i in range(4)
                   if min1[i] is not None and min2[i] is not None and min1[i] > min2[i] + EPS]

    out_rows.append([model, maker, source] + ours + official + openrouter
                    + min1 + min2 + [gap_in, gap_out, "، ".join(pricier) or None,
                                     "; ".join(notes) or None, r[23], r[24], r[25], r[26]])

headers = (
    ["مدل", "سازنده", "منبع خرید ما"]
    + [f"قیمت فعلی ما - {p}" for p in ("ورودی", "خروجی", "خواندن کش", "نوشتن کش")]
    + [f"پرووایدر اصلی - {p}" for p in ("ورودی", "خروجی", "خواندن کش", "نوشتن کش")]
    + [f"OpenRouter - {p}" for p in ("ورودی", "خروجی", "خواندن کش", "نوشتن کش")]
    + [f"حداقل قیمت ۱ (منبع خرید + ۵٪) - {p}" for p in ("ورودی", "خروجی", "خواندن کش", "نوشتن کش")]
    + [f"حداقل قیمت ۲ (پرووایدر اصلی + ۵٪) - {p}" for p in ("ورودی", "خروجی", "خواندن کش", "نوشتن کش")]
    + ["حداقل قیمت ۱ نسبت به پرووایدر اصلی - ورودی", "حداقل قیمت ۱ نسبت به پرووایدر اصلی - خروجی",
       "OpenRouter گران‌تر از پرووایدر اصلی در", "توضیح", "منبع قیمت رسمی",
       "وضعیت در دسترس بودن", "منسوخ/حذف‌شده؟", "تاریخ حذف از OpenRouter"]
)
GROUPS = [(1, 3, "404040"), (4, 7, "305496"), (8, 11, "548235"), (12, 15, "7030A0"),
          (16, 19, "C65911"), (20, 23, "BF8F00"), (24, 25, "404040"), (26, 26, "674EA7"),
          (27, 28, "404040"), (29, 31, "7F7F7F")]
WIDTHS = [36, 12, 16] + [11] * 20 + [13, 13, 22, 45, 40, 40, 12, 14]
DEPRECATED_COL = 29
PRICIER_COL = 25
MONEY_COLS = range(3, 23)
PCT_COLS = (23, 24)
MIN1_FILL = PatternFill("solid", fgColor="FCE4D6")
MIN2_FILL = PatternFill("solid", fgColor="FFF2CC")
ABOVE_REF = PatternFill("solid", fgColor="FFC7CE")
PRICIER_ROW = PatternFill("solid", fgColor="D9D2E9")
PRICIER_CELL = PatternFill("solid", fgColor="B4A7D6")
DEPRECATED = PatternFill("solid", fgColor="BFBFBF")
MAYBE_DEPRECATED = PatternFill("solid", fgColor="EDEDED")


def write_sheet(ws, data, title):
    ws.sheet_view.rightToLeft = True
    ws.append([title])
    ws.cell(1, 1).font = Font(bold=True, size=13, color="1F3864")
    ws.append([f"حداقل قیمت = قیمت خرید × ۱٫۰۵ (۵٪ کارمزد صراف). قیمت‌ها دلار برای هر یک میلیون توکن. "
               f"تاریخ داده‌ها: {date.today().isoformat()}"])
    ws.append([])
    ws.append(headers)
    head_row = ws.max_row
    for c in ws[head_row]:
        fill = next(f for a, b, f in GROUPS if a <= c.column <= b)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=fill)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[head_row].height = 60
    for d in data:
        ws.append(d)
        row = ws[ws.max_row]
        for i in MONEY_COLS:
            row[i].number_format = "$#,##0.00####"
        for i in range(15, 19):
            if row[i].value is not None:
                row[i].fill = MIN1_FILL
        for i in range(19, 23):
            if row[i].value is not None:
                row[i].fill = MIN2_FILL
        for i in PCT_COLS:
            row[i].number_format = "0.0%"
            if isinstance(row[i].value, float) and row[i].value > EPS:
                row[i].fill = ABOVE_REF
        if row[PRICIER_COL].value:
            for i in (0, 1, 2, PRICIER_COL):
                row[i].fill = PRICIER_ROW
            for i, part in enumerate(PARTS):
                if part in row[PRICIER_COL].value.split("، "):
                    row[15 + i].fill = PRICIER_CELL
        if row[DEPRECATED_COL].value in ("بله", "شاید"):
            fill = DEPRECATED if row[DEPRECATED_COL].value == "بله" else MAYBE_DEPRECATED
            for i in (0, DEPRECATED_COL - 1, DEPRECATED_COL):
                row[i].fill = fill
    ws.freeze_panes = ws.cell(head_row + 1, 2)
    ws.auto_filter.ref = f"A{head_row}:{get_column_letter(len(headers))}{ws.max_row}"
    for i, w in enumerate(WIDTHS, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.append([])
    ws.append(["نارنجی: حداقل قیمت بر اساس منبع خرید. زرد: حداقل قیمت بر اساس قیمت پرووایدر اصلی "
               "(فقط وقتی با منبع خرید فرق دارد). قرمز در ستون درصد: حداقل قیمت ما از قیمت پرووایدر "
               "اصلی بالاتر است."])
    ws.append(["بنفش: خرید از OpenRouter در این جزء‌ها گران‌تر از قیمت پرووایدر اصلی است "
               "(خانه‌ی پررنگ‌تر همان جزء در حداقل قیمت ۱)."])
    ws.append(["خاکستری تیره: منسوخ یا حذف‌شده (از OpenRouter حذف شده یا حذفش زمان‌بندی شده، یا پرووایدر "
               "اصلی بازنشسته‌اش کرده). خاکستری روشن: در صفحه‌ی قیمت پرووایدر اصلی نیست (شاید منسوخ)."])
    ws.append(["قیمت OpenRouter همان قیمتی است که در صفحه‌ی هر مدل در openrouter.ai نمایش داده می‌شود."])


def order(r):
    return (CUSTOMER_MAKERS.index(r[1]) if r[1] in CUSTOMER_MAKERS else 9, r[0])


customer = sorted([r for r in out_rows if r[1] in CUSTOMER_MAKERS], key=order)
wb = Workbook()
write_sheet(wb.active, customer, "قیمت پیشنهادی - مدل‌های OpenAI و Anthropic")
wb.active.title = "OpenAI و Anthropic"
write_sheet(wb.create_sheet("همه‌ی مدل‌ها"), sorted(out_rows, key=order),
            "قیمت پیشنهادی - همه‌ی مدل‌ها")
ws = wb.create_sheet("حذف‌شده از لیست")
ws.sheet_view.rightToLeft = True
ws.append(["مدل‌هایی که نه در OpenRouter هستند و نه نزد پرووایدر اصلی؛ از لیست پیشنهاد قیمت حذف شدند."])
ws.cell(1, 1).font = Font(bold=True, size=13, color="1F3864")
ws.append([])
ws.append(["مدل", "سازنده", "منبع فعلی ما", "قیمت فعلی ما - ورودی", "قیمت فعلی ما - خروجی",
           "قیمت فعلی ما - خواندن کش", "قیمت فعلی ما - نوشتن کش", "علت", "وضعیت در دسترس بودن",
           "منسوخ/حذف‌شده؟"])
for c in ws[ws.max_row]:
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="7F7F7F")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
for d in sorted(dropped, key=order):
    ws.append(d)
    for c in ws[ws.max_row][3:7]:
        c.number_format = "$#,##0.00####"
for i, w in enumerate([40, 14, 14, 12, 12, 12, 12, 45, 45, 12], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
wb.save(OUT)

two = sum(1 for r in out_rows if r[19] is not None)
print("OpenRouter pricier:", [(r[0], r[PRICIER_COL]) for r in out_rows if r[PRICIER_COL]])
print(f"{len(out_rows)} models ({len(customer)} OpenAI/Anthropic); {two} with a second price; "
      f"{len(dropped)} dropped -> {OUT}")
