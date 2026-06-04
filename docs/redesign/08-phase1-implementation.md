# Phase 1 — สรุปการ Implement (Foundation & Data Models)

เอกสารนี้สรุปสิ่งที่ implement จริงใน Phase 1 ตาม [07-roadmap.md](07-roadmap.md) Phase 1
เน้น data models, การ load/save/validate, การขยาย enum ของ pipeline และ CLI สำหรับ
workspace/glossary โดย **ไม่แตะ pipeline การ clean เดิม** และ `pcleaner clean` ทำงาน
เหมือนเดิมทุกประการ

## ไฟล์ที่เพิ่ม

| ไฟล์ | บทบาท |
|------|-------|
| `pcleaner/toml_utils.py` | อ่าน/เขียน TOML แบบ atomic (tomllib/tomli + tomli_w) ล้อ `Profile.safe_write` |
| `pcleaner/glossary.py` | `Glossary`, `GlossaryEntry`, `TermType` + load/save/validate + `to_prompt_block()` + `apply_postprocess()` |
| `pcleaner/workspace.py` | `Workspace`, `ProfileRef`, `ChapterEntry`, `PageEntry`, `PageState` + manifest TOML + `resolve_profile()`/`resolve_glossary()` + state tracking |
| `pcleaner/translator/config.py` | `TranslatorConfig` (`@define`) + `GlossaryMode` |
| `pcleaner/translator/structures.py` | `TranslationResult`, `PageTranslation`, `CostAccounting` (JSON sidecar `#translated.json`) |
| `pcleaner/rendering/config.py` | `RenderConfig` (`@define`) + `Alignment` |
| `pcleaner/workspace_cli.py` | CLI handlers: workspace new/add/list/info/status/open |
| `pcleaner/glossary_cli.py` | CLI handlers: glossary list/validate/add/remove/import/export (CSV) |
| `tests/test_glossary.py`, `test_workspace.py`, `test_translator_models.py`, `test_rendering_config.py`, `test_output_structures_translate.py` | unit tests |

## ไฟล์ที่ขยาย (additive)

- `pcleaner/output_structures.py` — เพิ่ม `Step.translator`, `Step.renderer`,
  `Output.translated_json`, `Output.rendered_output` (แทรกก่อน `output`/`write_output`
  เพื่อให้ทั้งสองยังเป็นค่าสูงสุด) + `output_to_step`/`step_to_output` +
  `OutputPathGenerator.translated_json`/`.rendered` + `for_output` cases
- `pcleaner/config.py` — `Config` เพิ่ม `openrouter_api_key`,
  `openrouter_default_model`, `default_workspace`, `saved_workspaces` +
  `add_workspace()`/`remove_workspace()`/`get_openrouter_api_key()` (env precedence) +
  section `[OpenRouter]` / `[Saved Workspaces]` ใน save/load (ทนต่อ config เก่าที่ไม่มี section)
- `pcleaner/cli_utils.py` — `get_workspaces_path()`
- `pcleaner/main.py` — docopt subcommand `workspace` / `glossary` + dispatch (ใช้
  dict-key access เลี่ยง collision ระหว่าง command กับ option ชื่อเดียวกัน)
- `requirements.txt`, `setup-cli.cfg`, `setup-cli-gui.cfg` — เพิ่ม `tomli_w` +
  `tomli` (สำหรับ Python < 3.11)

## คำสั่ง CLI ที่ใช้ได้แล้ว

```
pcleaner workspace new <name> [<path>] --source=<lang> --target=<lang> [--profile=<profile>]
pcleaner workspace (add <name> <path> | list | info <name> | status <name> | open <name>)
pcleaner glossary (list | validate | add <source> <target> [--type=<type>] [--notes=<notes>] |
    remove <source> | import <file> | export <file>) [--workspace=<ws>]
```

## การตรวจสอบ (verification)

```bash
# unit tests ของ Phase 1 (ไม่ต้องใช้ torch/PIL)
pytest tests/test_glossary.py tests/test_workspace.py \
       tests/test_translator_models.py tests/test_rendering_config.py \
       tests/test_output_structures_translate.py
```

ผลที่คาดหวัง: ผ่านทั้งหมด (มี 1 test ถูก skip คือ `box_obj` ที่ต้อง import
`structures.Box` ซึ่งดึง dependency chain หนัก — รันได้ในสภาพแวดล้อมเต็ม)

ตรวจเพิ่มเติมที่ทำแล้ว:
- enum: `max(Step) == Step.output` และ `max(Output) == Output.write_output` ยังคงจริง
- `Config` round-trip section `[OpenRouter]`/`[Saved Workspaces]` + backward compat
  กับ config เก่า (ไม่มี section ใหม่)
- docopt usage ของ `workspace`/`glossary` parse ครบทุก subcommand และ `clean`/`profile`
  เดิมไม่ได้รับผลกระทบ

## หมายเหตุข้อจำกัด (สำหรับ phase ถัดไป)

- ชื่อ workspace/profile ใน `[Saved ...]` ถูก ConfigUpdater แปลงเป็นตัวพิมพ์เล็ก
  (พฤติกรรมเดียวกับ `[Saved Profiles]` เดิม) — แนะนำใช้ชื่อ lowercase
- OpenRouter client, prompt, batching, การ render จริง ยังไม่ทำ (Phase 2–3)
