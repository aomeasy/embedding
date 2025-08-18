import os
import pandas as pd
import numpy as np
import base64
import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError
from dotenv import load_dotenv
from datetime import date

# โหลดค่าจาก environment variables
load_dotenv()

# --- Config ---
TIDB_URL = os.getenv("TIDB_URL")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")

print("\n🔧 Environment Setup")
print("🔎 Raw TIDB_URL =", repr(TIDB_URL))
if TIDB_URL:
    print("📦 Base64 of TIDB_URL =", base64.b64encode(TIDB_URL.encode()).decode())
else:
    print("❌ TIDB_URL is not set! Check your environment variables.")
    exit(1)

print("📡 EMBEDDING_API_URL =", EMBEDDING_API_URL)
print("📦 EMBEDDING_MODEL =", EMBEDDING_MODEL)

# --- Test Connection ---
try:
    engine = create_engine(TIDB_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Connected to TiDB:", result.scalar())
except ArgumentError as e:
    print("❌ Invalid TIDB_URL format:", e)
    exit(1)
except Exception as e:
    print("❌ Other error during DB connection:", e)
    exit(1)

# --- Check for existing tables and choose source ---
print("\n📋 Checking available tables...")
try:
    with engine.connect() as conn:
        tables_result = conn.execute(text("SHOW TABLES"))
        available_tables = [row[0] for row in tables_result.fetchall()]
        print(f"📊 Available tables: {available_tables}")
        
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
                    print(f"✅ {table}: {count} rows, columns: {columns}")
                else:
                    print(f"⚠️ {table}: {'no name column' if 'name' not in columns else 'empty table'}")
                    
            except Exception as e:
                print(f"⚠️ Error checking {table}: {e}")
        
        if not table_info:
            print("❌ No suitable tables found. Need tables with 'name' column and data.")
            exit(1)
            
        # เลือก table ที่จะใช้
        if len(table_info) == 1:
            source_table = list(table_info.keys())[0]
            print(f"🎯 Using table: {source_table}")
        else:
            print(f"📋 Multiple suitable tables found: {list(table_info.keys())}")
            source_table = list(table_info.keys())[0]  # ใช้ตัวแรก
            print(f"🎯 Using first table: {source_table}")
            
except Exception as e:
    print("❌ Failed to check tables:", e)
    exit(1)

# --- Load data from selected table ---
print(f"\n📥 Fetching data from {source_table} table...")
try:
    # สร้าง SELECT statement ตาม columns ที่มี
    table_columns = table_info[source_table]['columns']
    base_columns = ['id', 'name']
    optional_columns = ['email', 'age', 'city', 'signup_date']
    
    # เลือกเฉพาะ columns ที่มีอยู่จริง
    select_columns = [col for col in base_columns + optional_columns if col in table_columns]
    select_sql = f"SELECT {', '.join(select_columns)} FROM {source_table}"
    
    df = pd.read_sql(select_sql, con=engine)
    print(f"🔢 Found {len(df)} rows")
    print(f"📊 Columns: {list(df.columns)}")
    
except Exception as e:
    print("❌ Failed to fetch data:", e)
    exit(1)

if df.empty:
    print("⚠️ No data found. Skipping embedding.")
    exit(0)

# --- Check existing embeddings ---
embedding_table_name = f"{source_table}_vectors"
existing_embedded_ids = set()

print(f"\n🔍 Checking existing embeddings in {embedding_table_name}...")
try:
    with engine.connect() as conn:
        # ตรวจสอบว่ามี embedding table หรือไม่
        check_table = conn.execute(text(f"SHOW TABLES LIKE '{embedding_table_name}'"))
        if check_table.fetchone():
            # ดึง IDs ที่ embed แล้ว
            embedded_result = conn.execute(text(f"SELECT id FROM {embedding_table_name}"))
            existing_embedded_ids = set(row[0] for row in embedded_result.fetchall())
            print(f"📊 Found {len(existing_embedded_ids)} existing embeddings")
        else:
            print(f"📋 No existing embedding table found")
            
except Exception as e:
    print(f"⚠️ Error checking embeddings: {e}")

# กรองข้อมูลที่ยังไม่ได้ embed
if existing_embedded_ids:
    df_to_process = df[~df['id'].isin(existing_embedded_ids)]
    print(f"🔄 Will process {len(df_to_process)} new records (skipping {len(existing_embedded_ids)} existing)")
else:
    df_to_process = df
    print(f"🔄 Will process all {len(df_to_process)} records")

if df_to_process.empty:
    print("✅ All records are already embedded. Nothing to do.")
    exit(0)

# --- Call embedding API ---
def embed_text(texts):
    """สร้าง embeddings สำหรับ texts โดยเรียก API"""
    embeddings = []
    for i, t in enumerate(texts):
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": EMBEDDING_MODEL,
            "prompt": str(t)  # ใช้ prompt แทน input และแปลงเป็น string
        }
        try:
            print(f"🚀 Processing {i+1}/{len(texts)}: '{t}' -> {EMBEDDING_API_URL}")
            response = requests.post(EMBEDDING_API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "embedding" in result and result["embedding"]:
                    embeddings.append(result["embedding"])
                    print(f"✅ Got embedding with {len(result['embedding'])} dimensions")
                else:
                    print("⚠️ No embedding returned in response")
                    embeddings.append(None)
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                embeddings.append(None)
                
        except requests.exceptions.Timeout:
            print("⏰ Request timeout")
            embeddings.append(None)
        except Exception as e:
            print(f"❌ Embedding API error: {e}")
            embeddings.append(None)
            
    return embeddings

# --- Prepare data ---
texts = df_to_process["name"].tolist()
ids = df_to_process["id"].tolist()

# แก้ไขการจัดการ date - ป้องกัน callable issue
df_copy = df_to_process.copy()
if 'signup_date' in df_copy.columns:
    df_copy["signup_date"] = df_copy["signup_date"].apply(
        lambda d: d.isoformat() if hasattr(d, 'isoformat') else str(d)
    )
metadatas = df_copy.drop(columns=["name"]).to_dict(orient="records")

print(f"\n🔄 Processing {len(texts)} customer names for embeddings...")

# --- Get embeddings ---
vectors = embed_text(texts)

# --- Create embedding table if not exists ---
print(f"\n🔨 Creating {embedding_table_name} table if not exists...")
try:
    with engine.connect() as conn:
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
        print(f"✅ {embedding_table_name} table ready")
except Exception as e:
    print(f"❌ Failed to create table: {e}")
    exit(1)

# --- Insert into embedding table ---
print(f"\n💾 Inserting embeddings into {embedding_table_name}...")
inserted = 0
failed = 0

# ใช้ transaction เพื่อความปลอดภัย
try:
    with engine.begin() as conn:  # ใช้ begin() เพื่อ auto-commit
        for _id, name, vector, metadata in zip(ids, texts, vectors, metadatas):
            if vector is None:
                print(f"⚠️ Skipped id={_id} due to missing vector")
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
                        "name": str(name)[:255],  # ตัดชื่อให้ไม่เกิน 255 ตัวอักษร
                        "embedding": vector_bytes, 
                        "metadata": json.dumps(metadata, ensure_ascii=False)
                    }
                )
                inserted += 1
                print(f"✅ Inserted id={_id}: '{name}' (vector dim: {len(vector)})")
                
            except Exception as e:
                print(f"❌ Insert failed for id={_id}: {e}")
                failed += 1

    print(f"\n🎯 Summary:")
    print(f"✅ Successfully inserted: {inserted} embeddings")
    print(f"❌ Failed: {failed} records")
    print(f"📊 Total processed: {len(texts)} records")

except Exception as e:
    print(f"❌ Transaction failed: {e}")
    exit(1)

# --- Verify insertion ---
print(f"\n🔍 Verifying data in {embedding_table_name} table...")
try:
    with engine.connect() as conn:
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {embedding_table_name}"))
        total_count = count_result.scalar()
        
        print(f"📊 Total embeddings in table: {total_count}")
        
        # แสดงตัวอย่างข้อมูล
        sample_result = conn.execute(text(f"""
            SELECT id, name, LENGTH(embedding) as embedding_size, 
                   JSON_EXTRACT(metadata, '$.id') as original_id
            FROM {embedding_table_name} 
            ORDER BY created_at DESC 
            LIMIT 5
        """))
        
        sample_data = sample_result.fetchall()
        print("\n📋 Sample data:")
        for row in sample_data:
            print(f"  ID: {row[0]}, Name: '{row[1]}', Embedding Size: {row[2]} bytes")
            
        print(f"\n🎉 Embedding process completed successfully!")
        print(f"💾 Data saved to table: {embedding_table_name}")
        
except Exception as e:
    print(f"❌ Verification failed: {e}")
