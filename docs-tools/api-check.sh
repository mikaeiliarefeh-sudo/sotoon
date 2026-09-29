#!/usr/bin/env bash
# ------------------------------------------------------------------
# تست اندپوینت‌های API ستون (با curl)
# Sotoon AI Workspace API smoke test
#
# استفاده:
#   export SOTOON_API_KEY="کلید-شما"          # کلید را جایی چاپ یا ارسال نکنید
#   bash api-check.sh                         # تست سریع و ارزان
#   bash api-check.sh --full                  # + embeddings و تولید تصویر (ممکن است هزینه داشته باشد)
#
# متغیرهای اختیاری:
#   MODEL=...        مدلی که برای تست چت استفاده شود (پیش‌فرض: اولین مدل از /models)
#   EMBED_MODEL=...  مدل embedding برای --full
#   IMAGE_MODEL=...  مدل تصویر برای --full
#   BASE_URL=...     پیش‌فرض: https://api.intelligence.sotoon.ir/inference
#   TIMEOUT=60       حداکثر ثانیه‌ی انتظار برای هر درخواست
# ------------------------------------------------------------------

KEY="${SOTOON_API_KEY:-}"
BASE="${BASE_URL:-https://api.intelligence.sotoon.ir/inference}"
TIMEOUT="${TIMEOUT:-60}"
MODEL="${MODEL:-}"
EMBED_MODEL="${EMBED_MODEL:-openai/text-embedding-3-small}"
IMAGE_MODEL="${IMAGE_MODEL:-openai/dall-e-3}"
FULL=0
[ "$1" = "--full" ] && FULL=1

if [ -z "$KEY" ]; then
  echo "❌ متغیر SOTOON_API_KEY تنظیم نشده."
  echo '   اول این را بزنید:  export SOTOON_API_KEY="کلید-شما"'
  exit 1
fi

OUT="api-check-results"
mkdir -p "$OUT"
SUMMARY="$OUT/summary.txt"
: > "$SUMMARY"

snippet() { head -c 300 "$1" 2>/dev/null | tr '\n' ' '; }

record() { # name verdict detail
  printf '%-34s %s  %s\n' "$1" "$2" "$3" | tee -a "$SUMMARY"
}

curl_hint() { # exit code -> hint
  case "$1" in
    6)  echo "آدرس پیدا نشد (DNS). اینترنت/VPN را چک کنید." ;;
    7)  echo "اتصال برقرار نشد. اینترنت، VPN یا فایروال را چک کنید." ;;
    28) echo "تایم‌اوت (${TIMEOUT}s). سرور جواب نداد؛ VPN/پروکسی را چک کنید یا TIMEOUT را بیشتر کنید." ;;
    35|60) echo "مشکل گواهی SSL." ;;
    *)  echo "curl با کد $1 تمام شد." ;;
  esac
}

# call NAME METHOD PATH BODY [extra curl args...]
# نتیجه در متغیرهای CODE و TIME می‌ماند و فایل‌ها در پوشه‌ی نتایج ذخیره می‌شوند
call() {
  local name="$1" method="$2" path="$3" body="$4"
  shift 4
  local out="$OUT/$name.body" hdr="$OUT/$name.headers"
  local args=(-sS -X "$method" --max-time "$TIMEOUT" -D "$hdr" -o "$out"
              -w '%{http_code} %{time_total}' -H "Authorization: Bearer $KEY")
  if [ -n "$body" ]; then
    args+=(-H "Content-Type: application/json" -d "$body")
  fi
  local res rc
  res=$(curl "${args[@]}" "$@" "$BASE$path" 2>"$OUT/$name.err")
  rc=$?
  CODE="000"; TIME="-"
  if [ $rc -ne 0 ]; then
    CODE="ERR"
    LAST_ERR="$(curl_hint $rc) | $(head -c 200 "$OUT/$name.err" | tr '\n' ' ')"
    return 1
  fi
  CODE="${res%% *}"
  TIME="${res##* }"
  return 0
}

# verdict helper: ok if 2xx
report() { # name what-it-proves
  local name="$1"
  if [ "$CODE" = "ERR" ]; then
    record "$name" "❌" "بدون پاسخ: $LAST_ERR"
  elif [ "${CODE:0:1}" = "2" ]; then
    record "$name" "✅" "HTTP $CODE (${TIME}s)"
  else
    record "$name" "❌" "HTTP $CODE (${TIME}s) → $(snippet "$OUT/$name.body")"
  fi
}

echo "=== آدرس پایه: $BASE ==="
echo "=== نتایج کامل در پوشه‌ی $OUT ذخیره می‌شود (کلید در آن‌ها نیست) ==="
echo

# 0) آیا اصلاً سرور جواب می‌دهد؟ ------------------------------------
HOST=$(echo "$BASE" | sed -E 's#https?://([^/]+).*#\1#')
pre=$(curl -sS -o /dev/null --max-time 15 -w '%{http_code} %{time_total}' "https://$HOST/" 2>"$OUT/preflight.err")
prc=$?
if [ $prc -ne 0 ]; then
  record "0. اتصال به $HOST" "❌" "$(curl_hint $prc)"
  echo
  echo "تا وقتی اتصال برقرار نشود بقیه‌ی تست‌ها بی‌فایده است. اول این را تست کنید:"
  echo "  curl -v --max-time 15 https://$HOST/"
  exit 1
fi
record "0. اتصال به $HOST" "✅" "HTTP ${pre%% *} (${pre##* }s)"

# 1) لیست مدل‌ها ----------------------------------------------------
call models GET /v1/models ""
report models
if [ "$CODE" = "200" ]; then
  N=$(grep -o '"id"' "$OUT/models.body" | wc -l | tr -d ' ')
  echo "     ≈ $N مدل در پاسخ (تعداد تقریبی)"
  if [ -z "$MODEL" ]; then
    MODEL=$(grep -oE '"id" *: *"[^"]*"' "$OUT/models.body" | head -1 | sed -E 's/.*: *"([^"]*)"/\1/')
    echo "     مدل تست (خودکار): $MODEL   ← برای انتخاب مدل ارزان‌تر: MODEL=... bash api-check.sh"
  fi
fi
if [ -z "$MODEL" ]; then
  echo "❌ مدلی برای تست پیدا نشد. با MODEL=... مشخص کنید."
  exit 1
fi
echo

# 2) chat/completions ----------------------------------------------
BODY=$(printf '{"model":"%s","max_tokens":20,"messages":[{"role":"user","content":"Say hi in one word."}]}' "$MODEL")
call chat POST /v1/chat/completions "$BODY"
report chat
echo "     مدل: $MODEL"
# هدرهای rate limit (اگر وجود داشته باشد)
RL=$(grep -i 'ratelimit\|retry-after' "$OUT/chat.headers" 2>/dev/null | tr -d '\r' | tr '\n' ' ')
[ -n "$RL" ] && echo "     هدرهای rate limit: $RL" || echo "     هدر rate limit در پاسخ دیده نشد"

# 3) streaming ------------------------------------------------------
BODY=$(printf '{"model":"%s","max_tokens":20,"stream":true,"messages":[{"role":"user","content":"Count 1 to 3."}]}' "$MODEL")
call stream POST /v1/chat/completions "$BODY" -N
if [ "$CODE" = "200" ] && grep -q '^data:' "$OUT/stream.body"; then
  record stream "✅" "HTTP 200 (${TIME}s) — رشته‌ی data: دریافت شد"
else
  report stream
fi

# 4) tool calling ---------------------------------------------------
BODY=$(printf '{"model":"%s","max_tokens":200,"messages":[{"role":"user","content":"What is the weather in Tehran? Use the tool."}],"tools":[{"type":"function","function":{"name":"get_weather","description":"Get weather for a city","parameters":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}}],"tool_choice":"auto"}' "$MODEL")
call tools POST /v1/chat/completions "$BODY"
if [ "$CODE" = "200" ] && grep -q 'tool_calls' "$OUT/tools.body"; then
  record tools "✅" "HTTP 200 (${TIME}s) — مدل tool_calls برگرداند"
elif [ "$CODE" = "200" ]; then
  record tools "⚠️" "HTTP 200 ولی tool_calls برنگشت (شاید مدل پشتیبانی نمی‌کند)"
else
  report tools
fi

# 5) reasoning (دو فرمت) --------------------------------------------
BODY=$(printf '{"model":"%s","max_tokens":300,"reasoning_effort":"low","messages":[{"role":"user","content":"What is 17*23?"}]}' "$MODEL")
call reasoning_openai_style POST /v1/chat/completions "$BODY"
report reasoning_openai_style
BODY=$(printf '{"model":"%s","max_tokens":300,"reasoning":{"effort":"low"},"messages":[{"role":"user","content":"What is 17*23?"}]}' "$MODEL")
call reasoning_nested_style POST /v1/chat/completions "$BODY"
report reasoning_nested_style
echo "     (اگر مدل reasoning نداشته باشد خطای ۴۰۰ طبیعی است)"

# 6) Anthropic messages (برای Claude Code) --------------------------
for CM in "anthropic/claude-sonnet-4.5" "claude-sonnet-4-5"; do
  NAME="messages_$(echo "$CM" | tr '/.' '__')"
  BODY=$(printf '{"model":"%s","max_tokens":20,"messages":[{"role":"user","content":"Say hi."}]}' "$CM")
  call "$NAME" POST /v1/messages "$BODY" -H "anthropic-version: 2023-06-01" -H "x-api-key: $KEY"
  report "$NAME"
done

# 7) responses API --------------------------------------------------
BODY=$(printf '{"model":"%s","max_output_tokens":30,"input":"Say hi."}' "$MODEL")
call responses POST /v1/responses "$BODY"
report responses

# 8) خطاها (بدون هزینه) ---------------------------------------------
res=$(curl -sS -X POST --max-time "$TIMEOUT" -o "$OUT/err_bad_key.body" -w '%{http_code}' \
  -H "Authorization: Bearer sk-invalid-key" -H "Content-Type: application/json" \
  -d "$(printf '{"model":"%s","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}' "$MODEL")" \
  "$BASE/v1/chat/completions" 2>/dev/null)
record "err_bad_key (انتظار ۴۰۱)" "ℹ️" "HTTP $res → $(snippet "$OUT/err_bad_key.body")"

BODY='{"model":"this/model-does-not-exist","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}'
call err_bad_model POST /v1/chat/completions "$BODY"
record "err_bad_model (انتظار ۴۰۰/۴۰۴)" "ℹ️" "HTTP $CODE → $(snippet "$OUT/err_bad_model.body")"

# 9) اختیاری: embeddings و تصویر ------------------------------------
if [ "$FULL" = "1" ]; then
  BODY=$(printf '{"model":"%s","input":"hello"}' "$EMBED_MODEL")
  call embeddings POST /v1/embeddings "$BODY"
  report embeddings
  echo "     مدل embedding تست: $EMBED_MODEL (اگر ندارید با EMBED_MODEL=... عوض کنید)"

  BODY=$(printf '{"model":"%s","prompt":"a red circle on white background","size":"1024x1024"}' "$IMAGE_MODEL")
  call images POST /v1/images/generations "$BODY"
  report images
  echo "     مدل تصویر تست: $IMAGE_MODEL"
else
  echo
  echo "(embeddings و تولید تصویر رد شدند؛ برای تست: bash api-check.sh --full)"
fi

echo
echo "================ خلاصه ================"
cat "$SUMMARY"
echo "======================================="
echo "برای ارسال نتیجه، فقط همین خلاصه را کپی کنید (کلید در آن نیست)."
