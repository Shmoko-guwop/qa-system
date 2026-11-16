
from unittest.mock import patch

from rag import retrieve_context, generate_answer, rag_pipeline


def test_generate_answer_without_context():

    answer = generate_answer(
        "Explain transformers",
        ""
    )

    assert "couldn't find sufficiently relevant information" in answer


@patch("rag.client.models.generate_content")
def test_generate_answer_success(mock_generate):

    mock_generate.return_value.text = (
        "Autoencoders learn compressed representations."
    )

    answer = generate_answer(
        "What are autoencoders?",
        "Autoencoders learn compressed representations."
    )

    assert answer == (
        "Autoencoders learn compressed representations."
    )

    mock_generate.assert_called_once()


@patch("rag.client.models.generate_content")
def test_generate_answer_retries_on_503(mock_generate):

    mock_generate.side_effect = [
        Exception("503 Service Unavailable"),
        type(
            "Response",
            (),
            {"text": "Recovered answer"}
        )()
    ]

    with patch("rag.time.sleep"):
        answer = generate_answer(
            "Explain autoencoders",
            "Autoencoders learn representations."
        )

    assert answer == "Recovered answer"
    assert mock_generate.call_count == 2


@patch("rag.retrieve_context")
@patch("rag.generate_answer")
def test_rag_pipeline(mock_generate, mock_retrieve):

    mock_retrieve.return_value = (
        "Relevant document content",
        [
            {
                "filename": "sample.pdf",
                "page": 2,
                "distance": 0.2
            }
        ]
    )

    mock_generate.return_value = "This is a test answer."

    result = rag_pipeline(
        "What is an autoencoder?"
    )

    assert result["answer"] == "This is a test answer."

    assert result["sources"] == [
        {
            "filename": "sample.pdf",
            "page": 2,
            "distance": 0.2
        }
    ]


@patch("rag.collection.query")
@patch("rag.collection.count")
@patch("rag.client.models.embed_content")
def test_retrieve_context_filters_irrelevant_chunks(
    mock_embed,
    mock_count,
    mock_query
):

    mock_count.return_value = 2

    mock_embed.return_value.embeddings = [
        type(
            "Embedding",
            (),
            {
                "values": [0.1] * 768
            }
        )()
    ]

    mock_query.return_value = {
        "documents": [
            [
                "Autoencoders learn compressed representations.",
                "Unrelated information about another topic."
            ]
        ],
        "metadatas": [
            [
                {
                    "source": "sample.pdf",
                    "page": 3
                },
                {
                    "source": "sample.pdf",
                    "page": 5
                }
            ]
        ],
        "distances": [
            [0.2, 0.8]
        ]
    }

    context, sources = retrieve_context(
        "What are autoencoders?"
    )

    assert "Autoencoders" in context

    assert "Unrelated information" not in context

    assert len(sources) == 1

    assert sources[0]["filename"] == "sample.pdf"
    assert sources[0]["page"] == 3
    assert sources[0]["distance"] == 0.2


@patch("rag.collection.query")
@patch("rag.collection.count")
@patch("rag.client.models.embed_content")
def test_retrieve_context_returns_empty_when_all_chunks_irrelevant(
    mock_embed,
    mock_count,
    mock_query
):

    mock_count.return_value = 1

    mock_embed.return_value.embeddings = [
        type(
            "Embedding",
            (),
            {
                "values": [0.1] * 768
            }
        )()
    ]

    mock_query.return_value = {
        "documents": [
            ["Unrelated document content."]
        ],
        "metadatas": [
            [
                {
                    "source": "sample.pdf",
                    "page": 5
                }
            ]
        ],
        "distances": [
            [0.9]
        ]
    }

    context, sources = retrieve_context(
        "Explain quantum computing."
    )

    assert context == ""
    assert sources == []
