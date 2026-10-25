"""
ASR Engine — Local Speech-to-Text using faster-whisper (CTranslate2).
Accepts audio bytes in WAV, WebM, Opus, or raw PCM, transcribes locally on CPU,
and returns text with performance metrics and VAD fallback.
"""
from __future__ import annotations

import asyncio
import io
import logging
import time
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger("fitzone.voice.asr")

ASR_MODEL_SIZE = "base.en"
ASR_COMPUTE_TYPE = "int8"
ASR_BEAM_SIZE = 3
ASR_SAMPLE_RATE = 16000


class ASREngine:
    """
    Local Speech-to-Text engine using faster-whisper.
    Decodes diverse audio containers (WAV, WebM, Opus) via SoundFile and PyAV,
    with adaptive energy normalization and VAD fallback.
    """

    def __init__(self, model_size: str = ASR_MODEL_SIZE) -> None:
        self.model_size = model_size
        self.model = None
        self.is_initialized = False

    def initialize(self) -> bool:
        """Loads the faster-whisper model on CPU with INT8 quantization."""
        try:
            from faster_whisper import WhisperModel

            logger.info(f"Loading faster-whisper model '{self.model_size}'...")
            start = time.perf_counter()
            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type=ASR_COMPUTE_TYPE,
            )
            elapsed = time.perf_counter() - start
            self.is_initialized = True
            logger.info(f"ASR model '{self.model_size}' loaded in {elapsed:.2f}s")
            return True
        except ImportError:
            logger.error("faster-whisper is not installed. Install via: pip install faster-whisper")
            return False
        except Exception as exc:
            logger.error(f"Failed to initialize ASR ({self.model_size}): {exc}", exc_info=True)
            return False

    def _decode_audio_bytes(self, audio_bytes: bytes) -> tuple[np.ndarray | None, int]:
        """
        Decodes arbitrary audio bytes (WAV, WebM, Opus, Ogg, MP3) into a
        mono 16kHz float32 numpy array. Tries soundfile first, then PyAV.
        """
        audio_np = None
        sample_rate = ASR_SAMPLE_RATE

        # 1. Try SoundFile (standard for WAV containers)
        try:
            import soundfile as sf
            audio_np, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32")
        except Exception:
            audio_np = None

        # 2. Try PyAV (handles browser WebM, Opus, MP4, AAC, and corrupted headers)
        if audio_np is None:
            try:
                import av
                container = av.open(io.BytesIO(audio_bytes))
                frames = []
                for frame in container.decode(audio=0):
                    frames.append(frame.to_ndarray())
                if frames:
                    raw_audio = np.concatenate(frames, axis=-1)
                    if len(raw_audio.shape) > 1:
                        # Stereo to mono: average channels
                        raw_audio = raw_audio.mean(axis=0)
                    audio_np = raw_audio.astype(np.float32)
                    if audio_np.max() > 1.0 or audio_np.min() < -1.0:
                        audio_np = audio_np / 32768.0
                    sample_rate = container.streams.audio[0].rate or ASR_SAMPLE_RATE
            except Exception as av_exc:
                logger.debug(f"PyAV decoding attempt failed: {av_exc}")

        # 3. Fallback: treat as raw PCM 16-bit mono 16kHz
        if audio_np is None and len(audio_bytes) >= 200:
            try:
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                sample_rate = ASR_SAMPLE_RATE
            except Exception:
                audio_np = None

        if audio_np is None:
            return None, 0

        # Ensure mono
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)

        # Resample to 16kHz if needed
        if sample_rate != ASR_SAMPLE_RATE and sample_rate > 0:
            ratio = ASR_SAMPLE_RATE / sample_rate
            new_length = int(len(audio_np) * ratio)
            indices = np.linspace(0, len(audio_np) - 1, new_length)
            audio_np = np.interp(indices, np.arange(len(audio_np)), audio_np)

        # Normalize volume if quiet
        max_val = np.max(np.abs(audio_np)) if len(audio_np) > 0 else 0
        if 0.001 < max_val < 0.2:
            audio_np = audio_np / max_val * 0.7

        return audio_np, ASR_SAMPLE_RATE

    def transcribe_wav(self, wav_bytes: bytes) -> Dict[str, Any]:
        """Transcribes audio bytes (WAV, WebM, or PCM) to text."""
        if not self.is_initialized:
            if not self.initialize():
                return {"text": "", "error": "ASR model could not be initialized.", "latency_ms": 0}

        start_time = time.perf_counter()

        audio_np, sample_rate = self._decode_audio_bytes(wav_bytes)
        if audio_np is None or len(audio_np) < 320:  # < 20ms
            return {"text": "", "error": "No valid audio decoded.", "latency_ms": 0}

        try:
            # First attempt: transcribe with VAD filter to reject background noise
            segments, info = self.model.transcribe(
                audio_np,
                beam_size=ASR_BEAM_SIZE,
                language="en",
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=400,
                    speech_pad_ms=200,
                ),
            )
            text_parts = [seg.text.strip() for seg in segments if seg.text.strip()]
            full_text = " ".join(text_parts).strip()

            # Fallback attempt: if VAD filtered out quiet/short speech, retry without VAD
            if not full_text:
                segments, info = self.model.transcribe(
                    audio_np,
                    beam_size=1,
                    language="en",
                    vad_filter=False,
                )
                text_parts = [seg.text.strip() for seg in segments if seg.text.strip()]
                full_text = " ".join(text_parts).strip()

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            duration_ms = round(len(audio_np) / ASR_SAMPLE_RATE * 1000, 1)

            return {
                "text": full_text,
                "language": getattr(info, "language", "en"),
                "language_probability": round(getattr(info, "language_probability", 0.0), 3),
                "latency_ms": elapsed_ms,
                "audio_duration_ms": duration_ms,
            }

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"ASR transcription runtime error: {exc}", exc_info=True)
            return {"text": "", "error": str(exc), "latency_ms": elapsed_ms}

    def transcribe_audio(self, audio_data: bytes, sample_rate: int = ASR_SAMPLE_RATE) -> Dict[str, Any]:
        """Alias for transcribe_wav accepting raw PCM or encoded bytes."""
        return self.transcribe_wav(audio_data)

    async def async_transcribe(self, audio_data: bytes, sample_rate: int = ASR_SAMPLE_RATE) -> Dict[str, Any]:
        """Non-blocking async wrapper for transcription."""
        return await asyncio.to_thread(self.transcribe_wav, audio_data)


# Singleton
_asr_instance: Optional[ASREngine] = None


def get_asr_engine() -> ASREngine:
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = ASREngine()
        _asr_instance.initialize()
    return _asr_instance
