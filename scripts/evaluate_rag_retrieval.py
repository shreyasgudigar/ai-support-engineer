import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.retriever import search_knowledge

INPUT_FILE = BASE_DIR / "data" / "processed" / "rag_evaluation.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "rag_retrieval_results.csv"

results = []
recalls_at_3 = []
recalls_at_5 = []
complete_at_5 = []
unsupported_retrievals = 0

with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as file:
    test_cases = list(csv.DictReader(file))

print(f"Running retrieval evaluation on {len(test_cases)} questions...\n")

for case in test_cases:
    question = case["question"]
    expected_sources = [
        source.strip()
        for source in case["expected_sources"].split(";")
        if source.strip()
    ]

    retrieved = search_knowledge(question, top_k=5)

    titles = [doc["title"] for doc in retrieved]
    titles_at_3 = titles[:3]

    matched_at_3 = [
        source for source in expected_sources
        if source in titles_at_3
    ]
    matched_at_5 = [
        source for source in expected_sources
        if source in titles
    ]

    if expected_sources:
        recall_3 = len(matched_at_3) / len(expected_sources)
        recall_5 = len(matched_at_5) / len(expected_sources)

        recalls_at_3.append(recall_3)
        recalls_at_5.append(recall_5)
        complete_at_5.append(int(recall_5 == 1.0))
    else:
        recall_3 = ""
        recall_5 = ""
        unsupported_retrievals += int(len(retrieved) > 0)

    retrieved_details = " | ".join(
        f"{doc['title']} ({doc['similarity']:.4f})"
        for doc in retrieved
    )

    results.append({
        "case_id": case["case_id"],
        "question": question,
        "expected_behavior": case["expected_behavior"],
        "expected_sources": "; ".join(expected_sources),
        "retrieved_sources": retrieved_details,
        "matched_sources_at_3": "; ".join(matched_at_3),
        "matched_sources_at_5": "; ".join(matched_at_5),
        "recall_at_3": recall_3,
        "recall_at_5": recall_5,
    })

    print(
        f"{case['case_id']} | "
        f"Expected: {len(expected_sources)} | "
        f"Found@5: {len(matched_at_5)}"
    )

fieldnames = list(results[0].keys())

with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print("\n" + "=" * 55)
print("RETRIEVAL EVALUATION SUMMARY")
print("=" * 55)

if recalls_at_3:
    print(f"Mean Recall@3: {sum(recalls_at_3) / len(recalls_at_3):.2%}")
    print(f"Mean Recall@5: {sum(recalls_at_5) / len(recalls_at_5):.2%}")
    print(f"Complete expected sources at @5: {sum(complete_at_5)}/{len(complete_at_5)}")

print(
    "Unsupported questions returning documents: "
    f"{unsupported_retrievals}/"
    f"{sum(1 for r in results if not r['expected_sources'])}"
)

print(f"\nDetailed results saved to: {OUTPUT_FILE}")
