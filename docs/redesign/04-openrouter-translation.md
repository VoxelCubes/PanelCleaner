# Spec: ระบบแปลผ่าน OpenRouter

ระบบแปลรับข้อความ OCR ต่อบับเบิล (จาก `#clean.json` / `OCRAnalytic`) แล้วเรียก LLM ผ่าน
OpenRouter HTTP API เพื่อแปลเป็นภาษาเป้าหมาย โดย inject glossary + บริบทบับเบิลข้างเคียง
แล้วเขียนผลลง `#translated.json` (cache) พร้อมบัญชี token/ค่าใช้จ่าย

ใช้ `requests` (มีอยู่แล้วใน deps) — ไม่เพิ่ม SDK ภายนอก

---

## 1. โครงโมดูล (`pcleaner/translator/`)

```
translator/
  config.py        # TranslatorConfig (@define) + TOML import/export
  openrouter.py    # OpenRouter HTTP client (requests): call, retry, rate-limit
  prompt.py        # ประกอบ system prompt + glossary block + context
  batching.py      # จัดกลุ่มบับเบิลต่อหน้าเป็น batch
  cache.py         # อ่าน/เขียน #translated.json, cost accounting
  translate.py     # orchestration: translate_page(...) → เขียน sidecar
  structures.py    # TranslationResult, PageTranslation, CostAccounting
```

---

## 2. OpenRouter client (`openrouter.py`)

client บาง ๆ บน `requests`:

- `POST https://openrouter.ai/api/v1/chat/completions`
- headers: `Authorization: Bearer <key>`, `HTTP-Referer` / `X-Title` (เพื่อ attribution)
- **Retry/backoff:** exponential backoff เมื่อเจอ HTTP 429/5xx, เคารพ `Retry-After`,
  จำกัดที่ `max_retries`
- ดึง `usage` (prompt/completion tokens) และ `model` จาก response เพื่อทำบัญชีค่าใช้จ่าย

### API key precedence (สำคัญต่อความปลอดภัย)

```
env OPENROUTER_API_KEY  >  Config [OpenRouter] api_key  >  error
```

> **ไม่เก็บ key ใน `workspace.toml`** เพื่อให้ workspace แชร์/commit ได้อย่างปลอดภัย
> key อยู่ใน global `Config` หรือ env เท่านั้น

---

## 3. การประกอบ prompt (`prompt.py`)

- **System prompt** (จาก `data/prompts/system_prompt.txt`, override ได้): ระบุบทบาท,
  ภาษา source→target, "รักษา formatting, ตอบเป็น JSON array index ตามหมายเลขบับเบิล"
- **Glossary block** จาก `Glossary.to_prompt_block()` (ดู [03-glossary.md](03-glossary.md))
- **Context:** สำหรับแต่ละ batch แนบบับเบิลข้างเคียง `context_window` ตัว (อยู่ใน reading
  order จาก `PageData` แล้ว) เป็นบริบทอ่านอย่างเดียว แต่ขอแปลเฉพาะบับเบิลใน batch นั้น

---

## 4. Batching (`batching.py`)

- จัดกลุ่มบับเบิลของหน้าเป็น batch ละ `batch_size` ตัว โดยรักษา reading order เพื่อให้ LLM
  เห็นบทสนทนาต่อเนื่อง
- 1 HTTP request ต่อ 1 batch — คาดหวัง JSON array กลับมา index ตามลำดับ พร้อม fallback
  parser แบบแยกบรรทัดถ้า model ไม่ให้ JSON

---

## 5. Cache + cost accounting (`cache.py`)

- ก่อนเรียก API: เช็ค `#translated.json` — ข้ามบับเบิลที่แปลแล้ว (cache hit) ยกเว้น `--force`
  → ทำให้ re-render ฟรี และการปรับ glossary ถูก (re-run แค่ post-replace)
- `CostAccounting`: อ่าน `usage` ของ OpenRouter (+ optional `/generation` cost) สะสมต่อ
  หน้าและต่อ run แล้วพิมพ์สรุปคล้าย analytics เดิม

---

## 6. Data model (`translator/structures.py`)

### Translation cache sidecar (`#translated.json`)

```python
@frozen
class TranslationResult:
    box: Box                  # serialize เป็น tuple เหมือน PageData
    source_text: str
    target_text: str
    model: str
    glossary_applied: bool
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float

@define
class PageTranslation:
    image_path: str           # path ภาพต้นฉบับ/clean
    source_lang: str
    target_lang: str
    results: list[TranslationResult]
    total_cost_usd: float
    def from_json(...): ...    # Box เป็น tuple — mirror PageData
    def to_json(...): ...
```

sidecar ผูกกับหน้าด้วย **UUID เดียวกัน** ที่ cleaner ใช้ (อยู่ที่
`OutputPathGenerator.translated_json`) — renderer อ่าน `#clean.json` (geometry ต้นทาง) +
`#translated.json` (ข้อความแปล) จับคู่ตาม index/พิกัดกล่อง จึง **ไม่ทำซ้ำ geometry**
(`#translated.json` เก็บ box ไว้เพื่อความสะดวกเท่านั้น geometry จริงคือ `#clean.json`)

---

## 7. TranslatorConfig (`config.py`)

`@define` dataclass (serialize เป็น `[translator]` ใน `workspace.toml`):

```python
@define
class TranslatorConfig:
    model: str = "anthropic/claude-3.5-sonnet"
    batch_size: int = 12
    include_context: bool = True
    context_window: int = 2
    glossary_mode: str = "prompt+replace"   # prompt | replace | prompt+replace
    temperature: float = 0.3
    max_retries: int = 4
    def fix(self): ...          # clamp ช่วง, default enum ที่ผิด (ตาม convention เดิม)
    def from_toml(d): ... / def to_toml(): ...
```

---

## 8. orchestration (`translate.py`)

`translate_page(TranslateData)` ล้อรูปทรงของ `mask_page`/`denoise_page` (รับ struct
`@frozen` เข้า, เขียน sidecar ออก) จึงเสียบเข้า loop `tqdm`/Pool แบบเดียวกับ
`run_cleaner` ได้

> หมายเหตุ: งานนี้ติด network → ใช้ `ThreadPool` แทน `multiprocessing.Pool`

---

## 9. CLI (สรุป — ดูเต็มใน [06-cli.md](06-cli.md))

```
pcleaner translate [<image_path> ...] [--workspace=<ws>] [--model=<m>] [--force] [--dry-run] [--debug]
```

`--dry-run` ประเมิน token/ค่าใช้จ่ายโดย **ไม่เรียก API จริง**

---

## 10. การกันชนกัน (เฉพาะส่วน Translator)

- อ่าน geometry จาก `#clean.json` อย่างเดียว ไม่แก้ (`Box` เป็น `@frozen`)
- เขียนเฉพาะ `#translated.json` — การแปลใหม่ทำให้ **เฉพาะ `rendered_output` invalid**
- key/secret ไม่อยู่ใน manifest
- ภาษา src/tgt อ่านจาก workspace ที่เดียว

ดูภาพรวมการกันชนกันใน [01-architecture.md §3](01-architecture.md)
