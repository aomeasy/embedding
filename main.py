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

# โหลดค่าจาก .env
load_dotenv()

# --- Config (แก้ไข URL และ Port) ---
TIDB_URL = os.getenv("TIDB_URL")
# ✅ แก้ไข URL ให้ถูกต้องตามที่ทดสอบได้แล้ว
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")  # ✅ ใช้ model ที่ทดสอบแล้ว

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

# --- Load customer data ---
print("\n📥 Fetching data from customers table...")
try:
    df = pd.read_sql("SELECT id, name, email, age, city, signup_date FROM customers", con=engine)
    print(f"🔢 Found {len(df)} rows")
except Exception as e:
    print("❌ Failed to fetch data:", e)
    exit(1)

if df.empty:
    print("⚠️ No data found. Skipping embedding.")
    exit(0)

# --- Call embedding API (แก้ไขให้ถูกต้อง) ---
def embed_text(texts):
    embeddings = []
    for i, t in enumerate(texts):
        headers = {"Content-Type": "application/json"}
        # ✅ แก้ไข payload ให้ถูกต้องตาม API ที่ทดสอบแล้ว
        payload = {
            "model": EMBEDDING_MODEL,
            "prompt": str(t)  # ✅ ใช้ prompt แทน input และแปลงเป็น string
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
texts = df["name"].tolist()
ids = df["id"].tolist()
# ✅ แก้ไขการจัดการ date
df_copy = df.copy()
df_copy["signup_date"] = df_copy["signup_date"].apply(
    lambda d: d.isoformat() if isinstance(d, (date, pd.Timestamp)) else str(d)
)
metadatas = df_copy.drop(columns=["name"]).to_dict(orient="records")

print(f"\n🔄 Processing {len(texts)} customer names for embeddings...")

# --- Get embeddings ---
vectors = embed_text(texts)

# --- Insert into customer_vectors (แก้ไขการ insert) ---
print("\n💾 Inserting embeddings into customer_vectors...")
inserted = 0
failed = 0

# ✅ ใช้ transaction เพื่อความปลอดภัย
with engine.begin() as conn:  # ใช้ begin() แทน connect() เพื่อ auto-commit
    for _id, name, vector, metadata in zip(ids, texts, vectors, metadatas):
        if vector is None:
            print(f"⚠️ Skipped id={_id} due to missing vector")
            failed += 1
            continue
            
        try:
            # ✅ แปลง vector เป็น bytes อย่างถูกต้อง
            vector_array = np.array(vector, dtype=np.float32)
            vector_bytes = vector_array.tobytes()
            
            # ✅ แก้ไข SQL syntax สำหรับ MySQL/TiDB
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
                    "name": str(name)[:100],  # ✅ ตัดชื่อให้ไม่เกิน 100 ตัวอักษร
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

# --- Verify insertion ---
print(f"\n🔍 Verifying data in customer_vectors table...")
try:
    with engine.connect() as conn:
        count_result = conn.execute(text("SELECT COUNT(*) FROM customer_vectors"))
        total_count = count_result.scalar()
        print(f"📊 Total records in customer_vectors: {total_count}")
        
        # แสดงตัวอย่าง record แรก
        sample_result = conn.execute(text("SELECT id, name, LENGTH(embedding) as embedding_size FROM customer_vectors LIMIT 3"))
        print("\n📋 Sample records:")
        for row in sample_result:
            print(f"  ID: {row[0]}, Name: '{row[1]}', Embedding size: {row[2]} bytes")
            
except Exception as e:
    print(f"❌ Verification failed: {e}")

print("\n🎉 Process completed!")
