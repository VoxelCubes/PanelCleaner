# CLI Surface ใหม่

ทุก subcommand เพิ่มแบบ **additive** เข้า docopt block ใน `pcleaner/main.py` —
subcommand เดิม (`clean`, `profile`, `gui`, `ocr`, `config`, `cache`, `load models`,
`languages`) **ไม่เปลี่ยน**

---

## 1. Workspace

```
pcleaner workspace new <name> [<path>] --source=<lang> --target=<lang> [--profile=<profile>]
pcleaner workspace (list | info <name> | status <name> | open <name>)
pcleaner workspace add <name> <path>
```

| คำสั่ง | หน้าที่ |
|--------|---------|
| `new` | สร้าง workspace ใหม่ (สร้าง dir + `workspace.toml` + glossary เปล่า) |
| `add` | ลงทะเบียน workspace ที่มีอยู่เข้า `Config.saved_workspaces` |
| `list` | แสดง workspace ที่ลงทะเบียนทั้งหมด |
| `info` | แสดงรายละเอียด manifest (ภาษา, profile, glossary, model) |
| `status` | สรุปความคืบหน้า raw/cleaned/translated/rendered ต่อ chapter |
| `open` | เปิด `workspace.toml` ใน editor (ล้อ `profile open`) |

---

## 2. Glossary

```
pcleaner glossary (list | validate) [--workspace=<ws>]
pcleaner glossary add <source> <target> [--type=<t>] [--notes=<n>] [--workspace=<ws>]
pcleaner glossary remove <source> [--workspace=<ws>]
pcleaner glossary (import <file> | export <file>) [--workspace=<ws>]
```

- `--type` = `name` | `term` | `honorific` | `do_not_translate`
- `import`/`export` รองรับ CSV เพื่อแก้ใน spreadsheet

---

## 3. Translate

```
pcleaner translate [<image_path> ...] [--workspace=<ws>] [--model=<m>] [--force] [--dry-run] [--debug]
```

| ออปชัน | หน้าที่ |
|--------|---------|
| `--workspace` | ระบุ workspace (ชื่อหรือ path) ที่ให้ภาษา/glossary/translator config |
| `--model` | override model ของ run นี้ |
| `--force` | แปลใหม่แม้มี cache |
| `--dry-run` | ประเมิน token/ค่าใช้จ่าย **โดยไม่เรียก API** |

---

## 4. Render

```
pcleaner render [<image_path> ...] [--workspace=<ws>] [--debug]
```

---

## 5. Flow รวม (สะดวก)

```
pcleaner clean [...] [--workspace=<ws>] [--translate] [--render]
```

ทำ pipeline ครบ raw → rendered ในคำสั่งเดียวเมื่อระบุ workspace + flags

---

## 6. การ resolve `--workspace` / `--profile`

`--workspace` resolve ตามชื่อใน `Config.saved_workspaces` หรือ path ตรง ๆ โดยใช้
`closest_match` ล้อ logic การ resolve `--profile` ที่มีอยู่เป๊ะ

---

## 7. Backward compatibility

- `pcleaner clean myfolder` (ไม่มี `--workspace`/`--translate`/`--render`) ทำงาน
  **เหมือนเดิมทุกประการ** — ไม่แปล ไม่ render
- subcommand ใหม่ทั้งหมดเป็น opt-in
- step `translator`/`renderer` ทำงานเฉพาะเมื่อ workspace active หรือใส่ flag ที่เกี่ยวข้อง

ดูสถาปัตยกรรมเบื้องหลังใน [01-architecture.md](01-architecture.md)
