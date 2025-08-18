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

# Configuration
st.set_page_config(
    page_title="ระบบ Embedding SQL Database",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS with Dark/Neon Blue Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1d3a 100%);
        color: #e1e5f1;
    }
    
    .main {
        font-family: 'Inter', sans-serif;
        background: transparent;
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
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, 
            rgba(6, 182, 212, 0.1) 0%, 
            transparent 25%, 
            rgba(59, 130, 246, 0.1) 50%, 
            transparent 75%, 
            rgba(14, 165, 233, 0.1) 100%);
        animation: shimmer 4s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .main-header h1 {
        color: #ffffff;
        margin: 0;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        font-weight: 700;
        font-size: 2.5rem;
        position: relative;
        z-index: 2;
        background: linear-gradient(45deg, #ffffff, #e1e5f1, #ffffff);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 1rem 0 0 0;
        font-size: 1.2rem;
        text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
        position: relative;
        z-index: 2;
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
        position: relative;
        overflow: hidden;
    }
    
    .success-box::before {
        content: '✅';
        position: absolute;
        right: 1.5rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 2rem;
        opacity: 0.4;
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
        position: relative;
        overflow: hidden;
    }
    
    .error-box::before {
        content: '❌';
        position: absolute;
        right: 1.5rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 2rem;
        opacity: 0.4;
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
        position: relative;
        overflow: hidden;
    }
    
    .info-box::before {
        content: 'ℹ️';
        position: absolute;
        right: 1.5rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 2rem;
        opacity: 0.4;
    }
    
    /* Metric Card */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        padding: 2rem 1.5rem;
        border-radius: 20px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(71, 85, 105, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2), 0 0 0 1px rgba(59, 130, 246, 0.3);
        border-color: #3b82f6;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #06b6d4, #0ea5e9);
        border-radius: 20px 20px 0 0;
    }
    
    /* Section Header */
    .section-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%);
        color: #ffffff;
        padding: 1rem 2rem;
        border-radius: 16px;
        margin: 2rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.1rem;
        text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.25), 0 0 0 1px rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    /* Sidebar */
    .css-1d391kg, .css-1rs6os {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid #334155;
    }
    
    .css-1d391kg .css-10trblm {
        color: #e1e5f1;
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
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.875rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(59, 130, 246, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Form Elements */
    .stSelectbox > div > div {
        background: #1e293b !important;
        border: 2px solid #334155 !important;
        border-radius: 12px !important;
        color: #e1e5f1 !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    .stTextInput > div > div > input {
        background: #1e293b !important;
        border: 2px solid #334155 !important;
        border-radius: 12px !important;
        color: #e1e5f1 !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }
    
    /* Checkbox */
    .stCheckbox > label {
        color: #e1e5f1 !important;
    }
    
    /* Radio */
    .stRadio > label {
        color: #e1e5f1 !important;
    }
    
    /* DataFrame */
    .stDataFrame {
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(71, 85, 105, 0.3) !important;
        border: 1px solid #334155 !important;
    }
    
    /* Progress */
    .stProgress > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 50%, #0ea5e9 100%) !important;
        border-radius: 10px !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5) !important;
    }
    
    .progress-container {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        margin: 1rem 0;
    }
    
    /* File Uploader */
    .stFileUploader > div > div {
        background: #1e293b !important;
        border: 2px dashed #334155 !important;
        border-radius: 16px !important;
        color: #e1e5f1 !important;
    }
    
    .stFileUploader > div > div:hover {
        border-color: #3b82f6 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #1e293b !important;
        color: #e1e5f1 !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
    }
    
    .streamlit-expanderContent {
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #2563eb, #0ea5e9);
    }
    
    /* Neon glow effects */
    @keyframes neon-pulse {
        0%, 100% { 
            box-shadow: 0 0 5px rgba(59, 130, 246, 0.5),
                        0 0 10px rgba(59, 130, 246, 0.3),
                        0 0 20px rgba(59, 130, 246, 0.2);
        }
        50% { 
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.8),
                        0 0 20px rgba(59, 130, 246, 0.5),
                        0 0 30px rgba(59, 130, 246, 0.3);
        }
    }
    
    .stButton > button:hover {
        animation: neon-pulse 2s infinite;
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
    
    def check_embedded_records(self, table_name):
        """ตรวจสอบว่า record ไหน embedded แล้ว"""
        try:
            with self.engine.connect() as conn:
                # ตรวจสอบว่ามี customer_vectors table หรือไม่
                result = conn.execute(text("SHOW TABLES LIKE 'customer_vectors'"))
                if not result.fetchone():
                    return set(), 0
                
                # ดึง IDs ที่ embed แล้ว
                embedded_result = conn.execute(text("SELECT id FROM customer_vectors"))
                embedded_ids = set(row[0] for row in embedded_result.fetchall())
                
                # นับจำนวนรวม
                total_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                total_count = total_result.scalar()
                
                return embedded_ids, total_count
        except Exception as e:
            st.error(f"❌ ไม่สามารถตรวจสอบ embedded records ได้: {str(e)}")
            return set(), 0
    
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
    
    def create_embedding_table(self, base_table_name):
        """สร้าง table สำหรับเก็บ embeddings"""
        try:
            embedding_table_name = f"{base_table_name}_vectors"
            
            with self.engine.connect() as conn:
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {embedding_table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(255),
                        embedding LONGBLOB,
                        metadata JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_created_at (created_at)
                    )
                """))
                conn.commit()
            
            return embedding_table_name
        except Exception as e:
            st.error(f"❌ ไม่สามารถสร้าง embedding table ได้: {str(e)}")
            return None
    
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

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🗂️ ระบบ Embedding SQL Database</h1>
        <p>จัดการ Tables, Import ข้อมูล CSV และสร้าง Vector Embeddings</p>
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
    st.sidebar.markdown('<div class="section-header">📋 เมนูหลัก</div>', unsafe_allow_html=True)
    menu_option = st.sidebar.radio(
        "เลือกการดำเนินการ:",
        ["🆕 สร้าง Table ใหม่", "📋 เลือก Table ที่มีอยู่", "📁 Upload CSV File", "🤖 Run Embedding Process"],
        label_visibility="collapsed"
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
    st.markdown('<div class="section-header">🆕 สร้าง Table ใหม่</div>', unsafe_allow_html=True)
    
    # ชื่อ table
    table_name = st.text_input("ชื่อ Table:", placeholder="ระบุชื่อ table ใหม่")
    
    if not table_name:
        st.markdown("""
        <div class="info-box">
            <h4>💡 คำแนะนำ</h4>
            <p>กรุณาระบุชื่อ table ที่ต้องการสร้าง ระบบจะเพิ่ม ID column อัตโนมัติเป็น Primary Key</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<div class="section-header">📝 กำหนด Columns</div>', unsafe_allow_html=True)
    
    # จัดการ columns configuration
    if 'columns_config' not in st.session_state:
        st.session_state.columns_config = []
    
    # เพิ่ม column ใหม่
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            new_col_name = st.text_input("ชื่อ Column:", key="new_col_name", placeholder="เช่น name, email")
        with col2:
            new_col_type = st.selectbox("ประเภทข้อมูล:", 
                                       ["String", "Integer", "Float", "Text", "DateTime"], 
                                       key="new_col_type")
        with col3:
            new_col_nullable = st.checkbox("อนุญาต NULL", value=True, key="new_col_nullable")
        with col4:
            if st.button("➕ เพิ่ม", help="เพิ่ม column ใหม่"):
                if new_col_name:
                    if new_col_name.lower() != 'id':  # ป้องกันการเพิ่ม id column
                        st.session_state.columns_config.append({
                            'name': new_col_name,
                            'type': new_col_type,
                            'nullable': new_col_nullable
                        })
                        st.rerun()
                    else:
                        st.warning("⚠️ ไม่สามารถเพิ่ม 'id' column ได้ เนื่องจากระบบจะสร้างให้อัตโนมัติ")
    
    # แสดงรายการ columns ที่กำหนดแล้ว
    if st.session_state.columns_config:
        st.markdown('<div class="section-header">📋 Columns ที่กำหนด</div>', unsafe_allow_html=True)
        
        # แสดงข้อมูลในรูปแบบ table
        cols_data = []
        cols_data.append({
            'ชื่อ Column': 'id',
            'ประเภทข้อมูล': 'Integer',
            'อนุญาต NULL': 'ไม่ได้',
            'หมายเหตุ': 'Primary Key (Auto)'
        })
        
        for col_config in st.session_state.columns_config:
            cols_data.append({
                'ชื่อ Column': col_config['name'],
                'ประเภทข้อมูล': col_config['type'],
                'อนุญาต NULL': 'ได้' if col_config['nullable'] else 'ไม่ได้',
                'หมายเหตุ': ''
            })
        
        df_cols = pd.DataFrame(cols_data)
        st.dataframe(df_cols, use_container_width=True, hide_index=True)
        
        # ปุ่มจัดการ
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("🗑️ ล้างทั้งหมด", help="ล้าง columns ทั้งหมด"):
                st.session_state.columns_config = []
                st.rerun()
        
        with col3:
            if st.button("✅ สร้าง Table", type="primary", help="สร้าง table ใหม่"):
                with st.spinner("กำลังสร้าง table..."):
                    if st.session_state.db_manager.create_new_table(table_name, st.session_state.columns_config):
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>🎉 สร้าง Table สำเร็จ!</h4>
                            <p>สร้าง table '<strong>{table_name}</strong>' พร้อม {len(st.session_state.columns_config) + 1} columns แล้ว</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.columns_config = []  # ล้าง config
                        st.balloons()
                    else:
                        st.markdown("""
                        <div class="error-box">
                            <h4>❌ ไม่สามารถสร้าง Table ได้</h4>
                            <p>กรุณาตรวจสอบชื่อ table และ columns อีกครั้ง</p>
                        </div>
                        """, unsafe_allow_html=True)

def show_select_table_interface():
    """แสดง interface สำหรับเลือก table ที่มีอยู่"""
    st.markdown('<div class="section-header">📋 เลือก Table ที่มีอยู่</div>', unsafe_allow_html=True)
    
    # ดึงรายชื่อ tables
    tables = st.session_state.db_manager.get_existing_tables()
    
    if not tables:
        st.markdown("""
        <div class="info-box">
            <h4>💡 ไม่พบ Tables</h4>
            <p>ยังไม่มี tables ในระบบ กรุณาสร้าง table ใหม่ก่อน</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    selected_table = st.selectbox("เลือก Table:", tables, help="เลือก table ที่ต้องการดูข้อมูล")
    
    if selected_table:
        # ตรวจสอบ embedding status
        embedded_ids, total_count = st.session_state.db_manager.check_embedded_records(selected_table)
        
        # แสดงข้อมูลของ table ที่เลือก
        columns = st.session_state.db_manager.get_table_columns(selected_table)
        
        st.markdown(f'<div class="section-header">📊 ข้อมูล Table: {selected_table}</div>', unsafe_allow_html=True)
        
        # แสดง embedding status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #10b981; margin: 0;">{total_count:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">📝 รวมทั้งหมด</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #3b82f6; margin: 0;">{len(embedded_ids):,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">🤖 Embedded แล้ว</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            remaining = total_count - len(embedded_ids)
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #f59e0b; margin: 0;">{remaining:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">⏳ รอ Embedding</p>
            </div>
            """, unsafe_allow_html=True)
        
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
            st.dataframe(df_cols, use_container_width=True, hide_index=True)
            
            # แสดงข้อมูลในตาราง (ตัวอย่าง 10 แถวแรก)
            try:
                with st.session_state.db_manager.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT * FROM {selected_table} LIMIT 10"))
                    data = result.fetchall()
                    column_names = result.keys()
                    
                st.markdown(f'<div class="section-header">👀 ตัวอย่างข้อมูล</div>', unsafe_allow_html=True)
                
                if data:
                    df_preview = pd.DataFrame(data, columns=column_names)
                    st.dataframe(df_preview, use_container_width=True, hide_index=True)
                else:
                    st.markdown("""
                    <div class="info-box">
                        <h4>📭 Table ว่าง</h4>
                        <p>ไม่มีข้อมูลในตารางนี้ กรุณา import ข้อมูลก่อน</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"❌ ไม่สามารถดึงข้อมูลได้: {str(e)}")

def show_upload_csv_interface():
    """แสดง interface สำหรับ upload CSV file"""
    st.markdown('<div class="section-header">📁 Upload CSV File</div>', unsafe_allow_html=True)
    
    # เลือก table
    tables = st.session_state.db_manager.get_existing_tables()
    
    if not tables:
        st.markdown("""
        <div class="info-box">
            <h4>💡 ไม่พบ Tables</h4>
            <p>ไม่พบ tables ในระบบ กรุณาสร้าง table ก่อน</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    selected_table = st.selectbox("เลือก Table ปลายทาง:", tables, key="upload_table_select")
    
    if selected_table:
        # ดาวน์โหลด template
        columns = st.session_state.db_manager.get_table_columns(selected_table)
        
        if columns:
            st.markdown('<div class="section-header">📋 Template CSV</div>', unsafe_allow_html=True)
            
            # สร้าง template CSV (ไม่รวม id column)
            template_data = {}
            for col in columns:
                if col['name'] != 'id':  # ข้าม id column ที่เป็น auto increment
                    if col['type'].__class__.__name__ == 'VARCHAR' or 'String' in str(col['type']):
                        template_data[col['name']] = ['ตัวอย่างข้อความ']
                    elif 'Integer' in str(col['type']) or 'INT' in str(col['type']):
                        template_data[col['name']] = [123]
                    elif 'Float' in str(col['type']) or 'DECIMAL' in str(col['type']):
                        template_data[col['name']] = [123.45]
                    elif 'DateTime' in str(col['type']) or 'DATE' in str(col['type']):
                        template_data[col['name']] = ['2023-07-01']
                    else:
                        template_data[col['name']] = ['ตัวอย่างข้อมูล']
            
            template_df = pd.DataFrame(template_data)
            
            # แสดง template
            st.dataframe(template_df, use_container_width=True, hide_index=True)
            
            # ดาวน์โหลด template
            csv_buffer = io.StringIO()
            template_df.to_csv(csv_buffer, index=False)
            csv_string = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 ดาวน์โหลด Template CSV",
                data=csv_string,
                file_name=f"{selected_table}_template.csv",
                mime="text/csv",
                help="ดาวน์โหลดไฟล์ template สำหรับ import ข้อมูล"
            )
            
            st.divider()
            
            # Upload file
            st.markdown('<div class="section-header">📤 อัพโหลดไฟล์ CSV</div>', unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("เลือกไฟล์ CSV:", type=['csv'], help="เลือกไฟล์ CSV ที่จะ import")
            
            if uploaded_file is not None:
                try:
                    # อ่านไฟล์ CSV
                    df = pd.read_csv(uploaded_file)
                    
                    st.success(f"✅ อ่านไฟล์สำเร็จ: {len(df):,} แถว")
                    
                    # แสดงตัวอย่างข้อมูล
                    st.markdown('<div class="section-header">👀 ตัวอย่างข้อมูลที่จะ Import</div>', unsafe_allow_html=True)
                    st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                    
                    # ตรวจสอบ columns
                    table_columns = [col['name'] for col in columns if col['name'] != 'id']
                    csv_columns = df.columns.tolist()
                    
                    missing_columns = set(table_columns) - set(csv_columns)
                    extra_columns = set(csv_columns) - set(table_columns)
                    
                    # แสดงการตรวจสอบ columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if missing_columns:
                            st.markdown(f"""
                            <div class="error-box">
                                <h4>❌ Columns ที่ขาดหายไป</h4>
                                <p>{', '.join(missing_columns)}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="success-box">
                                <h4>✅ Columns ครบถ้วน</h4>
                                <p>ข้อมูล CSV มี columns ครบตามที่ต้องการ</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        if extra_columns:
                            st.markdown(f"""
                            <div class="info-box">
                                <h4>ℹ️ Columns เพิ่มเติม</h4>
                                <p>{', '.join(extra_columns)} (จะถูกเพิกเฉย)</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # ปุ่ม Import
                    if not missing_columns:
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            if st.button("🚀 Import ข้อมูล", type="primary", use_container_width=True, help="เริ่มการ import ข้อมูล"):
                                # กรองเฉพาะ columns ที่ตรงกัน
                                df_filtered = df[table_columns]
                                
                                # Import ข้อมูล
                                with st.spinner("กำลัง import ข้อมูล..."):
                                    success_count, error_count, errors = st.session_state.db_manager.insert_data_from_csv(
                                        selected_table, df_filtered
                                    )
                                
                                # แสดงผลสรุป
                                st.markdown('<div class="section-header">📊 สรุปผลการ Import</div>', unsafe_allow_html=True)
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <h2 style="color: #10b981; margin: 0;">{success_count:,}</h2>
                                        <p style="margin: 0.5rem 0 0 0; color: #64748b;">✅ สำเร็จ</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <h2 style="color: #ef4444; margin: 0;">{error_count:,}</h2>
                                        <p style="margin: 0.5rem 0 0 0; color: #64748b;">❌ ผิดพลาด</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col3:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <h2 style="color: #64748b; margin: 0;">{success_count + error_count:,}</h2>
                                        <p style="margin: 0.5rem 0 0 0; color: #64748b;">📝 รวม</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                if success_count > 0:
                                    st.markdown(f"""
                                    <div class="success-box">
                                        <h4>🎉 Import สำเร็จ!</h4>
                                        <p>เพิ่มข้อมูล <strong>{success_count:,}</strong> แถวเข้า table '<strong>{selected_table}</strong>' แล้ว</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.balloons()
                                
                                if errors:
                                    st.markdown("""
                                    <div class="error-box">
                                        <h4>❌ รายการข้อผิดพลาด:</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    with st.expander("ดูรายละเอียดข้อผิดพลาด", expanded=False):
                                        for error in errors[:10]:  # แสดงแค่ 10 ข้อผิดพลาดแรก
                                            st.error(error)
                                        
                                        if len(errors) > 10:
                                            st.warning(f"... และอีก {len(errors) - 10} ข้อผิดพลาด")
                    else:
                        st.markdown("""
                        <div class="error-box">
                            <h4>❌ ไม่สามารถ Import ได้</h4>
                            <p>ข้อมูล CSV ขาด columns ที่จำเป็น กรุณาแก้ไขไฟล์ก่อน</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>❌ ไม่สามารถอ่านไฟล์ CSV ได้</h4>
                        <p>{str(e)}</p>
                    </div>
                    """, unsafe_allow_html=True)

def show_embedding_interface():
    """แสดง interface สำหรับรัน embedding process"""
    st.markdown('<div class="section-header">🤖 Run Embedding Process</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h4>ℹ️ เกี่ยวกับ Embedding Process</h4>
        <p>กระบวนการนี้จะ:</p>
        <ul>
            <li>📊 อ่านข้อมูลจาก table ที่เลือก</li>
            <li>🤖 เรียก Embedding API เพื่อสร้าง vectors</li>
            <li>💾 บันทึกผลลัพธ์ใน embedding table</li>
            <li>🔄 ตรวจสอบข้อมูลที่ embed แล้วเพื่อไม่ทำซ้ำ</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # เลือก table สำหรับ embedding
    tables = st.session_state.db_manager.get_existing_tables()
    
    if not tables:
        st.markdown("""
        <div class="error-box">
            <h4>❌ ไม่พบ Tables</h4>
            <p>ไม่พบ tables ในระบบ กรุณาสร้าง table และ import ข้อมูลก่อน</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    selected_table = st.selectbox("เลือก Table สำหรับ Embedding:", tables, key="embedding_table_select")
    
    if selected_table:
        # ตรวจสอบข้อมูลในตาราง
        try:
            with st.session_state.db_manager.engine.connect() as conn:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {selected_table}"))
                total_count = count_result.scalar()
                
                if total_count == 0:
                    st.markdown("""
                    <div class="error-box">
                        <h4>❌ Table ว่าง</h4>
                        <p>ไม่มีข้อมูลใน table ที่เลือก กรุณา import ข้อมูลก่อน</p>
                    </div>
                    """, unsafe_allow_html=True)
                    return
                
                # ตรวจสอบว่ามี name column หรือไม่
                columns = st.session_state.db_manager.get_table_columns(selected_table)
                column_names = [col['name'] for col in columns]
                
                if 'name' not in column_names:
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>❌ ไม่พบ 'name' Column</h4>
                        <p>Table ที่เลือกต้องมี column ชื่อ 'name' สำหรับการสร้าง embedding</p>
                        <p>Columns ที่มี: {', '.join(column_names)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    return
        
        except Exception as e:
            st.error(f"❌ ไม่สามารถตรวจสอบข้อมูลได้: {str(e)}")
            return
        
        # ตรวจสอบ embedding status
        embedded_ids, _ = st.session_state.db_manager.check_embedded_records(selected_table)
        remaining_count = total_count - len(embedded_ids)
        
        # แสดงการตั้งค่าปัจจุบัน
        st.markdown('<div class="section-header">🔧 การตั้งค่าปัจจุบัน</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            embedding_api_url = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
            st.markdown(f"""
            <div class="info-box">
                <h4>🌐 Embedding API URL</h4>
                <p><code>{embedding_api_url}</code></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
            st.markdown(f"""
            <div class="info-box">
                <h4>🧠 Embedding Model</h4>
                <p><code>{embedding_model}</code></p>
            </div>
            """, unsafe_allow_html=True)
        
        # แสดงสถานะข้อมูล
        st.markdown('<div class="section-header">📊 สถานะข้อมูล</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #10b981; margin: 0;">{total_count:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">📝 รวมทั้งหมด</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #3b82f6; margin: 0;">{len(embedded_ids):,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">✅ Embedded แล้ว</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            color = "#f59e0b" if remaining_count > 0 else "#10b981"
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: {color}; margin: 0;">{remaining_count:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">⏳ รอ Processing</p>
            </div>
            """, unsafe_allow_html=True)
        
        if remaining_count == 0:
            st.markdown("""
            <div class="success-box">
                <h4>🎉 เสร็จสิ้นแล้ว!</h4>
                <p>ข้อมูลทั้งหมดถูก embed เรียบร้อยแล้ว ไม่จำเป็นต้องรันใหม่</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="info-box">
                <h4>🔄 พร้อมสำหรับ Embedding</h4>
                <p>มีข้อมูล <strong>{remaining_count:,}</strong> รายการที่รอการประมวลผล</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # ปุ่มรัน embedding
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            button_disabled = remaining_count == 0
            button_text = "✅ เสร็จสิ้นแล้ว" if button_disabled else "🚀 เริ่ม Embedding Process"
            
            if st.button(button_text, type="primary", use_container_width=True, 
                        disabled=button_disabled, help="เริ่มกระบวนการสร้าง embeddings"):
                run_embedding_process(selected_table, embedded_ids)

def run_embedding_process(table_name, existing_embedded_ids):
    """รันกระบวนการ embedding โดยตรวจสอบข้อมูลที่ embed แล้ว"""
    
    progress_container = st.container()
    
    with progress_container:
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)
    
    try:
        status_text.text("🔄 กำลังเริ่มต้น Embedding Process...")
        progress_bar.progress(10)
        
        # ตรวจสอบการตั้งค่า
        tidb_url = os.getenv("TIDB_URL")
        embedding_api_url = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
        
        if not tidb_url:
            st.markdown("""
            <div class="error-box">
                <h4>❌ การตั้งค่าไม่ครบ</h4>
                <p>TIDB_URL ไม่ได้กำหนด</p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        status_text.text("📡 ตรวจสอบการเชื่อมต่อ...")
        progress_bar.progress(20)
        
        # เชื่อมต่อ database
        engine = st.session_state.db_manager.engine
        
        status_text.text(f"📥 ดึงข้อมูลจาก {table_name} table...")
        progress_bar.progress(30)
        
        # ดึงข้อมูลเฉพาะที่ยังไม่ได้ embed
        columns = st.session_state.db_manager.get_table_columns(table_name)
        column_names = [col['name'] for col in columns]
        
        # สร้าง SELECT statement ตาม columns ที่มี
        base_columns = ['id', 'name']
        optional_columns = ['email', 'age', 'city', 'signup_date']
        available_columns = [col for col in base_columns + optional_columns if col in column_names]
        
        select_sql = f"SELECT {', '.join(available_columns)} FROM {table_name}"
        
        if existing_embedded_ids:
            ids_placeholder = ', '.join(map(str, existing_embedded_ids))
            select_sql += f" WHERE id NOT IN ({ids_placeholder})"
        
        df = pd.read_sql(select_sql, con=engine)
        
        if df.empty:
            st.markdown("""
            <div class="info-box">
                <h4>⚠️ ไม่มีข้อมูลใหม่</h4>
                <p>ข้อมูลทั้งหมดถูก embed แล้ว</p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        st.info(f"📊 พบข้อมูลใหม่ {len(df):,} รายการ")
        
        status_text.text("🤖 กำลังสร้าง embeddings...")
        progress_bar.progress(40)
        
        # เตรียมข้อมูล
        texts = df["name"].tolist()
        ids = df["id"].tolist()
        
        # จัดการ metadata
        df_copy = df.copy()
        if 'signup_date' in df_copy.columns:
            df_copy["signup_date"] = df_copy["signup_date"].apply(
                lambda d: d.isoformat() if hasattr(d, 'isoformat') else str(d)
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
        
        status_text.text(f"💾 บันทึกข้อมูลลง {table_name}_vectors...")
        progress_bar.progress(80)
        
        # สร้าง embedding table ถ้ายังไม่มี
        embedding_table_name = st.session_state.db_manager.create_embedding_table(table_name)
        if not embedding_table_name:
            st.error("❌ ไม่สามารถสร้าง embedding table ได้")
            return
        
        # บันทึกข้อมูล
        inserted = 0
        failed = 0
        
        with engine.begin() as conn:
            for _id, name, vector, metadata in zip(ids, texts, embeddings, metadatas):
                if vector is None:
                    failed += 1
                    continue
                
                try:
                    vector_array = np.array(vector, dtype=np.float32)
                    vector_bytes = vector_array.tobytes()
                    
                    conn.execute(
                        text(f"""
                            INSERT INTO {embedding_table_name} (id, name, embedding, metadata)
                            VALUES (:id, :name, :embedding, :metadata)
                            ON DUPLICATE KEY UPDATE
                              name = VALUES(name),
                              embedding = VALUES(embedding),
                              metadata = VALUES(metadata)
                        """),
                        {
                            "id": int(_id),
                            "name": str(name)[:255],
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
        st.markdown('<div class="section-header">🎯 สรุปผลการ Embedding</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #10b981; margin: 0;">{inserted:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">✅ สำเร็จ</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #ef4444; margin: 0;">{failed:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">❌ ผิดพลาด</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #64748b; margin: 0;">{inserted + failed:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">📝 รวม</p>
            </div>
            """, unsafe_allow_html=True)
        
        if inserted > 0:
            st.markdown(f"""
            <div class="success-box">
                <h4>🎉 Embedding Process สำเร็จ!</h4>
                <p>สร้าง embeddings สำหรับ <strong>{inserted:,}</strong> รายการแล้ว</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        
        # ตรวจสอบผลลัพธ์
        with engine.connect() as conn:
            verify_result = conn.execute(text(f"SELECT COUNT(*) FROM {embedding_table_name}"))
            total_vectors = verify_result.scalar()
            
            sample_result = conn.execute(text(f"SELECT id, name, LENGTH(embedding) as embedding_size FROM {embedding_table_name} LIMIT 3"))
            
            st.markdown('<div class="section-header">🔍 ตรวจสอบผลลัพธ์</div>', unsafe_allow_html=True)
            st.info(f"📊 รวมข้อมูลใน {embedding_table_name}: {total_vectors:,} รายการ")
            
            sample_data = sample_result.fetchall()
            if sample_data:
                sample_df = pd.DataFrame(sample_data, columns=['ID', 'Name', 'Embedding Size (bytes)'])
                st.dataframe(sample_df, use_container_width=True, hide_index=True)
    
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.markdown(f"""
        <div class="error-box">
            <h4>❌ เกิดข้อผิดพลาด: {str(e)}</h4>
            <p>กรุณาตรวจสอบการตั้งค่าและลองใหม่อีกครั้ง</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
