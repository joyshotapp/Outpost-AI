"""Tests for Whisper video transcription task"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.tasks.video import transcribe_video_with_whisper


def test_transcribe_video_with_whisper_success():
    mock_video = SimpleNamespace(
        id=101,
        supplier_id=22,
        title="Factory Tour",
        video_url="https://s3.example.com/factory-tour.mp4",
    )

    with patch("app.tasks.video._get_video", new=AsyncMock(return_value=mock_video)), \
         patch("app.tasks.video.get_whisper_service") as mock_get_whisper, \
         patch("app.tasks.video.get_pinecone_knowledge_service") as mock_get_pinecone, \
         patch("app.tasks.video._save_transcript_document", new=AsyncMock(return_value=88)):
        whisper_service = MagicMock()
        whisper_service.transcribe_video_url = AsyncMock(
            return_value={
                "success": True,
                "text": "Welcome to our factory line.",
                "language": "en",
            }
        )
        mock_get_whisper.return_value = whisper_service

        pinecone_service = MagicMock()
        pinecone_service.ensure_supplier_namespace.return_value = {
            "initialized": True,
            "namespace": "supplier-22",
            "index_name": "factory-insider-knowledge",
            "supplier_id": 22,
        }
        pinecone_service.upsert_document_chunks.return_value = {
            "namespace": "supplier-22",
            "document_id": "doc-22-abc",
            "chunk_count": 2,
        }
        mock_get_pinecone.return_value = pinecone_service

        result = transcribe_video_with_whisper(101)

    assert result["success"] is True
    assert result["video_id"] == 101
    assert result["knowledge_document_id"] == 88
    assert result["chunk_count"] == 2


def test_transcribe_video_with_whisper_video_not_found():
    with patch("app.tasks.video._get_video", new=AsyncMock(return_value=None)):
        result = transcribe_video_with_whisper(999)

    assert result["success"] is False
    assert result["error"] == "Video not found"
