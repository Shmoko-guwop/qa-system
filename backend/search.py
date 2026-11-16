
import os
from dotenv import load_dotenv
from google import genai
import chromadb

load_dotenv()

# Initialize Gemini
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

embedding_model = os.getenv("EMBEDDING_MODEL")

# Connect to existing ChromaDB
chroma_client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = chroma_client.get_collection(
    name="documents"
)


def search_documents(question, top_k=3):

    # Convert question into an embedding
    response = client.models.embed_content(
        model=embedding_model,
        contents=question,
        config={
            "output_dimensionality": 768
        }
    )

    query_embedding = response.embeddings[0].values

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Display retrieved results
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i in range(len(documents)):

        print(f"\nResult {i+1}")
        print("-------------------------")
        print("Page:", metadatas[i]["page"])
        print("Source:", metadatas[i]["source"])
        print("Distance:", distances[i])
        print("Content:", documents[i])

    return results


if __name__ == "__main__":

    question = input("Ask a question about your PDF: ")

    search_documents(question)
