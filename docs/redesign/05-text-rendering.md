# Spec: ระบบ Text Rendering

ระบบ render วาดข้อความที่แปลแล้วกลับลงในบับเบิลของภาพที่ clean แล้ว เป็น pipeline step
ใหม่หลัง translator ใช้ PIL ล้วน (ไม่เพิ่ม dependency หนัก) และ reuse geometry `Box` +
ภาพ clean จาก masker/inpainter

ปัจจุบันมีเพียง `PageData.visualize()` (ใน `structures.py`) ที่วาด debug box/label ด้วย
PIL + `LiberationSans-Regular.ttf` ที่ bundle ไว้ — ยังไม่มี wrapping/auto-fit/วาดข้อความ
แปลกลับ

---

## 1. โครงโมดูล (`pcleaner/rendering/`)

```
rendering/
  config.py    # RenderConfig (@define) + TOML import/export
  fonts.py     # font registry (bundled + user), เลือกตามภาษา
  layout.py    # wrapping, auto-fit font-size, vertical text, alignment
  render.py    # render_page(RenderData) → _rendered.png
```

---

## 2. Font management (`fonts.py`)

- font registry ค้นหา bundled fonts ใน `data/fonts/` (ใหม่) + user fonts (โฟลเดอร์
  `fonts/` ใน workspace + OS font dirs)
- การเลือก: `RenderConfig.default_font` → override ต่อภาษาด้วย map `[fonts]` ใน manifest
  → fallback เป็น bundled `LiberationSans`/`NotoSans` CJK (เหมือนที่ `visualize()` ทำวันนี้)
- ใช้ `hp.resource_path(pcleaner.data, ...)` โหลด bundled font แบบเดียวกับ `visualize()`

---

## 3. Layout (`layout.py`)

- **Word-wrap** แบบ greedy ให้พอดีความกว้าง `Box`; สำหรับภาษาเป้าหมายที่ไม่มีช่องว่าง
  (CJK) ใช้ wrap ระดับตัวอักษร
- **Auto-fit:** binary-search ขนาด font ระหว่าง `min_font_size`/`max_font_size` ให้
  ข้อความหลายบรรทัดพอดีทั้งความสูงและความกว้างของกล่อง — reuse `Box.area` และ
  width/height จาก `Box.as_tuple_xywh`
- **Alignment:** left/center/right
- **Vertical text (CJK):** เรียงคอลัมน์จากขวาไปซ้าย
- **Stroke/outline:** ผ่าน PIL `stroke_width`/`stroke_fill` (ใช้อยู่แล้วใน
  `PageData.visualize()`)

---

## 4. Render (`render.py`)

`render_page(RenderData)`:
1. เปิด canvas สะอาด — เลือกตัวที่ดีที่สุดตามลำดับ
   `inpainted_output → denoised_output → masked_output` (reuse `cleaned_outputs_whitelist`
   ใน `main.py`)
2. โหลดกล่องจาก `#clean.json` + ข้อความจาก `#translated.json`
3. วาดข้อความแปลแต่ละสตริงลงในกล่องด้วย font/fit/alignment ที่เลือก
4. เขียน `_rendered.png` (= `Output.rendered_output`)

---

## 5. RenderConfig (`config.py`)

`@define` dataclass (serialize เป็น `[render]` ใน `workspace.toml`):

```python
@define
class RenderConfig:
    default_font: str = "NotoSans"
    auto_fit: bool = True
    min_font_size: int = 10
    max_font_size: int = 48
    alignment: str = "center"       # left | center | right
    stroke_width: int = 0
    stroke_color: str = "#000000"
    vertical: bool = False
    def fix(self): ...              # clamp ช่วง ตาม convention เดิม
    def from_toml(d): ... / def to_toml(): ...
```

font override ต่อภาษาเก็บแยกใน `[fonts]` ของ manifest (ดู [02-workspace.md](02-workspace.md))

---

## 6. จุดเสียบใน pipeline

- เพิ่ม `Step.renderer` + `Output.rendered_output` แบบ **เพิ่มต่อท้าย** (ระวัง IntEnum
  ordering trap — ดู [01-architecture.md §1](01-architecture.md))
- renderer ทำงานเฉพาะเมื่อมี workspace active หรือใส่ `--render` → clean-only เดิมไม่กระทบ

---

## 7. CLI (สรุป — ดูเต็มใน [06-cli.md](06-cli.md))

```
pcleaner render [<image_path> ...] [--workspace=<ws>] [--debug]
```

---

## 8. การกันชนกัน (เฉพาะส่วน Rendering)

- อ่าน geometry จาก `#clean.json` และข้อความจาก `#translated.json` — ไม่แก้ทั้งคู่
- เขียนเฉพาะ `_rendered.png` — ไม่กระทบ artifact การ clean
- font config อยู่ใน Workspace ไม่ใช่ Profile

ดูภาพรวมการกันชนกันใน [01-architecture.md §3](01-architecture.md)
