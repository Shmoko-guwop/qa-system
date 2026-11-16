
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_documents_endpoint():
    response = client.get("/documents")

    assert response.status_code == 200
    assert "documents" in response.json()
    assert "total_documents" in response.json()


def test_empty_question():
    response = client.post(
        "/ask",
        json={"question": ""}
    )

    assert response.status_code == 422


def test_whitespace_question():
    response = client.post(
        "/ask",
        json={"question": "     "}
    )

    assert response.status_code == 422


def test_question_too_long():
    response = client.post(
        "/ask",
        json={"question": "a" * 1001}
    )

    assert response.status_code == 422


def test_invalid_filename():
    response = client.post(
        "/ask",
        json={
            "question": "Explain this document",
            "filename": "../sample.pdf"
        }
    )

    assert response.status_code == 422


def test_non_pdf_upload():
    response = client.post(
        "/upload",
        files={
            "file": (
                "test.txt",
                b"This is not a PDF",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400


def test_fake_pdf_upload():
    response = client.post(
        "/upload",
        files={
            "file": (
                "fake.pdf",
                b"This is not actually a PDF",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
