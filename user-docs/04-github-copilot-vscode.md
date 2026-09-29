# اتصال GitHub Copilot در VS Code

> ⚠️ **یادداشت داخلی (قبل از انتشار حذف شود):** بر اساس مستندات رسمی VS Code نوشته شده و روی VS Code واقعی با ستون تست نشده.

می‌توانید در بخش Chat مربوط به Copilot در VS Code، مدل‌های ستون را انتخاب کنید. VS Code برای این کار قابلیت **Custom Endpoint** دارد و دیگر نیازی به افزونه‌ی جانبی نیست.

---

## پیش‌نیازها

- نسخه‌ی به‌روز VS Code
- افزونه‌ی GitHub Copilot Chat
- کلید API از صفحه‌ی **کلیدهای API** ([شروع سریع](01-quickstart.md))
- اگر از Copilot Business یا Enterprise استفاده می‌کنید، مدیر سازمان باید سیاست «Bring Your Own Language Model Key» را فعال کرده باشد. در پلن‌های شخصی این محدودیت نیست.

---

## ۱. اضافه کردن Custom Endpoint

1. در VS Code، Command Palette را باز کنید (`Cmd+Shift+P` یا `Ctrl+Shift+P`) و دستور **Chat: Manage Language Models** را اجرا کنید.
2. **Add Models** و بعد **Custom Endpoint** را انتخاب کنید.
3. یک نام گروه (مثلاً `Sotoon`)، یک نام نمایشی و کلید API خود را وارد کنید.
4. نوع API را **Chat Completions** بگذارید.
5. VS Code فایل `chatLanguageModels.json` را باز می‌کند. مشخصات مدل‌ها را در آن بنویسید.

---

## ۲. مشخصات مدل‌ها

برای هر مدلی که می‌خواهید استفاده کنید یک ردیف اضافه کنید:

```json
[
  {
    "name": "Sotoon",
    "vendor": "customendpoint",
    "apiKey": "${input:sotoonApiKey}",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "MODEL_ID",
        "name": "نام دلخواه برای نمایش",
        "url": "https://api.intelligence.sotoon.ir/inference/v1/chat/completions",
        "toolCalling": true,
        "maxInputTokens": 128000,
        "maxOutputTokens": 16000
      }
    ]
  }
]
```

توضیح فیلدها:

| فیلد | چه بنویسم؟ |
|---|---|
| `id` | شناسه‌ی مدل، دقیقاً همان‌طور که در `GET /models` یا صفحه‌ی **مدل‌ها** آمده |
| `url` | همیشه `https://api.intelligence.sotoon.ir/inference/v1/chat/completions` |
| `toolCalling` | `true` اگر مدل از فراخوانی ابزار پشتیبانی می‌کند (برای حالت Agent لازم است) |
| `maxInputTokens` | اندازه‌ی context همان مدل، از صفحه‌ی **مدل‌ها**. عدد نمونه‌ی بالا فقط مثال است. |
| `maxOutputTokens` | سقف پاسخ. برای مدل‌های reasoning عدد بزرگ‌تری بگذارید، چون تفکر مدل هم از این سقف مصرف می‌شود. |

لیست مدل‌ها مرتب عوض می‌شود. برای اینکه اسم‌ها را دستی ننویسید، لیست را از API بگیرید:

```bash
curl -s https://api.intelligence.sotoon.ir/inference/v1/models \
  -H "Authorization: Bearer $SOTOON_API_KEY"
```

---

## ۳. انتخاب مدل در Copilot

1. پنجره‌ی Chat را باز کنید.
2. از منوی انتخاب مدل، مدلی را که ساختید انتخاب کنید.

---

## اگر کار نکرد

| نشانه | راه‌حل |
|---|---|
| مدل در منو دیده نمی‌شود | فایل `chatLanguageModels.json` را چک کنید. JSON باید معتبر باشد و `vendor` برابر `customendpoint` باشد. |
| خطای `401` | کلید را دوباره وارد کنید. |
| `Invalid model name` | `id` مدل غلط است. لیست مدل‌ها را دوباره بگیرید. |
| حالت Agent ابزار را صدا نمی‌زند | مدل ابزار را پشتیبانی نمی‌کند یا `toolCalling` روی `true` نیست. |
| گزینه‌ی Custom Endpoint نیست | VS Code را به‌روز کنید. در سازمان‌ها ممکن است مدیر آن را غیرفعال کرده باشد. |

---

## منبع رسمی

جزئیات کامل و تغییرات جدید را در [مستندات مدل‌های زبانی VS Code](https://code.visualstudio.com/docs/copilot/customization/language-models) ببینید. منوها ممکن است با نسخه‌ها کمی فرق کنند.
