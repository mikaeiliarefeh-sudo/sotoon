# اتصال Codex CLI

> ⚠️ **یادداشت داخلی (قبل از انتشار حذف شود):** بر اساس مستندات رسمی Codex نوشته شده و روی Codex واقعی با ستون تست نشده. مقدار `wire_api` باید تأیید شود (پایین را ببینید).

Codex CLI دستیار کدنویسی شرکت OpenAI است که در ترمینال اجرا می‌شود. با تعریف ستون به‌عنوان یک provider سفارشی، می‌توانید مدل‌های ستون را در آن استفاده کنید.

---

## پیش‌نیازها

- Codex CLI نصب‌شده (طبق [راهنمای رسمی](https://developers.openai.com/codex))
- کلید API از صفحه‌ی **کلیدهای API** ([شروع سریع](01-quickstart.md))

---

## ۱. کلید را در ترمینال ذخیره کنید

```bash
export SOTOON_API_KEY="کلید-شما"
```

برای ماندگار شدن، این خط را به `~/.zshrc` (یا `~/.bashrc`) اضافه کنید.

---

## ۲. provider را تعریف کنید

فایل `~/.codex/config.toml` را باز کنید (اگر نبود، بسازید) و این را اضافه کنید:

```toml
model = "MODEL_ID"
model_provider = "sotoon"

[model_providers.sotoon]
name = "Sotoon AI"
base_url = "https://api.intelligence.sotoon.ir/inference/v1"
env_key = "SOTOON_API_KEY"
wire_api = "chat"
```

| فیلد | توضیح |
|---|---|
| `model` | شناسه‌ی مدل از `GET /models` یا صفحه‌ی **مدل‌ها** |
| `model_provider` | باید با اسم بخش `[model_providers.…]` یکی باشد. اسم‌های `openai`، `ollama` و `lmstudio` رزرو هستند و نباید استفاده شوند. |
| `env_key` | **اسم** متغیر محیطی که کلید در آن است (نه خود کلید) |
| `wire_api` | `chat` یعنی از `/chat/completions` استفاده شود. |

> ⚠️ *نیاز به تأیید:* Codex پروتکل `responses` را پیشنهاد می‌کند. اندپوینت `/responses` ستون هنوز تست نشده، برای همین در بالا `chat` گذاشته‌ایم. اگر نسخه‌ی شما `chat` را نپذیرفت، اول این را تست کنید و اگر جواب داد `wire_api = "responses"` بگذارید:
>
> ```bash
> curl https://api.intelligence.sotoon.ir/inference/v1/responses \
>   -H "Authorization: Bearer $SOTOON_API_KEY" \
>   -H "Content-Type: application/json" \
>   -d '{"model":"MODEL_ID","input":"hi"}'
> ```

---

## ۳. اجرا

```bash
codex
```

اگر می‌خواهید فقط برای یک بار مدل را عوض کنید:

```bash
codex --model MODEL_ID
```

---

## اگر کار نکرد

| نشانه | راه‌حل |
|---|---|
| خطای `401` | `echo $SOTOON_API_KEY` را بزنید. اگر خالی بود، ترمینال را دوباره باز کنید. |
| `Invalid model name` | `model` در فایل با لیست مدل‌ها یکی نیست. |
| Codex به OpenAI وصل می‌شود، نه ستون | `model_provider` را در `config.toml` چک کنید. |
| خطا درباره‌ی `wire_api` یا `/responses` | بخش ⚠️ بالا را ببینید. |

---

## منبع رسمی

[تنظیمات پیشرفته‌ی Codex](https://learn.chatgpt.com/docs/config-file/config-advanced)
