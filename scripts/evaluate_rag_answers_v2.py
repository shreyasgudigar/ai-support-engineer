import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.generator import generate_support_answer

INPUT_FILE = BASE_DIR / "data" / "processed" / "rag_evaluation.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "rag_answer_results_v2.csv"

with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as file:
    test_cases = list(csv.DictReader(file))

fieldnames = [
    "case_id",
    "question",
    "expected_behavior",
    "expected_sources",
    "expected_facts",
    "generated_answer",
    "retrieved_sources",
    "needs_review",
    "generation_status",
]

print(f"Evaluating {len(test_cases)} customer questions...")
print("This may take several minutes because each question calls Ollama.\n")

completed = 0
failed = 0

with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    file.flush()

    for case in test_cases:
        case_id = case["case_id"]
        question = case["question"]

        print(f"[{completed + failed + 1}/{len(test_cases)}] {case_id}: {question}", flush=True)

        try:
            result = generate_support_answer(question)

            sources = " | ".join(
                f"{source['title']} ({source['similarity']:.4f})"
                for source in result.get("sources", [])
            )

            answer = result.get("answer", "")
            needs_review = result.get("needs_review", True)

            row = {
                "case_id": case_id,
                "question": question,
                "expected_behavior": case["expected_behavior"],
                "expected_sources": case["expected_sources"],
                "expected_facts": case["expected_facts"],
                "generated_answer": answer,
                "retrieved_sources": sources,
                "needs_review": needs_review,
                "generation_status": "success",
            }

            completed += 1

        except Exception as error:
            row = {
                "case_id": case_id,
                "question": question,
                "expected_behavior": case["expected_behavior"],
                "expected_sources": case["expected_sources"],
                "expected_facts": case["expected_facts"],
                "generated_answer": f"ERROR: {error}",
                "retrieved_sources": "",
                "needs_review": True,
                "generation_status": "error",
            }

            failed += 1

        writer.writerow(row)
        file.flush()

        print(f"    Status: {row['generation_status']}")
        print(f"    Review required: {row['needs_review']}\n")

print("=" * 55)
print("ANSWER GENERATION EVALUATION COMPLETE")
print("=" * 55)
print(f"Successful: {completed}")
print(f"Failed: {failed}")
print(f"Total: {len(test_cases)}")
print(f"\nResults saved to: {OUTPUT_FILE}")
