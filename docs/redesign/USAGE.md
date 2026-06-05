# คู่มือใช้งาน — Webtoon Translate & Cleaner

คู่มือนี้อธิบายวิธีติดตั้งและใช้งานฟีเจอร์ใหม่ (Glossary, OpenRouter translate, Workspace,
Text rendering) ทั้งบน **Windows (ไฟล์ .bat)** และ **pip ทั่วไป**

> ฟีเจอร์เดิม (`pcleaner clean`) ยังทำงานเหมือนเดิมทุกประการ ฟีเจอร์ใหม่เป็น opt-in

---

## 1. ติดตั้ง

### Windows (ง่ายสุด — ใช้ .bat)

รันจาก **โฟลเดอร์โปรเจกต์** (ไม่ใช่ในโฟลเดอร์ `Windows scripts`):

```bat
".\Windows scripts\webtoon-install.bat"
```
สคริปต์นี้จะสร้าง `venv` และติดตั้ง dependency ทั้งหมด (รวม torch, PySide6, tomli_w)

ตั้งค่า API key ของ OpenRouter (ครั้งเดียว ค่าจะถูกจำไว้):
```bat
".\Windows scripts\webtoon-set-apikey.bat" sk-or-xxxxxxxxxxxxxxxx
```
> ปิด-เปิด terminal ใหม่หลังตั้ง key เพื่อให้ค่ามีผล

### pip (ทุก OS)

ต้องใช้ **Python 3.10+**
```bash
python -m venv venv
venv/bin/pip install -r requirements.txt      # Windows: venv\Scripts\pip
export OPENROUTER_API_KEY=sk-or-...            # Windows: setx OPENROUTER_API_KEY "sk-or-..."
```
รันด้วย `python pcleaner/main.py <args>` หรือ (ถ้า pip install สำเร็จ) คำสั่ง `pcleaner`

---

## 2. แนวคิด

| สิ่ง | เจ้าของ | เก็บที่ |
|------|---------|---------|
| การ clean | **Profile** (เดิม) | `~/.config/pcleaner/profiles/*.conf` |
| ภาษา/glossary/แปล/render/สถานะ | **Workspace** | `<workspace>/workspace.toml` |
| API key | env `OPENROUTER_API_KEY` หรือ config | ไม่อยู่ใน workspace (ปลอดภัยต่อการแชร์) |

โครงโฟลเดอร์ workspace:
```
<workspace>/
  workspace.toml      glossary.toml
  chapters/ch001/
    raw/        ภาพต้นฉบับ
    cleaned/    ภาพที่ลบข้อความแล้ว
    rendered/   ภาพแปลเสร็จ
  cache/        #translated.json ฯลฯ
```

---

## 3. ใช้งาน end-to-end

> ตัวอย่างใช้ `python pcleaner/main.py` — บน Windows ใช้ `".\Windows scripts\webtoon.bat" <args>` แทนได้

```bash
# 1) สร้าง workspace (ตั้งภาษาได้อิสระ)
python pcleaner/main.py workspace new myseries --source=ja --target=th

# 2) วางภาพไว้ที่ <workspace>/chapters/ch001/raw/
#    ตำแหน่ง workspace: ~/.config/pcleaner/workspaces/myseries (หรือระบุ path เองตอน new)

# 3) OCR -> ได้ไฟล์ข้อความ+พิกัดกล่อง
python pcleaner/main.py ocr <raw_images> -o detected.csv --csv

# 4) ประเมินค่าใช้จ่ายก่อน (ไม่เรียก API)
python pcleaner/main.py translate detected.csv --workspace=myseries --dry-run

# 5) รันครบวงจร: clean -> translate -> render + ติดตามสถานะ + resume
python pcleaner/main.py workspace run myseries --ocr=detected.csv --clean

# ดูสถานะ
python pcleaner/main.py workspace status myseries
```

ผลลัพธ์: ภาพแปลอยู่ที่ `<workspace>/chapters/ch001/rendered/`

### แยกขั้น (ถ้าต้องการควบคุมเอง)
```bash
python pcleaner/main.py translate detected.csv --workspace=myseries     # แปลอย่างเดียว
python pcleaner/main.py clean <raw> -o <workspace>/chapters/ch001/cleaned
python pcleaner/main.py render <cleaned_images> --workspace=myseries     # วาดอย่างเดียว
```

---

## 4. Glossary (คลังศัพท์เฉพาะเรื่อง)

```bash
python pcleaner/main.py glossary add ハルカ ฮารุกะ --type=name --workspace=myseries
python pcleaner/main.py glossary add SFX SFX --type=do_not_translate --workspace=myseries
python pcleaner/main.py glossary list --workspace=myseries
python pcleaner/main.py glossary validate --workspace=myseries
python pcleaner/main.py glossary import terms.csv --workspace=myseries   # แก้ใน spreadsheet ได้
```
โหมดการใช้ (ตั้งใน `workspace.toml` `[translator] glossary_mode`): `prompt` / `replace` /
`prompt+replace` (ค่าเริ่มต้น)

---

## 5. GUI (จัดการ workspace + แก้ glossary)

```bash
python pcleaner/main.py workspace gui              # เปิด workspace browser
python pcleaner/main.py workspace gui myseries     # เปิด glossary editor ของเรื่องนั้นเลย
```
Windows: `".\Windows scripts\webtoon-gui.bat"`

---

## 6. ปรับแต่งใน `workspace.toml`

```toml
[translator]
model = "anthropic/claude-3.5-sonnet"   # โมเดล OpenRouter ใดก็ได้
batch_size = 12
glossary_mode = "prompt+replace"

[render]
default_font = "NotoSans"
auto_fit = true
alignment = "center"
stroke_width = 2          # ขอบตัวอักษร
vertical = false          # true = แนวตั้งแบบ CJK

[fonts]                   # ฟอนต์ต่อภาษา (วางไฟล์ฟอนต์ใน <workspace>/fonts/)
ja = "NotoSansJP"
```

---

## 7. สร้างไฟล์ .exe (Windows)

โปรเจกต์มีระบบ build ด้วย PyInstaller อยู่แล้ว ไฟล์ .exe ที่ได้จะรวมคำสั่งใหม่ทั้งหมด
(`workspace`/`glossary`/`translate`/`render`) โดยอัตโนมัติ:

```bat
".\Windows scripts\webtoon-build-exe.bat"
```
ผลลัพธ์อยู่ใน `dist_exe\PanelCleaner\` รันด้วย `PanelCleaner.exe workspace run ...`

---

## 8. แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ/วิธีแก้ |
|-------|---------------|
| `No OpenRouter API key found` | ตั้ง `OPENROUTER_API_KEY` (หรือ `[OpenRouter] api_key` ใน config) แล้วเปิด terminal ใหม่ |
| ข้อความแปล **ไม่ตรงตำแหน่งบับเบิล** | พิกัดกล่อง (OCR) กับภาพ clean คนละสเกล → ใช้ `--scale=<f>` ตอน render/run (ค่าจาก `PageData.scale` ใน `#clean.json`) |
| ตัวอักษรล้นบับเบิล | ลด `max_font_size` หรือเปิด `auto_fit=true` ใน `[render]` |
| ฟอนต์ภาษาเป้าหมายไม่แสดง | วางไฟล์ฟอนต์ใน `<workspace>/fonts/` แล้วตั้งใน `[fonts]` (เช่น `th = "NotoSansThai"`) |
| แปลซ้ำเปลือง cost | คำแปลถูก cache ใน `#translated.json` — รันซ้ำจะข้ามที่แปลแล้ว (ใช้ `--force` ถ้าต้องแปลใหม่) |
| อยากเช็คก่อนจ่าย | `translate ... --dry-run` ประเมินจำนวน request/อักษรโดยไม่เรียก API |

---

ดูสถาปัตยกรรมและรายละเอียดแต่ละระบบใน [00-overview.md](00-overview.md)
