# SCG Report Writer

แอปพลิเคชัน Streamlit สำหรับช่วยเขียนรายงานวิเคราะห์โซเชียลมีเดียรายเดือนของแบรนด์ SCG โดยอัตโนมัติ — รับไฟล์รายงานต้นแบบ (PPTX) และข้อมูลคะแนน (Excel) แล้วใช้ AI (OpenAI) สร้างบทวิเคราะห์ของแต่ละ section ในรายงาน

## ภาพรวม

รายงานฉบับจริงประกอบด้วยหลาย section (เช่น Key Thematic, CES Content, Key Point, Top PRI Content, PRE Key Point ฯลฯ) ซึ่งแต่ละ section ใช้ข้อมูลคนละชุดและมี prompt การวิเคราะห์ต่างกัน โปรเจกต์นี้ถูกออกแบบให้ **ขับเคลื่อนด้วย config** — ประกาศทุก section, pillar, และ prompt ไว้ใน `config.json` แล้วโค้ดกลางจะทำหน้าที่ดึงข้อมูล + เรียก AI ตามนั้น

ปัจจุบันส่วนที่ทำเสร็จแล้วคือ **CES Key Thematic** ส่วน section อื่น ๆ ยังรอการเติม prompt และข้อมูลที่ต้องใช้

## สิ่งที่ผู้ใช้ต้องใส่ (Input)

1. **ไฟล์ PPTX** — รายงานต้นแบบ (เช่น `SCG Monthly Report Automate Template July2.pptx`) ที่มี slide โพสต์ของแต่ละแบรนด์
2. **ไฟล์ Excel** — ตารางคะแนน CES (เช่น `ebmo_July_07082026_summary_Facebook.xlsx`) ซึ่งมีคอลัมน์ Pillar, Brand, และคะแนน + Growth

## กระบวนการทำงาน

### ขั้นที่ 1 — Extract โพสต์จาก PPTX
- แยก slide ที่เป็น "TOP POST" (โพสต์ของแบรนด์) และ "TOP PRI" (โพสต์สื่อ/PR)
- แต่ละโพสต์จะถูกดึงข้อมูลออกมาเป็น structured data:
  - `caption` — ข้อความโพสต์
  - `tag` — หมวดหมู่ (Environmental, Social, Governance, …)
  - `engagement` — ตัวเลข Like / Comment / Share
  - `image` — รูปภาพ thumbnail
- กลุ่มตาม **pillar** (ESG / Business / Employer Branding) และ **แบรนด์** (SCG / PTT / CP)

### ขั้นที่ 2 — อธิบายภาพด้วย AI (Vision)
- ส่งภาพ thumbnail ทั้งหมดใน slide ไปให้ OpenAI ใน request เดียว
- AI เขียนคำอธิบายภาพเป็นภาษาไทย 3 ประโยค (ฉาก / ข้อความภาษาไทยบนภาพ / สไตล์)
- เก็บเป็น `image_description` ต่อกับข้อมูลโพสต์

### ขั้นที่ 3 — วิเคราะห์แต่ละ section ด้วย AI
- ต่อ section ต่อ pillar ต่อแบรนด์ จะถูก filter ข้อมูลเฉพาะที่ section นั้นต้องใช้ แล้วส่งไปให้ AI พร้อม prompt ที่กำหนดไว้
- **ตัวอย่าง (CES Key Thematic):**
  - ส่งโพสต์ของแบรนด์นั้นใน pillar นั้น (เฉพาะ `TOP POST`)
  - ส่งคะแนน CES ของทั้ง 3 แบรนด์ใน pillar เดียวกัน (เพื่อใช้เปรียบเทียบ)
  - ใช้ prompt ใน `config.json` → ได้บทวิเคราะห์ Key Thematic 1 ย่อหน้า (ไม่เกิน 450 ตัวอักษร)

### ขั้นที่ 4 — นำผลไปประกอบเป็นรายงาน
- ผลลัพธ์ของทุก section จะถูกนำไปแทนที่ในเทมเพลต เพื่อประกอบเป็นรายงานฉบับสมบูรณ์ (อยู่ระหว่างพัฒนา)

## Expected Output

- **ระหว่างทาง:** โพสต์ที่ extract แล้วพร้อมภาพ, คำอธิบายภาพ, และคะแนน (แสดงในหน้าเว็บ)
- **ผลลัพธ์สุดท้าย (เป้าหมาย):** รายงานฉบับสมบูรณ์แบบเดียวกับ `SCG Monthly Report July Final.pdf` — แต่ละ section มีบทวิเคราะห์ภาษาไทยที่ AI เขียนจากข้อมูลจริง

## โครงสร้างโปรเจกต์

```
SCG_Report_Writer/
├── app.py                    # Streamlit frontend
├── config.json               # model, pillars, sections, prompts
├── CES_PRE_Reference.md      # คำอธิบายกรอบ CES/PRE (สำหรับอ้างอิงใน prompt)
├── requirements.txt
└── report_writer/
    ├── pptx_extractor.py     # extract โพสต์จาก PPTX + อธิบายภาพด้วย vision
    ├── ces_data.py           # อ่าน/filter ตารางคะแนน CES จาก Excel
    ├── key_thematic.py       # สร้าง request สำหรับวิเคราะห์ Key Thematic
    ├── config.py             # โหลด config
    ├── filters.py            # (legacy) filter ข้อมูล Excel
    └── openai_client.py      # (legacy) client เรียก OpenAI
```

## หมายเหตุ

- Model เริ่มต้นคือ `gpt-5.6-luna`
- ไฟล์ข้อมูล (PPTX/PDF/Excel) และ `.env` ถูก ignore ใน git — ผู้ใช้แต่ละคนใส่ไฟล์ของตัวเอง
