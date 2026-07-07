# Stage 5 — TTS Voice Alerts (Backend)

## Overview

The TTS module generates MP3 audio bytes from alert messages. The audio
is returned to the frontend, which plays it via an `<audio>` element.
This keeps audio generation server-side (where edge-tts/gTTS work
reliably) and playback client-side (non-blocking).

## Backend Design

### Fallback Chain

| Priority | Backend | When Used |
|----------|---------|-----------|
| 1 | `edge-tts` | Default — neural voice, no API key |
| 2 | `gTTS` | Fallback if edge-tts endpoint fails |
| 3 | `None` | All backends failed — text-only alert logged |

### edge-tts (Primary)

- Uses Microsoft Edge's online neural TTS voices
- No API key, no PyTorch, ~5MB install
- Default voice: `en-US-AriaNeural` (female, authoritative)
- Welding Zone (zone 3) uses `en-US-GuyNeural` (male, urgent)
- **Caveat**: Uses an unofficial endpoint. Could break if Microsoft
  changes it. gTTS fallback covers this.

### gTTS (Fallback)

- Uses Google Translate's TTS
- No API key, generates MP3
- Voice is less natural than edge-tts but reliable

### pyttsx3 (Not used in server)

- Synchronous/blocking — would freeze the FastAPI event loop
- Kept in requirements for CLI/demo use only
- Not exposed via the API

## Message Building

Messages are built by `message_builder.py` based on severity:

| Severity | Format |
|----------|--------|
| high | "Warning, {zone}. {ppe} is/are required. This is a high-risk area." |
| medium | "Attention, {zone}. {ppe} is/are required." |
| low | "Notice, {zone}. {ppe} recommended." |

PPE items use display names: `helmet` → "hard hat", `vest` → "safety
vest", `gloves` → "safety gloves".

### Examples

- "Warning, Welding Zone. Safety gloves is required. This is a high-risk area."
- "Attention, Entry Gate. Hard hat and safety vest are required."
- "Notice, Material Yard. Safety vest recommended."

## Zone-to-Voice Mapping

Defined in `backend/config/tts_config.py`:

| Zone | Voice | Reason |
|------|-------|--------|
| 1-2, 4-6 | `en-US-AriaNeural` | Default female voice |
| 3 (Welding) | `en-US-GuyNeural` | Male voice for high-risk urgency |

## Modules

### `message_builder.py`
- `build_alert_message(violation)` — single violation → message string
- `build_scan_summary_message(zone_name, violations)` — multi-violation summary

### `tts_engine.py`
- `TTSEngine.generate_audio(message)` — async, returns MP3 bytes or None
- `TTSEngine.generate_audio_sync(message)` — sync wrapper

### `speaker.py`
- `get_voice_for_zone(zone_id)` — resolve voice for a zone
- `get_all_zone_voices()` — all zone→voice mappings

## Test Coverage

21 tests across two files:

| File | Tests | Coverage |
|------|-------|----------|
| `test_message_builder.py` | 13 | PPE formatting, all severities, all zones, scan summary |
| `test_tts_engine.py` | 8 | edge-tts success/failure, gTTS success/failure, fallback chain, empty messages, sync wrapper |

All TTS tests use mocks — no network calls, no real audio generation.

## Files

- `backend/src/alerts/message_builder.py`
- `backend/src/alerts/tts_engine.py`
- `backend/src/alerts/speaker.py`
- `backend/tests/test_message_builder.py`
- `backend/tests/test_tts_engine.py`
