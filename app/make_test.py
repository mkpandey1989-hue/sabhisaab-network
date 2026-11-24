"""Test: ek video banao, jaancho, Telegram par bhejo.  Chalana:  ./sn-test"""
import json
import pathlib
import sys
import traceback
from . import tg, audit
from .render import render
from .guard import cleanup
from .log import log


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "test_emi"
    script = json.loads((pathlib.Path(__file__).parent / "scripts" / f"{name}.json").read_text(encoding="utf-8"))
    tg.say(f"🎬 Test video shuru: {script['title']} ({script['brand']})")
    try:
        meta = render(script, notify=tg.say)
        checks = audit.run(meta)
        report = "\n".join(f"{c} {m}" for c, m in checks)
        verdict = "✅ AUDIT PASS" if audit.passed(checks) else "❌ AUDIT FAIL"
        try:
            tg.video(meta["video"], f"{script['title']}\n⏱ {meta['duration']:.0f}s video, {meta['render_sec']:.0f}s mein bani",
                     meta["thumbs"][0])
        except Exception as e:
            log(f"video bhejna fail: {e}")
            tg.say(f"⚠️ Video bani hai par Telegram par nahi gayi (network). File VM par surakshit: {meta['video']}")
        tg.photos(meta["thumbs"], "🖼 3 thumbnail - kaun sa achha laga?")
        tg.say(f"{verdict}\n\n{report}\n\n📝 Description:\n{audit.description(meta)}")
        log(verdict)
        print(verdict)
        print(report)
    except Exception as e:
        log("ERROR " + traceback.format_exc())
        tg.say(f"❌ Test video mein galti: {e}")
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
