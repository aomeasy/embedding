import os
import pandas as pd
import numpy as np
import base64
import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError
from dotenv import load_dotenv

# โหลดค่าจาก .env
load_dotenv()

# --- Config ---
TIDB_URL = os.getenv("TIDB_URL")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47/embed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-base-en-v1.5")  # optional

tidb_url = os.getenv("TIDB_URL")

print("🔎 Raw TIDB_URL =", repr(tidb_url))  # แสดง raw string
print("📦 Base64 of TIDB_URL =", base64.b64encode(tidb_url.encode()).decode())

try:
    engine = create_engine(TIDB_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Connected to TiDB:", result.scalar())
except ArgumentError as e:
    print("❌ Invalid TIDB_URL format:", e)
except Exception as e:
    print("❌ Other error:", e)
    
# --- Connect TiDB ---
engine = create_engine(TIDB_URL)

# --- ดึงข้อมูลจากตาราง customers ---
query = "SELECT id, name, email, age, city, signup_date FROM customers"
df = pd.read_sql(query, con=engine)

# --- สร้างฟังก์ชันเรียก embedding API ---
def embed_text(texts, model_name=None):
    url = EMBEDDING_API_URL
    headers = {"Content-Type": "application/json"}
    payload = {
        "texts": texts,
        "truncate": True
    }
    # ถ้ามีการระบุ model → ส่งเข้า payload
    if model_name:
        payload["model"] = model_name

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["embeddings"]
    else:
        print("❌ ERROR:", response.status_code, response.text)
        return [None] * len(texts)

# --- เตรียมข้อมูลที่ต้องการ embedding ---
texts = df["name"].tolist()
ids = df["id"].tolist()
metadatas = df.drop(columns=["name"]).to_dict(orient="records")

# --- เรียก embedding จาก API ---
vectors = embed_text(texts, EMBEDDING_MODEL)

# --- Insert กลับเข้า TiDB ที่ตาราง customer_vectors ---
with engine.connect() as conn:
    for _id, name, vector, metadata in zip(ids, texts, vectors, metadatas):
        if vector is None:
            continue
        vector_bytes = np.array(vector, dtype=np.float32).tobytes()

        conn.execute(
            """
            INSERT INTO customer_vectors (id, name, embedding, metadata)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              name = VALUES(name),
              embedding = VALUES(embedding),
              metadata = VALUES(metadata)
            """,
            (_id, name, vector_bytes, json.dumps(metadata))
        )

print("✅ Done! Embeddings inserted into customer_vectors.")
