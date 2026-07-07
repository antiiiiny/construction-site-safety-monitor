"""TTS engine — generates MP3 audio bytes from text messages.

Primary backend: edge-tts (neural voice, no API key, no PyTTS).
Fallback: gTTS (online, generates MP3 via Google Translate).
Final fallback: returns None (text-only, logged).

The engine is async — edge-tts uses aiohttp under the hood. Callers
should await generate_audio() or use asyncio.run() for sync contexts.

Usage:
    import asyncio
    from backend.src.alerts.tts_engine import TTSEngine
    engine = TTSEngine()
    audio = asyncio.run(engine.generate_audio("Attention, Entry Gate. Hard hat is required."))
    # audio is MP3 bytes, or None if all backends failed
"""

from __future__ import annotations

import asyncio
import io
import logging

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class TTSEngine:
    """Text-to-speech engine with fallback chain.

    Attributes:
        backend: Active backend ("edge" or "gtts").
        voice: edge-tts voice ID (e.g. "en-US-AriaNeural").
    """

    def __init__(
        self,
        backend: str | None = None,
        voice: str | None = None,
    ) -> None:
        """Initialize the TTS engine.

        Args:
            backend: Override backend from settings. "edge" or "gtts".
            voice: Override voice from settings.
        """
        self.backend = backend or settings.tts_backend
        self.voice = voice or settings.tts_voice

    async def generate_audio(self, message: str) -> bytes | None:
        """Generate MP3 audio bytes from a text message.

        Tries the primary backend first, falls back to gTTS if it fails.
        Returns None if all backends fail (caller should log text-only).

        Args:
            message: Text to convert to speech.

        Returns:
            MP3 audio as bytes, or None if generation failed.
        """
        if not message or not message.strip():
            logger.warning("Empty message passed to TTS engine.")
            return None

        # Try primary backend
        if self.backend == "edge":
            audio = await self._generate_edge_tts(message)
            if audio is not None:
                return audio
            logger.warning("edge-tts failed, falling back to gTTS.")

        # Try gTTS (either as primary or fallback)
        audio = self._generate_gtts(message)
        if audio is not None:
            return audio

        logger.error("All TTS backends failed. Returning None (text-only).")
        return None

    async def _generate_edge_tts(self, message: str) -> bytes | None:
        """Generate audio using edge-tts.

        Args:
            message: Text to synthesize.

        Returns:
            MP3 bytes, or None if generation failed.
        """
        try:
            import edge_tts

            communicate = edge_tts.Communicate(message, self.voice)
            # Collect audio chunks into a buffer
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            audio_bytes = buffer.getvalue()
            if audio_bytes:
                logger.info("edge-tts generated %d bytes of audio.", len(audio_bytes))
                return audio_bytes
            logger.warning("edge-tts returned empty audio.")
            return None
        except Exception as e:
            logger.error("edge-tts error: %s", e)
            return None

    def _generate_gtts(self, message: str) -> bytes | None:
        """Generate audio using gTTS (Google Translate TTS).

        Args:
            message: Text to synthesize.

        Returns:
            MP3 bytes, or None if generation failed.
        """
        try:
            from gtts import gTTS

            tts = gTTS(text=message, lang="en", slow=False)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            audio_bytes = buffer.read()
            if audio_bytes:
                logger.info("gTTS generated %d bytes of audio.", len(audio_bytes))
                return audio_bytes
            logger.warning("gTTS returned empty audio.")
            return None
        except Exception as e:
            logger.error("gTTS error: %s", e)
            return None

    def generate_audio_sync(self, message: str) -> bytes | None:
        """Synchronous wrapper for generate_audio().

        Useful in non-async contexts. Uses asyncio.run() internally.

        Args:
            message: Text to synthesize.

        Returns:
            MP3 bytes, or None if generation failed.
        """
        return asyncio.run(self.generate_audio(message))
