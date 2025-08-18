import streamlit as st
import pandas as pd
import numpy as np
import json
import base64
import requests
from datetime import datetime, date
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, Text, DateTime, Float, event
from sqlalchemy.exc import SQLAlchemyError
import pymysql
import os
import time
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

# Configuration
st.set_page_config(
    page_title="NTOneEmbedding System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# เพิ่มการโหลด environment variables สำหรับ Streamlit Cloud
# Streamlit Cloud จะใช้ secrets management แทน .env file
try:
    TIDB_URL = st.secrets.get("TIDB_URL") or os.environ.get("TIDB_URL")
    EMBEDDING_API_URL = st.secrets.get("EMBEDDING_API_URL") or os.environ.get("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
    EMBEDDING_MODEL = st.secrets.get("EMBEDDING_MODEL") or os.environ.get("EMBEDDING_MODEL", "nomic-embed-text:latest")
    # เพิ่ม API URL สำหรับ chat/generation
    CHAT_API_URL = st.secrets.get("CHAT_API_URL") or os.environ.get("CHAT_API_URL", "http://209.15.123.47:11434/api/generate")
    CHAT_MODEL = st.secrets.get("CHAT_MODEL") or os.environ.get("CHAT_MODEL", "Qwen3:14b")
except:
    # Fallback สำหรับการรันใน local
    TIDB_URL = os.environ.get("TIDB_URL")
    EMBEDDING_API_URL = os.environ.get("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text:latest")
    CHAT_API_URL = os.environ.get("CHAT_API_URL", "http://209.15.123.47:11434/api/generate")
    CHAT_MODEL = os.environ.get("CHAT_MODEL", "Qwen3:14b")

# Modern CSS with Enhanced Sidebar and Dark/Neon Theme (เหมือนเดิม)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1d3a 100%);
        color: #e1e5f1;
    }
    
    .main {
        font-family: 'Inter', sans-serif;
        background: transparent;
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg, .css-1rs6os, .stSidebar {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important;
        border-right: 2px solid #3b82f6 !important;
        box-shadow: 5px 0 20px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 25%, #06b6d4 50%, #0ea5e9 75%, #2563eb 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(37, 99, 235, 0.3), 0 0 0 1px rgba(59, 130, 246, 0.2);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .main-header h1 {
        color: #ffffff;
        margin: 0;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        font-weight: 800;
        font-size: 2.8rem;
        position: relative;
        z-index: 2;
        background: linear-gradient(45deg, #ffffff, #e1e5f1, #ffffff);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    
    /* Status Indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    .status-running {
        background: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    }
    
    .status-waiting {
        background: #f59e0b;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
    }
    
    .status-complete {
        background: #3b82f6;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
    }
    
    /* Success Box */
    .success-box {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        border: 1px solid #10b981;
        color: #d1fae5;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.2), 0 0 0 1px rgba(16, 185, 129, 0.1);
    }
    
    /* Error Box */
    .error-box {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border: 1px solid #ef4444;
        color: #fecaca;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(239, 68, 68, 0.2), 0 0 0 1px rgba(239, 68, 68, 0.1);
    }
    
    /* Info Box */
    .info-box {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
        border: 1px solid #3b82f6;
        color: #dbeafe;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2), 0 0 0 1px rgba(59, 130, 246, 0.1);
    }
    
    /* Chat Box Styles */
    .chat-box {
        background: linear-gradient(135deg, #312e81 0%, #3730a3 100%);
        border: 1px solid #6366f1;
        color: #e0e7ff;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.2), 0 0 0 1px rgba(99, 102, 241, 0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
        border: 1px solid #3b82f6;
        color: #dbeafe;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        margin-left: 20%;
    }
    
    .ai-message {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        border: 1px solid #10b981;
        color: #d1fae5;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        margin-right: 20%;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3), 0 0 0 1px rgba(59, 130, 246, 0.2);
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# ===== Helpers for CSV -> Table (ใหม่) =====
def _sanitize_identifier(name: str) -> str:
    """แปลงชื่อ table/column ให้ปลอดภัย: เป็น snake_case และมีแต่ a-z0-9_"""
    import re
    if not isinstance(name, str):
        name = str(name)
    name = name.strip()
    name = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE)
    name = name.strip("_").lower()
    if not name:
        name = "col"
    return name[:64]

def _infer_sqlalchemy_type_from_series(s: pd.Series):
    """เดา SQLAlchemy type จาก pandas Series"""
    # ลอง datetime
    try:
        s_dt = pd.to_datetime(s, errors='coerce', utc=True)
        if s_dt.notna().mean() > 0.8:
            return DateTime
    except Exception:
        pass

    # ตัวเลข
    s_num = pd.to_numeric(s, errors='coerce')
    if s_num.notna().mean() > 0.9:
        if (s_num.dropna() % 1 != 0).any():
            return Float
        else:
            return Integer

    # boolean แบบข้อความ
    vals = s.dropna().astype(str).str.lower().unique().tolist()
    if set(vals).issubset({"true", "false", "0", "1", "yes", "no"}):
        return Integer  # เก็บเป็น 0/1

    # string: ประเมินความยาว
    try:
        max_len = int(s.dropna().astype(str).str.len().max())
        if max_len and max_len > 255:
            return Text
        else:
            return String(255)
    except Exception:
        return String(255)

def _ensure_mysql_utf8mb4(url: str) -> str:
    """ถ้าเป็น mysql+pymysql://... แล้วไม่มี charset ให้เติม ?charset=utf8mb4"""
    try:
        if not url or "mysql" not in url:
            return url
        parts = urlsplit(url)
        q = dict(parse_qsl(parts.query, keep_blank_values=True))
        if "charset" not in q:
            q["charset"] = "utf8mb4"
        new_query = urlencode(q, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
    except Exception:
        return url

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.connect_to_database()
    
    def connect_to_database(self):
        """เชื่อมต่อกับ TiDB/MySQL ด้วย utf8mb4"""
        try:
            if not TIDB_URL:
                st.error("❌ TIDB_URL ไม่ได้กำหนดใน environment variables")
                return False

            tidb_url = _ensure_mysql_utf8mb4(TIDB_URL)

            # บังคับ charset ฝั่ง driver ด้วย
            self.engine = create_engine(
                tidb_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"charset": "utf8mb4", "use_unicode": True}
            )

            # บังคับ session ให้เป็น utf8mb4 เสมอ
            @event.listens_for(self.engine, "connect")
            def _set_names_utf8mb4(dbapi_connection, connection_record):
                with dbapi_connection.cursor() as cur:
                    cur.execute("SET NAMES utf8mb4")

            # ทดสอบการเชื่อมต่อ
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อ Database ได้: {str(e)}")
            return False
    
    def get_existing_tables(self):
        """ดึงรายชื่อ tables ที่มีอยู่ในระบบ"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]
                return tables
        except Exception as e:
            st.error(f"❌ ไม่สามารถดึงรายชื่อ tables ได้: {str(e)}")
            return []
    
    def get_table_columns(self, table_name):
        """ดึง columns ของ table ที่เลือก"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            return columns
        except Exception as e:
            st.error(f"❌ ไม่สามารถดึง columns ของ table {table_name} ได้: {str(e)}")
            return []

    def get_table_data_sample(self, table_name, limit=5):
        """ดึงข้อมูลตัวอย่างจาก table"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                data = result.fetchall()
                columns = result.keys()
                return data, columns
        except Exception as e:
            st.error(f"❌ ไม่สามารถดึงข้อมูลตัวอย่างได้: {str(e)}")
            return [], []
    
    def search_similar_vectors(self, table_name, query_vector, top_k=5):
        """ค้นหา vectors ที่คล้ายกับ query vector โดยใช้ cosine similarity"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT id, combined_text, embedding, metadata FROM {table_name}"))
                
                similarities = []
                query_vector = np.array(query_vector, dtype=np.float32)
                query_norm = np.linalg.norm(query_vector)
                
                for row in result.fetchall():
                    try:
                        stored_vector = np.frombuffer(row[2], dtype=np.float32)
                        stored_norm = np.linalg.norm(stored_vector)
                        
                        if query_norm > 0 and stored_norm > 0:
                            similarity = np.dot(query_vector, stored_vector) / (query_norm * stored_norm)
                            similarities.append({
                                'id': row[0],
                                'text': row[1],
                                'similarity': float(similarity),
                                'metadata': json.loads(row[3]) if row[3] else {}
                            })
                    except Exception:
                        continue
                
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                return similarities[:top_k]
                
        except Exception as e:
            st.error(f"❌ ไม่สามารถค้นหา similar vectors ได้: {str(e)}")
            return []

    def create_new_table(self, table_name, columns_config):
        """สร้าง table ใหม่ตาม configuration ที่กำหนด (โหมดกำหนดเอง)"""
        try:
            metadata = MetaData()
            table_columns = []
            table_columns.append(Column('id', Integer, primary_key=True, autoincrement=True))
            
            for col_config in columns_config:
                col_name = col_config['name']
                col_type = col_config['type']
                col_nullable = col_config['nullable']
                
                if col_name.lower() == 'id':
                    continue
                
                if col_type == 'Integer':
                    column = Column(col_name, Integer, nullable=col_nullable)
                elif col_type == 'String':
                    column = Column(col_name, String(255), nullable=col_nullable)
                elif col_type == 'Text':
                    column = Column(col_name, Text, nullable=col_nullable)
                elif col_type == 'Float':
                    column = Column(col_name, Float, nullable=col_nullable)
                elif col_type == 'DateTime':
                    column = Column(col_name, DateTime, nullable=col_nullable)
                else:
                    column = Column(col_name, String(255), nullable=col_nullable)
                
                table_columns.append(column)
            
            table = Table(
                table_name, metadata, *table_columns,
                mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci'
            )
            metadata.create_all(self.engine)

            # เผื่อ default DB ไม่ใช่ utf8mb4
            with self.engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            
            return True
        except Exception as e:
            st.error(f"❌ ไม่สามารถสร้าง table {table_name} ได้: {str(e)}")
            return False

    # ====== เพิ่มใหม่: สร้างตารางจาก DataFrame (CSV) ======
    def create_table_from_dataframe(self, table_name, df, add_id_pk=True, dtype_overrides=None, nullables=None):
        """
        สร้างตารางจาก DataFrame:
        - table_name: ชื่อ table (จะ sanitize ให้อีกชั้น)
        - df: pandas DataFrame (ใช้ชื่อคอลัมน์ต้นฉบับ)
        - add_id_pk: เพิ่มคอลัมน์ id PK auto-increment
        - dtype_overrides: dict[original_col_name] -> SQLAlchemy type (String(255)/Text/Integer/Float/DateTime)
        - nullables: dict[original_col_name] -> True/False
        """
        try:
            safe_table_name = _sanitize_identifier(table_name)
            metadata = MetaData()
            columns = []

            if add_id_pk:
                columns.append(Column('id', Integer, primary_key=True, autoincrement=True))

            dtype_overrides = dtype_overrides or {}
            nullables = nullables or {}

            # เตรียมชื่อคอลัมน์ที่ปลอดภัย และ map กลับ
            safe_cols = []
            name_map = {}  # original -> safe
            for c in df.columns:
                safe_c = _sanitize_identifier(c)
                base, i = safe_c, 1
                while safe_c in safe_cols or (add_id_pk and safe_c == 'id'):
                    safe_c = f"{base}_{i}"
                    i += 1
                safe_cols.append(safe_c)
                name_map[c] = safe_c

            # สร้าง Columns ตามชนิด (ใช้ overrides ถ้ามี ไม่งั้นเดา)
            for original_c in df.columns:
                safe_c = name_map[original_c]
                if add_id_pk and safe_c == 'id':
                    continue

                if original_c in dtype_overrides and dtype_overrides[original_c]:
                    sa_type = dtype_overrides[original_c]
                else:
                    sa_type = _infer_sqlalchemy_type_from_series(df[original_c])

                is_nullable = nullables.get(original_c, True)

                if hasattr(sa_type, 'length') or sa_type in [Text, Integer, Float, DateTime]:
                    columns.append(Column(safe_c, sa_type, nullable=is_nullable))
                else:
                    if getattr(sa_type, "__name__", "") == 'String':
                        columns.append(Column(safe_c, String(255), nullable=is_nullable))
                    else:
                        columns.append(Column(safe_c, sa_type(), nullable=is_nullable))

            table = Table(
                safe_table_name, metadata, *columns,
                mysql_charset='utf8mb4', mysql_collate='utf8mb4_unicode_ci'
            )
            metadata.create_all(self.engine)
            with self.engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {safe_table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            return True, safe_table_name, name_map
        except Exception as e:
            st.error(f"❌ ไม่สามารถสร้าง table จาก CSV ได้: {str(e)}")
            return False, None, {}

    def bulk_insert_dataframe(self, table_name, df, add_id_pk=True, name_map=None):
        """
        นำเข้าข้อมูล df ลง table แบบ bulk (ใช้ to_sql)
        - หาก add_id_pk=True ให้ไม่พยายามเขียนลงคอลัมน์ id
        - name_map: map จากชื่อคอลัมน์ต้นฉบับ -> ชื่อคอลัมน์ในตาราง (ปลอดภัยแล้ว)
        """
        try:
            df_to_write = df.copy()
            if name_map:
                df_to_write.columns = [name_map.get(c, c) for c in df.columns]
            if add_id_pk and 'id' in df_to_write.columns:
                df_to_write = df_to_write.drop(columns=['id'])

            df_to_write = df_to_write.where(pd.notna(df_to_write), None)
            df_to_write.to_sql(table_name, con=self.engine, if_exists='append', index=False, chunksize=500)
            return True, len(df_to_write)
        except Exception as e:
            st.error(f"❌ นำเข้าข้อมูลล้มเหลว: {str(e)}")
            return False, 0

    def insert_data_from_csv(self, table_name, df):
        """เพิ่มข้อมูลจาก DataFrame เข้า table (เมนู Upload CSV เดิม)"""
        try:
            success_count = 0
            error_count = 0
            errors = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_rows = len(df)
            
            with self.engine.begin() as conn:
                for index, row in df.iterrows():
                    try:
                        row_dict = {k: v for k, v in row.to_dict().items() if k.lower() != 'id'}
                        for key, value in row_dict.items():
                            if pd.isna(value):
                                row_dict[key] = None
                        
                        columns = ', '.join(row_dict.keys())
                        placeholders = ', '.join([f':{key}' for key in row_dict.keys()])
                        
                        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        conn.execute(text(sql), row_dict)
                        
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"แถวที่ {index + 1}: {str(e)}")
                    
                    progress = (index + 1) / total_rows
                    progress_bar.progress(progress)
                    status_text.text(f"กำลังประมวลผล: {index + 1}/{total_rows}")
            
            progress_bar.empty()
            status_text.empty()
            
            return success_count, error_count, errors
            
        except Exception as e:
            st.error(f"❌ ไม่สามารถเพิ่มข้อมูลได้: {str(e)}")
            return 0, len(df), [str(e)]

# เพิ่มฟังก์ชันสำหรับ AI Q&A
def get_embedding_from_text(text):
    """สร้าง embedding จากข้อความ"""
    try:
        response = requests.post(
            EMBEDDING_API_URL,
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "embedding" in result:
                return result["embedding"]
    except Exception as e:
        st.error(f"ไม่สามารถสร้าง embedding ได้: {str(e)}")
    return None

def generate_ai_response(prompt, context=""):
    """เรียก AI API เพื่อตอบคำถาม"""
    try:
        full_prompt = f"""คุณเป็น AI ผู้ช่วยที่ฉลาดและมีประสิทธิภาพ กรุณาตอบคำถามอย่างละเอียดและครบถ้วน

ข้อมูลบริบท:
{context}

คำถาม: {prompt}

กรุณาตอบเป็นภาษาไทยอย่างชัดเจนและเป็นประโยชน์:"""

        response = requests.post(
            CHAT_API_URL,
            json={
                "model": CHAT_MODEL,
                "prompt": full_prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "ไม่สามารถได้รับคำตอบได้")
        else:
            return f"ข้อผิดพลาด API: {response.status_code}"
            
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

def show_ai_qa_interface():
    """แสดง interface สำหรับ AI Q&A"""
    st.markdown("""
    <div class="chat-box">
        <h3>🤖 AI Question & Answer</h3>
        <p>ถามคำถามกับ AI และค้นหาข้อมูลจากฐานข้อมูลของคุณ</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    st.markdown("### ⚙️ ตั้งค่าการทำงาน")
    
    col1, col2 = st.columns(2)
    with col1:
        qa_mode = st.radio(
            "เลือกโหมด:",
            ["💬 Chat ธรรมดา", "🔍 Chat + ค้นหาข้อมูล"],
            help="Chat ธรรมดา = ตอบจาก AI เท่านั้น, Chat + ค้นหา = ตอบพร้อมค้นหาข้อมูลจากฐานข้อมูล"
        )
    
    with col2:
        search_table = None
        if qa_mode == "🔍 Chat + ค้นหาข้อมูล":
            tables = st.session_state.db_manager.get_existing_tables()
            embedding_tables = [t for t in tables if t.endswith('_vectors')]
            
            if embedding_tables:
                search_table = st.selectbox(
                    "เลือก Vector Table สำหรับค้นหา:",
                    options=embedding_tables,
                    help="เลือก table ที่มี embeddings เพื่อใช้ในการค้นหา"
                )
            else:
                st.warning("⚠️ ยังไม่มี embedding tables")
    
    st.markdown("### 💬 การสนทนา")
    chat_container = st.container()
    
    with chat_container:
        for i, chat in enumerate(st.session_state.chat_history):
            if chat['type'] == 'user':
                st.markdown(f"""
                <div class="user-message">
                    <strong>👤 คุณ:</strong><br>
                    {chat['message']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="ai-message">
                    <strong>🤖 AI:</strong><br>
                    {chat['message']}
                </div>
                """, unsafe_allow_html=True)
                
                if 'search_results' in chat and chat['search_results']:
                    with st.expander("📊 ข้อมูลที่ค้นพบ"):
                        for j, result in enumerate(chat['search_results']):
                            st.text(f"🔍 ผลลัพธ์ {j+1} (คะแนน: {result['similarity']:.3f})")
                            st.text(result['text'])
                            st.markdown("---")
    
    st.markdown("### ❓ ถามคำถาม")
    
    with st.form("question_form"):
        user_question = st.text_area(
            "พิมพ์คำถามของคุณ:",
            placeholder="เช่น: อธิบายเกี่ยวกับข้อมูลในระบบ หรือ หาข้อมูลเกี่ยวกับ...",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit_button = st.form_submit_button("🚀 ส่งคำถาม", type="primary")
        with col2:
            clear_button = st.form_submit_button("🗑️ ล้างประวัติ")
        
        if clear_button:
            st.session_state.chat_history = []
            st.rerun()
    
    if submit_button and user_question.strip():
        st.session_state.chat_history.append({
            'type': 'user',
            'message': user_question,
            'timestamp': datetime.now()
        })
        
        with st.spinner("🤔 AI กำลังคิด..."):
            context = ""
            search_results = []
            
            if qa_mode == "🔍 Chat + ค้นหาข้อมูล" and search_table:
                question_embedding = get_embedding_from_text(user_question)
                
                if question_embedding:
                    search_results = st.session_state.db_manager.search_similar_vectors(
                        search_table, question_embedding, top_k=3
                    )
                    
                    if search_results:
                        context_parts = []
                        for result in search_results:
                            context_parts.append(f"ข้อมูล (คะแนน {result['similarity']:.3f}): {result['text']}")
                        context = "\n\n".join(context_parts)
            
            ai_response = generate_ai_response(user_question, context)
            
            chat_entry = {
                'type': 'ai',
                'message': ai_response,
                'timestamp': datetime.now()
            }
            
            if search_results:
                chat_entry['search_results'] = search_results
            
            st.session_state.chat_history.append(chat_entry)
        
        st.rerun()
    
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 📊 สถิติการสนทนา")
        
        user_messages = len([c for c in st.session_state.chat_history if c['type'] == 'user'])
        ai_messages = len([c for c in st.session_state.chat_history if c['type'] == 'ai'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👤 คำถามทั้งหมด", user_messages)
        with col2:
            st.metric("🤖 คำตอบทั้งหมด", ai_messages)
        with col3:
            if st.session_state.chat_history:
                last_chat = st.session_state.chat_history[-1]['timestamp']
                st.metric("🕒 สนทนาล่าสุด", last_chat.strftime("%H:%M:%S"))

def generate_csv_template(table_name, db_manager):
    """สร้าง CSV template สำหรับ table ที่เลือก"""
    try:
        columns = db_manager.get_table_columns(table_name)
        column_names = [col['name'] for col in columns if col['name'].lower() != 'id']
        
        sample_data = {}
        for col in columns:
            if col['name'].lower() == 'id':
                continue
            col_name = col['name']
            col_type = str(col['type']).lower()
            
            if 'varchar' in col_type or 'text' in col_type:
                sample_data[col_name] = f"ตัวอย่าง{col_name}"
            elif 'int' in col_type:
                sample_data[col_name] = 123
            elif 'float' in col_type or 'decimal' in col_type:
                sample_data[col_name] = 123.45
            elif 'date' in col_type or 'timestamp' in col_type:
                sample_data[col_name] = "2024-01-01"
            else:
                sample_data[col_name] = f"ตัวอย่าง{col_name}"
        
        template_df = pd.DataFrame([sample_data])
        return template_df, column_names
    
    except Exception as e:
        st.error(f"ไม่สามารถสร้าง template ได้: {str(e)}")
        return None, None

def check_api_status():
    """ตรวจสอบสถานะ API และ Server"""
    status = {
        'database': {'status': False, 'message': '', 'color': 'red'},
        'embedding_api': {'status': False, 'message': '', 'color': 'red'},
        'chat_api': {'status': False, 'message': '', 'color': 'red'}
    }
    
    try:
        if st.session_state.db_manager and st.session_state.db_manager.engine:
            with st.session_state.db_manager.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            status['database']['status'] = True
            status['database']['message'] = "เชื่อมต่อสำเร็จ"
            status['database']['color'] = 'green'
        else:
            status['database']['message'] = "ไม่ได้เชื่อมต่อ"
    except Exception as e:
        status['database']['message'] = f"ข้อผิดพลาด: {str(e)[:30]}..."
    
    try:
        test_payload = {"model": EMBEDDING_MODEL, "prompt": "test"}
        response = requests.post(EMBEDDING_API_URL, json=test_payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if "embedding" in result:
                status['embedding_api']['status'] = True
                status['embedding_api']['message'] = "API พร้อมใช้งาน"
                status['embedding_api']['color'] = 'green'
            else:
                status['embedding_api']['message'] = "API ตอบสนองผิดปกติ"
        else:
            status['embedding_api']['message'] = f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        status['embedding_api']['message'] = "API Timeout"
    except requests.exceptions.ConnectionError:
        status['embedding_api']['message'] = "ไม่สามารถเชื่อมต่อ"
    except Exception as e:
        status['embedding_api']['message'] = f"ข้อผิดพลาด: {str(e)[:20]}..."
    
    try:
        test_payload = {"model": CHAT_MODEL, "prompt": "test", "stream": False}
        response = requests.post(CHAT_API_URL, json=test_payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if "response" in result:
                status['chat_api']['status'] = True
                status['chat_api']['message'] = "API พร้อมใช้งาน"
                status['chat_api']['color'] = 'green'
            else:
                status['chat_api']['message'] = "API ตอบสนองผิดปกติ"
        else:
            status['chat_api']['message'] = f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        status['chat_api']['message'] = "API Timeout"
    except requests.exceptions.ConnectionError:
        status['chat_api']['message'] = "ไม่สามารถเชื่อมต่อ"
    except Exception as e:
        status['chat_api']['message'] = f"ข้อผิดพลาด: {str(e)[:20]}..."
    
    return status

# ================== มีแท็บ "สร้างจาก CSV" ==================
def show_create_table_interface():
    """แสดง interface สำหรับสร้าง table ใหม่ (กำหนดเอง / จาก CSV)"""
    st.markdown("""
    <div class="info-box">
        <h3>🆕 สร้าง Table ใหม่</h3>
        <p>สร้าง database table สำหรับเก็บข้อมูลของคุณ</p>
    </div>
    """, unsafe_allow_html=True)

    tab_manual, tab_csv = st.tabs(["🧩 กำหนด Columns เอง", "📁 สร้างจาก CSV"])

    # --------- แท็บ 1: เดิม (กำหนดเอง) ---------
    with tab_manual:
        table_name = st.text_input("🏷️ ชื่อ Table:", placeholder="เช่น users, products, etc.", key="manual_table_name")

        if table_name:
            st.markdown("### 📋 กำหนด Columns")

            if f"columns_config_{table_name}" not in st.session_state:
                st.session_state[f"columns_config_{table_name}"] = []

            with st.form(f"add_column_{table_name}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    col_name = st.text_input("Column Name")
                with col2:
                    col_type = st.selectbox("Data Type",
                                            ["String", "Integer", "Float", "Text", "DateTime"])
                with col3:
                    col_nullable = st.checkbox("Nullable", value=True)

                if st.form_submit_button("➕ เพิ่ม Column"):
                    if col_name:
                        st.session_state[f"columns_config_{table_name}"].append({
                            "name": col_name,
                            "type": col_type,
                            "nullable": col_nullable
                        })
                        st.success(f"เพิ่ม column '{col_name}' แล้ว")

            if st.session_state[f"columns_config_{table_name}"]:
                st.markdown("#### 📊 Columns ที่กำหนดแล้ว:")
                for i, col in enumerate(st.session_state[f"columns_config_{table_name}"]):
                    col_display1, col_display2 = st.columns([4, 1])
                    with col_display1:
                        st.text(f"📌 {col['name']} ({col['type']}) - {'NULL' if col['nullable'] else 'NOT NULL'}")
                    with col_display2:
                        if st.button("🗑️", key=f"remove_{table_name}_{i}"):
                            st.session_state[f"columns_config_{table_name}"].pop(i)
                            st.rerun()

                if st.button("🚀 สร้าง Table", type="primary"):
                    if st.session_state.db_manager.create_new_table(
                        table_name,
                        st.session_state[f"columns_config_{table_name}"]
                    ):
                        st.markdown(f"""
                        <div class="success-box">
                            <h3>✅ สร้าง Table สำเร็จ!</h3>
                            <p>Table '{table_name}' ถูกสร้างเรียบร้อยแล้ว</p>
                        </div>
                        """, unsafe_allow_html=True)
                        del st.session_state[f"columns_config_{table_name}"]

    # --------- แท็บ 2: สร้างจาก CSV ---------
    with tab_csv:
        st.info("อัปโหลดไฟล์ CSV → ตั้งชื่อ Table → ตรวจสอบชนิดข้อมูล → สร้างตาราง (เลือก import ข้อมูลได้)")

        uploaded = st.file_uploader("📤 เลือกไฟล์ CSV", type=['csv'], key="csv_uploader_create")
        if uploaded is not None:
            try:
                df_csv = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"อ่าน CSV ไม่ได้: {e}")
                return

            st.markdown("### 👁️ Preview")
            st.dataframe(df_csv.head(20), use_container_width=True)

            # ตั้งชื่อ table
            raw_table_name = st.text_input("🏷️ ตั้งชื่อ Table ใหม่:", value=uploaded.name.replace(".csv", ""), key="csv_table_name")
            add_pk = st.checkbox("เพิ่มคอลัมน์ id (AUTO_INCREMENT Primary Key)", value=True)
            do_import = st.checkbox("Import ข้อมูลจาก CSV เข้าตารางทันที", value=True)

            # เดา type เริ่มต้น + UI override
            st.markdown("### 🧠 เดาชนิดข้อมูล (แก้ได้ก่อนสร้าง)")
            type_choices = {
                "String(255)": "String",
                "Text": "Text",
                "Integer": "Integer",
                "Float": "Float",
                "DateTime": "DateTime"
            }

            sess_key = f"csv_types_{raw_table_name}"
            if sess_key not in st.session_state:
                st.session_state[sess_key] = {}
                st.session_state[sess_key+"_nullable"] = {}

                for c in df_csv.columns:
                    sa_t = _infer_sqlalchemy_type_from_series(df_csv[c])
                    # แปลงเป็น label
                    label = "String(255)"
                    tname = str(sa_t)
                    if hasattr(sa_t, "__name__"):
                        tname = sa_t.__name__
                    if tname.lower().startswith("string(") or tname.lower().startswith("string"):
                        label = "String(255)"
                    elif "text" in tname.lower():
                        label = "Text"
                    elif "integer" in tname.lower() or tname.lower() == "integer":
                        label = "Integer"
                    elif "float" in tname.lower() or tname.lower() == "float":
                        label = "Float"
                    elif "datetime" in tname.lower() or tname.lower() == "datetime":
                        label = "DateTime"
                    st.session_state[sess_key][c] = label
                    st.session_state[sess_key+"_nullable"][c] = True

            overrides = {}
            nullables = {}
            for c in df_csv.columns:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text_input("ชื่อคอลัมน์ (จากไฟล์)", value=str(c), key=f"name_{sess_key}_{c}", disabled=True)
                with col2:
                    st.session_state[sess_key][c] = st.selectbox(
                        "ชนิดข้อมูล",
                        options=list(type_choices.keys()),
                        index=list(type_choices.keys()).index(st.session_state[sess_key][c]),
                        key=f"type_{sess_key}_{c}"
                    )
                with col3:
                    st.session_state[sess_key+"_nullable"][c] = st.checkbox(
                        "Nullable",
                        value=st.session_state[sess_key+"_nullable"][c],
                        key=f"null_{sess_key}_{c}"
                    )

                label = st.session_state[sess_key][c]
                if label == "String(255)":
                    sa_type = String(255)
                elif label == "Text":
                    sa_type = Text
                elif label == "Integer":
                    sa_type = Integer
                elif label == "Float":
                    sa_type = Float
                elif label == "DateTime":
                    sa_type = DateTime
                else:
                    sa_type = String(255)

                overrides[c] = sa_type
                nullables[c] = st.session_state[sess_key+"_nullable"][c]

            st.markdown("---")
            if st.button("🚀 สร้างตารางจาก CSV", type="primary"):
                if not raw_table_name.strip():
                    st.error("กรุณาตั้งชื่อ Table")
                else:
                    ok, safe_table, name_map = st.session_state.db_manager.create_table_from_dataframe(
                        raw_table_name, df_csv, add_id_pk=add_pk,
                        dtype_overrides=overrides, nullables=nullables
                    )
                    if ok:
                        st.success(f"✅ สร้างตาราง `{safe_table}` สำเร็จ!")
                        if do_import:
                            ok2, nrows = st.session_state.db_manager.bulk_insert_dataframe(
                                safe_table, df_csv, add_id_pk=add_pk, name_map=name_map
                            )
                            if ok2:
                                st.success(f"📥 นำเข้าข้อมูล {nrows:,} แถว ลง `{safe_table}` เรียบร้อย")
                            else:
                                st.warning("ตารางถูกสร้างแล้ว แต่นำเข้าข้อมูลไม่สำเร็จ")
                        else:
                            st.info("สร้างเฉพาะโครงสร้างตาราง (ยังไม่นำเข้าข้อมูล)")

def show_select_table_interface():
    """แสดง interface สำหรับเลือก table ที่มีอยู่"""
    st.markdown("""
    <div class="info-box">
        <h3>📋 เลือก Table ที่มีอยู่</h3>
        <p>ดูข้อมูลและจัดการ tables ที่มีอยู่ในระบบ</p>
    </div>
    """, unsafe_allow_html=True)
    
    tables = st.session_state.db_manager.get_existing_tables()
    
    if tables:
        selected_table = st.selectbox("🎯 เลือก Table:", options=tables)
        
        if selected_table:
            columns = st.session_state.db_manager.get_table_columns(selected_table)
            data, column_names = st.session_state.db_manager.get_table_data_sample(selected_table)
            
            st.markdown(f"### 🏗️ Schema ของ {selected_table}")
            schema_data = []
            for col in columns:
                schema_data.append({
                    "Column": col['name'],
                    "Type": str(col['type']),
                    "Nullable": "YES" if col['nullable'] else "NO"
                })
            
            st.dataframe(pd.DataFrame(schema_data), use_container_width=True)
            
            if data:
                st.markdown(f"### 📊 ข้อมูลตัวอย่าง ({len(data)} แถว)")
                sample_df = pd.DataFrame(data, columns=column_names)
                st.dataframe(sample_df, use_container_width=True)
            else:
                st.info("Table นี้ยังไม่มีข้อมูล")
    else:
        st.markdown("""
        <div class="error-box">
            <h3>❌ ไม่พบ Tables</h3>
            <p>ยังไม่มี tables ในระบบ กรุณาสร้าง table ใหม่ก่อน</p>
        </div>
        """, unsafe_allow_html=True)

def show_upload_csv_interface():
    """แสดง interface สำหรับ upload CSV พร้อม template"""
    st.markdown("""
    <div class="info-box">
        <h3>📁 Upload CSV File</h3>
        <p>อัพโหลดไฟล์ CSV เพื่อเพิ่มข้อมูลเข้า table</p>
    </div>
    """, unsafe_allow_html=True)
    
    tables = st.session_state.db_manager.get_existing_tables()
    
    if tables:
        target_table = st.selectbox("🎯 เลือก Target Table:", options=tables)
        
        if target_table:
            st.markdown("### 📋 ดาวน์โหลด CSV Template")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info("💡 ดาวน์โหลด template CSV เพื่อให้แน่ใจว่าข้อมูลตรงตามโครงสร้าง table")
            
            with col2:
                if st.button("📥 ดาวน์โหลด Template", type="secondary"):
                    template_df, column_names = generate_csv_template(target_table, st.session_state.db_manager)
                    
                    if template_df is not None:
                        csv_data = template_df.to_csv(index=False, encoding='utf-8-sig')
                        
                        st.download_button(
                            label="💾 บันทึกไฟล์ Template",
                            data=csv_data,
                            file_name=f"{target_table}_template.csv",
                            mime="text/csv",
                            key=f"download_{target_table}"
                        )
                        
                        st.success("✅ Template พร้อมดาวน์โหลด!")
                        
                        st.markdown("#### 👁️ ตัวอย่าง Template:")
                        st.dataframe(template_df, use_container_width=True)
            
            st.markdown("---")
        
        uploaded_file = st.file_uploader("📤 เลือกไฟล์ CSV", type=['csv'])
        
        if uploaded_file and target_table:
            try:
                df = pd.read_csv(uploaded_file)
                
                st.markdown(f"### 📊 ข้อมูลใน CSV ({len(df)} แถว)")
                st.dataframe(df.head(10), use_container_width=True)
                
                table_columns = st.session_state.db_manager.get_table_columns(target_table)
                table_column_names = [col['name'] for col in table_columns]
                
                st.markdown("### 🔍 การตรวจสอบ Columns")
                
                csv_columns = list(df.columns)
                matching_columns = set(csv_columns) & set(table_column_names)
                missing_columns = set(table_column_names) - set(csv_columns)
                extra_columns = set(csv_columns) - set(table_column_names)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.success(f"✅ ตรงกัน: {len(matching_columns)}")
                with col2:
                    if missing_columns:
                        st.warning(f"⚠️ ไม่มีใน CSV: {len(missing_columns)}")
                    else:
                        st.info("📋 ครบถ้วน")
                with col3:
                    if extra_columns:
                        st.info(f"📎 เพิ่มเติม: {len(extra_columns)}")
                    else:
                        st.info("🎯 พอดี")
                
                if missing_columns:
                    st.warning(f"Columns ที่ไม่มีใน CSV: {', '.join(missing_columns)}")
                if extra_columns:
                    st.info(f"Columns เพิ่มเติมใน CSV: {', '.join(extra_columns)}")
                
                if st.button("🚀 Import ข้อมูล", type="primary"):
                    with st.spinner("กำลัง import ข้อมูล..."):
                        success_count, error_count, errors = st.session_state.db_manager.insert_data_from_csv(
                            target_table, df
                        )
                    
                    if success_count > 0:
                        st.markdown(f"""
                        <div class="success-box">
                            <h3>✅ Import สำเร็จ!</h3>
                            <p>Import สำเร็จ: {success_count:,} แถว</p>
                            <p>Error: {error_count:,} แถว</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="error-box">
                            <h3>❌ Import ไม่สำเร็จ</h3>
                            <p>กรุณาตรวจสอบข้อมูลและลองใหม่อีกครั้ง</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if errors and len(errors) <= 10:
                        st.error("Errors:")
                        for error in errors:
                            st.text(error)
            
            except Exception as e:
                st.error(f"❌ ไม่สามารถอ่านไฟล์ CSV ได้: {str(e)}")
    else:
        st.markdown("""
        <div class="error-box">
            <h3>❌ ไม่พบ Tables</h3>
            <p>ยังไม่มี tables ในระบบ กรุณาสร้าง table ใหม่ก่อน</p>
        </div>
        """, unsafe_allow_html=True)

def show_embedding_interface():
    """แสดง interface สำหรับ embedding process"""
    st.markdown("""
    <div class="info-box">
        <h3>🤖 Run Embedding Process</h3>
        <p>สร้าง vector embeddings จากข้อมูลข้อความ</p>
    </div>
    """, unsafe_allow_html=True)
    
    tables = st.session_state.db_manager.get_existing_tables()
    
    if tables:
        selected_table = st.selectbox("🎯 เลือก Table:", options=tables)
        
        if selected_table:
            columns = st.session_state.db_manager.get_table_columns(selected_table)
            column_names = [col['name'] for col in columns]
            
            text_columns = []
            for col in columns:
                col_type = str(col['type']).lower()
                if any(t in col_type for t in ['varchar', 'text', 'char', 'string']):
                    text_columns.append(col['name'])
            
            if text_columns:
                st.markdown("### 📝 เลือกวิธีการสร้าง Embedding")
                
                embedding_mode = st.radio(
                    "เลือกโหมด:",
                    ["🔗 รวม Text จากทุก Columns", "📋 เลือก Columns เฉพาะ", "🎯 เลือก Column เดียว"],
                    help="เลือกวิธีการประมวลผลข้อความสำหรับ embedding"
                )
                
                selected_columns = []
                
                if embedding_mode == "🔗 รวม Text จากทุก Columns":
                    selected_columns = text_columns
                    st.success(f"✅ จะใช้ทุก text columns: {', '.join(text_columns)}")
                    
                elif embedding_mode == "📋 เลือก Columns เฉพาะ":
                    selected_columns = st.multiselect(
                        "เลือก Columns ที่ต้องการ:",
                        options=text_columns,
                        default=text_columns,
                        help="เลือกหลาย columns เพื่อรวมข้อความ"
                    )
                    
                elif embedding_mode == "🎯 เลือก Column เดียว":
                    single_column = st.selectbox("เลือก Column:", options=text_columns)
                    selected_columns = [single_column] if single_column else []
                
                if selected_columns:
                    st.markdown("### 🔍 ตัวอย่างการรวม Text")
                    
                    separator = st.text_input("ตัวคั่นระหว่าง columns:", value=" | ",
                                            help="ข้อความที่ใช้คั่นระหว่าง columns")
                    
                    data, column_names = st.session_state.db_manager.get_table_data_sample(selected_table)
                    
                    if data:
                        st.markdown(f"### 📊 ข้อมูลตัวอย่างจาก {selected_table}")
                        sample_df = pd.DataFrame(data, columns=column_names)
                        
                        sample_df['🔗 Combined_Text_Preview'] = sample_df.apply(
                            lambda row: separator.join([
                                str(row[col]) if pd.notna(row[col]) and str(row[col]).strip() else ""
                                for col in selected_columns
                            ]).strip(), axis=1
                        )
                        
                        display_columns = ['id'] if 'id' in sample_df.columns else []
                        display_columns.extend(selected_columns[:3])
                        display_columns.append('🔗 Combined_Text_Preview')
                        
                        st.dataframe(sample_df[display_columns], use_container_width=True)
                        
                        try:
                            with st.session_state.db_manager.engine.connect() as conn:
                                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {selected_table}"))
                                total_count = count_result.scalar()
                                
                                embedding_table = f"{selected_table}_vectors"
                                embed_count = 0
                                try:
                                    embed_result = conn.execute(text(f"SELECT COUNT(*) FROM {embedding_table}"))
                                    embed_count = embed_result.scalar()
                                except:
                                    embed_count = 0
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("📊 ข้อมูลทั้งหมด", f"{total_count:,}")
                                with col2:
                                    st.metric("✅ Embedded แล้ว", f"{embed_count:,}")
                                with col3:
                                    remaining = total_count - embed_count
                                    st.metric("⏳ คงเหลือ", f"{remaining:,}")
                        
                        except Exception as e:
                            st.error(f"ไม่สามารถดึงข้อมูลสถิติได้: {str(e)}")
                        
                        st.markdown("### ⚙️ การตั้งค่า Embedding")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            batch_size = st.number_input("Batch Size", min_value=1, max_value=1000, value=100)
                        with col2:
                            max_records = st.number_input("จำนวดสูงสุดที่จะประมวลผล", 
                                                        min_value=1, max_value=10000, value=1000)
                        
                        st.markdown("### 🔧 ตัวเลือกขั้นสูง")
                        col1, col2 = st.columns(2)
                        with col1:
                            skip_empty = st.checkbox("ข้าม record ที่ว่างเปล่า", value=True,
                                                    help="ข้าม records ที่ไม่มีข้อความใน columns ที่เลือก")
                        with col2:
                            max_text_length = st.number_input("ความยาวข้อความสูงสุด (ตัวอักษร)", 
                                                            min_value=100, max_value=8000, value=2000,
                                                            help="จำกัดความยาวข้อความเพื่อป้องกัน API error")
                        
                        st.markdown("### 🔗 API Configuration")
                        st.text(f"API URL: {EMBEDDING_API_URL}")
                        st.text(f"Model: {EMBEDDING_MODEL}")
                        st.text(f"Source Columns: {', '.join(selected_columns)}")
                        st.text(f"Separator: '{separator}'")
                        
                        if st.button("🚀 เริ่มสร้าง Embeddings", type="primary"):
                            run_embedding_process(
                                selected_table, batch_size, max_records, 
                                selected_columns, separator, skip_empty, max_text_length
                            )
                            
                    else:
                        st.info("Table นี้ยังไม่มีข้อมูล")
                        
                else:
                    st.warning("กรุณาเลือก columns สำหรับสร้าง embedding")
                    
            else:
                st.markdown("""
                <div class="error-box">
                    <h3>❌ ไม่พบ Text Column ที่เหมาะสม</h3>
                    <p>Table นี้ไม่มี column ประเภท text/varchar ที่สามารถใช้สร้าง embeddings ได้</p>
                    <p>Columns ที่มีอยู่: {}</p>
                </div>
                """.format(', '.join(column_names)), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="error-box">
            <h3>❌ ไม่พบ Tables</h3>
            <p>ยังไม่มี tables ในระบบ กรุณาสร้าง table ใหม่ก่อน</p>
        </div>
        """, unsafe_allow_html=True)


def run_embedding_process(table_name, batch_size, max_records, source_columns, separator, skip_empty, max_text_length):
    """รันกระบวนการสร้าง embeddings จากหลาย columns"""
    try:
        embedding_table = f"{table_name}_vectors"
        
        with st.session_state.db_manager.engine.connect() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {embedding_table} (
                    id INT PRIMARY KEY,
                    combined_text TEXT,
                    source_columns JSON,
                    embedding LONGBLOB,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_created_at (created_at)
                )
            """))
            conn.commit()
        
        st.success(f"✅ สร้าง table {embedding_table} เรียบร้อยแล้ว")
        
        with st.session_state.db_manager.engine.connect() as conn:
            try:
                embedded_result = conn.execute(text(f"SELECT id FROM {embedding_table}"))
                embedded_ids = set(row[0] for row in embedded_result.fetchall())
            except:
                embedded_ids = set()
            
            columns_sql = ', '.join(source_columns)
            
            if embedded_ids:
                ids_placeholder = ', '.join(map(str, embedded_ids))
                query = f"""
                SELECT id, {columns_sql} FROM {table_name} 
                WHERE id NOT IN ({ids_placeholder}) 
                LIMIT {max_records}
                """
            else:
                query = f"""
                SELECT id, {columns_sql} FROM {table_name} 
                LIMIT {max_records}
                """
            
            result = conn.execute(text(query))
            data = result.fetchall()
        
        if not data:
            st.info("✅ ข้อมูลทั้งหมด embedded เรียบร้อยแล้ว")
            return
        
        st.info(f"🔄 กำลังประมวลผล {len(data):,} records จาก columns: {', '.join(source_columns)}")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i in range(0, len(data), batch_size):
            batch_data = data[i:i + batch_size]
            
            batch_embeddings = []
            for record in batch_data:
                try:
                    record_id = record[0]
                    text_parts = []
                    
                    for j, col_name in enumerate(source_columns):
                        col_value = record[j + 1]
                        if col_value is not None and str(col_value).strip():
                            text_parts.append(str(col_value).strip())
                    
                    combined_text = separator.join(text_parts)
                    
                    if skip_empty and not combined_text.strip():
                        skipped_count += 1
                        continue
                    
                    if len(combined_text) > max_text_length:
                        combined_text = combined_text[:max_text_length] + "..."
                    
                    if not combined_text.strip():
                        skipped_count += 1
                        continue
                    
                    response = requests.post(
                        EMBEDDING_API_URL,
                        json={
                            "model": EMBEDDING_MODEL,
                            "prompt": combined_text
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "embedding" in result:
                            batch_embeddings.append({
                                "id": record_id,
                                "combined_text": combined_text,
                                "embedding": result["embedding"],
                                "source_columns": source_columns
                            })
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                        
                except Exception:
                    error_count += 1
            
            if batch_embeddings:
                with st.session_state.db_manager.engine.begin() as conn:
                    for item in batch_embeddings:
                        try:
                            vector_array = np.array(item["embedding"], dtype=np.float32)
                            vector_bytes = vector_array.tobytes()
                            
                            conn.execute(
                                text(f"""
                                    INSERT INTO {embedding_table} (id, combined_text, source_columns, embedding, metadata)
                                    VALUES (:id, :combined_text, :source_columns, :embedding, :metadata)
                                    ON DUPLICATE KEY UPDATE
                                      combined_text = VALUES(combined_text),
                                      source_columns = VALUES(source_columns),
                                      embedding = VALUES(embedding),
                                      metadata = VALUES(metadata)
                                """),
                                {
                                    "id": item["id"],
                                    "combined_text": item["combined_text"][:1000],
                                    "source_columns": json.dumps(item["source_columns"]),
                                    "embedding": vector_bytes,
                                    "metadata": json.dumps({
                                        "original_id": item["id"],
                                        "source_columns": item["source_columns"],
                                        "separator": separator,
                                        "text_length": len(item["combined_text"]),
                                        "embedding_mode": "multi_column"
                                    })
                                }
                            )
                        except Exception as e:
                            st.error(f"Error saving embedding: {str(e)}")
            
            progress = min((i + batch_size) / len(data), 1.0)
            progress_bar.progress(progress)
            status_text.text(f"ประมวลผล: {min(i + batch_size, len(data))}/{len(data)} (✅ {success_count}, ❌ {error_count}, ⏭️ {skipped_count})")
        
        progress_bar.empty()
        status_text.empty()
        
        st.markdown(f"""
        <div class="success-box">
            <h3>🎉 Embedding Process เสร็จสิ้น!</h3>
            <p>✅ สำเร็จ: {success_count:,} records</p>
            <p>❌ ผิดพลาด: {error_count:,} records</p>
            <p>⏭️ ข้าม: {skipped_count:,} records</p>
            <p>📊 บันทึกใน table: {embedding_table}</p>
            <p>📝 Source columns: {', '.join(source_columns)}</p>
            <p>🔗 Separator: '{separator}'</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการสร้าง embeddings: {str(e)}")

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 NTOneEmbedding System</h1>
        <p>ระบบจัดการข้อมูล AI/ML ครบวงจร - จาก Table สู่ Vector Embeddings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database manager
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if not st.session_state.db_manager.engine:
        st.markdown("""
        <div class="error-box">
            <h3>❌ ไม่สามารถเชื่อมต่อ Database ได้</h3>
            <p>กรุณาตรวจสอบการตั้งค่า TIDB_URL ใน environment variables หรือ Streamlit secrets</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Sidebar menu
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem 1rem; margin-bottom: 1rem; border-bottom: 1px solid rgba(59, 130, 246, 0.2);">
            <h1 style="background: linear-gradient(45deg, #3b82f6, #06b6d4, #0ea5e9); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.5rem; font-weight: 800; margin: 0;">🚀 NTOneEmbedding</h1>
            <p style="color: rgba(255, 255, 255, 0.7); font-size: 0.8rem; margin: 0.5rem 0 0 0;">AI/ML Data Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        menu_option = st.radio(
            "เลือกเมนู:",
            ["🆕 สร้าง Table ใหม่", "📋 เลือก Table ที่มีอยู่", "📁 Upload CSV File", "🤖 Run Embedding Process", "🧠 AI Question & Answer"]
        )
        
        st.markdown("---")
        st.markdown("### 📊 สถานะระบบ")
        
        api_status = check_api_status()
        
        if api_status['database']['status']:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem; background: linear-gradient(135deg, #065f46, #047857); border-radius: 8px; margin-bottom: 0.5rem;">
                <span style="color: #10b981; margin-right: 0.5rem;">●</span>
                <div>
                    <div style="color: #d1fae5; font-weight: 600; font-size: 0.9rem;">Database</div>
                    <div style="color: #a7f3d0; font-size: 0.8rem;">{api_status['database']['message']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem; background: linear-gradient(135deg, #7f1d1d, #991b1b); border-radius: 8px; margin-bottom: 0.5rem;">
                <span style="color: #ef4444; margin-right: 0.5rem;">●</span>
                <div>
                    <div style="color: #fecaca; font-weight: 600; font-size: 0.9rem;">Database</div>
                    <div style="color: #fca5a5; font-size: 0.8rem;">{api_status['database']['message']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if api_status['embedding_api']['status']:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem; background: linear-gradient(135deg, #065f46, #047857); border-radius: 8px; margin-bottom: 0.5rem;">
                <span style="color: #10b981; margin-right: 0.5rem;">●</span>
                <div>
                    <div style="color: #d1fae5; font-weight: 600; font-size: 0.9rem;">Embedding API</div>
                    <div style="color: #a7f3d0; font-size: 0.8rem;">{api_status['embedding_api']['message']}</div>
                    <div style="color: #6ee7b7; font-size: 0.7rem;">Model: {EMBEDDING_MODEL}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem; background: linear-gradient(135deg, #7f1d1d, #991b1b); border-radius: 8px; margin-bottom: 0.5rem;">
                <span style="color: #ef4444; margin-right: 0.5rem;">●</span>
                <div>
                    <div style="color: #fca5a5; font-size: 0.8rem;">{api_status['embedding_api']['message']}</div>
                    <div style="color: #f87171; font-size: 0.7rem;">Server: {EMBEDDING_API_URL}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if api_status['chat_api']['status']:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem; background: linear-gradient(135deg, #065f46, #047857); border-radius: 8px; margin-bottom: 0.5rem;">
                <span style="color: #10b981; margin-right: 0.5rem;">●</span>
                <div>
                    <div style="color: #d1fae5; font-weight: 600; font-size: 0.9rem;">Chat API</div>
                    <div style="color: #a7f3d0; font-size: 0.8rem;">{api_status['chat_api']['message']}</div>
                    <div style="color: #6ee7b7; font-size: 0.7rem;">Model: {CHAT_MODEL}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem; background: linear-gradient(135deg, #7f1d1d, #991b1b); border-radius: 8px; margin-bottom: 0.5rem;">
                <span style="color: #ef4444; margin-right: 0.5rem;">●</span>
                <div>
                    <div style="color: #fca5a5; font-size: 0.8rem;">{api_status['chat_api']['message']}</div>
                    <div style="color: #f87171; font-size: 0.7rem;">Server: {CHAT_API_URL}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📈 ข้อมูลระบบ")
        
        try:
            tables = st.session_state.db_manager.get_existing_tables()
            st.metric("📋 Tables ทั้งหมด", len(tables))
            
            embedding_tables = [t for t in tables if t.endswith('_vectors')]
            st.metric("🤖 Embedding Tables", len(embedding_tables))
            
            chat_count = len(st.session_state.get('chat_history', []))
            st.metric("💬 Chat Messages", chat_count)
        except:
            st.metric("📋 Tables ทั้งหมด", "N/A")
            st.metric("🤖 Embedding Tables", "N/A")
            st.metric("💬 Chat Messages", "N/A")
    
    if menu_option == "🆕 สร้าง Table ใหม่":
        show_create_table_interface()
    elif menu_option == "📋 เลือก Table ที่มีอยู่":
        show_select_table_interface()
    elif menu_option == "📁 Upload CSV File":
        show_upload_csv_interface()
    elif menu_option == "🤖 Run Embedding Process":
        show_embedding_interface()
    elif menu_option == "🧠 AI Question & Answer":
        show_ai_qa_interface()

if __name__ == "__main__":
    main()
