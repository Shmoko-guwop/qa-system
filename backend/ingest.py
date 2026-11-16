
from pypdf import PdfReader


# --------------------------------------------------
# EXTRACT TEXT FROM PDF
# --------------------------------------------------

def extract_text(pdf_path):

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        if text.strip():

            # Normalize whitespace
            text = text.replace("\x00", "")
            text = text.strip()

            pages.append({
                "text": text,
                "page": page_number
            })

    return pages


# --------------------------------------------------
# PARAGRAPH-AWARE TEXT CHUNKING
# --------------------------------------------------

def chunk_text(text, chunk_size=1000, overlap=150):

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        # Handle paragraphs larger than chunk size
        if len(paragraph) > chunk_size:

            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            start = 0

            while start < len(paragraph):

                end = start + chunk_size

                chunk = paragraph[start:end].strip()

                if chunk:
                    chunks.append(chunk)

                start += chunk_size - overlap

            continue

        # Add paragraph if it fits
        if len(current_chunk) + len(paragraph) <= chunk_size:

            current_chunk += "\n" + paragraph

        else:

            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # Preserve some overlap from previous chunk
            previous_text = current_chunk[-overlap:] if current_chunk else ""

            current_chunk = previous_text + "\n" + paragraph

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
