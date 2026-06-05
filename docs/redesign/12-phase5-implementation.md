# Phase 5 — สรุปการ Implement (GUI — ชุดแรก)

Phase 5 เพิ่ม GUI (PySide6) สำหรับจัดการ workspace และแก้ glossary โดย **ไม่แตะ main
window เดิม** — เป็น dialog แยกที่เปิดผ่าน `pcleaner workspace gui` เพื่อให้ใช้งานได้จริง
และ decouple จากความซับซ้อนของ main window (การฝังเข้า main window ลึก ๆ เป็นงานต่อยอด)

## ไฟล์ที่เพิ่ม

| ไฟล์ | บทบาท |
|------|-------|
| `pcleaner/gui/glossary_editor.py` | `GlossaryEditor(QDialog)` — ตารางแก้ glossary (Source/Target/Type/DNT/Notes) + Add/Remove/Validate/Save, โหลด/เซฟผ่าน `Glossary` model เดียวกับ CLI |
| `pcleaner/gui/workspace_browser.py` | `WorkspaceBrowser(QDialog)` — list saved workspaces + ภาษา + ความคืบหน้า, ปุ่ม Edit Glossary / Open Manifest / Refresh |
| `pcleaner/gui/webtoon_launcher.py` | `launch(config, workspace?)` — สร้าง/ใช้ QApplication แล้วเปิด browser (และ glossary editor ถ้าระบุชื่อ) |
| `tests/test_gui_glossary_editor.py` | smoke tests (offscreen, skip ถ้าไม่มี PySide6) |

## ไฟล์ที่ขยาย

- `pcleaner/workspace_cli.py` — `gui_workspace(config, name)` (เปิด GUI, แจ้งถ้าไม่มี PySide6)
- `pcleaner/main.py` — subcommand `workspace gui [<name>]` (docopt + dispatch, แยกจาก
  top-level `pcleaner gui`)

## แนวทางออกแบบ (ตาม convention เดิม)

- import แบบ `import PySide6.QtWidgets as Qw` / `QtCore as Qc`, ใช้ `from pcleaner.helpers import tr`
- สร้าง widget แบบ **manual** (ไม่พึ่ง generated `Ui_` class → ไม่ต้องมี build step)
- ใช้ `QMessageBox` ตรง ๆ (ไม่ผูกกับ gui_utils chain) → โมดูล self-contained
- glossary editor อ่าน/เขียนผ่าน `pcleaner.glossary.Glossary` ตัวเดียวกับ CLI/translator →
  **GUI กับ CLI sync กันเสมอ** (กันชนกัน: data model เดียว)

## CLI

```
pcleaner workspace gui [<name>]
```
เปิด workspace browser; ถ้าระบุ `<name>` จะเด้ง glossary editor ของ workspace นั้นทันที

## การตรวจสอบ (verification)

```bash
# ในสภาพแวดล้อมที่มี PySide6 (headless ได้):
QT_QPA_PLATFORM=offscreen pytest tests/test_gui_glossary_editor.py
```

ทดสอบจริงด้วย **PySide6 6.11 แบบ offscreen**: populate ตารางจาก glossary, add row +
collect_entries, ข้าม row ว่าง, save→reload round-trip, DNT checkbox สะท้อนค่า — **5 passed**

รวมทุก phase (มี PySide6): **117 passed, 1 skipped**; ถ้าไม่มี PySide6 (CLI-only) GUI test
จะถูก skip อัตโนมัติ (`pytest.importorskip`)

## งานต่อยอด (ยังไม่ทำในชุดนี้)

- ฝัง action เข้า main window เดิม (เมนู/ปุ่ม) — ต้องรัน GUI จริงเพื่อทดสอบการเชื่อม
- translation review/edit panel (reuse แพทเทิร์น OCR-review) + render preview
- ปุ่มสั่ง `workspace run` (clean→translate→render) จาก GUI พร้อม progress bar
