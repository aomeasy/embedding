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
import time
import threading

# Configuration
st.set_page_config(
    page_title="NTOneEmbedding System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    .css-1d391kg .css-10trblm {
        color: #e1e5f1;
    }
    
    /* Modern Sidebar Menu */
    .sidebar-logo {
        text-align: center;
        padding: 2rem 1rem 1rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .sidebar-logo h1 {
        background: linear-gradient(45deg, #3b82f6, #06b6d4, #0ea5e9);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    
    .sidebar-logo p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.8rem;
        margin: 0.5rem 0 0 0;
        font-weight: 300;
    }
    
    /* Sidebar Radio Buttons - Modern Cards */
    .stRadio > div {
        gap: 0.75rem;
    }
    
    .stRadio > div > label {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin: 0;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        color: #e1e5f1;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .stRadio > div > label::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, #3b82f6, #06b6d4);
        transform: scaleY(0);
        transition: transform 0.3s ease;
        border-radius: 0 4px 4px 0;
    }
    
    .stRadio > div > label:hover {
        background: linear-gradient(135deg, #334155 0%, #475569 100%);
        border-color: #3b82f6;
        transform: translateX(8px) scale(1.02);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
    }
    
    .stRadio > div > label:hover::before {
        transform: scaleY(1);
    }
    
    /* Selected radio button */
    .stRadio > div > label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
    
    .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%);
        border-color: #06b6d4;
        color: white;
        transform: translateX(12px) scale(1.05);
        box-shadow: 0 12px 35px rgba(59, 130, 246, 0.4);
    }
    
    .stRadio > div > label[data-checked="true"]::before {
        transform: scaleY(1);
        background: linear-gradient(180deg, #ffffff, #e1e5f1);
        width: 6px;
    }
    
    /* Sidebar Section Headers */
    .sidebar-section {
        margin: 2rem 1rem 1rem;
        padding: 1rem;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        border-radius: 12px;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
    }
    
    .sidebar-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
        transform: rotate(45deg);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .sidebar-section h3 {
        color: white;
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        position: relative;
        z-index: 2;
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
        animation: headerShimmer 6s infinite;
    }
    
    @keyframes headerShimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
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
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 1rem 0 0 0;
        font-size: 1.2rem;
        text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
        position: relative;
        z-index: 2;
        font-weight: 300;
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
    
    /* Embedding Status */
    .embedding-status {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .embedding-status::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #10b981, #059669);
        animation: loadingBar 2s infinite;
    }
    
    @keyframes loadingBar {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* DataFrame */
    .stDataFrame {
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(71, 85, 105, 0.3) !important;
        border: 1px solid #334155 !important;
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
            
            self.engine = create_engine(tidb_url, pool_pre_ping=True, pool_recycle=300)
            
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
    
    def check_embedded_records(self, table_name):
        """ตรวจสอบว่า record ไหน embedded แล้ว"""
        try:
            embedding_table_name = f"{table_name}_vectors"
            
            with self.engine.connect() as conn:
                # ตรวจสอบว่ามี embedding table หรือไม่
                result = conn.execute(text(f"SHOW TABLES LIKE '{embedding_table_name}'"))
                if not result.fetchone():
                    return set(), 0
                
                # ดึง IDs ที่ embed แล้ว
                embedded_result = conn.execute(text(f"SELECT id FROM {embedding_table_name}"))
                embedded_ids = set(row[0] for row in embedded_result.fetchall())
                
                # นับจำนวนรวม
                total_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                total_count = total_result.scalar()
                
                return embedded_ids, total_count
        except Exception as e:
            st.error(f"❌ ไม่สามารถตรวจสอบ embedded records ได้: {str(e)}")
            return set(), 0
    
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
    # Modern Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <h1>🚀 NTOneEmbedding</h1>
            <p>AI/ML Data Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="sidebar-section">
            <h3>📋 เมนูหลัก</h3>
        </div>
        """, unsafe_allow_html=True)
    
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
            <p>กรุณาตรวจสอบการตั้งค่า TIDB_URL ใน environment variables</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Sidebar menu
    menu_option = st.sidebar.radio(
        "",  # ไม่ต้องมี label เพราะเรามี custom header แล้ว
        ["🆕 สร้าง Table ใหม่", "📋 เลือก Table ที่มีอยู่", "📁 Upload CSV File", "🤖 Run Embedding Process"],
        label_visibility="collapsed"
    )
    
    # System Status
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-section">
            <h3>📊 สถานะระบบ</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # แสดงสถานะการเชื่อมต่อ
        if st.session_state.db_manager.engine:
            st.markdown("""
            <div class="embedding-status">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span class="status-indicator status-complete"></span>
                    <span style="color: #10b981; font-weight: 600;">Database เชื่อมต่อแล้ว</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="embedding-status">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span class="status-indicator status-waiting"></span>
                    <span style="color: #ef4444; font-weight: 600;">Database ยังไม่เชื่อมต่อ</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # แสดงจำนวน tables
        try:
            tables = st.session_state.db_manager.get_existing_tables()
            st.markdown(f"""
            <div class="metric-card" style="margin: 1rem 0; padding: 1rem;">
                <h3 style="color: #3b82f6; margin: 0; font-size: 1.2rem;">{len(tables)}</h3>
                <p style="margin: 0.25rem 0 0 0; color: #64748b; font-size: 0.8rem;">📋 Tables ทั้งหมด</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            pass
    
    if menu_option == "🆕 สร้าง Table ใหม่":
        show_create_table_interface()
    elif menu_option == "📋 เลือก Table ที่มีอยู่":
        show_select_table_interface()
    elif menu_option == "📁 Upload CSV File":
        show_upload_csv_interface()
    elif menu_option == "🤖 Run Embedding Process":
        show_embedding_interface()
