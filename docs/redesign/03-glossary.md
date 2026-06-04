# Spec: ระบบ Glossary

Glossary คือคลังศัพท์เฉพาะเรื่องที่ช่วยให้การแปลคงเส้นคงวา: ชื่อตัวละคร, คำเฉพาะของเรื่อง,
honorific (เช่น 先輩 → senpai), และคำที่ห้ามแปล (do-not-translate) ถูก inject เข้า prompt
ของ LLM และ/หรือใช้แทนที่หลังแปล

---

## 1. รูปแบบไฟล์ (`glossary.toml`)

```toml
[meta]
name = "My Series Glossary"
source_lang = "ja"
target_lang = "th"
version = 1

# ชื่อตัวละคร / คำแปลที่ต้องการ
[[terms]]
source = "ハルカ"
target = "ฮารุกะ"
type = "name"          # name | term | honorific | do_not_translate
notes = "ตัวเอก, หญิง"
case_sensitive = false

[[terms]]
source = "先輩"
target = "รุ่นพี่"
type = "honorific"
do_not_translate = false

[[terms]]
source = "ACME社"
target = "ACME Corp."
type = "term"

[[terms]]
source = "SFX-DOON"
target = "SFX-DOON"
type = "do_not_translate"
```

> เลือก **TOML** เพราะเป็น list ของ entry จำนวนมาก แก้มือใน editor/spreadsheet-export ได้
> และ diff/version-control ง่าย (เทียบกับ INI ที่ออกแบบมาเพื่อ flat section) — ดูเหตุผลใน
> [01-architecture.md §4](01-architecture.md)

---

## 2. Data model (`pcleaner/glossary.py`)

```python
class TermType(StrEnum):
    name = "name"
    term = "term"
    honorific = "honorific"
    do_not_translate = "do_not_translate"

@define
class GlossaryEntry:
    source: str
    target: str
    type: TermType = TermType.term
    notes: str = ""
    case_sensitive: bool = False
    do_not_translate: bool = False

@define
class Glossary:
    name: str = ""
    source_lang: str | None = None
    target_lang: str | None = None
    entries: list[GlossaryEntry] = field(factory=list)

    @classmethod
    def load(cls, path: Path) -> "Glossary": ...
    def save(self, path: Path) -> bool: ...                 # safe_write tmp+move เหมือน Profile
    def validate(self) -> list[str]: ...                    # source ซ้ำ, field ว่าง, lang mismatch
    def to_prompt_block(self, max_entries: int | None) -> str: ...   # inject เข้า prompt LLM
    def apply_postprocess(self, text: str) -> str: ...      # แทนที่หลังแปล
```

---

## 3. โหมดการใช้งาน (ตั้งใน `TranslatorConfig.glossary_mode`)

รองรับ 2 โหมด ใช้ร่วมกันได้:

| โหมด | กลไก | เหมาะกับ |
|------|------|----------|
| **prompt** (แนะนำ) | `to_prompt_block()` แทรกรายการ term เข้า system prompt ให้ LLM ใช้ในบริบท | คำทั่วไป, honorific ที่ขึ้นกับบริบท |
| **replace** | `apply_postprocess()` แทนที่ตรง ๆ หลังแปล (deterministic) | ชื่อเฉพาะ, do-not-translate, SFX |
| **prompt+replace** | ทั้งสอง: ให้ LLM ใช้บริบท + บังคับแทนที่คำสำคัญ | ค่าเริ่มต้นที่แนะนำ |

- `do_not_translate` และ honorific ถูกส่งเป็นคำสั่งชัดเจนใน prompt block
- `case_sensitive` ควบคุมการ match ตอน `apply_postprocess()`

### ตัวอย่าง prompt block ที่ generate

```
Glossary (use these exact translations):
- ハルカ → ฮารุกะ (character name; keep consistent)
- 先輩 → รุ่นพี่ (honorific)
- ACME社 → ACME Corp.
Do NOT translate (keep verbatim): SFX-DOON
```

---

## 4. Validation

`validate()` คืน list ของข้อความเตือน (ว่างถ้าผ่าน):
- `source` ซ้ำกัน (เสี่ยง replace ทับกัน)
- `source` หรือ `target` ว่าง (ยกเว้น do-not-translate ที่ target = source ได้)
- `source_lang`/`target_lang` ไม่ตรงกับ workspace
- `type` ไม่อยู่ใน enum

---

## 5. CLI (สรุป — ดูเต็มใน [06-cli.md](06-cli.md))

```
pcleaner glossary (list | validate) [--workspace=<ws>]
pcleaner glossary add <source> <target> [--type=<t>] [--notes=<n>] [--workspace=<ws>]
pcleaner glossary remove <source> [--workspace=<ws>]
pcleaner glossary (import <file> | export <file>) [--workspace=<ws>]
```

`import`/`export` รองรับ CSV เพื่อให้แก้ใน spreadsheet ได้ (mapping column → field)

---

## 6. การกันชนกัน (เฉพาะส่วน Glossary)

- Glossary เป็นไฟล์เดี่ยวที่ `workspace.toml` ชี้ถึง — **translator เป็นผู้บริโภครายเดียว**
- ไม่มีข้อมูล glossary รั่วเข้า Profile หรือ Config global
- การแก้ glossary ทำให้ต้อง re-run เฉพาะขั้น translate/render ไม่กระทบ artifact การ clean

ดูภาพรวมการกันชนกันใน [01-architecture.md §3](01-architecture.md)
