# SCG Report Writer

แอปพลิเคชัน Streamlit สำหรับช่วยเขียนรายงานวิเคราะห์โซเชียลมีเดียรายเดือนของแบรนด์ SCG โดยอัตโนมัติ — รับไฟล์รายงานต้นแบบ (PPTX) และข้อมูลคะแนน (Excel) แล้วใช้ AI (OpenAI) สร้างบทวิเคราะห์ของแต่ละ section ในรายงาน

## ภาพรวม

รายงานฉบับจริงประกอบด้วยหลาย section (เช่น Key Thematic, CES Content, Key Point, Top PRI Content, PRE Key Point ฯลฯ) ซึ่งแต่ละ section ใช้ข้อมูลคนละชุดและมี prompt การวิเคราะห์ต่างกัน โปรเจกต์นี้ถูกออกแบบให้ **ขับเคลื่อนด้วย config** — ประกาศทุก section, pillar, และ prompt ไว้ใน `config.json` แล้วโค้ดกลางจะทำหน้าที่ดึงข้อมูล + เรียก AI ตามนั้น

ปัจจุบันระบบรองรับการวิเคราะห์ **CES Key Thematic**, **Top PRI Content**, **Overview CES** และ **PRE Overview**

## สิ่งที่ผู้ใช้ต้องใส่ (Input)

1. **ไฟล์ PPTX** — รายงานต้นแบบ (เช่น `SCG Monthly Report Automate Template July2.pptx`) ที่มี slide โพสต์ของแต่ละแบรนด์
2. **ไฟล์ Excel คะแนน CES** — ตารางที่มีคอลัมน์ Pillar, Brand, คะแนน CES แต่ละเกณฑ์ และ Growth
3. **ไฟล์ Excel คะแนน PRE** — ตารางที่มี 8 คอลัมน์: Pillar, Brand, PRI, PRI Growth, Standard Rate Card, Standard Rate Card Growth, PRE และ PRE Growth

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

## ข้อมูลประกอบการวิเคราะห์แต่ละส่วน

ระบบแยกข้อมูลด้วย **Pillar** และ **Brand** ก่อนส่งให้ OpenAI เสมอ เพื่อป้องกันข้อมูลต่าง Pillar หรือข้อมูลของแบรนด์อื่นปะปนกัน การกด `Generate All Analysis` หนึ่งครั้งจะประมวลผลตามลำดับ: Key Thematic → Top PRI Content → Overview CES → PRE Overview

### 1. CES Key Thematic

สร้างผลลัพธ์แยกตาม Pillar และ Brand รวมสูงสุด 9 ผลลัพธ์ โดยใช้ข้อมูลดังนี้:

- โพสต์ `TOP POST` เฉพาะแบรนด์ที่กำลังวิเคราะห์ใน Pillar นั้น ได้แก่ caption, tag, engagement, like, comment, share และคำอธิบายภาพจาก AI
- คะแนนของ SCG, PTT และ CP ใน Pillar เดียวกัน เพื่อใช้เปรียบเทียบ ได้แก่ CES Score, Competitive Score, Efficiency Score, Sentiment (Influencer & Publisher), Sentiment (Consumer) และ Growth ของทุกเกณฑ์

### 2. Top PRI Content

สร้างผลลัพธ์แยกตาม Pillar และ Brand รวมสูงสุด 9 ผลลัพธ์ โดยใช้ข้อมูลดังนี้:

- โพสต์ `TOP PRI` เฉพาะแบรนด์ที่กำลังวิเคราะห์ใน Pillar นั้น ได้แก่ caption, tag, publisher, PRI, PRE, engagement และคำอธิบายภาพจาก AI
- ข้อมูลสรุปของ SCG, PTT และ CP ใน Pillar เดียวกัน ได้แก่ PRI, PRI Growth, Standard Rate Card, Standard Rate Card Growth, PRE และ PRE Growth

### 3. Overview CES

สร้างผลลัพธ์แยกตาม Pillar รวมสูงสุด 3 ผลลัพธ์ แต่ละผลลัพธ์มี 3 ย่อหน้า เรียง SCG → PTT → CP โดยใช้ข้อมูลดังนี้:

- คะแนน CES และ Growth ทุกเกณฑ์ของทั้งสามแบรนด์ใน Pillar เดียวกัน
- คำตอบ CES Key Thematic ที่สร้างสำเร็จแล้วของ SCG, PTT และ CP ใน Pillar นั้น
- อันดับ CES และเครื่องหมาย ⭐ ซึ่งระบบคำนวณก่อนส่งข้อมูลให้ OpenAI

Overview CES ไม่ได้รับโพสต์ดิบโดยตรง แต่ใช้คำตอบ Key Thematic เป็นข้อมูลสรุปอ้างอิง หาก Key Thematic หรือ CES Score ไม่ครบทั้งสามแบรนด์ ระบบจะไม่เรียก OpenAI สำหรับ Pillar นั้นและจะแสดงสาเหตุ

### 4. PRE Overview

สร้างผลลัพธ์แยกตาม Pillar รวมสูงสุด 3 ผลลัพธ์ แต่ละผลลัพธ์เรียง SCG → PTT → CP โดยใช้ข้อมูลดังนี้:

- PRI และ PRI Growth ของทั้งสามแบรนด์ใน Pillar เดียวกัน โดยระบบแปลงเป็นหน่วย M และใช้ทศนิยมไม่เกินหนึ่งตำแหน่งก่อนส่ง
- คำตอบ Top PRI Content ที่สร้างสำเร็จแล้วของ SCG, PTT และ CP ใน Pillar นั้น
- สถานะว่าแบรนด์ใดมี PRI สูงสุดในกลุ่ม โดยไม่มีการใส่เครื่องหมายดาว

PRE Overview ไม่ได้รับโพสต์ดิบโดยตรง แต่ใช้คำตอบ Top PRI Content เป็นข้อมูลสรุปอ้างอิง หาก Top PRI Content หรือ PRI/PRI Growth ไม่ครบทั้งสามแบรนด์ ระบบจะไม่เรียก OpenAI สำหรับ Pillar นั้นและจะแสดงสาเหตุ

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
