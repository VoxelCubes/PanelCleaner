# Spec: ระบบ Workspace เฉพาะเรื่อง

Workspace คือแนวคิด **บนสุด** ที่ครอบงานแปลของเรื่องหนึ่งทั้งหมด: ชี้ไปยัง Profile ที่ใช้
clean, อ้างอิง Glossary, กำหนดภาษา source/target, เก็บการตั้งค่า translator/render และ
จัดระเบียบ chapter/page พร้อมติดตามสถานะ raw → cleaned → translated → rendered

---

## 1. ความสัมพันธ์กับของเดิม

```
Workspace (ใหม่, ต่อเรื่อง)
 ├─ profile      → อ้างอิง Profile เดิม (cleaning settings) — ไม่ทำซ้ำ
 ├─ glossary     → อ้างอิงไฟล์ glossary.toml
 ├─ languages    → source / target (เป็นเจ้าของแต่เพียงผู้เดียว)
 ├─ translator   → TranslatorConfig
 ├─ render       → RenderConfig
 └─ chapters[]   → pages[] + state
```

Workspace **ไม่** เก็บ cleaning settings เอง — มันอ้างอิง Profile ที่มีอยู่ (ผ่านชื่อใน
`Config.saved_profiles` หรือ path) เพื่อไม่ให้เกิด config ซ้ำซ้อน (ดู
[01-architecture.md §3](01-architecture.md))

---

## 2. โครงสร้างไดเรกทอรีบนดิสก์

```
<workspace_root>/
  workspace.toml          # manifest
  glossary.toml           # คลังศัพท์ของเรื่องนี้
  profile.conf            # (ออปชัน) สำเนา profile แบบ vendored
  chapters/
    ch001/
      raw/      001.png 002.png ...     # ภาพต้นฉบับ
      cleaned/  001.png ...             # ผล masker/inpainter
      rendered/ 001.png ...             # ภาพแปลเสร็จสุดท้าย
  cache/                  # cache ของ cleaner เฉพาะ workspace (UUID artifacts + #*.json)
```

โดย default workspace อยู่ใต้ `get_config_path().parent / "workspaces"` และลงทะเบียนใน
`Config.saved_workspaces` แต่สร้างที่ path ใดก็ได้ (เหมือน profile)

`cache/` ของ workspace **แทน** global cleaner cache เมื่อ workspace active เพื่อให้หลาย
เรื่องไม่ชนกัน — ล้อแนวคิด env `GUARDED_CLEANER_CACHE` ที่มีอยู่

---

## 3. รูปแบบ manifest (`workspace.toml`)

```toml
[workspace]
name = "Series XYZ"
created = "2026-06-04T10:00:00Z"
schema_version = 1

[languages]
source = "ja"
target = "th"

[profile]
# อ้างด้วยชื่อ saved-profile หรือ path สัมพัทธ์ของ workspace
name = "my_clean_profile"        # resolve ผ่าน Config.saved_profiles
# path = "profile.conf"          # ทางเลือก: สำเนา vendored

[glossary]
path = "glossary.toml"           # สัมพัทธ์กับ workspace root

[translator]
model = "anthropic/claude-3.5-sonnet"
batch_size = 12
include_context = true
context_window = 2               # บับเบิลข้างเคียงก่อน/หลัง
glossary_mode = "prompt+replace" # prompt | replace | prompt+replace
temperature = 0.3
max_retries = 4

[render]
default_font = "NotoSans"
auto_fit = true
min_font_size = 10
max_font_size = 48
alignment = "center"
stroke_width = 0
stroke_color = "#000000"
vertical = false

[fonts]              # override ต่อภาษา
ja = "NotoSansJP"
ko = "NotoSansKR"

[[chapters]]
id = "ch001"
title = "Chapter 1"
[[chapters.pages]]
file = "001.png"
state = "rendered"   # raw | cleaned | translated | rendered
uuid = "d91d86d1-..." # ผูกกับ artifact ใน cache
```

---

## 4. Data model (`pcleaner/workspace.py`)

ใช้แพทเทิร์น `@define` เดียวกับ `Profile` ใน `config.py`:

```python
class PageState(StrEnum):
    raw = "raw"; cleaned = "cleaned"; translated = "translated"; rendered = "rendered"

@define
class PageEntry:
    file: str
    state: PageState = PageState.raw
    uuid: str | None = None

@define
class ChapterEntry:
    id: str
    title: str = ""
    pages: list[PageEntry] = field(factory=list)

@define
class Workspace:
    root: Path
    name: str
    source_lang: str
    target_lang: str
    profile_ref: ProfileRef           # name | path
    glossary_path: Path
    translator: TranslatorConfig
    render: RenderConfig
    fonts: dict[str, str]
    chapters: list[ChapterEntry]

    @classmethod
    def create(cls, root, name, source, target, profile, ...) -> "Workspace": ...
    @classmethod
    def load(cls, root: Path) -> "Workspace": ...
    def save(self) -> bool: ...                       # safe_write tmp+move เหมือน Profile
    def resolve_profile(self, config) -> cfg.Profile: ...  # bridge ไป Profile.load เดิม
    def resolve_glossary(self) -> Glossary: ...
    def cache_dir(self) -> Path: ...
    def set_page_state(self, ch, page, state, uuid): ...   # state tracking ต้นทางเดียว
```

`resolve_profile()` คือสะพานสำคัญ: มันแปลง `profile_ref` → `Profile` object โดยเรียก
`Profile.load()` เดิม ทำให้ pipeline เดิมไม่รู้เลยว่ามี workspace อยู่

---

## 5. State machine ของหน้า

```
raw ──clean──▶ cleaned ──translate──▶ translated ──render──▶ rendered
```

- แต่ละ step อัปเดต `PageEntry.state` ใน manifest (เขียนกลับโดย `set_page_state`)
- `pcleaner workspace status` อ่าน state รวมแล้วสรุปความคืบหน้าต่อ chapter
- การ resume: ข้าม page ที่ถึง state เป้าหมายแล้ว (ใช้ร่วมกับ cache UUID)

---

## 6. CLI (สรุป — ดูเต็มใน [06-cli.md](06-cli.md))

```
pcleaner workspace new <name> [<path>] --source=<lang> --target=<lang> [--profile=<profile>]
pcleaner workspace (list | info <name> | status <name> | open <name>)
pcleaner workspace add <name> <path>
```

การ resolve `<name>` ใช้ `Config.saved_workspaces` + `closest_match` ล้อ logic ของ
`--profile` เดิมเป๊ะ

---

## 7. การกันชนกัน (เฉพาะส่วน Workspace)

- Workspace เขียนกลับเฉพาะ `workspace.toml` เท่านั้น — ไม่แก้ Profile, ไม่แก้ Config global
- ภาษาเป็นของ Workspace ที่เดียว — Profile ไม่มี field ภาษาแปล
- cache แยกต่อ workspace กันชนข้ามเรื่อง

ดูภาพรวมการกันชนกันใน [01-architecture.md §3](01-architecture.md)
