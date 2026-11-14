
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

# Use the same model that generated the stored embeddings.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def search_knowledge(query: str, top_k: int = 3) -> list[dict]:
    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10.")

    # Convert the customer question into a 384-dimensional vector.
    query_embedding = embedding_model.encode(query).tolist()

    embedding_value = (
        "[" + ",".join(map(str, query_embedding)) + "]"
    )

    sql = """
        SELECT
            id,
            title,
            content,
            1 - (embedding <=> %s::vector) AS similarity
        FROM knowledge_documents
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """

    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (embedding_value, embedding_value, top_k),
            )
            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "similarity": round(float(row[3]), 4),
        }
        for row in rows
    ]
