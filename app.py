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
    page_title="ระบบ embedding sql database",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS with Yellow/Gold Theme and Gradients
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    .main {
        font-family: 'Poppins', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #f39f86 0%, #f9d71c 25%, #deb992 50%, #f39f86 75%, #f9d71c 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.1) 100%);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-weight: 700;
        position: relative;
        z-index: 2;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        position: relative;
        z-index: 2;
    }
    
    .success-box {
        padding: 1.5rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #28a745;
        color: #155724;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(40, 167, 69, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .success-box::before {
        content: '✅';
        position: absolute;
        right: 1rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 2rem;
        opacity: 0.3;
    }
    
    .error-box {
        padding: 1.5rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #dc3545;
        color: #721c24;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(220, 53, 69, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .error-box::before {
        content: '❌';
        position: absolute;
        right: 1rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 2rem;
        opacity: 0.3;
    }
    
    .info-box {
        padding: 1.5rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffc107;
        color: #856404;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(255, 193, 7, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .info-box::before {
        content: 'ℹ️';
        position: absolute;
        right: 1rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 2rem;
        opacity: 0.3;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        text-align: center;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f9d71c 0%, #deb992 100%);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #f9d71c 0%, #f39f86 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        box-shadow: 0 5px 15px rgba(243, 159, 134, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(243, 159, 134, 0.4);
        background: linear-gradient(135deg, #f39f86 0%, #f9d71c 100%);
    }
    
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #f9d71c;
    }
    
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #f9d71c;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #f39f86;
        box-shadow: 0 0 0 0.2rem rgba(249, 215, 28, 0.25);
    }
    
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .section-header {
        background: linear-gradient(90deg, #f9d71c 0%, #f39f86 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    .progress-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #f9d71c 0%, #f39f86 100%);
        border-radius: 10px;
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

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🗂️ ระบบจัดการข้อมูล Table</h1>
        <p>จัดการ Tables และ Import ข้อมูล CSV แบบทันสมัย</p>
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
                        st.rerun()  # ใช้ st.rerun() แทน st.experimental_rerun()
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
        # แสดงข้อมูลของ table ที่เลือก
        columns = st.session_state.db_manager.get_table_columns(selected_table)
        
        st.markdown(f'<div class="section-header">📊 ข้อมูล Table: {selected_table}</div>', unsafe_allow_html=True)
        
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
                    # นับจำนวนข้อมูลทั้งหมด
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {selected_table}"))
                    total_count = count_result.scalar()
                    
                    result = conn.execute(text(f"SELECT * FROM {selected_table} LIMIT 10"))
                    data = result.fetchall()
                    column_names = result.keys()
                    
                st.markdown(f'<div class="section-header">👀 ตัวอย่างข้อมูล (รวม {total_count:,} รายการ)</div>', unsafe_allow_html=True)
                
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
                                        <h2 style="color: #28a745; margin: 0;">{success_count:,}</h2>
                                        <p style="margin: 0.5rem 0 0 0; color: #666;">✅ สำเร็จ</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <h2 style="color: #dc3545; margin: 0;">{error_count:,}</h2>
                                        <p style="margin: 0.5rem 0 0 0; color: #666;">❌ ผิดพลาด</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col3:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <h2 style="color: #6c757d; margin: 0;">{success_count + error_count:,}</h2>
                                        <p style="margin: 0.5rem 0 0 0; color: #666;">📝 รวม</p>
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
            <li>📊 อ่านข้อมูลจาก customers table</li>
            <li>🤖 เรียก Embedding API เพื่อสร้าง vectors</li>
            <li>💾 บันทึกผลลัพธ์ใน customer_vectors table</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # ตรวจสอบ customers table
    st.markdown('<div class="section-header">📊 ตรวจสอบข้อมูล</div>', unsafe_allow_html=True)
    
    try:
        with st.session_state.db_manager.engine.connect() as conn:
            # ตรวจสอบว่ามี customers table หรือไม่
            result = conn.execute(text("SHOW TABLES LIKE 'customers'"))
            customers_exists = result.fetchone() is not None
            
            col1, col2 = st.columns(2)
            
            with col1:
                if customers_exists:
                    # นับจำนวนข้อมูลใน customers
                    count_result = conn.execute(text("SELECT COUNT(*) FROM customers"))
                    customers_count = count_result.scalar()
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>✅ Customers Table</h4>
                        <p><strong>{customers_count:,}</strong> รายการ</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # แสดงตัวอย่างข้อมูล
                    if customers_count > 0:
                        sample_result = conn.execute(text("SELECT id, name, email FROM customers LIMIT 5"))
                        sample_data = sample_result.fetchall()
                        
                        st.markdown('<div class="section-header">👀 ตัวอย่างข้อมูล Customers</div>', unsafe_allow_html=True)
                        sample_df = pd.DataFrame(sample_data, columns=['ID', 'Name', 'Email'])
                        st.dataframe(sample_df, use_container_width=True, hide_index=True)
                else:
                    st.markdown("""
                    <div class="error-box">
                        <h4>❌ ไม่พบ Customers Table</h4>
                        <p>กรุณาสร้าง customers table ก่อน หรือ import ข้อมูล customers</p>
                    </div>
                    """, unsafe_allow_html=True)
                    return
            
            with col2:
                # ตรวจสอบ customer_vectors table
                vectors_result = conn.execute(text("SHOW TABLES LIKE 'customer_vectors'"))
                vectors_exists = vectors_result.fetchone() is not None
                
                if vectors_exists:
                    vectors_count_result = conn.execute(text("SELECT COUNT(*) FROM customer_vectors"))
                    vectors_count = vectors_count_result.scalar()
                    
                    st.markdown(f"""
                    <div class="info-box">
                        <h4>📊 Customer Vectors Table</h4>
                        <p><strong>{vectors_count:,}</strong> รายการ</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="info-box">
                        <h4>⚠️ Customer Vectors Table</h4>
                        <p>ยังไม่มี table (จะถูกสร้างอัตโนมัติ)</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    except Exception as e:
        st.markdown(f"""
        <div class="error-box">
            <h4>❌ ไม่สามารถตรวจสอบข้อมูลได้</h4>
            <p>{str(e)}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.divider()
    
    # ปุ่มรัน embedding
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 เริ่ม Embedding Process", type="primary", use_container_width=True, help="เริ่มกระบวนการสร้าง embeddings"):
            run_embedding_process()

def run_embedding_process():
    """รันกระบวนการ embedding โดยเรียกโค้ดจาก main.py"""
    
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
        engine = create_engine(tidb_url)
        
        status_text.text("📥 ดึงข้อมูลจาก customers table...")
        progress_bar.progress(30)
        
        # ดึงข้อมูล customers
        df = pd.read_sql("SELECT id, name, email, age, city, signup_date FROM customers", con=engine)
        
        if df.empty:
            st.markdown("""
            <div class="info-box">
                <h4>⚠️ ไม่มีข้อมูล</h4>
                <p>ไม่มีข้อมูลใน customers table</p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        st.info(f"📊 พบข้อมูล {len(df):,} รายการ")
        
        status_text.text("🤖 กำลังสร้าง embeddings...")
        progress_bar.progress(40)
        
        # เตรียมข้อมูล
        texts = df["name"].tolist()
        ids = df["id"].tolist()
        
        # จัดการ date - แก้ไข callable issue
        df_copy = df.copy()
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
            conn.commit()
        
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
        st.markdown('<div class="section-header">🎯 สรุปผลการ Embedding</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #28a745; margin: 0;">{inserted:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #666;">✅ สำเร็จ</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #dc3545; margin: 0;">{failed:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #666;">❌ ผิดพลาด</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h2 style="color: #6c757d; margin: 0;">{inserted + failed:,}</h2>
                <p style="margin: 0.5rem 0 0 0; color: #666;">📝 รวม</p>
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
            verify_result = conn.execute(text("SELECT COUNT(*) FROM customer_vectors"))
            total_vectors = verify_result.scalar()
            
            sample_result = conn.execute(text("SELECT id, name, LENGTH(embedding) as embedding_size FROM customer_vectors LIMIT 3"))
            
            st.markdown('<div class="section-header">🔍 ตรวจสอบผลลัพธ์</div>', unsafe_allow_html=True)
            st.info(f"📊 รวมข้อมูลใน customer_vectors: {total_vectors:,} รายการ")
            
            sample_data = sample_result.fetchall()
            if sample_data:
                sample_df = pd.DataFrame(sample_data, columns=['ID', 'Name', 'Embedding Size (bytes)'])
                st.dataframe(sample_df, use_container_width=True, hide_index=True)
    
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.markdown(f"""
        <div class="error-box">
            <h4>❌ เกิดข้อผิดพลาด</h4>
            <p>{str(e)}</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
