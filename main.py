import os
import pandas as pd
import numpy as np
import base64
import requests
import json
import time
import signal
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError
from dotenv import load_dotenv
from datetime import date
from contextlib import contextmanager

# โหลดค่าจาก environment variables
load_dotenv()

# --- Config ---
TIDB_URL = os.getenv("TIDB_URL")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")

class Colors:
    """ANSI Color codes สำหรับ terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """พิมพ์ header สวยๆ"""
    print(f"\n{Colors.CYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}🚀 NTOneEmbedding System{Colors.ENDC}")
    print(f"{Colors.BLUE}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.ENDC}\n")

def print_status(status, message):
    """พิมพ์สถานะพร้อมสี"""
    if status == "info":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")
    elif status == "success":
        print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")
    elif status == "warning":
        print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")
    elif status == "error":
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
    elif status == "running":
        print(f"{Colors.CYAN}🔄 {message}{Colors.ENDC}")

def print_progress_bar(current, total, prefix="Progress", suffix="Complete", length=50):
    """แสดง progress bar"""
    percent = ("{0:.1f}").format(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{Colors.CYAN}{prefix} |{bar}| {percent}% {suffix}{Colors.ENDC}', end='', flush=True)
    if current == total:
        print()

class GracefulKiller:
    """จัดการการยกเลิก process อย่างสุภาพ"""
    kill_now = False
    
    def __init__(self):
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)
    
    def _exit_gracefully(self, signum, frame):
        print_status("warning", "กำลังยกเลิกการประมวลผล...")
        self.kill_now = True

@contextmanager
def database_connection(tidb_url):
    """Context manager สำหรับการเชื่อมต่อ database"""
    engine = None
    conn = None
    try:
        engine = create_engine(tidb_url, pool_pre_ping=True, pool_recycle=300)
        conn = engine.connect()
        yield conn
    except Exception as e:
        print_status("error", f"Database connection failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
        if engine:
            engine.dispose()

def check_environment():
    """ตรวจสอบ environment variables"""
    print_header("Environment Setup")
    
    print_status("info", f"Raw TIDB_URL = {repr(TIDB_URL)}")
    
    if TIDB_URL:
        encoded_url = base64.b64encode(TIDB_URL.encode()).decode()
        print_status("info", f"Base64 of TIDB_URL = {encoded_url[:50]}...")
    else:
        print_status("error", "TIDB_URL is not set! Check your environment variables.")
        return False
    
    print_status("info", f"EMBEDDING_API_URL = {EMBEDDING_API_URL}")
    print_status("info", f"EMBEDDING_MODEL = {EMBEDDING_MODEL}")
    
    return True

def test_database_connection():
    """ทดสอบการเชื่อมต่อ database"""
    print_status("running", "Testing database connection...")
    
    try:
        with database_connection(TIDB_URL) as conn:
            result = conn.execute(text("SELECT 1"))
            print_status("success", f"Connected to TiDB: {result.scalar()}")
            return True
    except ArgumentError as e:
        print_status("error", f"Invalid TIDB_URL format: {e}")
        return False
    except Exception as e:
        print_status("error", f"Database connection error: {e}")
        return False

def get_suitable_tables():
    """ดึงรายชื่อ tables ที่เหมาะสมสำหรับ embedding"""
    print_status("running", "Checking available tables...")
    
    try:
        with database_connection(TIDB_URL) as conn:
            tables_result = conn.execute(text("SHOW TABLES"))
            available_tables = [row[0] for row in tables_result.fetchall()]
            print_status("info", f"Available tables: {available_tables}")
            
            # ตรวจสอบ tables ที่มีข้อมูล
            table_info = {}
            for table in available_tables:
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    
                    # ตรวจสอบว่ามี name column หรือไม่
                    columns_result = conn.execute(text(f"SHOW COLUMNS FROM {table}"))
                    columns = [row[0] for row in columns_result.fetchall()]
                    
                    if 'name' in columns and count > 0:
                        table_info[table] = {
                            'count': count,
                            'columns': columns
                        }
                        print_status("success", f"{table}: {count:,} rows, columns: {columns}")
                    else:
                        reason = 'no name column' if 'name' not in columns else 'empty table'
                        print_status("warning", f"{table}: {reason}")
                        
                except Exception as e:
                    print_status("warning", f"Error checking {table}: {e}")
            
            return table_info
            
    except Exception as e:
        print_status("error", f"Failed to check tables: {e}")
        return {}

def get_existing_embeddings(table_name):
    """ตรวจสอบ embeddings ที่มีอยู่"""
    embedding_table_name = f"{table_name}_vectors"
    existing_embedded_ids = set()
    
    print_status("running", f"Checking existing embeddings in {embedding_table_name}...")
    
    try:
        with database_connection(TIDB_URL) as conn:
            # ตรวจสอบว่ามี embedding table หรือไม่
            check_table = conn.execute(text(f"SHOW TABLES LIKE '{embedding_table_name}'"))
            if check_table.fetchone():
                # ดึง IDs ที่ embed แล้ว
                embedded_result = conn.execute(text(f"SELECT id FROM {embedding_table_name}"))
                existing_embedded_ids = set(row[0] for row in embedded_result.fetchall())
                print_status("info", f"Found {len(existing_embedded_ids):,} existing embeddings")
            else:
                print_status("info", "No existing embedding table found")
                
    except Exception as e:
        print_status("warning", f"Error checking embeddings: {e}")
    
    return existing_embedded_ids

def load_data_for_embedding(table_name, existing_embedded_ids, table_info):
    """โหลดข้อมูลสำหรับ embedding"""
    print_status("running", f"Loading data from {table_name} table...")
    
    try:
        with database_connection(TIDB_URL) as conn:
            table_columns = table_info[table_name]['columns']
            base_columns = ['id', 'name']
            optional_columns = ['email', 'age', 'city', 'signup_date']
            
            # เลือกเฉพาะ columns ที่มีอยู่จริง
            select_columns = [col for col in base_columns + optional_columns if col in table_columns]
            select_sql = f"SELECT {', '.join(select_columns)} FROM {table_name}"
            
            # กรองข้อมูลที่ยังไม่ได้ embed
            if existing_embedded_ids:
                # ใช้ batch processing สำหรับ NOT IN clause
                batch_size = 1000
                embedded_ids_list = list(existing_embedded_ids)
                
                if len(embedded_ids_list) > batch_size:
                    # หากมี ID เยอะเกินไป ให้ใช้วิธีอื่น
                    temp_table = f"temp_embedded_{int(time.time())}"
                    conn.execute(text(f"CREATE TEMPORARY TABLE {temp_table} (id INT PRIMARY KEY)"))
                    
                    # Insert IDs ที่ embed แล้ว
                    print_status("running", f"Creating temporary table for {len(embedded_ids_list):,} IDs...")
                    for i in range(0, len(embedded_ids_list), batch_size):
                        batch = embedded_ids_list[i:i+batch_size]
                        values = ', '.join([f"({id})" for id in batch])
                        conn.execute(text(f"INSERT INTO {temp_table} VALUES {values}"))
                        
                        print_progress_bar(i + len(batch), len(embedded_ids_list), 
                                         "Creating temp table", "Complete")
                    
                    # Query ข้อมูลที่ยังไม่ได้ embed
                    select_sql += f" WHERE {table_name}.id NOT IN (SELECT id FROM {temp_table})"
                else:
                    ids_placeholder = ', '.join(map(str, embedded_ids_list))
                    select_sql += f" WHERE id NOT IN ({ids_placeholder})"
            
            # Add LIMIT เพื่อป้องกันการดึงข้อมูลเยอะเกินไป
            select_sql += " LIMIT 10000"
            
            print_status("running", "Executing query...")
            df = pd.read_sql(select_sql, con=conn)
            
            print_status("success", f"Found {len(df):,} records to process")
            return df
            
    except Exception as e:
        print_status("error", f"Failed to load data: {e}")
        return pd.DataFrame()

def create_embeddings_with_api(texts, killer):
    """สร้าง embeddings โดยเรียก API"""
    print_status("running", f"Creating embeddings for {len(texts):,} texts...")
    
    embeddings = []
    success_count = 0
    failed_count = 0
    
    for i, text in enumerate(texts):
        if killer.kill_now:
            print_status("warning", "Process interrupted by user")
            break
            
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": EMBEDDING_MODEL,
                "prompt": str(text)
            }
            
            # แสดง progress
            print_progress_bar(i + 1, len(texts), 
                             f"Processing ({success_count} success, {failed_count} failed)", 
                             f"Complete")
            
            response = requests.post(EMBEDDING_API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if "embedding" in result and result["embedding"]:
                    embeddings.append(result["embedding"])
                    success_count += 1
                else:
                    embeddings.append(None)
                    failed_count += 1
            else:
                embeddings.append(None)
                failed_count += 1
                
        except requests.exceptions.Timeout:
            print_status("warning", f"Request timeout for text: {str(text)[:50]}...")
            embeddings.append(None)
            failed_count += 1
        except Exception as e:
            embeddings.append(None)
            failed_count += 1
    
    print_status("info", f"Embedding API results: {success_count} success, {failed_count} failed")
    return embeddings

def create_embedding_table(table_name):
    """สร้าง table สำหรับเก็บ embeddings"""
    embedding_table_name = f"{table_name}_vectors"
    print_status("running", f"Creating {embedding_table_name} table if not exists...")
    
    try:
        with database_connection(TIDB_URL) as conn:
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
            print_status("success", f"{embedding_table_name} table ready")
            return embedding_table_name
    except Exception as e:
        print_status("error", f"Failed to create table: {e}")
        return None

def save_embeddings_to_database(embedding_table_name, ids, texts, vectors, metadatas, killer):
    """บันทึก embeddings ลงฐานข้อมูล"""
    print_status("running", f"Saving embeddings to {embedding_table_name}...")
    
    inserted = 0
    failed = 0
    
    try:
        with database_connection(TIDB_URL) as conn:
            # เริ่ม transaction
            trans = conn.begin()
            
            try:
                for i, (_id, name, vector, metadata) in enumerate(zip(ids, texts, vectors, metadatas)):
                    if killer.kill_now:
                        print_status("warning", "Save process interrupted by user")
                        break
                    
                    if vector is None:
                        failed += 1
                        continue
                        
                    try:
                        # แปลง vector เป็น bytes อย่างถูกต้อง
                        vector_array = np.array(vector, dtype=np.float32)
                        vector_bytes = vector_array.tobytes()
                        
                        # ใช้ INSERT ... ON DUPLICATE KEY UPDATE
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
                        
                        # แสดง progress ทุก 100 records
                        if (i + 1) % 100 == 0:
                            print_progress_bar(i + 1, len(ids), 
                                             f"Saving ({inserted} inserted, {failed} failed)", 
                                             "Complete")
                        
                    except Exception as e:
                        failed += 1
                
                # Commit transaction
                trans.commit()
                print_status("success", f"Transaction committed successfully")
                
            except Exception as e:
                trans.rollback()
                print_status("error", f"Transaction rolled back: {e}")
                raise
                
    except Exception as e:
        print_status("error", f"Failed to save embeddings: {e}")
        return 0, len(texts)
    
    print_status("info", f"Save results: {inserted} inserted, {failed} failed")
    return inserted, failed

def verify_results(embedding_table_name):
    """ตรวจสอบผลลัพธ์"""
    print_status("running", f"Verifying data in {embedding_table_name}...")
    
    try:
        with database_connection(TIDB_URL) as conn:
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {embedding_table_name}"))
            total_count = count_result.scalar()
            
            print_status("success", f"Total embeddings in table: {total_count:,}")
            
            # แสดงตัวอย่างข้อมูล
            sample_result = conn.execute(text(f"""
                SELECT id, name, LENGTH(embedding) as embedding_size, 
                       JSON_EXTRACT(metadata, '$.id') as original_id
                FROM {embedding_table_name} 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            
            sample_data = sample_result.fetchall()
            print_status("info", "Sample data:")
            for row in sample_data:
                print(f"  ID: {row[0]}, Name: '{row[1][:30]}...', Embedding Size: {row[2]} bytes")
                
    except Exception as e:
        print_status("error", f"Verification failed: {e}")

def main():
    """Main function"""
    print_header("AI/ML Data Management System - CLI Version")
    
    # สร้าง GracefulKiller instance
    killer = GracefulKiller()
    
    try:
        # ตรวจสอบ environment
        if not check_environment():
            sys.exit(1)
        
        # ทดสอบการเชื่อมต่อ database
        if not test_database_connection():
            sys.exit(1)
        
        # ตรวจสอบ tables
        table_info = get_suitable_tables()
        if not table_info:
            print_status("error", "No suitable tables found. Need tables with 'name' column and data.")
            sys.exit(1)
        
        # เลือก table ที่จะใช้
        if len(table_info) == 1:
            source_table = list(table_info.keys())[0]
            print_status("info", f"Using table: {source_table}")
        else:
            print_status("info", f"Multiple suitable tables found: {list(table_info.keys())}")
            source_table = list(table_info.keys())[0]  # ใช้ตัวแรก
            print_status("info", f"Using first table: {source_table}")
        
        # ตรวจสอบ existing embeddings
        existing_embedded_ids = get_existing_embeddings(source_table)
        
        # โหลดข้อมูลสำหรับ embedding
        df = load_data_for_embedding(source_table, existing_embedded_ids, table_info)
        
        if df.empty:
            print_status("success", "All records are already embedded. Nothing to do.")
            return
        
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
        
        print_status("info", f"Processing {len(texts):,} records for embeddings...")
        
        # สร้าง embeddings
        vectors = create_embeddings_with_api(texts, killer)
        
        if killer.kill_now:
            print_status("warning", "Process was interrupted. Exiting...")
            return
        
        # สร้าง embedding table
        embedding_table_name = create_embedding_table(source_table)
        if not embedding_table_name:
            sys.exit(1)
        
        # บันทึกข้อมูล
        inserted, failed = save_embeddings_to_database(
            embedding_table_name, ids, texts, vectors, metadatas, killer
        )
        
        if killer.kill_now:
            print_status("warning", "Process was interrupted during save. Some data may have been saved.")
            return
        
        # แสดงสรุปผล
        print_header("Summary")
        print_status("success", f"Successfully processed: {inserted:,} embeddings")
        print_status("warning" if failed > 0 else "info", f"Failed: {failed:,} records")
        print_status("info", f"Total processed: {len(texts):,} records")
        
        # ตรวจสอบผลลัพธ์
        verify_results(embedding_table_name)
        
        print_status("success", "Embedding process completed successfully!")
        print_status("info", f"Data saved to table: {embedding_table_name}")
        
    except KeyboardInterrupt:
        print_status("warning", "Process interrupted by user")
    except Exception as e:
        print_status("error", f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
