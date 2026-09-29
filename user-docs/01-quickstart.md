# شروع سریع

در ۳ دقیقه اولین درخواست را به API هوش مصنوعی ستون بفرستید.

API ستون با API شرکت OpenAI سازگار است. یعنی می‌توانید از کتابخانه‌ها و ابزارهایی که برای OpenAI نوشته شده‌اند استفاده کنید و فقط **آدرس پایه** و **کلید** را عوض کنید.

| | |
|---|---|
| آدرس پایه (Base URL) | `https://api.intelligence.sotoon.ir/inference/v1` |
| احراز هویت | هدر `Authorization: Bearer کلید-شما` |

---

## ۱. کلید API بسازید

1. وارد داشبورد AI Workspace شوید و به بخش **کلیدهای API** بروید.
   ⚠️ *نیاز به تأیید: لینک دقیق این بخش.*
2. یک کلید جدید بسازید و اسمی برای آن بگذارید.
3. کلید را همان لحظه کپی کنید و جای امنی نگه دارید.
   ⚠️ *نیاز به تأیید: آیا کلید بعداً هم قابل نمایش است؟*

> **مراقب کلید باشید.** آن را در کد یا مخزن Git نگذارید و با کسی به اشتراک نگذارید. هر کسی که کلید را داشته باشد، هزینه‌ی مصرف به حساب شما می‌آید.

برای اینکه در مثال‌های زیر مجبور نباشید کلید را هر بار بنویسید، آن را در ترمینال ذخیره کنید:

```bash
export SOTOON_API_KEY="کلید-شما"
```

---

## ۲. مدل‌های در دسترس را ببینید

مدل‌ها مرتب اضافه و کم می‌شوند؛ برای همین همیشه لیست را از خود API بگیرید:

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/models \
  -H "Authorization: Bearer $SOTOON_API_KEY"
```

در پاسخ، لیستی از مدل‌ها می‌بینید. مقدار `id` هر مدل، همان چیزی است که باید در درخواست‌ها بنویسید:

```json
{
  "data": [
    { "id": "provider/model-name", "object": "model" }
  ]
}
```

چند نکته:

- اسم مدل را **دقیقاً همان‌طور که برگشته** کپی کنید. بعضی مدل‌ها پیشوند ندارند و بعضی دارند (مثل `provider/model-name`).
- مدل‌هایی که می‌بینید به کلید شما بستگی دارد و ممکن است با دیگران فرق کند.
- قیمت، اندازه‌ی context و نوع ورودی هر مدل (متن، تصویر، صدا) در این پاسخ نیست. آن‌ها را در صفحه‌ی **مدل‌ها** در داشبورد ببینید.
  ⚠️ *نیاز به تأیید: لینک دقیق صفحه‌ی مدل‌ها.*

---

## ۳. اولین درخواست را بفرستید

در مثال‌ها به‌جای `MODEL_ID` یکی از اسم‌های مرحله‌ی قبل را بگذارید.

### curl

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/chat/completions \
  -H "Authorization: Bearer $SOTOON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_ID",
    "messages": [
      { "role": "user", "content": "مکانیک کوانتومی را به زبان ساده توضیح بده." }
    ]
  }'
```

### Python

```bash
pip install openai
```

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["SOTOON_API_KEY"],
    base_url="https://api.intelligence.sotoon.ir/inference/v1",
)

response = client.chat.completions.create(
    model="MODEL_ID",
    messages=[{"role": "user", "content": "مکانیک کوانتومی را به زبان ساده توضیح بده."}],
)

print(response.choices[0].message.content)
```

### JavaScript (Node.js)

```bash
npm install openai
```

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.SOTOON_API_KEY,
  baseURL: "https://api.intelligence.sotoon.ir/inference/v1",
});

const response = await client.chat.completions.create({
  model: "MODEL_ID",
  messages: [{ role: "user", content: "مکانیک کوانتومی را به زبان ساده توضیح بده." }],
});

console.log(response.choices[0].message.content);
```

### پاسخ

متن جواب مدل در `choices[0].message.content` است:

```json
{
  "choices": [
    {
      "finish_reason": "stop",
      "message": { "role": "assistant", "content": "..." }
    }
  ],
  "usage": { "prompt_tokens": 7, "completion_tokens": 178, "total_tokens": 185 }
}
```

بخش `usage` تعداد توکن‌های مصرفی را نشان می‌دهد. هزینه‌ی شما بر اساس همین عددها حساب می‌شود.

---

## ۴. پاسخ را به‌صورت زنده (استریم) بگیرید

برای پاسخ‌های طولانی بهتر است متن همزمان با تولید نمایش داده شود. کافی است `stream` را `true` کنید:

```python
stream = client.chat.completions.create(
    model="MODEL_ID",
    messages=[{"role": "user", "content": "یک داستان کوتاه بنویس."}],
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## اگر پاسخ خالی بود

بعضی مدل‌ها قبل از جواب دادن «فکر می‌کنند» (مدل‌های reasoning). توکن‌های این تفکر هم از سقف `max_tokens` کم می‌شوند.

اگر `max_tokens` را کوچک بگذارید، ممکن است تمام سقف صرف تفکر شود و جواب **خالی** برگردد. نشانه‌اش این است:

```json
{ "finish_reason": "length", "message": { "content": "" } }
```

راه‌حل: `max_tokens` را بزرگ‌تر کنید (مثلاً چند صد یا چند هزار)، یا اصلاً آن را ننویسید.

---

## اگر خطا گرفتید

خطاها همیشه این قالب را دارند:

```json
{
  "error": {
    "message": "توضیح خطا",
    "type": "...",
    "param": "...",
    "code": "401"
  }
}
```

| کد | معنی | چه کنم؟ |
|---|---|---|
| `401` | کلید شناخته نشد | کلید را دوباره کپی کنید. مطمئن شوید کلید باطل نشده باشد و بعد از `Bearer` یک فاصله باشد. |
| `400` با پیام `Invalid model name` | اسم مدل اشتباه است یا کلید شما به آن دسترسی ندارد | لیست مدل‌ها را (مرحله ۲) دوباره بگیرید و اسم را دقیقاً کپی کنید. |
| هیچ پاسخی نمی‌آید | مشکل اتصال | اینترنت و VPN را بررسی کنید. در `curl` گزینه‌ی `--max-time 60` بگذارید تا بعد از مدتی خطا بدهد. |

⚠️ *نیاز به تأیید: محدودیت تعداد درخواست (خطای ۴۲۹) و قالب آن.*

---

## قدم بعدی

- **مرجع API:** همه‌ی اندپوینت‌ها و پارامترها *(به‌زودی)*
- **اتصال ابزارهای کدنویسی:** Claude Code، GitHub Copilot و دیگران *(به‌زودی)*
- **انتخاب مدل مناسب** *(به‌زودی)*
- **قیمت‌گذاری** *(به‌زودی)*
