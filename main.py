import os
import pandas as pd
import numpy as np
import base64
import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError
from dotenv import load_dotenv

# โหลดค่า env
load_dotenv()

TIDB_URL = os.getenv("TIDB_URL")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47:11434/api/embed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "dengcao/Qwen3-Embedding-8B:Q4_K_M")

print(f"🔎 Raw TIDB_URL = {repr(TIDB_URL)}")
print(f"📦 Base64 of TIDB_URL = {base64.b64encode(TIDB_URL.encode()).decode()}")
print(f"📡 EMBEDDING_API_URL = {EMBEDDING_API_URL}")
print(f"📦 EMBEDDING_MODEL = {EMBEDDING_MODEL}")

# --- Connect to TiDB ---
print("\n🔧 Environment Setup")
try:
    engine = create_engine(TIDB_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Connected to TiDB:", result.scalar())
except ArgumentError as e:
    print("❌ Invalid TIDB_URL format:", e)
    exit(1)
except Exception as e:
    print("❌ DB connection error:", e)
    exit(1)

# --- Load data ---
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
def embed_text(texts):
    url = EMBEDDING_API_URL
    headers = {"Content-Type": "application/json"}

    embeddings = []
    for t in texts:
        payload = {
            "text": t,          # ✅ ไม่ใช้ "texts"
            "truncate": True
        }

        try:
            print(f"📨 Sending text: {t}")
            res = requests.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

            if "embedding" in data and isinstance(data["embedding"], list):
                embeddings.append(data["embedding"])
            else:
                print(f"⚠️ Invalid response: {data}")
                embeddings.append(None)

        except Exception as e:
            print(f"❌ Error while embedding text '{t}':", e)
            embeddings.append(None)

    return embeddings


# --- Prepare for insert ---
texts = df["name"].tolist()
ids = df["id"].tolist()
metadatas = df.drop(columns=["name"]).to_dict(orient="records")

vectors = embed_text(texts, EMBEDDING_MODEL)

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
