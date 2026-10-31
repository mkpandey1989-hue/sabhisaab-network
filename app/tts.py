"""Awaaz banana. Engine badalna ho to sirf config.TTS_ENGINE."""
import wave
from .config import TTS_ENGINE, VOICE, VOICE_SPEED

SR = 24000
PAD_SEC = 0.35
_pipe = None


def synth(text: str, out_wav: str) -> float:
    """text bolkar wav banao, lambai (second) lautao."""
    if TTS_ENGINE == "silent":
        return _silent(text, out_wav)
    import numpy as np
    import soundfile as sf
    global _pipe
    if _pipe is None:
        from kokoro import KPipeline
        _pipe = KPipeline(lang_code="h", repo_id="hexgrad/Kokoro-82M")
    parts = [np.asarray(a, dtype="float32") for _, _, a in _pipe(text, voice=VOICE, speed=VOICE_SPEED)]
    audio = np.concatenate(parts) if parts else np.zeros(SR // 2, dtype="float32")
    audio = np.concatenate([audio, np.zeros(int(SR * PAD_SEC), dtype="float32")])
    sf.write(out_wav, audio, SR)
    return len(audio) / SR


def _silent(text: str, out_wav: str) -> float:
    dur = max(1.5, len(text) * 0.075) + PAD_SEC
    n = int(SR * dur)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"\0\0" * n)
    return n / SR
