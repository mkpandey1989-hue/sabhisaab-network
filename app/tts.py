"""Awaaz banana. Engine badalna ho to sirf config.TTS_ENGINE.
v2.3.0 Step 3 (v11 se): Hindi ank/acronym uchcharan + scene ke hisaab se raftaar + sound effect + dheema music (sfx.py)."""
import threading
import wave
from .config import TTS_ENGINE, VOICE, VOICE_SPEED

SR = 24000
PAD_SEC = 0.30
_pipe = None
_LOCK = threading.RLock()          # v3.8.8: Kokoro ek waqt mein ek hi awaaz (do video saath banein to awaaz kharab na ho)


class TTSDead(RuntimeError):
    """Awaaz engine se khaali/dheemi awaaz aa rahi hai (3 tareeke se koshish ke baad bhi)."""


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
    hold = max(0.0, min(5.5, float(hold or 0)))      # v3.3.7: 5 second tak (video '5 सेकंड' kehti hai)      # v3.1.1: sochne ki chuppi (answers.think_hold) - awaaz ke baad itni der shaant
    if TTS_ENGINE == "silent":
        return _silent(clean_text, out_wav, hold)
    import numpy as np
    import soundfile as sf
    global _pipe
    with _LOCK:
        if _pipe is None:
            from kokoro import KPipeline
            _pipe = KPipeline(lang_code="h", repo_id="hexgrad/Kokoro-82M")
        parts = [np.asarray(a, dtype="float32") for _, _, a in _pipe(clean_text, voice=VOICE, speed=dyn_speed) if a is not None]
    audio = np.concatenate(parts) if parts else np.zeros(SR // 2, dtype="float32")
    try:
        audio = sfx.trim_silence(audio, SR)
        audio = sfx.mix_scene_audio(audio, scene_idx, total_scenes, text, SR)
    except Exception as e:                          # sound effect fail -> saadi awaaz (video kabhi na ruke)
        from .log import log
        log(f"sfx: {e}")
    tail = np.zeros(int(SR * (PAD_SEC + hold)), dtype="float32")
    if hold > 0:                                    # v3.3.7: sochne ki chuppi mein dheema tick-tock (ghatte timer ke saath)
        try:
            if sfx._on("sfx"):
                tk = sfx.tick_tock_loop(hold, SR)
                tail[int(SR * PAD_SEC):int(SR * PAD_SEC) + len(tk)] += tk[:len(tail) - int(SR * PAD_SEC)]
        except Exception:
            pass
    audio = np.concatenate([audio, tail])
    sf.write(out_wav, audio, SR)
    return len(audio) / SR


def _silent(text: str, out_wav: str, hold: float = 0.0) -> float:
    dur = max(1.5, len(text) * 0.075) + PAD_SEC + hold
    n = int(SR * dur)
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"\0\0" * n)
    return n / SR


# ---------------- v3.8.8: awaaz ki jaanch + khud ilaaj (owner: "baar baar audit fail - doctor baithao") ----------------
def wav_level(path):
    """(peak, rms) 0-1. Khaali/kharab file = (0, 0)."""
    try:
        import numpy as np
        import soundfile as sf
        a, _ = sf.read(str(path), dtype="float32")
        if a.ndim > 1:
            a = a.mean(axis=1)
        if not len(a):
            return 0.0, 0.0
        return float(np.max(np.abs(a))), float(np.sqrt(np.mean(a * a)))
    except Exception:
        try:
            with wave.open(str(path), "rb") as w:
                import array
                x = array.array("h", w.readframes(w.getnframes()))
            if not x:
                return 0.0, 0.0
            pk = max(abs(v) for v in x) / 32768
            return pk, (sum(v * v for v in x) / len(x)) ** .5 / 32768
        except Exception:
            return 0.0, 0.0


def _subprocess_synth(text, out_wav, scene_idx, total):
    """Bot ke lambe process se alag, naye process mein awaaz (agar bot ke andar model atka/bigda ho)."""
    import pathlib
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "app.tts_once", str(out_wav), str(scene_idx), str(total)], input=text, text=True,
                       capture_output=True, timeout=600, cwd=str(pathlib.Path(__file__).resolve().parent.parent))
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "tts_once fail")[-200:])
    return float((r.stdout or "0").strip().splitlines()[-1])


def synth_checked(text, out_wav, scene_idx=1, total=5, min_peak=0.05):
    """synth + jaanch. Awaaz khaali/dheemi ho to: (1) model dobara load (2) alag process. Phir bhi nahi = TTSDead.
    Lautata hai (lambai, kaise_bani, peak)."""
    global _pipe
    if TTS_ENGINE == "silent":
        return synth(text, out_wav, scene_idx, total), "test", 1.0
    how, err = "seedha", ""
    try:
        ln = synth(text, out_wav, scene_idx, total)
        pk, _ = wav_level(out_wav)
        if pk >= min_peak:
            return ln, how, pk
    except Exception as e:
        err, pk = str(e)[:120], 0.0
    from .log import log
    log(f"tts: awaaz khaali (peak {pk:.3f}) '{text[:40]}' {err} - model dobara load")
    with _LOCK:
        _pipe = None
    try:
        ln = synth(text, out_wav, scene_idx, total)
        pk, _ = wav_level(out_wav)
        if pk >= min_peak:
            return ln, "model dobara load", pk
    except Exception as e:
        err = str(e)[:120]
    log(f"tts: phir bhi khaali (peak {pk:.3f}) - alag process")
    try:
        ln = _subprocess_synth(text, out_wav, scene_idx, total)
        pk, _ = wav_level(out_wav)
        if pk >= min_peak:
            return ln, "alag process", pk
    except Exception as e:
        err = str(e)[:160]
    raise TTSDead(f"awaaz khaali bani (peak {pk:.3f}) '{text[:30]}…' {err}".strip())


def selftest():
    """Chhoti jaanch: alag process mein 'नमस्ते' bol kar dekho. (ok, sandesh)"""
    import tempfile
    import os
    if TTS_ENGINE == "silent":
        return True, "test engine"
    fd, p = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        _subprocess_synth("नमस्ते, ये आवाज़ की जाँच है।", p, 1, 5)
        pk, rms = wav_level(p)
        return pk >= 0.05, f"peak {pk:.2f}"
    except Exception as e:
        return False, str(e)[:160]
    finally:
        try:
            os.unlink(p)
        except Exception:
            pass
