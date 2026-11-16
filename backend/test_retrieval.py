
from rag import retrieve_context

test_questions = [
    "What is YOLO and what problem does it solve?",
    "Explain the architecture of YOLO.",
    "How does YOLO perform object detection?",
    "What are the advantages of YOLO?",
    "What are the limitations of YOLO?"
]

print("\n========== RETRIEVAL EVALUATION ==========\n")

for question in test_questions:

    print(f"\nQUESTION: {question}")

    try:
        context, sources = retrieve_context(
            question,
            filename="YOLO_CVPR2016.pdf",
            top_k=3
        )

        print("\nRETRIEVED SOURCES:")

        for source in sources:
            print(
                f"- {source['filename']} | Page {source['page']}"
            )

        print("\nRETRIEVED CONTEXT:")
        print(context[:1000])

        print("\n" + "-" * 60)

    except Exception as error:
        print(f"Retrieval failed: {error}")

print("\nEvaluation completed.")
