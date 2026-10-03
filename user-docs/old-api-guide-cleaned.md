# راهنمای استفاده از API

از طریق API هوش مصنوعی Workspace، به‌صورت برنامه‌نویسی با مدل‌های پیشرفته LLM تعامل داشته باشید.

## آدرس پایه (Base URL)

تمام درخواست‌ها به این آدرس ارسال می‌شوند:

```
https://api.intelligence.sotoon.ir/inference/v1
```

## احراز هویت

از کلید API خود برای احراز هویت استفاده کنید. کلیدهای خود را می‌توانید در بخش [کلیدهای API](https://workspace.intelligence.sotoon.ir/documentation?section=api-usage) مدیریت کنید.

کلید را در هدر `Authorization` ارسال کنید:

```
Authorization: Bearer YOUR_API_KEY
```

## شناسه‌ی مدل

مدل‌ها مرتب عوض می‌شوند، پس شناسه‌ی مدل را از صفحه‌ی **مدل‌ها** یا از خود API بردارید و دقیقاً کپی کنید:

```
curl 'https://api.intelligence.sotoon.ir/inference/v1/models' \
  -H 'Authorization: Bearer YOUR_API_KEY'
```

در مثال‌های زیر `MODEL_ID` را با شناسه‌ی مدل عوض کنید.

## تکمیل چت (Chat Completions)

با استفاده از اندپوینت Chat Completions، به مدل‌ها پیام بفرستید و پاسخ‌های هوشمند دریافت کنید.

### اندپوینت

`POST /chat/completions`

### نمونه درخواست

cURL

```
curl -X POST 'https://api.intelligence.sotoon.ir/inference/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{
    "model": "MODEL_ID",
    "messages": [
      { "role": "user", "content": "مکانیک کوانتومی را به زبان ساده توضیح دهید." }
    ]
  }'
```

Python (OpenAI SDK)

```
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://api.intelligence.sotoon.ir/inference/v1"
)

response = client.chat.completions.create(
    model="MODEL_ID",
    messages=[{"role": "user", "content": "مکانیک کوانتومی را به زبان ساده توضیح دهید."}]
)

print(response.choices[0].message.content)
```

### پارامترهای کلیدی

* model (الزامی): شناسه مدل (به شکل `provider/model-name`).
* messages (الزامی): لیستی از اشیاء پیام (شامل `role` و `content`).
* temperature: کنترل میزان خلاقیت. بازه‌ی مجاز بسته به مدل فرق می‌کند.
* stream: برای دریافت پاسخ به‌صورت استریم، روی `true` تنظیم کنید.

## پاسخ‌های استریمینگ (Streaming)

پاسخ‌ها را به‌محض تولید، تکه‌تکه دریافت کنید.

نمونه پایتون

```
stream = client.chat.completions.create(
    model="MODEL_ID",
    messages=[{"role": "user", "content": "یک داستان کوتاه بنویس."}],
    stream=True
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```
