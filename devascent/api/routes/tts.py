"""Local TTS — Kokoro-82M (CPU-friendly, ~327MB, Apache-2.0).

POST /api/tts {text, voice?} -> audio/wav.

Kokoro is lazy-loaded once and cached. If it isn't installed, we return 503
with a hint so the frontend silently falls back to the browser Web Speech API
(the always-available default). This keeps narration working out of the box and
makes premium local voice an opt-in upgrade.

Install on the user's box (16GB / i7, CPU-only):  scripts/setup_tts.sh
"""
import io
import wave
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter(tags=["tts"])

_PIPELINE = None
_FAILED = False


class TTSRequest(BaseModel):
    text: str
    voice: str = "am_michael"  # default Kokoro voice — American male


def _get_pipeline():
    """Lazy-load the Kokoro pipeline once (CPU)."""
    global _PIPELINE, _FAILED
    if _PIPELINE is not None or _FAILED:
        return _PIPELINE
    try:
        from kokoro import KPipeline  # type: ignore
        _PIPELINE = KPipeline(lang_code="a")  # American English
    except Exception:
        _FAILED = True
        _PIPELINE = None
    return _PIPELINE


def _to_wav(samples, sample_rate: int = 24000) -> bytes:
    import numpy as np

    audio = np.asarray(samples, dtype="float32")
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


@router.post("")
@router.post("/")
def synthesize(body: TTSRequest):
    pipe = _get_pipeline()
    if pipe is None:
        raise HTTPException(
            status_code=503,
            detail="Local TTS (Kokoro) not installed. Run scripts/setup_tts.sh, "
                   "or use the browser voice (default).",
        )
    try:
        import numpy as np

        chunks = [audio for _, _, audio in pipe(body.text, voice=body.voice)]
        if not chunks:
            raise RuntimeError("no audio produced")
        full = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
        return Response(content=_to_wav(full), media_type="audio/wav")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


@router.get("/status")
def status():
    pipe = _get_pipeline()
    return {"available": pipe is not None, "engine": "kokoro-82m" if pipe else None}
