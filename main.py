import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import subprocess
import sys
import base64
import requests
from datetime import datetime, date
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.exc import SQLAlchemyError
import pymysql
from dotenv import load_dotenv
import os

# โหลดค่าจาก environment variables (GitHub Secrets)
# ไม่ต้องใช้ .env file เพราะใช้ GitHub Secrets
# load_dotenv()  # Comment ออกเพราะใช้ GitHub Secrets

# Configuration
st.set_page_config(
    page_title="ระบบจัดการข้อมูล Table",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
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
            tidb_url = os.getenv("TIDB_URL")
            if not tidb_url:
                st.error("❌ TIDB_URL ไม่ได้กำหนดใน environment variables")
                return False
            
            self.engine = create_engine(tidb_url)
            
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
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
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
    
    def create_new_table(self, table_name, columns_config):
        """สร้าง table ใหม่ตาม configuration ที่กำหนด"""
        try:
            metadata = MetaData()
            
            # สร้าง columns ตาม config
            table_columns = []
            for col_config in columns_config:
                col_name = col_config['name']
                col_type = col_config['type']
                col_nullable = col_config['nullable']
                
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
            
            # เพิ่ม ID column เป็น primary key
            if not any(col.name == 'id' for col in table_columns):
                table_columns.insert(0, Column('id', Integer, primary_key=True, autoincrement=True))
            
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
                        # แปลงข้อมูลให้เป็น dict
                        row_dict = row.to_dict()
                        
                        # จัดการข้อมูล NaN และ None
                        for key, value in row_dict.items():
                            if pd.isna(value):
                                row_dict[key] = None
                        
                        # สร้าง SQL insert statement
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

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0;">🗂️ ระบบจัดการข้อมูล Table</h1>
        <p style="color: white; margin: 0;">จัดการ Tables และ Import ข้อมูล CSV</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database manager
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if not st.session_state.db_manager.engine:
        st.markdown("""
        <div class="error-box">
            <h3>❌ ไม่สามารถเชื่อมต่อ Database ได้</h3>
            <p>กรุณาตรวจสอบการตั้งค่า TIDB_URL ใน environment variables</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Sidebar menu
    st.sidebar.title("📋 เมนูหลัก")
    menu_option = st.sidebar.radio(
        "เลือกการดำเนินการ:",
        ["🆕 สร้าง Table ใหม่", "📋 เลือก Table ที่มีอยู่", "📁 Upload CSV File", "🤖 Run Embedding Process"]
    )
    
    if menu_option == "🆕 สร้าง Table ใหม่":
        show_create_table_interface()
    elif menu_option == "📋 เลือก Table ที่มีอยู่":
        show_select_table_interface()
    elif menu_option == "📁 Upload CSV File":
        show_upload_csv_interface()
    elif menu_option == "🤖 Run Embedding Process":
        show_embedding_interface()

def show_create_table_interface():
    """แสดง interface สำหรับสร้าง table ใหม่"""
    st.header("🆕 สร้าง Table ใหม่")
    
    # ชื่อ table
    table_name = st.text_input("ชื่อ Table:", placeholder="ระบุชื่อ table ใหม่")
    
    if not table_name:
        st.info("กรุณาระบุชื่อ table ก่อน")
        return
    
    st.subheader("📝 กำหนด Columns")
    
    # จัดการ columns configuration
    if 'columns_config' not in st.session_state:
        st.session_state.columns_config = []
    
    # เพิ่ม column ใหม่
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        new_col_name = st.text_input("ชื่อ Column:", key="new_col_name")
    with col2:
        new_col_type = st.selectbox("ประเภทข้อมูล:", 
                                   ["String", "Integer", "Float", "Text", "DateTime"], 
                                   key="new_col_type")
    with col3:
        new_col_nullable = st.checkbox("อนุญาต NULL", value=True, key="new_col_nullable")
    with col4:
        if st.button("➕ เพิ่ม"):
            if new_col_name:
                st.session_state.columns_config.append({
                    'name': new_col_name,
                    'type': new_col_type,
                    'nullable': new_col_nullable
                })
                st.experimental_rerun()
    
    # แสดงรายการ columns ที่กำหนดแล้ว
    if st.session_state.columns_config:
        st.subheader("📋 Columns ที่กำหนด:")
        
        for i, col_config in enumerate(st.session_state.columns_config):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.text(col_config['name'])
            with col2:
                st.text(col_config['type'])
            with col3:
                st.text("ได้" if col_config['nullable'] else "ไม่ได้")
            with col4:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.columns_config.pop(i)
                    st.experimental_rerun()
        
        # สร้าง table
        if st.button("✅ สร้าง Table", type="primary"):
            if st.session_state.db_manager.create_new_table(table_name, st.session_state.columns_config):
                st.success(f"✅ สร้าง table '{table_name}' เรียบร้อยแล้ว!")
                st.session_state.columns_config = []  # ล้าง config
            else:
                st.error("❌ ไม่สามารถสร้าง table ได้")

def show_select_table_interface():
    """แสดง interface สำหรับเลือก table ที่มีอยู่"""
    st.header("📋 เลือก Table ที่มีอยู่")
    
    # ดึงรายชื่อ tables
    tables = st.session_state.db_manager.get_existing_tables()
    
    if not tables:
        st.warning("⚠️ ไม่พบ tables ในระบบ")
        return
    
    selected_table = st.selectbox("เลือก Table:", tables)
    
    if selected_table:
        # แสดงข้อมูลของ table ที่เลือก
        columns = st.session_state.db_manager.get_table_columns(selected_table)
        
        st.subheader(f"📊 ข้อมูล Table: {selected_table}")
        
        if columns:
            # แสดง column information
            col_data = []
            for col in columns:
                col_data.append({
                    'ชื่อ Column': col['name'],
                    'ประเภทข้อมูล': str(col['type']),
                    'อนุญาต NULL': 'ได้' if col['nullable'] else 'ไม่ได้'
                })
            
            df_cols = pd.DataFrame(col_data)
            st.dataframe(df_cols, use_container_width=True)
            
            # แสดงข้อมูลในตาราง (ตัวอย่าง 10 แถวแรก)
            try:
                with st.session_state.db_manager.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT * FROM {selected_table} LIMIT 10"))
                    data = result.fetchall()
                    column_names = result.keys()
                    
                if data:
                    df_preview = pd.DataFrame(data, columns=column_names)
                    st.subheader("👀 ตัวอย่างข้อมูล (10 แถวแรก)")
                    st.dataframe(df_preview, use_container_width=True)
                else:
                    st.info("ไม่มีข้อมูลในตารางนี้")
                    
            except Exception as e:
                st.error(f"❌ ไม่สามารถดึงข้อมูลได้: {str(e)}")

def show_upload_csv_interface():
    """แสดง interface สำหรับ upload CSV file"""
    st.header("📁 Upload CSV File")
    
    # เลือก table
    tables = st.session_state.db_manager.get_existing_tables()
    
    if not tables:
        st.warning("⚠️ ไม่พบ tables ในระบบ กรุณาสร้าง table ก่อน")
        return
    
    selected_table = st.selectbox("เลือก Table ปลายทาง:", tables, key="upload_table_select")
    
    if selected_table:
        # ดาวน์โหลด template
        columns = st.session_state.db_manager.get_table_columns(selected_table)
        
        if columns:
            st.subheader("📋 Template CSV")
            
            # สร้าง template CSV
            template_data = {}
            for col in columns:
                if col['name'] != 'id':  # ข้าม id column ที่เป็น auto increment
                    template_data[col['name']] = ['ตัวอย่างข้อมูล']
            
            template_df = pd.DataFrame(template_data)
            
            # แสดง template
            st.dataframe(template_df, use_container_width=True)
            
            # ดาวน์โหลด template
            csv_buffer = io.StringIO()
            template_df.to_csv(csv_buffer, index=False)
            csv_string = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 ดาวน์โหลด Template CSV",
                data=csv_string,
                file_name=f"{selected_table}_template.csv",
                mime="text/csv"
            )
            
            st.divider()
            
            # Upload file
            st.subheader("📤 อัพโหลดไฟล์ CSV")
            
            uploaded_file = st.file_uploader("เลือกไฟล์ CSV:", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    # อ่านไฟล์ CSV
                    df = pd.read_csv(uploaded_file)
                    
                    st.success(f"✅ อ่านไฟล์สำเร็จ: {len(df)} แถว")
                    
                    # แสดงตัวอย่างข้อมูล
                    st.subheader("👀 ตัวอย่างข้อมูลที่จะ Import")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # ตรวจสอบ columns
                    table_columns = [col['name'] for col in columns if col['name'] != 'id']
                    csv_columns = df.columns.tolist()
                    
                    missing_columns = set(table_columns) - set(csv_columns)
                    extra_columns = set(csv_columns) - set(table_columns)
                    
                    if missing_columns:
                        st.error(f"❌ ข้อมูลใน CSV ขาด columns: {list(missing_columns)}")
                    if extra_columns:
                        st.warning(f"⚠️ ข้อมูลใน CSV มี columns เพิ่มเติม: {list(extra_columns)} (จะถูกเพิกเฉย)")
                    
                    # ปุ่ม Import
                    if st.button("🚀 Import ข้อมูล", type="primary"):
                        if not missing_columns:
                            # กรองเฉพาะ columns ที่ตรงกัน
                            df_filtered = df[table_columns]
                            
                            # Import ข้อมูล
                            success_count, error_count, errors = st.session_state.db_manager.insert_data_from_csv(
                                selected_table, df_filtered
                            )
                            
                            # แสดงผลสรุป
                            st.markdown("### 📊 สรุปผลการ Import")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("✅ สำเร็จ", success_count)
                            with col2:
                                st.metric("❌ ผิดพลาด", error_count)
                            with col3:
                                st.metric("📝 รวม", success_count + error_count)
                            
                            if success_count > 0:
                                st.markdown(f"""
                                <div class="success-box">
                                    <h4>✅ Import สำเร็จ!</h4>
                                    <p>เพิ่มข้อมูล {success_count} แถวเข้า table '{selected_table}' แล้ว</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            if errors:
                                st.markdown("""
                                <div class="error-box">
                                    <h4>❌ รายการข้อผิดพลาด:</h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                for error in errors[:10]:  # แสดงแค่ 10 ข้อผิดพลาดแรก
                                    st.error(error)
                                
                                if len(errors) > 10:
                                    st.warning(f"... และอีก {len(errors) - 10} ข้อผิดพลาด")
                        else:
                            st.error("❌ ไม่สามารถ Import ได้เนื่องจาก columns ไม่ครบ")
                    
                except Exception as e:
                    st.error(f"❌ ไม่สามารถอ่านไฟล์ CSV ได้: {str(e)}")

def show_embedding_interface():
    """แสดง interface สำหรับรัน embedding process"""
    st.header("🤖 Run Embedding Process")
    
    st.markdown("""
    <div class="info-box">
        <h4>ℹ️ เกี่ยวกับ Embedding Process</h4>
        <p>กระบวนการนี้จะ:</p>
        <ul>
            <li>อ่านข้อมูลจาก customers table</li>
            <li>เรียก Embedding API เพื่อสร้าง vectors</li>
            <li>บันทึกผลลัพธ์ใน customer_vectors table</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # แสดงการตั้งค่าปัจจุบัน
    st.subheader("🔧 การตั้งค่าปัจจุบัน")
    
    col1, col2 = st.columns(2)
    
    with col1:
        embedding_api_url = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
        st.info(f"**Embedding API URL:**\n{embedding_api_url}")
    
    with col2:
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
        st.info(f"**Embedding Model:**\n{embedding_model}")
    
    # ตรวจสอบ customers table
    st.subheader("📊 ตรวจสอบข้อมูล")
    
    try:
        with st.session_state.db_manager.engine.connect() as conn:
            # ตรวจสอบว่ามี customers table หรือไม่
            result = conn.execute(text("SHOW TABLES LIKE 'customers'"))
            customers_exists = result.fetchone() is not None
            
            if customers_exists:
                # นับจำนวนข้อมูลใน customers
                count_result = conn.execute(text("SELECT COUNT(*) FROM customers"))
                customers_count = count_result.scalar()
                
                st.success(f"✅ พบ customers table: {customers_count} รายการ")
                
                # แสดงตัวอย่างข้อมูล
                if customers_count > 0:
                    sample_result = conn.execute(text("SELECT id, name, email FROM customers LIMIT 5"))
                    sample_data = sample_result.fetchall()
                    
                    st.subheader("👀 ตัวอย่างข้อมูล customers")
                    sample_df = pd.DataFrame(sample_data, columns=['ID', 'Name', 'Email'])
                    st.dataframe(sample_df, use_container_width=True)
            else:
                st.error("❌ ไม่พบ customers table")
                st.info("กรุณาสร้าง customers table ก่อน หรือ import ข้อมูล customers")
                return
            
            # ตรวจสอบ customer_vectors table
            vectors_result = conn.execute(text("SHOW TABLES LIKE 'customer_vectors'"))
            vectors_exists = vectors_result.fetchone() is not None
            
            if vectors_exists:
                vectors_count_result = conn.execute(text("SELECT COUNT(*) FROM customer_vectors"))
                vectors_count = vectors_count_result.scalar()
                st.info(f"📊 customer_vectors table มีข้อมูล: {vectors_count} รายการ")
            else:
                st.warning("⚠️ ยังไม่มี customer_vectors table (จะถูกสร้างอัตโนมัติ)")
    
    except Exception as e:
        st.error(f"❌ ไม่สามารถตรวจสอบข้อมูลได้: {str(e)}")
        return
    
    st.divider()
    
    # ปุ่มรัน embedding
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 เริ่ม Embedding Process", type="primary", use_container_width=True):
            run_embedding_process()

def run_embedding_process():
    """รันกระบวนการ embedding โดยเรียกโค้ดจาก main.py"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 กำลังเริ่มต้น Embedding Process...")
        progress_bar.progress(10)
        
        # ตรวจสอบการตั้งค่า
        tidb_url = os.getenv("TIDB_URL")
        embedding_api_url = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
        
        if not tidb_url:
            st.error("❌ TIDB_URL ไม่ได้กำหนด")
            return
        
        status_text.text("📡 ตรวจสอบการเชื่อมต่อ...")
        progress_bar.progress(20)
        
        # เชื่อมต่อ database
        engine = create_engine(tidb_url)
        
        status_text.text("📥 ดึงข้อมูลจาก customers table...")
        progress_bar.progress(30)
        
        # ดึงข้อมูล customers
        df = pd.read_sql("SELECT id, name, email, age, city, signup_date FROM customers", con=engine)
        
        if df.empty:
            st.warning("⚠️ ไม่มีข้อมูลใน customers table")
            return
        
        st.info(f"📊 พบข้อมูล {len(df)} รายการ")
        
        status_text.text("🤖 กำลังสร้าง embeddings...")
        progress_bar.progress(40)
        
        # เตรียมข้อมูล
        texts = df["name"].tolist()
        ids = df["id"].tolist()
        
        # จัดการ date
        df_copy = df.copy()
        df_copy["signup_date"] = df_copy["signup_date"].apply(
            lambda d: d.isoformat() if isinstance(d, (date, pd.Timestamp)) else str(d)
        )
        metadatas = df_copy.drop(columns=["name"]).to_dict(orient="records")
        
        # สร้าง embeddings
        embeddings = []
        total_texts = len(texts)
        
        for i, text in enumerate(texts):
            try:
                headers = {"Content-Type": "application/json"}
                payload = {
                    "model": embedding_model,
                    "prompt": str(text)
                }
                
                response = requests.post(embedding_api_url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if "embedding" in result and result["embedding"]:
                        embeddings.append(result["embedding"])
                    else:
                        embeddings.append(None)
                else:
                    embeddings.append(None)
                
                # อัพเดท progress
                embed_progress = 40 + (i + 1) / total_texts * 40  # 40-80%
                progress_bar.progress(int(embed_progress))
                status_text.text(f"🤖 สร้าง embedding: {i + 1}/{total_texts}")
                
            except Exception as e:
                embeddings.append(None)
        
        status_text.text("💾 บันทึกข้อมูลลง customer_vectors...")
        progress_bar.progress(80)
        
        # บันทึกข้อมูล
        inserted = 0
        failed = 0
        
        # สร้าง customer_vectors table ถ้ายังไม่มี
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS customer_vectors (
                    id INT PRIMARY KEY,
                    name VARCHAR(100),
                    embedding LONGBLOB,
                    metadata JSON
                )
            """))
        
        with engine.begin() as conn:
            for _id, name, vector, metadata in zip(ids, texts, embeddings, metadatas):
                if vector is None:
                    failed += 1
                    continue
                
                try:
                    vector_array = np.array(vector, dtype=np.float32)
                    vector_bytes = vector_array.tobytes()
                    
                    conn.execute(
                        text("""
                            INSERT INTO customer_vectors (id, name, embedding, metadata)
                            VALUES (:id, :name, :embedding, :metadata)
                            ON DUPLICATE KEY UPDATE
                              name = VALUES(name),
                              embedding = VALUES(embedding),
                              metadata = VALUES(metadata)
                        """),
                        {
                            "id": int(_id),
                            "name": str(name)[:100],
                            "embedding": vector_bytes,
                            "metadata": json.dumps(metadata, ensure_ascii=False)
                        }
                    )
                    inserted += 1
                    
                except Exception as e:
                    failed += 1
        
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()
        
        # แสดงผลสรุป
        st.markdown("### 🎯 สรุปผลการ Embedding")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("✅ สำเร็จ", inserted)
        with col2:
            st.metric("❌ ผิดพลาด", failed)  
        with col3:
            st.metric("📝 รวม", inserted + failed)
        
        if inserted > 0:
            st.markdown(f"""
            <div class="success-box">
                <h4>🎉 Embedding Process สำเร็จ!</h4>
                <p>สร้าง embeddings สำหรับ {inserted} รายการแล้ว</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ตรวจสอบผลลัพธ์
        with engine.connect() as conn:
            verify_result = conn.execute(text("SELECT COUNT(*) FROM customer_vectors"))
            total_vectors = verify_result.scalar()
            
            sample_result = conn.execute(text("SELECT id, name, LENGTH(embedding) as embedding_size FROM customer_vectors LIMIT 3"))
            
            st.subheader("🔍 ตรวจสอบผลลัพธ์")
            st.info(f"📊 รวมข้อมูลใน customer_vectors: {total_vectors} รายการ")
            
            sample_data = sample_result.fetchall()
            if sample_data:
                sample_df = pd.DataFrame(sample_data, columns=['ID', 'Name', 'Embedding Size (bytes)'])
                st.dataframe(sample_df, use_container_width=True)
    
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    main()
