# Roadmap (สำหรับรอบ implement)

แบ่งการ implement เป็น 5 phase แต่ละ phase มีเกณฑ์ "เสร็จ" ชัดเจน Phase 1–4 เป็น CLI-first
ตามที่ผู้ใช้เลือก, Phase 5 ค่อยทำ GUI

> รอบเอกสารนี้ครอบเฉพาะการ **ออกแบบ** — ทุก phase ด้านล่างคือ "งานรอบถัดไป"

---

## Phase 1 — Foundation & data models (ไม่มี network, ไม่มี GUI) ✅ implemented

> สถานะ: **ทำแล้ว** — ดูสรุปการ implement ใน [08-phase1-implementation.md](08-phase1-implementation.md)


**สร้าง:** `glossary.py`, `workspace.py`, `translator/structures.py`,
`translator/config.py`, `rendering/config.py`

**งาน:**
- TOML load/save/validate สำหรับ Glossary + Workspace manifest
- JSON sidecar ที่ compatible กับ `Box` (round-trip เป็น tuple เหมือน `PageData`)
- ขยาย `Step`/`Output` enum + `OutputPathGenerator` (เพิ่มต่อท้าย — ระวัง ordering trap)
- helper dir ใน `cli_utils.py` (`get_workspaces_path` ฯลฯ)
- ขยาย `Config`: `[OpenRouter]` + `[Saved Workspaces]`
- CLI handler `workspace` / `glossary`
- unit tests: round-trip + validation

**เสร็จเมื่อ:** สร้าง/เปิด/list workspace และ glossary ได้ — ยังไม่แปล

---

## Phase 2 — OpenRouter + Glossary injection ✅ implemented

> สถานะ: **ทำแล้ว** — ดูสรุปการ implement ใน [09-phase2-implementation.md](09-phase2-implementation.md)


**สร้าง:** `translator/openrouter.py`, `prompt.py`, `batching.py`, `cache.py`,
`translate.py`

**งาน:**
- OpenRouter client (requests) + retry/rate-limit + cost accounting
- glossary prompt-injection + post-replacement
- CLI `translate` พร้อม `--dry-run`
- เขียน `#translated.json`

**เสร็จเมื่อ:** `pcleaner translate --workspace ...` สร้างคำแปลที่ cache ได้

---

## Phase 3 — Rendering ✅ implemented

> สถานะ: **ทำแล้ว** — ดูสรุปการ implement ใน [10-phase3-implementation.md](10-phase3-implementation.md)


**สร้าง:** `rendering/fonts.py`, `layout.py`, `render.py`; bundle fonts ใน `data/fonts/`

**งาน:**
- font registry + เลือกตามภาษา
- wrapping + auto-fit + alignment + vertical + stroke
- CLI `render` → `_rendered.png`

**เสร็จเมื่อ:** วาดข้อความแปลลงบับเบิลที่ clean ได้

---

## Phase 4 — Workspace orchestration

**งาน:**
- ต่อ translator + renderer เข้า tail ของ `run_cleaner` ภายใต้
  `--workspace`/`--translate`/`--render`
- pipeline ครบ raw → rendered
- page-state tracking ใน manifest
- `workspace status`

**เสร็จเมื่อ:** ประมวลผลทั้งเรื่อง end-to-end ในคำสั่งเดียวได้

---

## Phase 5 — GUI

**งาน (out of scope ของรอบออกแบบนี้):**
- workspace browser (PySide6)
- glossary editor (table)
- translation review/edit panel (reuse แพทเทิร์น OCR-review เดิม)
- render preview

---

## ลำดับการพึ่งพา

```
Phase 1 (foundation)
   ├─▶ Phase 2 (translate)  ─┐
   └─▶ Phase 3 (render)  ────┼─▶ Phase 4 (orchestration) ─▶ Phase 5 (GUI)
                             ┘
```

Phase 2 และ 3 ทำขนานกันได้หลัง Phase 1 เสร็จ (render ใช้ผลของ translate แต่ทดสอบด้วย
`#translated.json` ปลอมได้)

---

## เกณฑ์คุณภาพรวม (ทุก phase)

- ไม่แก้ signature ฟังก์ชันเดิม / ไม่เปลี่ยนค่า enum เดิม
- `pcleaner clean myfolder` เดิมทำงานเหมือนเดิมทุก phase
- ทุกระบบเขียนเฉพาะ config ของตน (ดู checklist ใน [01-architecture.md §3](01-architecture.md))
- มี unit test สำหรับ data model + validation
