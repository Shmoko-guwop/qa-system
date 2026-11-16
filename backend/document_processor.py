
import os
import time

from dotenv import load_dotenv
from google import genai
import chromadb

from ingest import extract_text, chunk_text


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

embedding_model = os.getenv("EMBEDDING_MODEL")


# --------------------------------------------------
# CHROMADB INITIALIZATION
# --------------------------------------------------

chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# PROCESS PDF
# --------------------------------------------------

def process_pdf(file_path):

    filename = os.path.basename(file_path)

    print(f"\nProcessing PDF: {filename}")

    # Extract text from PDF
    pages = extract_text(file_path)

    if not pages:
        raise ValueError(
            "No extractable text found in PDF."
        )

    print(f"Pages extracted: {len(pages)}")

    # Generate chunks and metadata
    all_chunks = []
    all_metadata = []

    for page in pages:

        chunks = chunk_text(page["text"])

        for chunk in chunks:

            all_chunks.append(chunk)

            all_metadata.append({
                "page": page["page"],
                "source": filename
            })

    print(f"Total chunks: {len(all_chunks)}")

    if not all_chunks:
        raise ValueError("No text chunks generated.")

    # --------------------------------------------------
    # GENERATE EMBEDDINGS
    # --------------------------------------------------

    embeddings = []

    for i, chunk in enumerate(all_chunks):

        while True:

            try:

                response = client.models.embed_content(
                    model=embedding_model,
                    contents=chunk,
                    config={
                        "output_dimensionality": 768
                    }
                )

                embedding = response.embeddings[0].values

                embeddings.append(embedding)

                print(
                    f"Embedded {i + 1}/{len(all_chunks)} chunks"
                )

                time.sleep(0.7)

                break

            except Exception as e:

                if "429" in str(e):

                    print(
                        "Rate limit reached. Waiting 50 seconds..."
                    )

                    time.sleep(50)

                else:
                    raise

    # --------------------------------------------------
    # VALIDATE DATA
    # --------------------------------------------------

    if not (
        len(all_chunks)
        == len(embeddings)
        == len(all_metadata)
    ):
        raise ValueError(
            "Chunks, embeddings and metadata counts do not match."
        )

    print("\nEmbedding validation successful!")

    # --------------------------------------------------
    # REPLACE EXISTING INDEX FOR THIS PDF
    # --------------------------------------------------

    ids = [
        f"{filename}_chunk_{i}"
        for i in range(len(all_chunks))
    ]

    # Delete old chunks only after new embeddings succeed
    collection.delete(
        where={"source": filename}
    )

    # Store the newly generated chunks
    collection.add(
        ids=ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadata
    )

    print("\nSuccessfully indexed PDF!")

    print(
        "Total stored chunks:",
        collection.count()
    )

    return {
        "filename": filename,
        "pages_processed": len(pages),
        "chunks_stored": len(all_chunks)
    }
