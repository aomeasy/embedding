# 🗂️ ระบบจัดการข้อมูล Table & Embedding

โปรเจคนี้ประกอบด้วย 2 ส่วนหลัก:
1. **Streamlit UI** - สำหรับจัดการ Tables และ Import ข้อมูล CSV
2. **Embedding System** - สำหรับสร้าง embeddings อัตโนมัติทุกวัน

## 🚀 วิธีการติดตั้ง

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. สร้าง Virtual Environment (แนะนำ)
```bash
python -m venv venv
source venv/bin/activate  # บน macOS/Linux
# หรือ
venv\Scripts\activate     # บน Windows
```

### 3. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 4. ตั้งค่า Environment Variables
```bash
# คัดลอกไฟล์ตัวอย่าง
cp .env.example .env

# แก้ไขไฟล์ .env และใส่ข้อมูลจริง
# ⚠️ สำคัญ: ต้องใส่ TIDB_URL ที่ถูกต้อง
```

## 📝 การตั้งค่า GitHub Secrets

ไปที่ GitHub Repository Settings > Secrets and variables > Actions และเพิ่ม:

```bash
# TiDB Database Connection (จำเป็น)
TIDB_URL=mysql+pymysql://username:password@host:port/database_name

# Embedding API
EMBEDDING_API_URL=http://209.15.123.47:11434/api/embeddings
EMBEDDING_MODEL=nomic-embed-text:latest
```

### วิธีหา TIDB_URL:
1. เข้า TiDB Cloud Console
2. เลือก Cluster ของคุณ
3. คลิก "Connect" 
4. เลือก "Python" และคัดลอก Connection String
5. แปลงเป็นรูปแบบ SQLAlchemy: `mysql+pymysql://...`

## 🚀 การ Deploy บน GitHub

### วิธีที่ 1: Streamlit Cloud (แนะนำ)
1. ไปที่ https://share.streamlit.io
2. Sign in ด้วย GitHub account
3. คลิก "New app" 
4. เลือก Repository นี้
5. ตั้งค่า main file path: `app.py`
6. เพิ่ม Secrets ใน Streamlit Cloud dashboard

### วิธีที่ 2: GitHub Codespaces
1. ไปที่ GitHub Repository
2. คลิก "Code" > "Codespaces" > "Create codespace"
3. รอจนสร้างเสร็จ แล้วรัน: `streamlit run app.py`

### วิธีที่ 3: Local Development
```bash
# Clone repository
git clone <your-repo-url>
cd <your-repo-name>

# สร้าง .env file (สำหรับ local เท่านั้น)
cp .env.example .env
# แก้ไข .env และใส่ข้อมูลจริง

# ติดตั้งและรัน
pip install -r requirements.txt
streamlit run app.py
```

## 🎯 วิธีการใช้งาน

### 1. เรียกใช้ Streamlit UI
```bash
streamlit run app.py
```

จากนั้นเปิดเบราว์เซอร์ไปที่ `http://localhost:8501`

#### ฟีเจอร์ใน Streamlit UI:
- ✅ **สร้าง Table ใหม่** - กำหนด columns และประเภทข้อมูล
- ✅ **เลือก Table ที่มีอยู่** - ดูโครงสร้างและข้อมูลตัวอย่าง  
- ✅ **Upload CSV File** - ดาวน์โหลด template และ import ข้อมูล
- ✅ **Run Embedding Process** - รัน embedding แบบ interactive
- ✅ **แสดง Status** - progress bar และสรุปผลการ import

### 2. รัน Embedding Script (เดิม)
```bash
python main.py
```

#### ฟีเจอร์ใน main.py:
- อ่านข้อมูลจาก `customers` table
- เรียก Embedding API 
- บันทึก embeddings ใน `customer_vectors` table

## 🤖 GitHub Actions

ระบบจะรัน embedding script อัตโนมัติทุกวันเวลา 00:00 UTC

### Manual Run:
1. ไปที่ GitHub Repository
2. คลิก "Actions" tab
3. เลือก "Embed to TiDB" workflow
4. คลิก "Run workflow"

## 📂 โครงสร้างไฟล์

```
project/
├── app.py                    # Streamlit UI application
├── main.py                   # Embedding script (เดิม)
├── requirements.txt          # Python dependencies
├── .env.example             # ตัวอย่างการตั้งค่า
├── .env                     # การตั้งค่าจริง (ไม่ commit)
├── .gitignore              # ไฟล์ที่ไม่ต้อง commit
├── README.md               # คู่มือนี้
└── .github/
    └── workflows/
        └── embedding-cron.yml  # GitHub Actions config
```

## 🔧 Dependencies

- `streamlit` - สำหรับสร้าง web UI
- `pandas` - จัดการข้อมูล
- `sqlalchemy` - เชื่อมต่อ database
- `pymysql` - MySQL/TiDB driver
- `requests` - เรียก API
- `numpy` - คำนวณ mathematical
- `python-dotenv` - โหลด environment variables

## ⚠️ ข้อควรระวัง

1. **ไฟล์ `.env`** - อย่า commit เข้า git (มีข้อมูลรหัสผ่าน)
2. **TIDB_URL** - ต้องกรอกให้ถูกต้องเสมอ
3. **Database Tables** - `customers` table ต้องมีก่อนใช้ main.py
4. **Embedding API** - ต้องสามารถเข้าถึงได้จากเครื่องที่รัน

## 🆘 Troubleshooting

### ปัญหา Database Connection:
```bash
# ทดสอบการเชื่อมต่อ
python -c "
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('TIDB_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Connected successfully:', result.scalar())
"
```

### ปัญหา Streamlit ไม่เปิด:
```bash
# ตรวจสอบ port
streamlit run app.py --server.port 8502
```

### ปัญหา CSV Import:
- ตรวจสอบว่า columns ใน CSV ตรงกับ table structure
- ดูข้อความ error ในส่วน status
- ลองดาวน์โหลด template ใหม่

## 📞 การติดต่อ

หากมีปัญหาการใช้งาน กรุณาสร้าง Issue ใน GitHub Repository นี้

---
**อัพเดทล่าสุด:** สร้างใน August 2025
