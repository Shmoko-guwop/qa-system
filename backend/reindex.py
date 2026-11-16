
import os

from document_processor import process_pdf


DOCUMENTS_DIR = "documents"


def reindex_documents():

    if not os.path.exists(DOCUMENTS_DIR):
        print("Documents directory does not exist.")
        return

    pdf_files = [
        filename
        for filename in os.listdir(DOCUMENTS_DIR)
        if filename.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print("No PDF documents found.")
        return

    print(f"\nFound {len(pdf_files)} PDF documents.")

    successful = 0
    failed = 0

    for filename in pdf_files:

        file_path = os.path.join(
            DOCUMENTS_DIR,
            filename
        )

        print("\n" + "=" * 60)

        try:

            result = process_pdf(file_path)

            print("\nRe-indexing successful!")
            print("Filename:", result["filename"])
            print("Pages:", result["pages_processed"])
            print("Chunks:", result["chunks_stored"])

            successful += 1

        except Exception as e:

            print(f"\nFailed to re-index {filename}: {e}")

            failed += 1

    print("\n" + "=" * 60)
    print("RE-INDEXING SUMMARY")
    print("=" * 60)

    print("Successful:", successful)
    print("Failed:", failed)


if __name__ == "__main__":
    reindex_documents()
