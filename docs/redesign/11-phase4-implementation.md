# Phase 4 — สรุปการ Implement (Workspace Orchestration)

Phase 4 เชื่อม clean → translate → render เป็น end-to-end ภายใต้ workspace เดียว พร้อม
**ติดตามสถานะหน้า** ใน manifest และ **resume** หน้าที่ทำไปแล้ว โดย **ไม่แตะ pipeline การ
clean เดิม** — stage clean ถูก delegate ไปยัง `run_cleaner` เดิม

## ไฟล์ที่เพิ่ม

| ไฟล์ | บทบาท |
|------|-------|
| `pcleaner/workspace_runner.py` | orchestration core (ทดสอบได้): discovery, manifest sync, state machine, translate/render ต่อ workspace ผ่าน injected seams |
| `tests/test_workspace_runner.py` | unit tests (8) |

### ส่วนประกอบใน `workspace_runner.py`
- `STAGE_RANK` / `stage_rank` / `at_least` — state machine `raw < cleaned < translated < rendered`
- `sync_manifest(ws, chapter?)` — สแกน `chapters/<id>/raw/` → เพิ่ม chapter/page เข้า manifest
  (assign uuid, รักษา state/uuid เดิม), idempotent
- `build_jobs(ws, chapter?)` — สร้าง `PageJob` (raw/cleaned/rendered paths + state + uuid)
- `read_scale_from_clean_json(cache_dir, image)` — อ่าน `PageData.scale` จาก `#clean.json`
  (best-effort) เพื่อ map พิกัด box (png space) → ภาพ clean (original res)
- `build_font_registry(ws)` — สร้าง `FontRegistry` จาก render config + `[fonts]` + `fonts/` dir
- `WorkspaceTranslateRender` — `translate_job()` (เขียน `#translated.json` + set state translated),
  `render_job(scale)` (วาดลงภาพ clean→ถ้าไม่มี fallback raw + set state rendered); client + OCR
  bubbles inject ได้

## ไฟล์ที่ขยาย

- `pcleaner/workspace_cli.py` — `run_workspace()` (orchestrate) + `_run_clean_stage()`
  (delegate ไป `main.run_cleaner`) + `_ocr_bubbles_by_stem()` (parse OCR file → Bubbles)
- `pcleaner/render_cli.py` — ใช้ `build_font_registry` ร่วม (ลบโค้ดซ้ำ)
- `pcleaner/main.py` — subcommand `workspace run` (docopt + dispatch)

## CLI

```
pcleaner workspace run <name> [--ocr=<ocr_file>] [--chapter=<chapter>] [--stage=<stage>]
    [--clean] [--scale=<scale>] [--force] [--dry-run]
```

| ออปชัน | หน้าที่ |
|--------|---------|
| `--ocr` | ไฟล์ OCR (จาก `pcleaner ocr`) ให้ text+box ต่อหน้า |
| `--chapter` | จำกัดเฉพาะ chapter เดียว |
| `--stage` | หยุดที่ stage: `clean` / `translate` / `render` (default render) |
| `--clean` | รัน clean (delegate) ก่อน translate/render |
| `--scale` | override coordinate scale ตอน render |
| `--force` | รัน stage ใหม่แม้หน้าจะผ่านแล้ว |
| `--dry-run` | แสดงแผน + สถานะ โดยไม่แปล/วาด/เรียก API |

## Flow ครบวงจร

```
pcleaner workspace new myseries --source=ja --target=th
# วางภาพไว้ที่ <workspace>/chapters/ch001/raw/
pcleaner ocr <raw_images> -o detected.csv
pcleaner clean <raw_images> -o <workspace>/chapters/ch001/cleaned   # หรือใช้ --clean
pcleaner workspace run myseries --ocr=detected.csv
#  -> sync manifest -> translate (cache #translated.json) -> render -> chapters/ch001/rendered/
#  -> อัปเดตสถานะหน้า + สรุป cost; รันซ้ำจะ resume เฉพาะหน้าที่ยังไม่เสร็จ
```

## การกันชนกัน + resume

- **state machine** เป็น single source of truth ใน manifest; แต่ละ stage ข้ามหน้าที่
  `at_least(state, target)` แล้ว (ยกเว้น `--force`)
- translate cache (`#translated.json`) ทำให้รันซ้ำข้ามบับเบิลที่แปลแล้ว
- clean delegate ไป `run_cleaner` เดิม — Profile ยังเป็นเจ้าของการ clean, workspace แค่ชี้
- API key จาก env/global config; geometry จาก OCR/`#clean.json`

## การตรวจสอบ (verification)

```bash
pytest tests/test_workspace_runner.py
```

ครอบคลุม: state machine, sync_manifest (เพิ่ม/idempotent/รักษา state), build_jobs (paths +
filter chapter), read_scale_from_clean_json, translate_job + render_job (เขียน sidecar/PNG +
advance state), render โดยไม่มี translation, translate cache reuse (ส่งเฉพาะบับเบิลใหม่)

> รวม Phase 1–4: **112 passed, 1 skipped** (ตัว skip ต้อง import `structures` ที่ดึง torch)
>
> หมายเหตุ: stage clean และการ parse OCR ใน CLI แตะ torch chain จึงรันได้ในสภาพแวดล้อม
> เต็มเท่านั้น — orchestration core ถูกครอบด้วย unit test ผ่าน fake client + PIL จริง

## ขั้นถัดไป

Phase 5 — GUI: workspace browser, glossary editor, translation review/edit, render preview
