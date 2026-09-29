# اتصال OpenCode

> ⚠️ **یادداشت داخلی (قبل از انتشار حذف شود):** بر اساس مستندات رسمی OpenCode نوشته شده و روی OpenCode واقعی با ستون تست نشده.

OpenCode یک دستیار کدنویسی متن‌باز است که در ترمینال اجرا می‌شود. با تعریف ستون به‌عنوان یک «provider سازگار با OpenAI»، همه‌ی مدل‌های ستون در آن در دسترس می‌شوند.

---

## پیش‌نیازها

- OpenCode نصب‌شده ([راهنمای نصب رسمی](https://opencode.ai/docs/))
- کلید API از صفحه‌ی **کلیدهای API** ([شروع سریع](01-quickstart.md))

---

## ۱. کلید را در ترمینال ذخیره کنید

```bash
export SOTOON_API_KEY="کلید-شما"
```

برای ماندگار شدن، این خط را به `~/.zshrc` (یا `~/.bashrc`) اضافه کنید.

---

## ۲. ستون را به‌عنوان provider تعریف کنید

فایل `opencode.json` را در ریشه‌ی پروژه بسازید (یا در فایل تنظیمات سراسری OpenCode):

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
        "MODEL_ID": {
          "name": "نام دلخواه برای نمایش"
        }
      }
    }
  }
}
```

در OpenCode باید مدل‌ها را **خودتان در `models` فهرست کنید**. برای هر مدلی که می‌خواهید، یک ردیف با شناسه‌ی آن اضافه کنید. اگر چند مدل می‌خواهید، این دستور بخش `models` را از لیست فعلی ستون می‌سازد. خروجی را در فایل کپی کنید:

```bash
curl -s https://api.intelligence.sotoon.ir/inference/v1/models \
  -H "Authorization: Bearer $SOTOON_API_KEY" \
| python3 -c 'import sys,json; print(json.dumps({m["id"]:{"name":m["id"]} for m in json.load(sys.stdin)["data"]}, indent=2))'
```

برای مدل‌هایی که می‌خواهید سقف context یا خروجی را دقیق تنظیم کنید، فیلد `limit` را اضافه کنید (اعداد را از صفحه‌ی **مدل‌ها** بردارید):

```json
"MODEL_ID": {
  "name": "...",
  "limit": { "context": 200000, "output": 32000 }
}
```

---

## ۳. انتخاب و استفاده

در OpenCode دستور `/models` را بزنید. مدل‌های ستون را زیر نام **Sotoon** می‌بینید. یکی را انتخاب کنید و شروع کنید.

---

## اگر کار نکرد

| نشانه | راه‌حل |
|---|---|
| Sotoon در `/models` نیست | مطمئن شوید `opencode.json` در پوشه‌ی درست است و JSON معتبر است. OpenCode را ببندید و دوباره باز کنید. |
| خطای `401` | `echo $SOTOON_API_KEY` را بزنید. اگر خالی بود، ترمینال را دوباره باز کنید یا متغیر را تنظیم کنید. |
| `Invalid model name` | شناسه‌ی مدل در فایل با لیست مدل‌ها یکی نیست. |
| پاسخ خالی | مدل reasoning است و سقف خروجی کم است. `limit.output` را بزرگ‌تر کنید. |

---

## منبع رسمی

[مستندات providerهای OpenCode](https://opencode.ai/docs/providers/)
