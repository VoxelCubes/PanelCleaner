# Phase 3 — สรุปการ Implement (Text Rendering)

Phase 3 วาดข้อความที่แปลแล้วจาก `#translated.json` ลงบนภาพที่ clean แล้ว เป็น PIL ล้วน
(ไม่เพิ่ม dependency หนัก) พร้อม font ต่อภาษา, wrapping, auto-fit, vertical และ stroke
รวมถึง CLI `render` โดย **ไม่แตะ pipeline การ clean เดิม**

## ไฟล์ที่เพิ่ม

| ไฟล์ | บทบาท |
|------|-------|
| `pcleaner/rendering/fonts.py` | `FontRegistry`: resolve font ต่อภาษา (per-language → default → bundled fallback `LiberationSans`), ค้นหาจาก path/ชื่อใน user dirs + `pcleaner/data[/fonts]`, โหลดด้วย `ImageFont.truetype`, มี cache |
| `pcleaner/rendering/layout.py` | `wrap_text` (word + char wrap, รองรับภาษาไม่มีช่องว่าง + `\n`), `layout_text` (binary-search auto-fit ใน `[min,max]`), `layout_vertical` (คอลัมน์ขวา→ซ้าย), วัดด้วย PIL (`load_font` inject ได้) |
| `pcleaner/rendering/render.py` | `render_page` วาดข้อความลงแต่ละ box (alignment, stroke, vertical, `scale`), `render_to_file` เปิดภาพ→วาด→เซฟ `_rendered.png` |
| `pcleaner/render_cli.py` | CLI `render`: หา sidecar `#translated.json` ต่อภาพ → วาด → เขียน `<stem>_rendered.png` |
| tests: `test_rendering_fonts.py`, `test_rendering_layout.py`, `test_rendering_render.py` |

## ไฟล์ที่ขยาย

- `pcleaner/rendering/config.py` — เพิ่ม `text_color` (default `#000000`); `stroke_color`
  default เปลี่ยนเป็น `#FFFFFF` (ขอบขาวรอบตัวอักษรดำ แบบมังงะ)
- `pcleaner/main.py` — เพิ่ม subcommand `render` (docopt + dispatch)

## Data flow ของ `render`

```
pcleaner ocr <images> -o detected_text.csv
pcleaner translate detected_text.csv --workspace=<ws>      # -> <stem>#translated.json
pcleaner clean <images>                                    # -> ภาพ clean
pcleaner render <cleaned_images> --workspace=<ws> [--translations=<dir>] [--out=<dir>] [--scale=<f>]
```

1. resolve workspace → `RenderConfig` + `[fonts]` map + fonts dir → สร้าง `FontRegistry`
2. ต่อภาพ: หา `<stem>#translated.json` (จาก `--translations` หรือ workspace cache หรือข้างภาพ)
3. โหลด `PageTranslation` → `render_page` วาดแต่ละ box (auto-fit/align/stroke/vertical)
4. เซฟ `<stem>_rendered.png` (`--out` หรือข้างภาพ)

## รายละเอียดสำคัญ

- **Auto-fit:** binary search หา font size ใหญ่สุดที่ wrap แล้วพอดีทั้งกว้างและสูงของ box;
  ถ้าไม่พอจริง ๆ ใช้ `min_font_size` เป็นพื้น (ยังวาดเสมอ)
- **Wrapping:** word-wrap สำหรับภาษามีช่องว่าง, char-wrap สำหรับ token ยาว/ภาษาไม่มีช่องว่าง,
  เคารพ `\n`
- **Vertical:** เรียงตัวอักษรเป็นคอลัมน์ ขวา→ซ้าย พร้อม auto-fit
- **scale:** map พิกัด box จาก resolution ของ OCR/translation ไปยัง canvas (เผื่อ OCR รันบน
  ภาพย่อส่วน) — Phase 4 จะ wire scale อัตโนมัติใน workspace pipeline
- **กันชนกัน:** อ่าน geometry+ข้อความจาก `#translated.json`/`#clean.json` เท่านั้น ไม่แก้;
  เขียนเฉพาะ `_rendered.png`; font config อยู่ใน Workspace ไม่ใช่ Profile

## การตรวจสอบ (verification)

```bash
pytest tests/test_rendering_fonts.py tests/test_rendering_layout.py \
       tests/test_rendering_render.py tests/test_rendering_config.py
```

ครอบคลุม: font resolution (fallback/override/path/prefix-match) + load size,
wrap (word/char/newline/empty), auto-fit (กล่องเล็ก→font เล็ก, ไม่ auto-fit ใช้ max,
floor ที่ min), vertical layout, render วาดจริง (มี ink ใน box), blank ไม่วาด, scale,
เซฟ PNG, แปลง canvas ที่ไม่ใช่ RGB

> รวม Phase 1–3: **104 passed, 1 skipped** (ตัว skip ต้อง import `structures` ที่ดึง torch)

## ขั้นถัดไป

Phase 4 — Workspace orchestration: เชื่อม clean → translate → render เป็น end-to-end
ภายใต้ workspace + จัดการ scale อัตโนมัติ + ติดตามสถานะหน้าใน manifest
