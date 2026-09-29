# شروع سریع

در ۳ دقیقه اولین درخواست را به API هوش مصنوعی ستون بفرستید. این API با API شرکت OpenAI سازگار است؛ یعنی می‌توانید از کتابخانه‌ها و ابزارهای OpenAI استفاده کنید و فقط آدرس و کلید را عوض کنید.

| | |
|---|---|
| آدرس پایه | `https://api.intelligence.sotoon.ir/inference/v1` |
| احراز هویت | هدر `Authorization: Bearer کلید-شما` |

---

## ۱. کلید API را بردارید

1. در AI Workspace، از منوی کناری وارد **کلیدهای API** شوید. آدرس پایه بالای همین صفحه است و کنارش دکمه‌ی کپی دارد.
2. یکی از دو راه:
   - **کلید شخصی:** در بخش «کلید شخصی» روی **نمایش** بزنید. هر وقت لازم شد دوباره نمایش می‌دهد.
   - **کلید جدید:** برای هر پروژه یک کلید جدا با **ایجاد کلید** بسازید. ⚠️ *نیاز به تأیید: آیا کلید ساخته‌شده فقط یک بار کامل نمایش داده می‌شود؟*
3. کلید را در ترمینال ذخیره کنید تا در مثال‌ها هر بار ننویسید:

```bash
export SOTOON_API_KEY="کلید-شما"
```

> کلید را در کد، Git یا جای عمومی نگذارید. هزینه‌ی هر کسی که کلید را داشته باشد به حساب شما می‌آید.
> کلیدها و مصرف به workspace انتخاب‌شده در نوار بالا وابسته‌اند. ⚠️ *نیاز به تأیید*

---

## ۲. شناسه‌ی مدل را بردارید

مدل‌ها مرتب عوض می‌شوند، پس اسمشان را از خود API بگیرید:

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/models \
  -H "Authorization: Bearer $SOTOON_API_KEY"
```

مقدار `id` هر مدل را دقیقاً کپی کنید (بعضی مدل‌ها پیشوند دارند، مثل `provider/model-name`، و بعضی ندارند). لیست به کلید شما بستگی دارد. قیمت و مشخصات هر مدل در صفحه‌ی **مدل‌ها** (منوی کناری) است.

---

## ۳. اولین درخواست

در مثال‌ها `MODEL_ID` را با شناسه‌ی مدل عوض کنید.

**curl**

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/chat/completions \
  -H "Authorization: Bearer $SOTOON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_ID",
    "messages": [{ "role": "user", "content": "مکانیک کوانتومی را به زبان ساده توضیح بده." }]
  }'
```

**Python** (`pip install openai`)

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

**JavaScript** (`npm install openai`)

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

متن جواب در `choices[0].message.content` است. اگر خطا گرفتید یا جواب خالی بود، بخش «خطاها» و «پاسخ خالی» در [مرجع API](02-api-reference.md) را ببینید.

---

## قدم بعد

- **[مرجع API](02-api-reference.md):** streaming، فراخوانی ابزار، embeddings، خطاها، هزینه
- **[اتصال ابزارهای کدنویسی](03-coding-tools.md):** Claude Code، GitHub Copilot، OpenCode، Cursor، Codex
