# اتصال ابزارهای کدنویسی

> ⚠️ **یادداشت داخلی (قبل از انتشار حذف شود):** وضعیت هر بخش:
> - **VS Code (Copilot):** مراحل از راهنمای قبلی است که قبلاً (توسط تیم) کار کرده. در تست ما (اکتبر ۲۰۲۶) با طرح **Copilot Free**: افزونه‌ی OAI Compatible نصب و Provider و مدل (`deepseek/deepseek-v4-flash-0731`) ثبت شد و در Language Models با برچسب Tools دیده شد، ولی در منوی مدل چت (فقط Auto و مدل‌های Copilot) ظاهر نشد؛ علت نامشخص (احتمالاً محدودیت طرح رایگان یا سیاست حساب). چت با Auto خطای «Sorry, something went wrong» داد. پس در این محیط تا انتها تأیید نشد.
> - **Claude Code:** روی افزونه‌ی VS Code با مدل‌های `deepseek/deepseek-v4-flash-0731` و `qwen/qwen3-next-80b-a3b-instruct` تا انتها تست شده (پیام ساده، خوندن فایل، ساخت و اجرای فایل، و دستور `/model` با اسم مدل). `/status` تأیید کرد که مدل، آدرس و کلید درست‌اند. مدل‌های `openai/...` خطا می‌دهند (در دست بررسی). روش ترمینال و دسکتاپ از مستند رسمی است و تست نشده.
> - **OpenCode و Codex:** از مستندات رسمی؛ تست نشده.
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
| Claude Code | `https://api.intelligence.sotoon.ir/inference` (بدون `/` آخر و بدون `/v1`) |
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

Claude Code را می‌توانید با **افزونه‌ی VS Code** (ساده‌تر، بدون ترمینال) یا از **ترمینال** به ستون وصل کنید. هر دو بدون اشتراک Claude کار می‌کنند و هزینه بر اساس توکن از حساب ستون محاسبه می‌شود.

> **اپ دسکتاپ و وب Claude Code (claude.ai/code) به‌طور پیش‌فرض به ستون وصل نمی‌شوند.** وب همیشه از سرور خود Anthropic استفاده می‌کند و اپ دسکتاپ فقط با تنظیم جداگانه‌ی «Third-Party Inference» ممکن است. اشتراک Claude هم فقط برای همان‌ها لازم است، نه برای اتصال به ستون.

### تنظیمات لازم (برای هر دو روش)

| متغیر | مقدار | توضیح |
|---|---|---|
| `ANTHROPIC_BASE_URL` | `https://api.intelligence.sotoon.ir/inference` | بدون `/` آخر و بدون `/v1` |
| `ANTHROPIC_AUTH_TOKEN` | کلید API | |
| `ANTHROPIC_MODEL` | `MODEL_ID` | شناسه‌ی مدل از صفحه‌ی **مدل‌ها** |
| `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` | `1` | قابلیت‌های آزمایشی مخصوص Anthropic را خاموش می‌کند. بدون آن مدل‌های غیر Claude خطای `400` می‌دهند. |

### روش ۱: افزونه‌ی VS Code (پیشنهادی)

1. در Extensions، افزونه‌ی **Claude Code** (ناشر: Anthropic) را نصب کنید. این افزونه نسخه‌ی خودش از Claude Code را همراه دارد و نصب جداگانه‌ی ترمینالی لازم نیست.
2. `Cmd+Shift+P` (در Windows: `Ctrl+Shift+P`) را بزنید و **Preferences: Open User Settings (JSON)** را انتخاب کنید.
3. این بلوک را داخل آکولاد اصلی فایل اضافه کنید. اگر خط قبلی ویرگول ندارد، ویرگول بگذارید:

```json
"claudeCode.environmentVariables": [
  { "name": "ANTHROPIC_BASE_URL", "value": "https://api.intelligence.sotoon.ir/inference" },
  { "name": "ANTHROPIC_AUTH_TOKEN", "value": "کلید-شما" },
  { "name": "ANTHROPIC_MODEL", "value": "MODEL_ID" },
  { "name": "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS", "value": "1" }
],
"claudeCode.disableLoginPrompt": true
```

4. فایل را ذخیره کنید و VS Code را کامل ببندید و دوباره باز کنید (`Cmd+Q`).
5. پنل Claude Code را باز کنید. اگر کادر پیام را دیدید (نه صفحه‌ی ورود)، وصل شده است.

> کلید در این فایل به‌صورت متن ساده ذخیره می‌شود. اگر Settings Sync روشن است یا فایل را به اشتراک می‌گذارید، مراقب باشید.

### روش ۲: ترمینال

نصب (macOS و Linux):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

بعد ترمینال را ببندید و دوباره باز کنید و با `claude --version` مطمئن شوید نصب شده است. سپس:

```bash
export ANTHROPIC_BASE_URL="https://api.intelligence.sotoon.ir/inference"
export ANTHROPIC_AUTH_TOKEN="کلید-شما"
export ANTHROPIC_MODEL="MODEL_ID"
export CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
claude
```

برای ماندگار شدن، همین خطوط را به `~/.zshrc` اضافه کنید. روی Windows از `$env:NAME="..."` در PowerShell استفاده کنید. داخل Claude Code دستور `/status` را بزنید: خط `Anthropic base URL` باید آدرس ستون، خط `Auth token` باید `ANTHROPIC_AUTH_TOKEN` و خط `Model` مدل شما باشد.

### انتخاب مدل در Claude Code

منوی `/model` فقط مدل‌های خود Anthropic (Fable، Sonnet، Haiku) و مدل `ANTHROPIC_MODEL` را نشان می‌دهد و **لیست مدل‌های ستون را خودکار نمی‌آورد**. مدل‌های Anthropic این منو را انتخاب نکنید، چون اسمشان در ستون نیست. برای مدل دیگر:

- **تایپ اسم:** داخل Claude Code بنویسید `/model MODEL_ID`. هر اسمی که ستون بپذیرد قبول می‌شود. این تغییر فقط برای همان گفتگوست؛ برای عوض کردن مدل پیش‌فرض، `ANTHROPIC_MODEL` را تغییر دهید. برچسب مدل پایین کادر پیام ممکن است بعد از `/model` به‌روز نشود؛ مدل واقعی را با `/status` ببینید.
- **لیست دلخواه:** در فایل `~/.claude/settings.json` یک `modelPicker` بسازید و مدل‌های مورد نظرتان را یک بار در آن بنویسید.
- **لیست خودکار (محدود):** با `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` فقط مدل‌هایی که اسمشان `claude` یا `anthropic` دارد در منو می‌آیند.

اسم‌های دقیق را از صفحه‌ی **مدل‌ها** بردارید.

### محدودیت‌های شناخته‌شده

- **مدل‌های OpenAI (`openai/...`) فعلاً خطای `400 Unknown parameter: 'output_config'` می‌دهند.** علت از سمت سرویس است (فیلدهای مخصوص Anthropic که Claude Code می‌فرستد به مدل‌های OpenAI رد می‌شوند) و با تنظیم کلاینت حل نمی‌شود. ⚠️ *رفع آن در دست بررسی توسط تیم فنی است. تا آن زمان، برای Claude Code از مدل‌های دیگر (غیر `openai/...`) استفاده کنید.*
- **مدل باید tool calling را پشتیبانی کند.** Claude Code و ابزارهای کدنویسی همیشه ابزار (`tools`) می‌فرستند. بعضی مدل‌ها (مثلاً بعضی مدل‌های میزبانی‌شده‌ی خود سرویس مثل `google/gemma3-27b`) با خطای `400 ... "auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set` رد می‌کنند. در این صورت مدل دیگری انتخاب کنید. ⚠️ *فهرست مدل‌های سازگار با ابزارهای کدنویسی هنوز مشخص نیست؛ از تیم فنی بپرسید یا در صفحه‌ی مدل‌ها نشان داده شود.*
- **دستور `/model openai/...` ممکن است با `model not changed` رد شود** (خطای OpenAI درباره‌ی سقف خروجی، چون درخواست تأیید مدل سقف خیلی کوچکی دارد). به‌جای آن مدل را با متغیر `ANTHROPIC_MODEL` تنظیم کنید. ⚠️ *بعد از رفع مشکل بالا دوباره تست شود.*
- ⚠️ *Anthropic استفاده از Claude Code با مدل‌های غیر Claude را به‌صورت رسمی پشتیبانی نمی‌کند. این روش کار می‌کند ولی ممکن است بعضی قابلیت‌ها (مثل سطح تفکر) رفتار متفاوتی داشته باشند.*
- اولین پاسخ بعد از باز کردن VS Code ممکن است ۱۰ تا ۱۵ ثانیه طول بکشد. پاسخ‌های بعدی سریع‌تر است (حدود ۵ ثانیه). ⚠️ *با یک تست و یک مدل اندازه‌گیری شده.*
- **از خود مدل نپرسید «چه مدلی هستی؟».** Claude Code به همه‌ی مدل‌ها می‌گوید «تو Claude هستی»، پس هر مدلی همین را جواب می‌دهد. مدل فعلی را با `/status` ببینید.
- ⚠️ *نیاز به تأیید حقوقی/محصول: مستند رسمی Claude Code استفاده از آن را به «کشورهای پشتیبانی‌شده‌ی Anthropic» محدود می‌کند.*

### اگر کار نکرد

| نشانه | راه‌حل |
|---|---|
| افزونه صفحه‌ی ورود نشان می‌دهد | `claudeCode.disableLoginPrompt` را `true` کنید، فایل را ذخیره کنید و VS Code را کامل ببندید و باز کنید. |
| `400 ... Unknown parameter` | متغیر `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` را اضافه کنید. اگر برای مدل `openai/...` است، به بخش «محدودیت‌های شناخته‌شده» نگاه کنید. |
| `Invalid model name` | شناسه‌ی مدل غلط است یا از منوی Anthropic انتخاب شده. با `/model MODEL_ID` اسم دقیق را بنویسید. |
| مدل می‌گوید «من Claude هستم» | عادی است و به معنی اشتباه بودن تنظیمات نیست. مدل واقعی را با `/status` ببینید. |
| `command not found: claude` (ترمینال) | ترمینال را ببندید و باز کنید. اگر نشد: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc` |

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
