
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = os.getenv("GEMINI_MODEL")

for attempt in range(3):
    try:
        print(f"Attempt {attempt + 1}...")

        response = client.models.generate_content(
            model=model,
            contents="Explain RAG in simple terms."
        )

        print("\nGemini Response:\n")
        print(response.text)
        break

    except ServerError as e:
        if attempt == 2:
            print("Gemini is temporarily unavailable.")
            print(e)
        else:
            wait = 5 * (2 ** attempt)
            print(f"Server unavailable. Retrying in {wait} seconds...")
            time.sleep(wait)
