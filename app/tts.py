"""Awaaz banana. Engine badalna ho to sirf config.TTS_ENGINE.
v2.3.0 Step 3 (v11 se): Hindi ank/acronym uchcharan + scene ke hisaab se raftaar + sound effect + dheema music (sfx.py)."""
import wave
from .config import TTS_ENGINE, VOICE, VOICE_SPEED

SR = 24000
PAD_SEC = 0.30
_pipe = None


def synth(text: str, out_wav: str, scene_idx: int = 0, total_scenes: int = 5, hold: float = 0.0) -> float:
    """text bolkar wav banao, lambai (second) lautao. Scene ke hisaab se awaaz + SFX (har hissa setting se band ho sakta)."""
    from . import sfx
    clean_text = sfx.normalize_pronunciation(text)
    base_speed = VOICE_SPEED
    try:                                            # v3.1.0: owner ki pakki raftaar ('awaaz raftaar 1.1', dohri pushti) - na ho to purani
        from .finalgate import voice_speed as _vs
        base_speed = _vs(VOICE_SPEED)
    except Exception:
        pass
    dyn_speed = sfx.scene_voice_speed(scene_idx, total_scenes, text, base_speed)
    hold = max(0.0, min(4.0, float(hold or 0)))      # v3.1.1: sochne ki chuppi (answers.think_hold) - awaaz ke baad itni der shaant
    if TTS_ENGINE == "silent":
        return _silent(clean_text, out_wav, hold)
    import numpy as np
    import soundfile as sf
    global _pipe
    if _pipe is None:
        from kokoro import KPipeline
        _pipe = KPipeline(lang_code="h", repo_id="hexgrad/Kokoro-82M")
    parts = [np.asarray(a, dtype="float32") for _, _, a in _pipe(clean_text, voice=VOICE, speed=dyn_speed)]
    audio = np.concatenate(parts) if parts else np.zeros(SR // 2, dtype="float32")
    try:
        audio = sfx.trim_silence(audio, SR)
        audio = sfx.mix_scene_audio(audio, scene_idx, total_scenes, text, SR)
    except Exception as e:                          # sound effect fail -> saadi awaaz (video kabhi na ruke)
        from .log import log
        log(f"sfx: {e}")
    audio = np.concatenate([audio, np.zeros(int(SR * (PAD_SEC + hold)), dtype="float32")])
    sf.write(out_wav, audio, SR)
    return len(audio) / SR


def _silent(text: str, out_wav: str, hold: float = 0.0) -> float:
    dur = max(1.5, len(text) * 0.075) + PAD_SEC + hold
    n = int(SR * dur)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"\0\0" * n)
    return n / SR
