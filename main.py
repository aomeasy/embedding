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
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embeddings")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-base-en-v1.5")

print("🔎 Raw TIDB_URL =", repr(TIDB_URL))
print("📦 Base64 of TIDB_URL =", base64.b64encode(TIDB_URL.encode()).decode())
print("📡 EMBEDDING_API_URL =", EMBEDDING_API_URL)
print("📦 EMBEDDING_MODEL =", EMBEDDING_MODEL)


print("\n🔧 Environment Setup")
print("🔎 Raw TIDB_URL =", repr(TIDB_URL))
if TIDB_URL:
    print("📦 Base64 of TIDB_URL =", base64.b64encode(TIDB_URL.encode()).decode())
else:
    print("❌ TIDB_URL is not set! Check your environment variables.")
    exit(1)

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

# --- Call embedding API ---
def embed_text(texts, model_name=None):
    url = EMBEDDING_API_URL
    headers = {"Content-Type": "application/json"}
    payload = {"input": texts}  # ตามรูปแบบของ nomic embed API
    if model_name:
        payload["model"] = model_name

    try:
        print(f"🚀 Sending {len(texts)} texts to embedding API...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print("✅ Embedding received")
        return data.get("data", [])
    except Exception as e:
        print("❌ Embedding API error:", e)
        return [None] * len(texts)

# --- Prepare data ---
texts = df["name"].tolist()
ids = df["id"].tolist()
metadatas = df.drop(columns=["name"]).to_dict(orient="records")

# --- Get embeddings ---
vectors_raw = embed_text(texts, EMBEDDING_MODEL)

# --- Parse nomic format to raw vectors ---
vectors = [item["embedding"] if item else None for item in vectors_raw]

# --- Insert into customer_vectors ---
print("\n💾 Inserting embeddings into customer_vectors...")
inserted = 0
with engine.connect() as conn:
    for _id, name, vector, metadata in zip(ids, texts, vectors, metadatas):
        if vector is None:
            print(f"⚠️ Skipped id={_id} due to missing vector")
            continue
        try:
            vector_bytes = np.array(vector, dtype=np.float32).tobytes()
            conn.execute(
                text("""
                    INSERT INTO customer_vectors (id, name, embedding, metadata)
                    VALUES (:id, :name, :embedding, :metadata)
                    ON DUPLICATE KEY UPDATE
                      name = VALUES(name),
                      embedding = VALUES(embedding),
                      metadata = VALUES(metadata)
                """),
                {"id": _id, "name": name, "embedding": vector_bytes, "metadata": json.dumps(metadata)}
            )
            inserted += 1
        except Exception as e:
            print(f"❌ Insert failed for id={_id}:", e)

print(f"\n✅ Done! {inserted} embeddings inserted into customer_vectors.")
