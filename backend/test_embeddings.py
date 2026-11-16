
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = os.getenv("EMBEDDING_MODEL")

text = "RAG retrieves relevant information from documents before generating an answer."

response = client.models.embed_content(
    model=model,
    contents=text,
    config=types.EmbedContentConfig(
        output_dimensionality=768
    )
)

embedding = response.embeddings[0].values

print("Embedding generated successfully!")
print("Embedding dimensions:", len(embedding))
print("First 5 values:", embedding[:5])
