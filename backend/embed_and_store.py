
import os
from dotenv import load_dotenv
from google import genai
import chromadb

from ingest import extract_text, chunk_text

# Load environment variables
load_dotenv()

# Initialize Gemini
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

embedding_model = os.getenv("EMBEDDING_MODEL")

# Initialize persistent ChromaDB
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Extract PDF text
pages = extract_text("documents/sample.pdf")

all_chunks = []
all_metadata = []

# Generate chunks and preserve metadata
for page in pages:

    chunks = chunk_text(page["text"])

    for chunk in chunks:

        all_chunks.append(chunk)

        all_metadata.append({
            "page": page["page"],
            "source": "sample.pdf"
        })

print("Total chunks:", len(all_chunks))

# Generate one embedding per chunk
embeddings = []

for i, chunk in enumerate(all_chunks):

    response = client.models.embed_content(
        model=embedding_model,
        contents=chunk,
        config={
            "output_dimensionality": 768
        }
    )

    embedding = response.embeddings[0].values

    embeddings.append(embedding)

    print(f"Embedded chunk {i+1}/{len(all_chunks)}")

# Validate data lengths
assert len(all_chunks) == len(embeddings)
assert len(all_chunks) == len(all_metadata)

print("\nValidation:")
print("Chunks:", len(all_chunks))
print("Embeddings:", len(embeddings))
print("Metadata:", len(all_metadata))

# Generate unique IDs
ids = [
    f"sample_pdf_chunk_{i}"
    for i in range(len(all_chunks))
]

# Store in ChromaDB
collection.upsert(
    ids=ids,
    documents=all_chunks,
    embeddings=embeddings,
    metadatas=all_metadata
)

print("\nSuccessfully stored chunks in ChromaDB!")
print("Total stored documents:", collection.count())
