import os
import pandas as pd
import numpy as np
import requests
import json
from sqlalchemy import create_engine
from dotenv import load_dotenv

# โหลด config จาก .env
load_dotenv()
TIDB_URL = os.getenv("TIDB_URL")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://209.15.123.47")

# เชื่อมต่อ TiDB
engine = create_engine(TIDB_URL)

# ดึงข้อมูลจากตาราง customers
df = pd.read_sql("SELECT id, name, email, age, city, signup_date FROM customers", con=engine)

# ฟังก์ชันเรียก embedding API
def embed_text(texts):
    url = f"{EMBEDDING_API_URL}/embed"
    headers = {"Content-Type": "application/json"}
    payload = {
        "texts": texts,
        "truncate": True
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["embeddings"]
    else:
        print("❌ Error from embedding API:", response.text)
        return [None] * len(texts)

# เตรียม batch ข้อมูล
texts = df["name"].tolist()
ids = df["id"].tolist()
metadatas = df.drop(columns=["name"]).to_dict(orient="records")

# เรียก embeddings
vectors = embed_text(texts)

# Insert ลง customer_vectors
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

print("✅ Embedding inserted into customer_vectors")
