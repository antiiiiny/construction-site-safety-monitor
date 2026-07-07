"""Tests for the TTS engine.

Tests mock edge-tts and gTTS to verify:
  - MP3 bytes are returned from the primary backend
  - Fallback to gTTS when edge-tts fails
  - None returned when all backends fail
  - Empty message handling
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.src.alerts.tts_engine import TTSEngine


# Helper for async iteration in mocks
class AsyncIterator:
    """Helper to make an async iterator from a list."""

    def __init__(self, items: list) -> None:
        self._items = items
        self._index = 0

    def __aiter__(self) -> AsyncIterator:
        return self

    async def __anext__(self):
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        return item


class TestTTSEngineEdgeTts:
    """Tests for edge-tts backend."""

    @pytest.mark.asyncio
    async def test_edge_tts_success(self) -> None:
        """edge-tts should return MP3 bytes when successful."""
        engine = TTSEngine(backend="edge", voice="en-US-AriaNeural")

        # Mock edge_tts.Communicate
        mock_communicate = MagicMock()
        mock_chunk = {"type": "audio", "data": b"fake_mp3_data"}
        mock_communicate.stream = MagicMock(return_value=AsyncIterator([mock_chunk]))

        with patch("edge_tts.Communicate", return_value=mock_communicate):
            audio = await engine.generate_audio("Test message")

        assert audio is not None
        assert audio == b"fake_mp3_data"

    @pytest.mark.asyncio
    async def test_edge_tts_failure_falls_back_to_gtts(self) -> None:
        """If edge-tts fails, should fall back to gTTS."""
        engine = TTSEngine(backend="edge", voice="en-US-AriaNeural")

        # Mock edge_tts to raise an exception
        with patch("edge_tts.Communicate", side_effect=Exception("Network error")):
            # Mock gTTS to succeed
            mock_gtts = MagicMock()
            mock_gtts.write_to_fp = MagicMock(
                side_effect=lambda buf: buf.write(b"gtts_mp3_data")
            )
            with patch("gtts.gTTS", return_value=mock_gtts):
                audio = await engine.generate_audio("Test message")

        assert audio is not None
        assert audio == b"gtts_mp3_data"


class TestTTSEngineGTts:
    """Tests for gTTS backend."""

    @pytest.mark.asyncio
    async def test_gtts_success(self) -> None:
        """gTTS backend should return MP3 bytes."""
        engine = TTSEngine(backend="gtts")

        mock_gtts = MagicMock()
        mock_gtts.write_to_fp = MagicMock(
            side_effect=lambda buf: buf.write(b"gtts_mp3_data")
        )
        with patch("gtts.gTTS", return_value=mock_gtts):
            audio = await engine.generate_audio("Test message")

        assert audio is not None
        assert audio == b"gtts_mp3_data"

    @pytest.mark.asyncio
    async def test_gtts_failure_returns_none(self) -> None:
        """If gTTS fails and no other backend, should return None."""
        engine = TTSEngine(backend="gtts")

        with patch("gtts.gTTS", side_effect=Exception("Network error")):
            audio = await engine.generate_audio("Test message")

        assert audio is None


class TestTTSEngineEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_message(self) -> None:
        """Empty message should return None without calling backends."""
        engine = TTSEngine(backend="edge")
        audio = await engine.generate_audio("")
        assert audio is None

    @pytest.mark.asyncio
    async def test_whitespace_message(self) -> None:
        """Whitespace-only message should return None."""
        engine = TTSEngine(backend="edge")
        audio = await engine.generate_audio("   ")
        assert audio is None

    @pytest.mark.asyncio
    async def test_all_backends_fail(self) -> None:
        """If all backends fail, should return None."""
        engine = TTSEngine(backend="edge")

        with (
            patch("edge_tts.Communicate", side_effect=Exception("edge failed")),
            patch("gtts.gTTS", side_effect=Exception("gtts failed")),
        ):
            audio = await engine.generate_audio("Test message")

        assert audio is None


class TestTTSEngineSync:
    """Tests for the sync wrapper."""

    def test_generate_audio_sync(self) -> None:
        """generate_audio_sync should work in non-async context."""
        engine = TTSEngine(backend="gtts")

        mock_gtts = MagicMock()
        mock_gtts.write_to_fp = MagicMock(
            side_effect=lambda buf: buf.write(b"sync_mp3_data")
        )
        with patch("gtts.gTTS", return_value=mock_gtts):
            audio = engine.generate_audio_sync("Test message")

        assert audio is not None
        assert audio == b"sync_mp3_data"
