# 🚀 NTOneEmbedding System

ระบบจัดการข้อมูล AI/ML ครบวงจร - จาก Table สู่ Vector Embeddings

## 📋 Overview

NTOneEmbedding System เป็นเครื่องมือสำหรับการจัดการข้อมูลและสร้าง embeddings สำหรับงาน AI/ML โดยมีความสามารถดังนี้:

- ✅ เชื่อมต่อกับ TiDB Database
- ✅ สร้าง Table ใหม่และจัดการข้อมูล
- ✅ Upload CSV File เพื่อเพิ่มข้อมูล
- ✅ สร้าง Vector Embeddings จากข้อมูลข้อความ
- ✅ UI ที่ทันสมัยด้วย Streamlit

## 🔧 Installation

### 1. Clone Repository

```bash
git clone <your-repository-url>
cd ntone-embedding-system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

สร้างไฟล์ `.env` และตั้งค่าตัวแปรต่อไปนี้:

```env
TIDB_URL=mysql+pymysql://username:password@host:port/database_name
EMBEDDING_API_URL=http://209.15.123.47:11434/api/embeddings
EMBEDDING_MODEL=nomic-embed-text:latest
```

## 📦 Dependencies

สร้างไฟล์ `requirements.txt`:

```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
sqlalchemy>=2.0.0
pymysql>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

## 🚀 Usage

### การใช้งานผ่าน Web Interface (Streamlit)

```bash
streamlit run app.py
```

### การใช้งานผ่าน Command Line

```bash
python main.py
```

## 📁 Project Structure

```
ntone-embedding-system/
├── app.py                 # Streamlit web interface
├── main.py               # Command line interface
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (create this file)
├── .streamlit/          # Streamlit configuration
│   └── config.toml
└── README.md            # This file
```

## 🌐 Deployment on Streamlit Cloud

### 1. GitHub Repository Setup

1. สร้าง GitHub repository
2. Upload โค้ดทั้งหมดไปยัง repository

### 2. Streamlit Cloud Configuration

1. ไปที่ [share.streamlit.io](https://share.streamlit.io)
2. เชื่อมต่อกับ GitHub account
3. เลือก repository ของคุณ
4. ตั้งค่า environment variables ใน Streamlit Cloud:
   - `TIDB_URL`
   - `EMBEDDING_API_URL`
   - `EMBEDDING_MODEL`

### 3. Streamlit Configuration

สร้างโฟลเดอร์ `.streamlit/` และไฟล์ `config.toml`:

```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

## 🔍 Features

### 1. การสร้าง Table ใหม่
- สร้าง database table ด้วย UI ที่ใช้งานง่าย
- กำหนด column types และ constraints

### 2. การจัดการข้อมูล
- Upload CSV files
- ตรวจสอบข้อมูลก่อน import
- แสดง progress การ import

### 3. Vector Embeddings
- สร้าง embeddings จาก text data
- เก็บ embeddings ใน database
- ตรวจสอบ existing embeddings เพื่อหลีกเลี่ยงการทำซ้ำ

### 4. Modern UI
- Dark theme with neon accents
- Responsive design
- Real-time status updates
- Progress indicators

## 🛠️ Technical Details

### Database Schema

**Main Table Example:**
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    age INT,
    city VARCHAR(255),
    signup_date DATE
);
```

**Embedding Table:**
```sql
CREATE TABLE users_vectors (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    embedding LONGBLOB,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
);
```

### API Integration

System ใช้ Ollama API สำหรับการสร้าง embeddings:

```python
payload = {
    "model": "nomic-embed-text:latest",
    "prompt": "text to embed"
}
```

## 🔒 Security

- Environment variables สำหรับข้อมูลสำคัญ
- Database connection pooling
- Error handling และ logging
- Input validation

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - ตรวจสอบ TIDB_URL format
   - ตรวจสอบ network connectivity

2. **Embedding API Error**
   - ตรวจสอบ API endpoint availability
   - ตรวจสอบ model name

3. **Memory Issues**
   - ลดจำนวน batch size
   - ใช้ streaming สำหรับไฟล์ใหญ่

## 📞 Support

สำหรับการสนับสนุนและข้อสงสัย:
- สร้าง GitHub Issue
- ติดต่อ development team

## 📄 License

This project is licensed under the MIT License.

## 🔄 Updates

### Version 1.0.0
- เพิ่ม Streamlit web interface
- รองรับ CSV upload
- ระบบ embedding automation

---

Made with ❤️ by NTOne Team
