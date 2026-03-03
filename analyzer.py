from difflib import SequenceMatcher
from db import fetch_all, update_relevance


def calculate_similarity(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio()


def analyze_repo():
    records = fetch_all()

    for record in records:
        id = record[0]
        response = record[2]
        file_path = record[3]

        if not file_path:
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            score = calculate_similarity(response, file_content)

            is_relevant = score > 0.4

            update_relevance(id, score, is_relevant)

        except:
            continue

    print("Analysis complete.")


def generate_report():
    records = fetch_all()

    total = len(records)
    relevant = len([r for r in records if r[7] == 1])

    print("\n====== AI CONTRIBUTION REPORT ======")
    print(f"Total Prompts: {total}")
    print(f"Relevant Prompts: {relevant}")
    print(f"Irrelevant Prompts: {total - relevant}")
    print("====================================\n")