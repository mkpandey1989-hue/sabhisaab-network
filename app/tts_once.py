"""v3.8.8: ek awaaz alag process mein (bot ke andar model atka ho to). python -m app.tts_once out.wav idx total < text"""
import sys

from . import tts

if __name__ == "__main__":
    out, idx, tot = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    print(tts.synth(sys.stdin.read().strip(), out, idx, tot))
