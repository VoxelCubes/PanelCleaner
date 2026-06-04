# Phase 2 — สรุปการ Implement (OpenRouter + Glossary injection)

Phase 2 เพิ่มการแปลจริงผ่าน OpenRouter พร้อม glossary injection, batching, retry/rate-limit,
caching และ cost accounting รวมถึง CLI `translate` โดย **ไม่แตะ pipeline การ clean เดิม**

## ไฟล์ที่เพิ่ม

| ไฟล์ | บทบาท |
|------|-------|
| `pcleaner/translator/openrouter.py` | `OpenRouterClient` (requests) + retry/backoff บน 429/5xx เคารพ `Retry-After` + parse `usage` (tokens + cost). `session`/`sleep` inject ได้เพื่อทดสอบ |
| `pcleaner/translator/prompt.py` | `build_system_prompt`, `build_user_message`, `parse_translation_response` (JSON array + code-fence + fallback line-split + pad/truncate) |
| `pcleaner/translator/batching.py` | `Bubble`, `make_batches`, `context_for_batch` (context window รอบ batch) |
| `pcleaner/translator/cache.py` | `sidecar_path`, `load_if_exists` สำหรับ `#translated.json` |
| `pcleaner/translator/translate.py` | `translate_page()` orchestration: cache → batch → prompt → client → glossary post-replace → `PageTranslation` + usage split/accounting; `TranslatorClient` Protocol (inject ได้) |
| `pcleaner/translate_cli.py` | CLI `translate`: อ่าน OCR file → แปลต่อหน้า → เขียน sidecar |
| tests: `test_translator_openrouter.py`, `test_translator_prompt.py`, `test_translator_batching.py`, `test_translator_translate.py`, `test_translator_cache.py` |

## ไฟล์ที่ขยาย

- `pcleaner/main.py` — เพิ่ม subcommand `translate` (docopt + dispatch ผ่าน dict-key)

## Data flow ของ `translate`

```
pcleaner ocr <images> -o detected_text.csv      # ขั้นเดิม: ได้ OCR text + box ต่อหน้า
pcleaner translate detected_text.csv --workspace=<ws> [--dry-run] [--force] [--model=<m>] [--out=<dir>]
```

1. resolve workspace → ได้ภาษา src/tgt, glossary, `TranslatorConfig`
2. parse OCR file (`ocr.parsers.parse_ocr_data`) → `OCRAnalytic` ต่อหน้า → `Bubble(index, box, text)`
3. ต่อหน้า: โหลด `#translated.json` เดิม (cache) → ข้ามบับเบิลที่แปลแล้ว (ยกเว้น `--force`)
4. batch บับเบิลที่เหลือ → ประกอบ prompt (system + glossary block + context) → เรียก OpenRouter
5. parse JSON array → (ถ้าโหมดมี replace) `glossary.apply_postprocess` → `TranslationResult`
6. เขียน `<image_stem>#translated.json` ลง output dir (default = workspace cache) + สรุป cost

## การกันชนกัน (จุดที่ย้ำ)

- อ่าน geometry (box) จาก OCR/`#clean.json` เท่านั้น ไม่แก้
- เขียนเฉพาะ `#translated.json` — ไม่กระทบ artifact การ clean
- **API key**: env `OPENROUTER_API_KEY` > `Config [OpenRouter] api_key` — ไม่อยู่ใน manifest
- ภาษา/glossary/model อ่านจาก workspace ที่เดียว

## Glossary modes

| โหมด | prompt block | post-replace |
|------|:---:|:---:|
| `prompt` | ✅ | ❌ |
| `replace` | ❌ | ✅ |
| `prompt+replace` (default) | ✅ | ✅ |

## การตรวจสอบ (verification)

```bash
pytest tests/test_translator_openrouter.py tests/test_translator_prompt.py \
       tests/test_translator_batching.py tests/test_translator_translate.py \
       tests/test_translator_cache.py
```

ครอบคลุม: retry บน 429/5xx + เคารพ Retry-After + exponential backoff, network-error retry,
non-retryable ราย immediate, parse JSON/code-fence/prose/fallback/pad/truncate, batching +
context window, caching (skip/force), glossary prompt vs replace, usage split + accounting,
sidecar round-trip

> รวม Phase 1 + 2: **74 passed, 1 skipped** (ตัว skip ต้อง import `structures` ที่ดึง torch)
>
> หมายเหตุ: `translate_cli.run_translate` แตะ `ocr.parsers` (ดึง torch chain) จึงรันได้ใน
> สภาพแวดล้อมเต็มเท่านั้น — ตรรกะแกนกลางถูกครอบด้วย unit test ผ่าน fake client แล้ว

## ขั้นถัดไป

Phase 3 — Text rendering (วาดข้อความแปลจาก `#translated.json` ลงบับเบิลที่ clean)
