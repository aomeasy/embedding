import streamlit as st
import pandas as pd
import numpy as np
import json
import base64
import requests
from datetime import datetime, date
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.exc import SQLAlchemyError
import pymysql
import os
import time

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
except:
    # Fallback สำหรับการรันใน local
    TIDB_URL = os.environ.get("TIDB_URL")
    EMBEDDING_API_URL = os.environ.get("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text:latest")

# Modern CSS with Enhanced Sidebar and Dark/Neon Theme
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

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.connect_to_database()
    
    def connect_to_database(self):
        """เชื่อมต่อกับ TiDB Database"""
        try:
            if not TIDB_URL:
                st.error("❌ TIDB_URL ไม่ได้กำหนดใน environment variables")
                return False
            
            self.engine = create_engine(TIDB_URL, pool_pre_ping=True, pool_recycle=300)
            
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

    def create_new_table(self, table_name, columns_config):
        """สร้าง table ใหม่ตาม configuration ที่กำหนด"""
        try:
            metadata = MetaData()
            
            # สร้าง columns ตาม config
            table_columns = []
            
            # เพิ่ม ID column เป็น primary key ก่อนเสมอ
            table_columns.append(Column('id', Integer, primary_key=True, autoincrement=True))
            
            for col_config in columns_config:
                col_name = col_config['name']
                col_type = col_config['type']
                col_nullable = col_config['nullable']
                
                # ป้องกันการสร้าง id column ซ้ำ
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
                
                table_columns.append(column)
            
            table = Table(table_name, metadata, *table_columns)
            metadata.create_all(self.engine)
            
            return True
        except Exception as e:
            st.error(f"❌ ไม่สามารถสร้าง table {table_name} ได้: {str(e)}")
            return False

    def insert_data_from_csv(self, table_name, df):
        """เพิ่มข้อมูลจาก DataFrame เข้า table"""
        try:
            success_count = 0
            error_count = 0
            errors = []
            
            # สร้าง progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_rows = len(df)
            
            with self.engine.begin() as conn:
                for index, row in df.iterrows():
                    try:
                        # แปลงข้อมูลให้เป็น dict และกรองเฉพาะ columns ที่ไม่ใช่ id
                        row_dict = {k: v for k, v in row.to_dict().items() if k.lower() != 'id'}
                        
                        # จัดการข้อมูล NaN และ None
                        for key, value in row_dict.items():
                            if pd.isna(value):
                                row_dict[key] = None
                        
                        # สร้าง SQL insert statement (ไม่รวม id เพราะเป็น AUTO_INCREMENT)
                        columns = ', '.join(row_dict.keys())
                        placeholders = ', '.join([f':{key}' for key in row_dict.keys()])
                        
                        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        conn.execute(text(sql), row_dict)
                        
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"แถวที่ {index + 1}: {str(e)}")
                    
                    # อัพเดท progress
                    progress = (index + 1) / total_rows
                    progress_bar.progress(progress)
                    status_text.text(f"กำลังประมวลผล: {index + 1}/{total_rows}")
            
            # แสดงผลสรุป
            progress_bar.empty()
            status_text.empty()
            
            return success_count, error_count, errors
            
        except Exception as e:
            st.error(f"❌ ไม่สามารถเพิ่มข้อมูลได้: {str(e)}")
            return 0, len(df), [str(e)]

def generate_csv_template(table_name, db_manager):
    """สร้าง CSV template สำหรับ table ที่เลือก"""
    try:
        columns = db_manager.get_table_columns(table_name)
        column_names = [col['name'] for col in columns if col['name'].lower() != 'id']
        
        # สร้าง sample data
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
        
        # สร้าง DataFrame template
        template_df = pd.DataFrame([sample_data])
        return template_df, column_names
    
    except Exception as e:
        st.error(f"ไม่สามารถสร้าง template ได้: {str(e)}")
        return None, None

def check_api_status():
    """ตรวจสอบสถานะ API และ Server"""
    status = {
        'database': {'status': False, 'message': '', 'color': 'red'},
        'embedding_api': {'status': False, 'message': '', 'color': 'red'}
    }
    
    # ตรวจสอบ Database
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
    
    # ตรวจสอบ Embedding API
    try:
        test_payload = {
            "model": EMBEDDING_MODEL,
            "prompt": "test"
        }
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
    
    return status

def show_create_table_interface():
    """แสดง interface สำหรับสร้าง table ใหม่"""
    st.markdown("""
    <div class="info-box">
        <h3>🆕 สร้าง Table ใหม่</h3>
        <p>สร้าง database table สำหรับเก็บข้อมูลของคุณ</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input สำหรับชื่อ table
    table_name = st.text_input("🏷️ ชื่อ Table:", placeholder="เช่น users, products, etc.")
    
    if table_name:
        st.markdown("### 📋 กำหนด Columns")
        
        # เก็บ columns configuration ใน session state
        if f"columns_config_{table_name}" not in st.session_state:
            st.session_state[f"columns_config_{table_name}"] = []
        
        # Form สำหรับเพิ่ม column
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
        
        # แสดง columns ที่กำหนดแล้ว
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
            
            # ปุ่มสร้าง table
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
                    
                    # รีเซ็ต configuration
                    del st.session_state[f"columns_config_{table_name}"]

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
            # แสดงข้อมูล table
            columns = st.session_state.db_manager.get_table_columns(selected_table)
            data, column_names = st.session_state.db_manager.get_table_data_sample(selected_table)
            
            # แสดง schema
            st.markdown(f"### 🏗️ Schema ของ {selected_table}")
            schema_data = []
            for col in columns:
                schema_data.append({
                    "Column": col['name'],
                    "Type": str(col['type']),
                    "Nullable": "YES" if col['nullable'] else "NO"
                })
            
            st.dataframe(pd.DataFrame(schema_data), use_container_width=True)
            
            # แสดงข้อมูลตัวอย่าง
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
    
    # เลือก table ที่จะ insert ข้อมูล
    tables = st.session_state.db_manager.get_existing_tables()
    
    if tables:
        target_table = st.selectbox("🎯 เลือก Target Table:", options=tables)
        
        if target_table:
            # แสดงส่วน Template Download
            st.markdown("### 📋 ดาวน์โหลด CSV Template")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info("💡 ดาวน์โหลด template CSV เพื่อให้แน่ใจว่าข้อมูลตรงตามโครงสร้าง table")
            
            with col2:
                if st.button("📥 ดาวน์โหลด Template", type="secondary"):
                    template_df, column_names = generate_csv_template(target_table, st.session_state.db_manager)
                    
                    if template_df is not None:
                        # แปลง DataFrame เป็น CSV
                        csv_data = template_df.to_csv(index=False, encoding='utf-8-sig')
                        
                        st.download_button(
                            label="💾 บันทึกไฟล์ Template",
                            data=csv_data,
                            file_name=f"{target_table}_template.csv",
                            mime="text/csv",
                            key=f"download_{target_table}"
                        )
                        
                        st.success("✅ Template พร้อมดาวน์โหลด!")
                        
                        # แสดง preview template
                        st.markdown("#### 👁️ ตัวอย่าง Template:")
                        st.dataframe(template_df, use_container_width=True)
            
            st.markdown("---")
        
        # Upload file section
        uploaded_file = st.file_uploader("📤 เลือกไฟล์ CSV", type=['csv'])
        
        if uploaded_file and target_table:
            try:
                # อ่านไฟล์ CSV
                df = pd.read_csv(uploaded_file)
                
                st.markdown(f"### 📊 ข้อมูลใน CSV ({len(df)} แถว)")
                st.dataframe(df.head(10), use_container_width=True)
                
                # ตรวจสอบ columns
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
                
                # แสดงรายละเอียด columns
                if missing_columns:
                    st.warning(f"Columns ที่ไม่มีใน CSV: {', '.join(missing_columns)}")
                if extra_columns:
                    st.info(f"Columns เพิ่มเติมใน CSV: {', '.join(extra_columns)}")
                
                # ปุ่ม import
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
                    
                    # แสดง errors ถ้ามี
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
    
    # เลือก table สำหรับ embedding
    tables = st.session_state.db_manager.get_existing_tables()
    
    if tables:
        selected_table = st.selectbox("🎯 เลือก Table:", options=tables)
        
        if selected_table:
            # ดึงข้อมูล columns ของ table ที่เลือก
            columns = st.session_state.db_manager.get_table_columns(selected_table)
            column_names = [col['name'] for col in columns]
            
            # ให้ผู้ใช้เลือก column ที่จะใช้สำหรับสร้าง embedding
            text_columns = []
            for col in columns:
                col_type = str(col['type']).lower()
                # กรองเฉพาะ columns ที่เป็น text/string
                if any(t in col_type for t in ['varchar', 'text', 'char', 'string']):
                    text_columns.append(col['name'])
            
            if text_columns:
                source_column = st.selectbox("📝 เลือก Column สำหรับสร้าง Embedding:", 
                                           options=text_columns, 
                                           help="เลือก column ที่มีข้อความสำหรับสร้าง vector embeddings")
                
                # แสดงข้อมูล table
                data, column_names = st.session_state.db_manager.get_table_data_sample(selected_table)
                
                if data:
                    st.markdown(f"### 📊 ข้อมูลตัวอย่างจาก {selected_table}")
                    sample_df = pd.DataFrame(data, columns=column_names)
                    
                    # แสดงเฉพาะ columns ที่สำคัญ (id, source column, และ columns อื่นๆ ที่เกี่ยวข้อง)
                    display_columns = ['id'] if 'id' in sample_df.columns else []
                    if source_column in sample_df.columns:
                        display_columns.append(source_column)
                    # เพิ่ม columns อื่นๆ ไม่เกิน 5 columns ทั้งหมด
                    other_cols = [col for col in sample_df.columns if col not in display_columns][:3]
                    display_columns.extend(other_cols)
                    
                    st.dataframe(sample_df[display_columns], use_container_width=True)
                    
                    # แสดงจำนวนข้อมูลทั้งหมด
                    try:
                        with st.session_state.db_manager.engine.connect() as conn:
                            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {selected_table}"))
                            total_count = count_result.scalar()
                            
                            # ตรวจสอบ embedding table ที่มีอยู่
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
                    
                    # แสดงการตั้งค่า
                    st.markdown("### ⚙️ การตั้งค่า Embedding")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        batch_size = st.number_input("Batch Size", min_value=1, max_value=1000, value=100)
                    with col2:
                        max_records = st.number_input("จำนวนสูงสุดที่จะประมวลผล", 
                                                    min_value=1, max_value=10000, value=1000)
                    
                    # แสดงข้อมูล API
                    st.markdown("### 🔗 API Configuration")
                    st.text(f"API URL: {EMBEDDING_API_URL}")
                    st.text(f"Model: {EMBEDDING_MODEL}")
                    st.text(f"Source Column: {source_column}")
                    
                    # ปุ่มเริ่มประมวลผล
                    if st.button("🚀 เริ่มสร้าง Embeddings", type="primary"):
                        run_embedding_process(selected_table, batch_size, max_records, source_column)
                        
                else:
                    st.info("Table นี้ยังไม่มีข้อมูล")
                    
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


def run_embedding_process(table_name, batch_size, max_records, source_column):
    """รันกระบวนการสร้าง embeddings"""
    try:
        # สร้าง embedding table
        embedding_table = f"{table_name}_vectors"
        
        with st.session_state.db_manager.engine.connect() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {embedding_table} (
                    id INT PRIMARY KEY,
                    source_text TEXT,
                    embedding LONGBLOB,
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_created_at (created_at)
                )
            """))
            conn.commit()
        
        st.success(f"✅ สร้าง table {embedding_table} เรียบร้อยแล้ว")
        
        # ดึงข้อมูลที่ยังไม่ได้ embed
        with st.session_state.db_manager.engine.connect() as conn:
            # ตรวจสอบ IDs ที่ embed แล้ว
            try:
                embedded_result = conn.execute(text(f"SELECT id FROM {embedding_table}"))
                embedded_ids = set(row[0] for row in embedded_result.fetchall())
            except:
                embedded_ids = set()
            
            # ดึงข้อมูลที่ยังไม่ได้ embed โดยใช้ source_column ที่เลือก
            if embedded_ids:
                ids_placeholder = ', '.join(map(str, embedded_ids))
                query = f"""
                SELECT id, {source_column} FROM {table_name} 
                WHERE id NOT IN ({ids_placeholder}) 
                AND {source_column} IS NOT NULL 
                AND TRIM({source_column}) != ''
                LIMIT {max_records}
                """
            else:
                query = f"""
                SELECT id, {source_column} FROM {table_name} 
                WHERE {source_column} IS NOT NULL 
                AND TRIM({source_column}) != ''
                LIMIT {max_records}
                """
            
            result = conn.execute(text(query))
            data = result.fetchall()
        
        if not data:
            st.info("✅ ข้อมูลทั้งหมด embedded เรียบร้อยแล้ว หรือไม่มีข้อมูลที่ไม่เป็นค่าว่าง")
            return
        
        st.info(f"🔄 กำลังประมวลผล {len(data):,} records จาก column '{source_column}'...")
        
        # สร้าง progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        error_count = 0
        
        # ประมวลผลเป็น batch
        for i in range(0, len(data), batch_size):
            batch_data = data[i:i + batch_size]
            
            # สร้าง embeddings สำหรับ batch นี้
            batch_embeddings = []
            for record in batch_data:
                try:
                    # เรียก API สร้าง embedding
                    text_content = str(record[1]) if record[1] else ""
                    
                    if not text_content.strip():
                        error_count += 1
                        continue
                    
                    response = requests.post(
                        EMBEDDING_API_URL,
                        json={
                            "model": EMBEDDING_MODEL,
                            "prompt": text_content
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "embedding" in result:
                            batch_embeddings.append({
                                "id": record[0],
                                "source_text": text_content,
                                "embedding": result["embedding"]
                            })
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
            
            # บันทึก batch นี้ลง database
            if batch_embeddings:
                with st.session_state.db_manager.engine.begin() as conn:
                    for item in batch_embeddings:
                        try:
                            vector_array = np.array(item["embedding"], dtype=np.float32)
                            vector_bytes = vector_array.tobytes()
                            
                            conn.execute(
                                text(f"""
                                    INSERT INTO {embedding_table} (id, source_text, embedding, metadata)
                                    VALUES (:id, :source_text, :embedding, :metadata)
                                    ON DUPLICATE KEY UPDATE
                                      source_text = VALUES(source_text),
                                      embedding = VALUES(embedding),
                                      metadata = VALUES(metadata)
                                """),
                                {
                                    "id": item["id"],
                                    "source_text": item["source_text"][:500],  # จำกัดความยาว
                                    "embedding": vector_bytes,
                                    "metadata": json.dumps({
                                        "original_id": item["id"],
                                        "source_column": source_column,
                                        "text_length": len(item["source_text"])
                                    })
                                }
                            )
                        except Exception as e:
                            st.error(f"Error saving embedding: {str(e)}")
            
            # อัพเดท progress
            progress = min((i + batch_size) / len(data), 1.0)
            progress_bar.progress(progress)
            status_text.text(f"ประมวลผล: {min(i + batch_size, len(data))}/{len(data)} (✅ {success_count}, ❌ {error_count})")
        
        # แสดงผลสรุป
        progress_bar.empty()
        status_text.empty()
        
        st.markdown(f"""
        <div class="success-box">
            <h3>🎉 Embedding Process เสร็จสิ้น!</h3>
            <p>✅ สำเร็จ: {success_count:,} records</p>
            <p>❌ ผิดพลาด: {error_count:,} records</p>
            <p>📊 บันทึกใน table: {embedding_table}</p>
            <p>📝 Source column: {source_column}</p>
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
            ["🆕 สร้าง Table ใหม่", "📋 เลือก Table ที่มีอยู่", "📁 Upload CSV File", "🤖 Run Embedding Process"]
        )
        
        # System Status - เพิ่มการแสดงสถานะ API
        st.markdown("---")
        st.markdown("### 📊 สถานะระบบ")
        
        # ตรวจสอบสถานะ API
        api_status = check_api_status()
        
        # แสดงสถานะ Database
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
        
        # แสดงสถานะ Embedding API
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
                    <div style="color: #fecaca; font-weight: 600; font-size: 0.9rem;">Embedding API</div>
                    <div style="color: #fca5a5; font-size: 0.8rem;">{api_status['embedding_api']['message']}</div>
                    <div style="color: #f87171; font-size: 0.7rem;">Server: {EMBEDDING_API_URL}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # แสดงข้อมูลเพิ่มเติม
        st.markdown("---")
        st.markdown("### 📈 ข้อมูลระบบ")
        
        # แสดงจำนวน tables
        try:
            tables = st.session_state.db_manager.get_existing_tables()
            st.metric("📋 Tables ทั้งหมด", len(tables))
            
            # แสดงจำนวน embedding tables
            embedding_tables = [t for t in tables if t.endswith('_vectors')]
            st.metric("🤖 Embedding Tables", len(embedding_tables))
        except:
            st.metric("📋 Tables ทั้งหมด", "N/A")
            st.metric("🤖 Embedding Tables", "N/A")
    
    # Main content
    if menu_option == "🆕 สร้าง Table ใหม่":
        show_create_table_interface()
    elif menu_option == "📋 เลือก Table ที่มีอยู่":
        show_select_table_interface()
    elif menu_option == "📁 Upload CSV File":
        show_upload_csv_interface()
    elif menu_option == "🤖 Run Embedding Process":
        show_embedding_interface()

if __name__ == "__main__":
    main()
