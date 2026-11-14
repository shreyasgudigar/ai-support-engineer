
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "raw" / "knowledge_base.csv"

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")


def main():
    print("Loading embedding model...")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Reading knowledge-base CSV...")

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
        documents = list(csv.DictReader(file))

    if not documents:
        raise ValueError("Knowledge-base CSV is empty.")

    for document in documents:
        if not document.get("title") or not document.get("content"):
            raise ValueError("Every document needs a title and content.")

    texts = [
        f"{doc['title']}. {doc['content']}"
        for doc in documents
    ]

    print(f"Generating embeddings for {len(texts)} documents...")

    embeddings = model.encode(texts)

    if embeddings.shape[1] != 384:
        raise ValueError("Expected 384-dimensional embeddings.")

    print("Connecting to PostgreSQL...")

    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            for document, embedding in zip(documents, embeddings):
                title = document["title"]
                content = document["content"]

                # Update existing articles instead of inserting duplicates.
                cursor.execute(
                    """
                    SELECT id
                    FROM knowledge_documents
                    WHERE title = %s
                    ORDER BY id
                    LIMIT 1
                    """,
                    (title,),
                )

                existing = cursor.fetchone()

                embedding_value = (
                    "[" + ",".join(map(str, embedding.tolist())) + "]"
                )

                if existing:
                    cursor.execute(
                        """
                        UPDATE knowledge_documents
                        SET content = %s,
                            embedding = %s::vector
                        WHERE id = %s
                        """,
                        (content, embedding_value, existing[0]),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO knowledge_documents
                            (title, content, embedding)
                        VALUES (%s, %s, %s::vector)
                        """,
                        (title, content, embedding_value),
                    )

    print(f"Successfully ingested {len(documents)} knowledge documents!")


if __name__ == "__main__":
    main()
