# اتصال ابزارهای کدنویسی

> ⚠️ **یادداشت داخلی (قبل از انتشار حذف شود):** وضعیت هر بخش:
> - **VS Code:** از راهنمای قبلی که تست شده و کار کرده.
> - **Claude Code:** از راهنمای قبلی؛ اسلش پایانی آدرس و مدل سبک باید تست شود.
> - **OpenCode و Codex:** از مستندات رسمی آن‌ها؛ تست نشده.
> - **Cursor:** از راهنمای‌های عمومی؛ تست نشده و کم‌اطمینان‌تر است.

ستون با API شرکت OpenAI (و قالب Anthropic) سازگار است، پس هر ابزاری که آدرس و کلید سفارشی بپذیرد به آن وصل می‌شود. اینجا تنظیم پنج ابزار پرکاربرد آمده. هر بخش فقط چیزی را می‌گوید که مخصوص همان ابزار است.

---

## قبل از شروع (برای همه‌ی ابزارها)

| چه چیزی لازم است | از کجا بردارم |
|---|---|
| کلید API | AI Workspace ← **کلیدهای API** |
| آدرس پایه | بالای همان صفحه (کنارش دکمه‌ی کپی است) |
| شناسه‌ی مدل، `MODEL_ID` | صفحه‌ی **مدل‌ها** یا `GET /models`. دقیقاً کپی کنید. |

آدرس پایه بسته به ابزار کمی فرق دارد:

| ابزار | آدرس |
|---|---|
| Claude Code | `https://api.intelligence.sotoon.ir/inference/` |
| بقیه (VS Code، OpenCode، Cursor، Codex) | `https://api.intelligence.sotoon.ir/inference/v1` |

**مدل را چطور انتخاب کنم؟** ابزارهای کدنویسی برای کار کردن به فراخوانی ابزار (Tool Calling) نیاز دارند. مدلی با این قابلیت و context بزرگ انتخاب کنید (مشخصات در صفحه‌ی **مدل‌ها**).

**قبل از تنظیم ابزار، اتصال را تست کنید.** اگر لیست مدل‌ها برگشت، کلید و آدرس درست است:

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/models \
  -H "Authorization: Bearer $SOTOON_API_KEY"
```

برای ابزارهایی که کلید را از متغیر محیطی می‌خوانند (Claude Code، OpenCode، Codex)، کلید را ذخیره کنید. برای ماندگار شدن، همین خط را به `~/.zshrc` (یا `~/.bashrc`) اضافه کنید و ترمینال را دوباره باز کنید:

```bash
export SOTOON_API_KEY="کلید-شما"
```

---

## Claude Code

**نصب:**

```bash
npm install -g @anthropic-ai/claude-code
```

**تنظیم آدرس و کلید.** به آدرس پایانی `/` دقت کنید.

macOS و Linux (به `~/.zshrc` یا `~/.bashrc` اضافه کنید و `source ~/.zshrc` بزنید):

```bash
export ANTHROPIC_BASE_URL="https://api.intelligence.sotoon.ir/inference/"
export ANTHROPIC_AUTH_TOKEN="کلید-شما"
```

Windows (PowerShell). برای همین نشست:

```powershell
$env:ANTHROPIC_BASE_URL="https://api.intelligence.sotoon.ir/inference/"
$env:ANTHROPIC_AUTH_TOKEN="کلید-شما"
```

**اجرا با مدل دلخواه:**

```bash
claude --model MODEL_ID
```

یا برای همیشه: `export ANTHROPIC_MODEL="MODEL_ID"`.

> ⚠️ *نیاز به تأیید:* Claude Code برای کارهای سبک پس‌زمینه از یک مدل کوچک جدا استفاده می‌کند. اگر خطای «مدل پیدا نشد» دیدید، یک مدل سبک از لیست انتخاب کنید و تنظیم کنید: `export ANTHROPIC_DEFAULT_HAIKU_MODEL="MODEL_ID_سبک"`

---

## GitHub Copilot در VS Code

با افزونه‌ی **OAI Compatible Provider for Copilot** مدل‌های ستون را به Copilot اضافه می‌کنید.

**۱. نصب افزونه**

1. بخش Extensions را باز کنید (`Cmd+Shift+X` یا `Ctrl+Shift+X`).
2. عبارت «OAI Compatible Provider for Copilot» را جستجو و نصب کنید.

**۲. تنظیم آدرس و کلید**

1. Command Palette را باز کنید (`Cmd+Shift+P` یا `Ctrl+Shift+P`).
2. دستور **OAICopilot: Open Configuration UI** را اجرا کنید.
3. در بخش **Global Configuration**:
   - **Base URL:** `https://api.intelligence.sotoon.ir/inference/v1`
   - **API Key:** کلید شما
4. روی **Save Global Configuration** کلیک کنید.

**۳. اضافه کردن مدل**

1. در بخش **Provider Management** روی **Add Provider** کلیک کنید:
   - **ID:** `sotoon` (یا هر اسم دلخواه)
   - **Mode:** `OpenAI`
2. در بخش **Model Management** روی **Add Model** کلیک کنید:
   - **Display Name:** شناسه‌ی مدل (`MODEL_ID`)
   - **Context Length:** اندازه‌ی context همان مدل از صفحه‌ی **مدل‌ها** (اگر ندارید، `128000` را بگذارید)

**۴. فعال‌سازی در Copilot**

1. در نوار کناری Copilot، روی منوی انتخاب مدل کلیک کنید.
2. **Manage Models** ← **Add Model** ← **OAI-compatible** را انتخاب کنید.
3. مدلی که ساختید را انتخاب کنید.

هر مدل جدید را با همین روش (مرحله ۳ و ۴) اضافه کنید.

---

## OpenCode

فایل `opencode.json` را در ریشه‌ی پروژه بسازید (یا در تنظیمات سراسری OpenCode). در OpenCode مدل‌ها را باید **خودتان در `models` فهرست کنید:**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "sotoon": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Sotoon",
      "options": {
        "baseURL": "https://api.intelligence.sotoon.ir/inference/v1",
        "apiKey": "{env:SOTOON_API_KEY}"
      },
      "models": {
        "MODEL_ID": { "name": "نام دلخواه برای نمایش" }
      }
    }
  }
}
```

برای ساختن خودکار بخش `models` از لیست فعلی ستون:

```bash
curl -s https://api.intelligence.sotoon.ir/inference/v1/models \
  -H "Authorization: Bearer $SOTOON_API_KEY" \
| python3 -c 'import sys,json; print(json.dumps({m["id"]:{"name":m["id"]} for m in json.load(sys.stdin)["data"]}, indent=2))'
```

داخل OpenCode دستور `/models` را بزنید و مدل‌های **Sotoon** را ببینید. اگر می‌خواهید سقف context یا خروجی را تنظیم کنید، به مدل `"limit": { "context": ..., "output": ... }` اضافه کنید (اعداد از صفحه‌ی **مدل‌ها**).

---

## Cursor

1. Cursor Settings ← **Models** ← بخش **API Keys**.
2. در بخش OpenAI، کلید ستون را وارد کنید.
3. **Override OpenAI Base URL** را روشن کنید و `https://api.intelligence.sotoon.ir/inference/v1` را بنویسید (بدون `/chat/completions` در انتها).
4. **Add Custom Model** بزنید و `MODEL_ID` را وارد کنید. هر مدل را جداگانه اضافه کنید، چون Cursor مدل‌های ستون را خودش نمی‌شناسد.
5. **Verify** بزنید. Cursor یک درخواست آزمایشی می‌فرستد.
6. در Chat مدل را انتخاب کنید.

کلید و آدرس ستون جایگزین کلید OpenAI می‌شود. اگر Cursor را با کلید واقعی OpenAI هم استفاده می‌کنید، مراقب باشید مدل‌ها قاطی نشوند.

---

## Codex CLI

فایل `~/.codex/config.toml` را باز کنید (اگر نبود بسازید):

```toml
model = "MODEL_ID"
model_provider = "sotoon"

[model_providers.sotoon]
name = "Sotoon AI"
base_url = "https://api.intelligence.sotoon.ir/inference/v1"
env_key = "SOTOON_API_KEY"
wire_api = "chat"
```

- `env_key` **اسم** متغیر محیطی است، نه خود کلید.
- `model_provider` باید با اسم بخش `[model_providers.…]` یکی باشد. اسم‌های `openai`، `ollama` و `lmstudio` رزرو هستند.
- بعد `codex` را اجرا کنید، یا برای یک بار `codex --model MODEL_ID`.

> ⚠️ *نیاز به تأیید:* Codex پروتکل `responses` را ترجیح می‌دهد، ولی فقط `/chat/completions` ستون تست شده، برای همین `wire_api = "chat"` گذاشته‌ایم. اگر نسخه‌ی شما `chat` را نپذیرفت، اول `/responses` را با `curl` تست کنید (`{"model":"MODEL_ID","input":"hi"}`) و اگر جواب داد `wire_api = "responses"` بگذارید.

---

## اگر کار نکرد (برای همه‌ی ابزارها)

| نشانه | راه‌حل |
|---|---|
| خطای `401` | کلید را دوباره کپی کنید. برای ابزارهایی که از متغیر محیطی می‌خوانند، ترمینال را دوباره باز کنید و `echo $SOTOON_API_KEY` را بزنید. |
| `Invalid model name` | شناسه‌ی مدل با لیست یکی نیست یا کلید شما به آن دسترسی ندارد. لیست را دوباره بگیرید. |
| هیچ پاسخی نمی‌آید | اینترنت و VPN را چک کنید و با `curl` بالا تست کنید. برای Claude Code آدرس را با و بدون `/` امتحان کنید. |
| ابزار هنوز به سرویس اصلی وصل می‌شود | تنظیمات اعمال نشده. ترمینال یا ابزار را ببندید و دوباره باز کنید. |
| پاسخ خالی | مدل reasoning است و سقف توکن کم است. [مرجع API](02-api-reference.md)، بخش «پاسخ خالی». |
| حالت Agent ابزار را صدا نمی‌زند | مدل Tool Calling را پشتیبانی نمی‌کند. مدل دیگری انتخاب کنید. |

جزئیات همه‌ی خطاها، هزینه و بودجه در [مرجع API](02-api-reference.md) است. هزینه‌ی ابزارهای کدنویسی مثل API بر اساس توکن است و معمولاً زیاد می‌شود، پس صفحه‌ی **مصرف** را زیر نظر داشته باشید.

---

## منبع‌های رسمی

[VS Code](https://code.visualstudio.com/docs/copilot/customization/language-models) · [OpenCode](https://opencode.ai/docs/providers/) · [Codex](https://learn.chatgpt.com/docs/config-file/config-advanced) · [Cursor](https://cursor.com/docs)
