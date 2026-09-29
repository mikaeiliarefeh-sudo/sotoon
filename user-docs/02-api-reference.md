# مرجع API

> ⚠️ **یادداشت داخلی (قبل از انتشار حذف شود):** هر جا علامت ⚠️ هست یعنی هنوز روی API واقعی تأیید نشده.

API ستون با API شرکت OpenAI سازگار است. اگر با OpenAI کار کرده‌اید، همان روش را اینجا هم به کار ببرید.

**آدرس پایه:** `https://api.intelligence.sotoon.ir/inference/v1`

**احراز هویت:** کلید API را در هدر `Authorization` بفرستید:

```
Authorization: Bearer کلید-شما
```

در مثال‌ها فرض شده کلید در متغیر `SOTOON_API_KEY` ذخیره شده است. اگر هنوز کلید ندارید، [شروع سریع](01-quickstart.md) را ببینید.

---

## اندپوینت‌ها

| اندپوینت | کاربرد |
|---|---|
| `GET /models` | لیست مدل‌های در دسترس |
| `POST /chat/completions` | گفتگو با مدل (پرکاربردترین) |
| `POST /messages` | گفتگو با قالب Anthropic (برای Claude Code و SDK آنتروپیک) |
| `POST /embeddings` | تبدیل متن به بردار عددی |
| `POST /responses` ⚠️ | قالب Responses شرکت OpenAI (تأیید نشده) |
| تولید تصویر ⚠️ | فعلاً در دست بررسی است |

---

## لیست مدل‌ها

`GET /models`

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/models \
  -H "Authorization: Bearer $SOTOON_API_KEY"
```

پاسخ فقط شناسه‌ی مدل‌ها را می‌دهد:

```json
{ "data": [ { "id": "provider/model-name", "object": "model" } ] }
```

- شناسه را دقیقاً همان‌طور که برگشته در فیلد `model` بنویسید.
- لیست به کلید شما بستگی دارد.
- قیمت و مشخصات هر مدل در صفحه‌ی **مدل‌ها** در داشبورد است.
- فیلد `owned_by` معنای خاصی ندارد و به آن تکیه نکنید.

---

## گفتگو (Chat Completions)

`POST /chat/completions`

### پارامترها

| پارامتر | الزامی | توضیح |
|---|---|---|
| `model` | بله | شناسه‌ی مدل از `/models` |
| `messages` | بله | لیست پیام‌ها. هر پیام `role` (`system`، `user`، `assistant` یا `tool`) و `content` دارد. |
| `stream` | خیر | با `true` پاسخ زنده (استریم) می‌گیرید. |
| `max_tokens` | خیر | سقف توکن‌های پاسخ. **به هشدار زیر توجه کنید.** |
| `temperature` | خیر | میزان خلاقیت. ⚠️ *بازه‌ی مجاز بسته به مدل فرق می‌کند.* |
| `tools` و `tool_choice` | خیر | تعریف ابزار برای Tool Calling (پایین‌تر) |

هر پارامتر دیگری که مدل پشتیبانی کند، همان‌طور که در مستندات OpenAI است کار می‌کند.

### نمونه

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/chat/completions \
  -H "Authorization: Bearer $SOTOON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_ID",
    "messages": [
      { "role": "system", "content": "تو یک دستیار مفید هستی." },
      { "role": "user", "content": "سلام!" }
    ]
  }'
```

### پاسخ

| فیلد | معنی |
|---|---|
| `choices[0].message.content` | متن پاسخ |
| `choices[0].finish_reason` | دلیل پایان: `stop` (تمام شد)، `length` (به سقف توکن رسید)، `tool_calls` (مدل ابزار خواسته) |
| `usage` | توکن‌های ورودی، خروجی و کل. هزینه بر اساس همین حساب می‌شود. |
| `model` | نسخه‌ی دقیق مدلی که جواب داده. ممکن است کمی با چیزی که فرستادید فرق داشته باشد. |

### ⚠️ هشدار: پاسخ خالی در مدل‌های reasoning

مدل‌های reasoning قبل از جواب «فکر می‌کنند» و توکن‌های تفکر هم از `max_tokens` کم می‌شود. اگر سقف کوچک باشد، همه‌اش صرف تفکر می‌شود و `content` **خالی** برمی‌گردد و `finish_reason` برابر `length` است. `max_tokens` را بزرگ‌تر کنید یا ننویسید.

تعداد توکن‌های تفکر در `usage.completion_tokens_details.reasoning_tokens` دیده می‌شود.

### کنترل میزان تفکر ⚠️

بعضی مدل‌ها میزان تفکر را قابل تنظیم می‌کنند، ولی نام پارامتر بسته به سازنده‌ی مدل فرق دارد:

- مدل‌های OpenAI: `"reasoning_effort": "low"` (یا `medium`، `high`)
- بقیه‌ی مدل‌ها: `"reasoning": { "effort": "low" }`

اگر مدل reasoning را پشتیبانی نکند و این پارامتر را بفرستید، خطای ۴۰۰ می‌گیرید.
⚠️ *هر دو فرمت هنوز روی API واقعی تست نشده‌اند.*

---

## پاسخ زنده (Streaming)

با `"stream": true` پاسخ تکه‌تکه و در حین تولید می‌رسد. هر تکه یک خط `data: {...}` است. اگر از کتابخانه‌ی OpenAI استفاده می‌کنید، خودش این را مدیریت می‌کند:

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

متن هر تکه در `choices[0].delta.content` است.

---

## فراخوانی ابزار (Tool Calling)

می‌توانید به مدل بگویید چه ابزارهایی (تابع‌هایی) دارید. مدل خودش تصمیم می‌گیرد کی و با چه ورودی‌ای آن‌ها را صدا بزند. اجرای ابزار با کد شماست، نه مدل.

**۱. ابزار را تعریف کنید و درخواست بفرستید:**

```json
{
  "model": "MODEL_ID",
  "messages": [{ "role": "user", "content": "هوای تهران چطوره؟" }],
  "tools": [{
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "هوای یک شهر را برمی‌گرداند",
      "parameters": {
        "type": "object",
        "properties": { "city": { "type": "string" } },
        "required": ["city"]
      }
    }
  }]
}
```

**۲. اگر مدل ابزار خواست،** `finish_reason` برابر `tool_calls` است و پاسخ چنین چیزی دارد:

```json
"tool_calls": [{
  "id": "call_abc123",
  "type": "function",
  "function": { "name": "get_weather", "arguments": "{\"city\":\"Tehran\"}" }
}]
```

توجه کنید `arguments` یک **رشته‌ی JSON** است و باید آن را parse کنید.

**۳. تابع را خودتان اجرا کنید** و نتیجه را با نقش `tool` به مدل برگردانید:

```json
{ "role": "assistant", "content": null, "tool_calls": [ ...همان tool_calls بالا... ] },
{ "role": "tool", "tool_call_id": "call_abc123", "content": "۲۸ درجه، آفتابی" }
```

حالا همه‌ی `messages` را دوباره بفرستید. مدل جواب نهایی را می‌نویسد.

همه‌ی مدل‌ها ابزار را پشتیبانی نمی‌کنند. برای مطمئن شدن، مشخصات مدل را در داشبورد ببینید. ⚠️ *نیاز به تأیید: آیا مشخصات مدل در داشبورد پشتیبانی از ابزار را نشان می‌دهد؟*

---

## Embeddings

`POST /embeddings`

متن را به بردار عددی تبدیل می‌کند (برای جستجوی معنایی، دسته‌بندی و RAG). مدل‌های embedding در همان `/models` هستند.

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/embeddings \
  -H "Authorization: Bearer $SOTOON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "model": "EMBEDDING_MODEL_ID", "input": "سلام دنیا" }'
```

بردار در `data[0].embedding` برمی‌گردد. مدل‌های گفتگو را برای embedding به کار نبرید و برعکس.

---

## قالب Anthropic

`POST /messages`

برای Claude Code و ابزارهایی که با قالب Anthropic کار می‌کنند. این اندپوینت با **همه‌ی مدل‌ها** کار می‌کند، نه فقط مدل‌های Claude.

```bash
curl https://api.intelligence.sotoon.ir/inference/v1/messages \
  -H "Authorization: Bearer $SOTOON_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MODEL_ID",
    "max_tokens": 1024,
    "messages": [{ "role": "user", "content": "سلام!" }]
  }'
```

در این قالب `max_tokens` الزامی است. پاسخ در `content[0].text` است.

راه‌اندازی Claude Code در صفحه‌ی اتصال ابزارها توضیح داده می‌شود *(به‌زودی)*.

---

## خطاها

همه‌ی خطاها این قالب را دارند:

```json
{ "error": { "message": "...", "type": "...", "param": "...", "code": "400" } }
```

توجه: `code` یک **رشته** است، نه عدد.

| کد HTTP | دلیل رایج |
|---|---|
| `400` | پارامتر اشتباه. مثلاً `Invalid model name` یعنی اسم مدل غلط است یا کلید شما به آن دسترسی ندارد. |
| `401` | کلید شناخته نشد (اشتباه یا باطل شده). |
| `429` ⚠️ | تعداد درخواست‌ها زیاد است. *(قالب دقیق و محدودیت‌ها تأیید نشده)* |
| ⚠️ | بودجه‌ی workspace تمام شده است. *(کد و پیام دقیق تأیید نشده؛ بودجه را در صفحه‌ی «مصرف» ببینید و افزایش دهید.)* |
| `5xx` | خطای موقت سمت سرور یا ارائه‌دهنده‌ی مدل |

**توصیه:** برای خطاهای `429` و `5xx` درخواست را با فاصله‌ی زمانی رو به افزایش (۱ ثانیه، ۲، ۴، ...) دوباره بفرستید. برای `400` و `401` تکرار فایده ندارد.

---

## محدودیت‌ها ⚠️

- **حداکثر تعداد درخواست و توکن در دقیقه:** *نیاز به تأیید از تیم*
- **حداکثر اندازه‌ی ورودی (context):** برای هر مدل فرق دارد و در صفحه‌ی مدل‌ها در داشبورد است.

---

## نکات کاربردی

- **مصرف توکن را زیر نظر بگیرید.** فیلد `usage` در هر پاسخ تعداد دقیق توکن را می‌دهد.
- **برای پاسخ‌های طولانی از streaming استفاده کنید.** کاربر زودتر متن را می‌بیند.
- **اسم مدل را در تنظیمات نگه دارید، نه در کد.** مدل‌ها عوض می‌شوند و اینطوری بدون تغییر کد می‌توانید مدل را عوض کنید.
- **کلید API را هیچ‌وقت در کد سمت کاربر (مرورگر یا اپ موبایل) نگذارید.** درخواست‌ها را از سرور خودتان بفرستید.
