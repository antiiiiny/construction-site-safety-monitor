"""TTS backend configuration.

edge-tts is the primary backend (neural voice, no API key, no PyTorch).
gTTS is the fallback if the edge-tts endpoint is unreachable. pyttsx3 is
CLI-only and not used inside the FastAPI server (it is synchronous and
would block the event loop).
"""

# Primary TTS backend: "edge" or "gtts".
TTS_BACKEND: str = "edge"

# edge-tts voice. See https://github.com/rany2/edge-tts for full list.
# en-US-AriaNeural  — female, natural, authoritative (default)
# en-US-GuyNeural   — male
TTS_VOICE: str = "en-US-AriaNeural"

# Master toggle. If False, no audio is generated (text-only alerts).
TTS_ENABLED: bool = True

# Optional zone-to-voice mapping. If a zone_id is present here, that voice
# is used instead of TTS_VOICE. Useful for giving the Welding Zone a more
# urgent male voice, for example. Leave empty to use the default everywhere.
ZONE_VOICE_MAP: dict[int, str] = {
    3: "en-US-GuyNeural",  # Welding Zone — male, urgent
}

# gTTS language code (used only when TTS_BACKEND == "gtts" or as fallback).
GTTS_LANG: str = "en"
