# Webtoon Translate & Cleaner — Project Overview

> เอกสารชุดนี้คือ **แผนการออกแบบใหม่ (redesign)** ของ PanelCleaner เพื่อยกระดับจาก
> เครื่องมือ "ลบข้อความ" ให้กลายเป็นเครื่องมือ **แปลและทำความสะอาด webtoon/มังงะ ครบวงจร**
>
> **สถานะ:** รอบนี้เป็น *เอกสารออกแบบ* เท่านั้น — ยังไม่มีการเขียนโค้ดจริง
> การ implement จะทำตาม [Roadmap](07-roadmap.md) ในรอบถัดไป

---

## 1. วิสัยทัศน์

PanelCleaner วันนี้ทำได้ดีมากในการ **ตรวจจับและลบข้อความ** ออกจากภาพการ์ตูน (AI text
detection → masking → inpainting) แต่ผู้แปลยังต้องนำภาพที่ clean แล้วไปแปลและพิมพ์
ข้อความใหม่ด้วยเครื่องมืออื่นเอง

เป้าหมายของการออกแบบใหม่คือทำให้ขั้นตอน **แปล → วางข้อความกลับ** อยู่ในเครื่องมือเดียว
โดยเพิ่ม 4 ระบบที่ทำงานร่วมกันได้อย่างไม่ชนกัน:

| ระบบ | หน้าที่ | เอกสาร |
|------|---------|--------|
| **Glossary** | คลังศัพท์เฉพาะเรื่อง: ชื่อตัวละคร, คำเฉพาะ, honorific, do-not-translate | [03-glossary.md](03-glossary.md) |
| **OpenRouter Translation** | แปลด้วย LLM ผ่าน OpenRouter HTTP API | [04-openrouter-translation.md](04-openrouter-translation.md) |
| **Workspace เฉพาะเรื่อง** | โปรเจกต์ต่อเรื่องที่ครอบ Profile + Glossary + ภาษา + การตั้งค่าแปล/render | [02-workspace.md](02-workspace.md) |
| **Text Rendering** | วาดข้อความที่แปลแล้วกลับลงในบับเบิลที่ clean แล้ว | [05-text-rendering.md](05-text-rendering.md) |

---

## 2. หลักการสำคัญ: "ไม่ชนกันเอง"

ผู้ใช้ย้ำว่าทั้ง 4 ระบบต้องทำงานร่วมกันได้โดยไม่ติดขัดกันเอง หัวใจของการกันชนกันคือ
**ความเป็นเจ้าของ config ที่ชัดเจน (single source of truth)**:

| สิ่งที่ตั้งค่า | เจ้าของ | เก็บที่ |
|---------------|---------|---------|
| การ clean (detect/preprocess/mask/denoise/inpaint) | `Profile` | `~/.config/pcleaner/profiles/*.conf` (INI, **ไม่แตะ**) |
| ภาษา source/target | Workspace | `<workspace>/workspace.toml` |
| คลังศัพท์ (terms) | Glossary | `<workspace>/glossary.toml` |
| การตั้งค่าแปล (model, batch, prompt) | `TranslatorConfig` | `[translator]` ใน `workspace.toml` |
| การตั้งค่า render (font, fit, stroke) | `RenderConfig` | `[render]` ใน `workspace.toml` |
| API key, default model, cache dir | `Config` (global) | `pcleanerrc` (INI, ขยายเพิ่ม) |
| geometry กล่อง, สถานะหน้า | cache JSON + sidecar | cache dir (ใช้ UUID เดิม) |

> **กฎเหล็ก:** Profile เป็นเจ้าของ "การ clean" เท่านั้น — Workspace เป็นเจ้าของทุกอย่าง
> ที่เกี่ยวกับการแปล/render/ภาษา — Glossary เป็นไฟล์ที่ Workspace อ้างอิง —
> ไม่มีระบบไหนเขียนทับ config ของระบบอื่น

ดูรายละเอียดการกันชนกันใน [01-architecture.md §3](01-architecture.md)

---

## 3. สถานะปัจจุบัน vs เป้าหมาย

| ด้าน | ปัจจุบัน | เป้าหมาย |
|------|----------|----------|
| Pipeline | 6 step: detect → preprocess → mask → denoise → inpaint → output | + 2 step: **translator → renderer** (เปิด/ปิดได้) |
| OCR | MangaOCR / Tesseract / PaddleOCR-VL (per-box language มีอยู่แล้ว) | ใช้เหมือนเดิม เป็น input ของ translator |
| แปล | ❌ ไม่มี | ✅ OpenRouter LLM + glossary injection |
| Render ข้อความกลับ | ❌ มีแค่ `PageData.visualize()` วาด debug box | ✅ ระบบ layout/auto-fit/font ต่อภาษา |
| จัดระเบียบงานต่อเรื่อง | ❌ มีแค่ Profile (cleaning settings) | ✅ Workspace ครอบ profile + glossary + ภาษา + chapters |
| Interface | CLI + GUI (PySide6) | CLI ก่อน → GUI ตามใน Phase 5 |

---

## 4. ขอบเขตของรอบนี้

- ✅ เขียน **เอกสารออกแบบ** ครบทั้ง 4 ระบบ + สถาปัตยกรรมการเชื่อมต่อ
- ❌ **ไม่** เขียนโค้ด `.py` ใด ๆ
- ❌ **ไม่** แก้ pipeline เดิม

การ implement จริงแบ่งเป็น 5 phase ดู [07-roadmap.md](07-roadmap.md)

---

## 5. สารบัญเอกสาร

| ไฟล์ | เนื้อหา |
|------|---------|
| [00-overview.md](00-overview.md) | (ไฟล์นี้) ภาพรวมโปรเจกต์ |
| [01-architecture.md](01-architecture.md) | สถาปัตยกรรมรวม, data flow, ความเป็นเจ้าของ config, โครงโมดูล |
| [02-workspace.md](02-workspace.md) | Spec ระบบ Workspace |
| [03-glossary.md](03-glossary.md) | Spec ระบบ Glossary |
| [04-openrouter-translation.md](04-openrouter-translation.md) | Spec ระบบแปลผ่าน OpenRouter |
| [05-text-rendering.md](05-text-rendering.md) | Spec ระบบ render ข้อความ |
| [06-cli.md](06-cli.md) | สรุป CLI surface ใหม่ทั้งหมด |
| [07-roadmap.md](07-roadmap.md) | Roadmap ราย phase + เกณฑ์เสร็จ |

---

## 6. ข้อควรระวังที่พบจากการสำรวจโค้ด

`Output` / `Step` ใน `pcleaner/output_structures.py` เป็น `IntEnum` ที่ถูก **เปรียบเทียบ
ตามลำดับค่า** (ดูคอมเมนต์บรรทัด 9–13 และ `get_output_representing_step`) และ logic ใน
`main.py` พึ่งพาว่า `write_output` อยู่ท้ายสุด — ดังนั้นการเพิ่ม `translator`/`renderer`
ต้อง **เพิ่มต่อท้ายและ route ผ่าน `output_to_step`/`step_to_output` map** ไม่ใช่พึ่งลำดับ
enum ดิบ ดูรายละเอียดใน [01-architecture.md §1](01-architecture.md)
