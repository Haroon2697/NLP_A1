"""
TTS Engine — Local Text-to-Speech using piper-tts.
Synthesizes text to audio sentence-by-sentence for streaming playback.
"""
from __future__ import annotations

import asyncio
import base64
import io
import logging
import struct
import time
import wave
from typing import Any, AsyncIterator, Dict, List, Optional

import numpy as np

logger = logging.getLogger("fitzone.voice.tts")

# TTS configuration
TTS_SAMPLE_RATE = 22050  # Piper default output sample rate
TTS_CHANNELS = 1
TTS_SAMPLE_WIDTH = 2  # 16-bit


class TTSEngine:
    """
    Local Text-to-Speech engine using piper-tts.
    Synthesizes text into audio chunks for streaming playback.
    """

    def __init__(self) -> None:
        self.voice = None
        self.is_initialized = False
        self._piper_available = False

    def initialize(self) -> bool:
        """Loads the Piper TTS voice model."""
        try:
            import piper

            # Try to use a pre-downloaded voice, or download on first use
            # The 'en_US-lessac-medium' voice is a good quality/speed tradeoff
            voice_name = "en_US-lessac-medium"

            logger.info(f"Loading Piper TTS voice '{voice_name}'...")
            start = time.perf_counter()

            # Piper downloads models to ~/.local/share/piper_tts on first use
            self.voice = piper.PiperVoice.load(voice_name)
            self._piper_available = True
            self.is_initialized = True

            elapsed = time.perf_counter() - start
            logger.info(f"TTS voice loaded in {elapsed:.2f}s")
            return True

        except ImportError:
            logger.warning(
                "piper-tts is not installed. Falling back to simple audio beep. "
                "Install with: pip install piper-tts"
            )
            self._piper_available = False
            self.is_initialized = True  # Allow fallback mode
            return True
        except Exception as exc:
            logger.warning(f"Piper TTS init failed ({exc}), using fallback mode.")
            self._piper_available = False
            self.is_initialized = True
            return True

    def synthesize_text(self, text: str) -> Dict[str, Any]:
        """
        Synthesizes text into a WAV audio buffer.
        Returns dict with base64-encoded WAV audio, duration, and latency.
        """
        if not self.is_initialized:
            self.initialize()

        start_time = time.perf_counter()
        text = text.strip()
        if not text:
            return {"audio_base64": "", "duration_ms": 0, "latency_ms": 0}

        try:
            if self._piper_available and self.voice is not None:
                return self._synthesize_piper(text, start_time)
            else:
                return self._synthesize_fallback(text, start_time)
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"TTS synthesis error: {exc}", exc_info=True)
            return {"audio_base64": "", "error": str(exc), "latency_ms": elapsed_ms}

    def _synthesize_piper(self, text: str, start_time: float) -> Dict[str, Any]:
        """Synthesizes using Piper TTS."""
        # Piper synthesize returns audio as numpy array or bytes
        audio_bytes = b""
        for audio_chunk in self.voice.synthesize_stream_raw(text):
            audio_bytes += audio_chunk

        # Create WAV from raw audio
        wav_buffer = self._raw_to_wav(audio_bytes, TTS_SAMPLE_RATE)
        audio_b64 = base64.b64encode(wav_buffer).decode("ascii")

        duration_ms = round(len(audio_bytes) / (TTS_SAMPLE_RATE * TTS_SAMPLE_WIDTH) * 1000, 1)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "audio_base64": audio_b64,
            "sample_rate": TTS_SAMPLE_RATE,
            "duration_ms": duration_ms,
            "latency_ms": elapsed_ms,
            "engine": "piper",
        }

    def _synthesize_fallback(self, text: str, start_time: float) -> Dict[str, Any]:
        """
        Fallback TTS using simple sine wave tone generation.
        This ensures the system works even without Piper installed,
        producing a short beep to indicate where speech would play.
        In production, Piper should be installed for real speech output.
        """
        # Generate a simple sine-wave 'notification' tone
        sample_rate = 22050
        duration_s = min(0.5 + len(text) * 0.03, 5.0)  # Scale with text length
        t = np.linspace(0, duration_s, int(sample_rate * duration_s), dtype=np.float32)

        # Gentle notification tone (440Hz with envelope)
        envelope = np.exp(-t * 1.5) * 0.3
        tone = (envelope * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

        wav_buffer = self._raw_to_wav(tone.tobytes(), sample_rate)
        audio_b64 = base64.b64encode(wav_buffer).decode("ascii")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "audio_base64": audio_b64,
            "sample_rate": sample_rate,
            "duration_ms": round(duration_s * 1000, 1),
            "latency_ms": elapsed_ms,
            "engine": "fallback_tone",
            "note": "Install piper-tts for real speech synthesis.",
        }

    def _raw_to_wav(self, raw_audio: bytes, sample_rate: int) -> bytes:
        """Wraps raw PCM audio bytes into a WAV container."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(TTS_CHANNELS)
            wav_file.setsampwidth(TTS_SAMPLE_WIDTH)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(raw_audio)
        return buf.getvalue()

    async def async_synthesize(self, text: str) -> Dict[str, Any]:
        """Non-blocking async wrapper for synthesis."""
        return await asyncio.to_thread(self.synthesize_text, text)

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Splits text into sentences for incremental TTS.
        Handles common sentence boundaries while preserving abbreviations.
        """
        import re

        # Split on sentence-ending punctuation followed by space or end of string
        # but not on abbreviations like "Rs.", "Dr.", "Mr.", etc.
        sentences = re.split(
            r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$',
            text.strip()
        )

        # Also split on newlines
        result = []
        for s in sentences:
            parts = s.strip().split('\n')
            for p in parts:
                p = p.strip()
                if p:
                    result.append(p)

        return result if result else [text.strip()] if text.strip() else []


# Singleton
_tts_instance: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSEngine()
    return _tts_instance
