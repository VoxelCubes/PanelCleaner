# สถาปัตยกรรมรวม (Architecture)

เอกสารนี้อธิบายว่า 4 ระบบใหม่ (Glossary, OpenRouter, Workspace, Rendering) เสียบเข้ากับ
codebase เดิมอย่างไร และทำงานร่วมกันโดยไม่ชนกันได้อย่างไร อ้างอิงโค้ดจริง:
`config.py` (แพทเทิร์น `attrs @define` + `configupdater`), `structures.py`
(`Box`/`PageData`/`OCRResult`), `output_structures.py`
(`Output`/`Step`/`OutputPathGenerator`), `main.py` (docopt CLI), `cli_utils.py`
(XDG dir resolution)

---

## 1. Data flow ใหม่

### Pipeline เดิม (ไม่แตะ — 6 step)

```
text_detection → preprocessor(OCR) → masker → denoiser → inpainter → output
```
(นิยามใน `pcleaner/output_structures.py` คลาส `Step`)

### Pipeline ใหม่ (+2 step)

```
text_detection → preprocessor(OCR) → masker → denoiser → inpainter
   → [NEW] translator → [NEW] renderer → output
```

**ลำดับนี้เพราะ:**
- `translator` ต้องการข้อความ OCR (จาก `#clean.json` / `OCRAnalytic` ของ preprocessor)
  + reading order — **ไม่ต้องการภาพ** จึงทำหลัง inpaint ได้สบาย และทำให้ขั้นตอน "สร้าง
  canvas สะอาด" เสร็จก่อน
- `renderer` ต้องการ **ภาพ clean** (เลือกตัวที่ดีที่สุดในลำดับ
  inpainted_output → denoised_output → masked_output ตาม `cleaned_outputs_whitelist`
  ใน `main.py`) + **ข้อความที่แปลแล้ว** + **geometry กล่อง** (`Box` จาก `#clean.json`)

### การเพิ่ม enum (⚠️ ระวัง ordering trap)

`Output`/`Step` เป็น `IntEnum` ที่เทียบกันตามลำดับ และ `write_output` ต้องอยู่ "ท้ายสุด"
เชิงตรรกะ → **ห้ามแทรกก่อน `write_output`** เพราะจะ renumber ค่าเดิม ให้เพิ่มต่อท้ายแล้ว
route ผ่าน map `output_to_step` / `step_to_output` แทนการพึ่งลำดับ enum ดิบ

```python
# pcleaner/output_structures.py (ออกแบบ — ยังไม่แก้)
class Step(IntEnum):
    text_detection = 1
    preprocessor = auto()
    masker = auto()
    denoiser = auto()
    inpainter = auto()
    translator = auto()   # NEW
    renderer = auto()     # NEW
    output = auto()       # ยังเป็นตัวสุดท้าย

class Output(IntEnum):
    ...
    inpainted_output = ...
    translated_json = auto()   # NEW: #translated.json sidecar
    rendered_output = auto()   # NEW: _rendered.png
    write_output = auto()      # ต้องอยู่ท้ายสุดเสมอ
```

เพิ่ม property ใน `OutputPathGenerator` (ได้ UUID-prefixed cache path ฟรีเหมือน output เดิม):
```python
@property
def translated_json(self) -> Path: return self._attach("#translated.json")
@property
def rendered(self) -> Path:        return self._attach("_rendered.png")
```
พร้อมเพิ่ม case ใน `output_to_step` และ `step_to_output`

### End-to-end (โหมด workspace)

```
raw image  ──text_detection──▶ #raw.json (+ ai_mask, base.png)
           ──preprocessor───▶ #clean.json (PageData: boxes, box_language) + OCRAnalytic
           ──masker/denoise/inpaint──▶ _clean.png / _clean_denoised.png / _clean_inpaint.png
           ──translator─────▶ #translated.json (TranslationResult/box, cached + costed)
           ──renderer───────▶ _rendered.png  (canvas สะอาด + ข้อความแปลวางในกล่อง)
           ──output─────────▶ workspace/chapters/<ch>/rendered/<page>.png + อัปเดตสถานะ manifest
```

---

## 2. โครงไฟล์/โมดูลใหม่

ตามแพทเทิร์นเดิม (`@define`, `configupdater`, `OutputPathGenerator`, dir resolution ใน
`cli_utils.py`):

```
pcleaner/
  glossary.py                 # Glossary model, load/save (TOML), validation, apply/inject
  workspace.py                # Workspace + manifest model, dir layout, state tracking
  translator/
    __init__.py
    config.py                 # TranslatorConfig (@define) + TOML import/export
    openrouter.py             # OpenRouter HTTP client (requests): call, retry, rate-limit
    prompt.py                 # system prompt + glossary injection + context/reading-order
    batching.py               # จัดกลุ่มบับเบิลต่อหน้าเป็น batch
    cache.py                  # อ่าน/เขียน #translated.json, cost accounting
    translate.py              # orchestration: translate_page(...) → เขียน sidecar
    structures.py             # TranslationResult, PageTranslation, CostAccounting
  rendering/
    __init__.py
    config.py                 # RenderConfig (@define) + TOML import/export
    fonts.py                  # font registry (bundled + user), เลือกตามภาษา
    layout.py                 # wrapping, auto-fit, vertical text, alignment
    render.py                 # render_page(...) → _rendered.png ด้วย PIL
  workspace_cli.py            # CLI: workspace new/open/list/info/status
  glossary_cli.py             # CLI: glossary add/remove/list/validate/import/export
  translate_cli.py            # CLI: translate
  render_cli.py               # CLI: render
  data/
    fonts/                    # ใหม่: bundled fonts ต่อภาษา (CJK, Latin ...)
    prompts/system_prompt.txt # ใหม่: template system prompt
```

### ไฟล์ที่ **ขยาย** (เพิ่มแบบ additive เท่านั้น)
- `output_structures.py` — เพิ่ม Step/Output + mapping + `OutputPathGenerator` properties
- `config.py` (`Config`) — เพิ่ม `openrouter_api_key`, `openrouter_default_model`,
  `default_workspace`, `saved_workspaces`, และ section `[OpenRouter]` / `[Saved Workspaces]`
- `cli_utils.py` — เพิ่ม `get_workspaces_path()`, `get_translation_cache_path()`,
  `get_bundled_font_path(lang)` (ล้อ `get_default_profile_path`)
- `main.py` — เพิ่ม docopt subcommand + dispatch ไป `*_cli.py`
- `structures.py` — **ไม่เปลี่ยนรูป** `OCRResult`/`PageData`; ของใหม่อยู่ใน
  `translator/structures.py`

### ไฟล์ที่ **ไม่แตะ**
`masker.py`, `denoiser.py`, `inpainting.py`, `preprocessor.py`, `ctd_interface.py`,
`image_export.py`, `ocr/*`, GUI modules (ไว้ Phase 5)

---

## 3. การกันชนกัน — single source of truth

- **ภาษา:** มีแค่ Workspace ที่นิยาม source/target —
  `Profile.preprocessor.ocr_language` ยังเป็นแค่ hint ของ OCR *detection* เท่านั้น
- **Glossary:** เป็นไฟล์เดี่ยวที่ manifest อ้างถึง — translator เป็นผู้บริโภคเพียงรายเดียว
  ไม่มีข้อมูล glossary รั่วเข้า Profile/Config
- **Box geometry:** `#clean.json` (`PageData`) เป็น geometry ต้นทางเดียว — ทั้ง translator
  และ renderer อ่านอย่างเดียว ไม่แก้ (`Box` เป็น `@frozen` แก้ไม่ได้อยู่แล้ว)
- **Cache:** คำแปลเป็น JSON sidecar (`#translated.json`) วางข้าง `#clean.json` ใน cache
  dir ของ workspace ใช้ UUID scheme เดิมผ่าน `OutputPathGenerator` — การแปลใหม่ทำให้
  **เฉพาะ `rendered_output` invalid** ไม่กระทบ artifact ของการ clean
- **การเขียน config:** แต่ละระบบเขียนเฉพาะไฟล์ของตน — Workspace orchestrator อ่านจาก
  Profile/Glossary/Config แต่เขียนกลับเฉพาะ `workspace.toml` (สถานะ chapter/page)
- **API key:** precedence = env `OPENROUTER_API_KEY` > `Config` (`[OpenRouter] api_key`) >
  error — **ไม่เก็บใน manifest** เพื่อให้ workspace แชร์/commit ได้ปลอดภัย

### Checklist กันทับซ้อน
- [ ] ไม่มี field ภาษาใน Profile (มีแค่ ocr_language สำหรับ detection)
- [ ] ไม่มี glossary/translator/render field ใน Profile หรือ Config (global)
- [ ] geometry มาจาก `#clean.json` ที่เดียว
- [ ] translation cache อยู่ใต้ workspace cache dir แยกต่อเรื่อง
- [ ] API key ไม่อยู่ใน manifest

---

## 4. รูปแบบไฟล์ (เลือกให้เข้ากับ convention)

| ข้อมูล | รูปแบบ | เหตุผล |
|--------|--------|--------|
| `Profile` | INI (`.conf`) | **คงเดิม** — `configupdater` ออกแบบมาเพื่อ flat section + comment |
| `Config` (global) | INI (`pcleanerrc`) | **คงเดิม** ขยาย section เพิ่ม |
| Workspace manifest | **TOML** (`workspace.toml`) | nested + list (chapters) เหมาะกว่า INI, แก้มือ/diff ง่าย |
| Glossary | **TOML** (`glossary.toml`) | list ของ entry จำนวนมาก, version-control ได้ |
| Translation cache | **JSON** (`#translated.json`) | คู่กับ `#clean.json`, round-trip `Box` เป็น tuple เหมือนกัน |

**หมายเหตุ dependency:** env เป็น Python ≥3.10 — `tomllib` มาใน 3.11+ ดังนั้นการ
implement ต้องเพิ่ม `tomli` (อ่าน) + `tomli_w` (เขียน) ซึ่งเล็กและไม่มี dependency ลูก
อาจทำเป็น optional extra `[translate]` เพื่อให้การติดตั้งแบบ clean-only ไม่ต้องลง

---

## 5. Backward compatibility

- enum ใหม่ทั้งหมด **เพิ่มต่อท้าย** — step translator/renderer ทำงาน **เฉพาะ** เมื่อมี
  workspace active หรือใส่ `--translate`/`--render` → `pcleaner clean myfolder` เดิม
  ทำงานเหมือนเดิมทุก byte
- รูปแบบ INI ของ `Profile` ไม่เปลี่ยน — profile เก่าโหลดได้
- section ใหม่ใน `Config` เป็น optional — `from_config_updater` ทนต่อ section ที่หายอยู่แล้ว
- ไม่มี signature ของฟังก์ชันเดิมเปลี่ยน — พฤติกรรมใหม่เพิ่มผ่านโมดูลใหม่ + branch ใหม่
  ใน `main()`

---

## 6. ดูต่อ

- การจัดระเบียบต่อเรื่อง → [02-workspace.md](02-workspace.md)
- คลังศัพท์ → [03-glossary.md](03-glossary.md)
- การแปล → [04-openrouter-translation.md](04-openrouter-translation.md)
- การ render → [05-text-rendering.md](05-text-rendering.md)
- CLI → [06-cli.md](06-cli.md)
