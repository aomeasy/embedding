# 🗂️ ระบบ Embedding SQL Database

ระบบจัดการ Tables, Import ข้อมูل CSV และสร้าง Vector Embeddings อย่างทันสมัยด้วย Streamlit UI ที่สวยงาม

## ✨ ฟีเจอร์หลัก

### 🆕 สร้าง Table ใหม่
- ✅ กำหนด columns และประเภทข้อมูลได้หลากหลาย
- ✅ ระบบ Auto-increment ID primary key
- ✅ ตรวจสอบและแสดงโครงสร้าง table
- ✅ UI ทันสมัยด้วยธีมสีดำ/น้ำเงินนีออน

### 📋 เลือก Table ที่มีอยู่
- ✅ ดูโครงสร้างและข้อมูลตัวอย่าง
- ✅ แสดงสถานะ Embedding (embedded แล้ว/รอ embedding)
- ✅ เมตริกส์แสดงจำนวนข้อมูลแบบเรียลไทม์
- ✅ ตรวจสอบ records ที่ embed แล้วเพื่อไม่ทำซ้ำ

### 📁 Upload CSV File
- ✅ ดาวน์โหลด Template CSV อัตโนมัติ
- ✅ ตรวจสอบ columns และแสดงสถานะ
- ✅ Import ข้อมูลพร้อม Progress Bar
- ✅ รายงานสรุปผลและข้อผิดพลาด

### 🤖 Run Embedding Process
- ✅ รัน embedding แบบ interactive
- ✅ เลือก Table ที่มีอยู่สำหรับทำ embedding
- ✅ ตรวจสอบก่อนว่า record ไหน embedding แล้ว (ไม่ทำซ้ำ)
- ✅ สร้าง embedding table อัตโนมัติ
- ✅ แสดง Progress และสถานะแบบเรียลไทม์
- ✅ **แก้ไข Error: 'str' object is not callable แล้ว**

## 🎨 UI Design

### ธีมสีใหม่: Dark/Neon Blue Modern
- 🌃 พื้นหลังสีดำไล่เฉดน้ำเงินเข้ม
- 💎 ปุ่มและองค์ประกอบ UI สีน้ำเงินนีออน
- ✨ เอฟเฟ็กต์เรืองแสงและ Animation
- 🎯 การ์ดและกล่องข้อมูลสไตล์ทันสมัย
- 📱 Responsive Design

### การปรับปรุง UI
- 🔥 Header แบบไล่สีพร้อม Animation
- 💫 ปุ่มที่มีเอฟเฟ็กต์ Hover และ Neon Glow
- 📊 Metric Cards ที่สวยงามพร้อม Hover Effects
- 🌈 Progress Bar แบบไล่สีนีออน
- 📋 Form Elements สีดำทันสมัย

## 🚀 การติดตั้ง

### Requirements
```bash
streamlit
pandas
numpy
requests
sqlalchemy
pymysql
python-dotenv
```

### ติดตั้ง Dependencies
```bash
pip install streamlit pandas numpy requests sqlalchemy pymysql python-dotenv
```

## ⚙️ การตั้งค่า

### Environment Variables (.env)
สร้างไฟล์ `.env` หรือตั้งค่าใน Streamlit Cloud:

```env
TIDB_URL=mysql+pymysql://username:password@host:port/database_name
EMBEDDING_API_URL=http://209.15.123.47:11434/api/embeddings
EMBEDDING_MODEL=nomic-embed-text:latest
```

### สำหรับ Streamlit Cloud
ไปที่ **Settings > Environment Variables** และเพิ่ม:
```toml
TIDB_URL = "mysql+pymysql://username:password@host:port/database_name"
EMBEDDING_API_URL = "http://209.15.123.47:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text:latest"
```

## 🏃‍♂️ วิธีใช้งาน

### รันแบบ Local
```bash
streamlit run app.py
```

### รันแบบ Command Line (สำหรับ Embedding อย่างเดียว)
```bash
python main.py
```

### Deploy บน Streamlit Cloud
1. Push โค้ดไปยัง GitHub Repository
2. ไปที่ [share.streamlit.io](https://share.streamlit.io)
3. เชื่อมต่อกับ GitHub Repository
4. ตั้งค่า Environment Variables
5. Deploy!

## 📁 โครงสร้างไฟล์

```
.
├── app.py              # Streamlit Web Application (UI สวยงาม)
├── main.py            # Command Line Tool สำหรับ Embedding
├── .env               # Environment Variables (อย่าใส่ใน Git!)
├── README.md          # เอกสารนี้
└── requirements.txt   # Python Dependencies
```

## 🔧 ฟีเจอร์ที่แก้ไขแล้ว

### ✅ แก้ไข Error ใน Embedding Process
- **ปัญหา**: `'str' object is not callable` ใน signup_date
- **แก้ไข**: ใช้ `lambda d: d.isoformat() if hasattr(d, 'isoformat') else str(d)`
- **ผลลัพธ์**: ระบบทำงานได้ปกติโดยไม่มี error

### ✅ ปรับปรุงการจัดการข้อมูล
- เลือก Table ที่มีอยู่สำหรับทำ embedding
- ตรวจสอบข้อมูลที่ embed แล้วเพื่อไม่ทำซ้ำ
- สร้าง embedding table อัตโนมัติ
- รองรับ columns ที่หลากหลาย

### ✅ ปรับปรุง UI ให้ทันสมัย
- ธีมสีดำ/น้ำเงินนีออนทันสมัย
- Animation และ Visual Effects
- Responsive Design
- ปรับปรุง UX/UI ทุกส่วน

## 🛠️ การแก้ปัญหา

### Database Connection
- ตรวจสอบ TIDB_URL ให้ถูกต้อง
- ตรวจสอบ Network connectivity
- ตรวจสอบ Username/Password

### Embedding API
- ตรวจสอบ EMBEDDING_API_URL
- ตรวจสอบว่า API Server ทำงานอยู่
- ตรวจสอบ Model name

### Common Issues
- ตรวจสอบ Dependencies ให้ครบถ้วน
- ตรวจสอบ Python version (แนะนำ 3.8+)
- ตรวจสอบ Environment Variables

## 🎯 การใช้งานจริง

### สำหรับ Development
1. ใช้ `app.py` สำหรับทดสอบและจัดการข้อมูล
2. ใช้ `main.py` สำหรับ batch processing

### สำหรับ Production
1. Deploy `app.py` บน Streamlit Cloud
2. ตั้งค่า Environment Variables ใน Cloud
3. ใช้งานผ่าน Web Interface

## 📊 ตัวอย่างข้อมูล

### CSV Template
```csv
name,email,age,city,signup_date
John Doe,john@example.com,30,Bangkok,2023-07-01
Jane Smith,jane@example.com,25,Chiang Mai,2023-07-02
```

### Database Schema
```sql
-- Main Table
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    age INT,
    city VARCHAR(255),
    signup_date DATE
);

-- Embedding Table (สร้างอัตโนมัติ)
CREATE TABLE customers_vectors (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    embedding LONGBLOB,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 สรุป

ระบบนี้จัดการครบวงจร ตั้งแต่การสร้าง Table, Import CSV, ไปจนถึงการสร้าง Vector Embeddings พร้อม UI ที่สวยงามและทันสมัย เหมาะสำหรับงาน AI/ML ที่ต้องการจัดการข้อมูลและ embeddings อย่างมีประสิทธิภาพ

### 🎉 ผลลัพธ์
- ✅ UI ทันสมัยธีมสีดำ/น้
