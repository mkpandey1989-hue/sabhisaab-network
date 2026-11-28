"""v3.9.6: 'raqm_layout() failed' (26 Nov 00:54 - poori video ka 'prepare' gira) ka pakka ilaaj.

Pillow ka RAQM engine kuch akshar (emoji, variation selector, toota surrogate, bahut lamba text) par OSError deta hai.
Ab har font naap/likhawat (getmask2, getbbox, getlength) par: galti aaye to (1) text saaf karke dobara, (2) phir BASIC
engine wale usi font se. Video kabhi is wajah se nahi rukti. app/__init__.py import par ek baar lagta hai.
"""
import re
import unicodedata

_BAD = re.compile("[\U00010000-\U0010FFFF︀-️​⁠﻿◌\uD800-\uDFFF]")
_DONE = False
_BASIC = {}


def clean(t):
    if not isinstance(t, str):
        return t
    t = _BAD.sub("", unicodedata.normalize("NFC", t))
    return t[:2000]


def _basic(font):
    from PIL import ImageFont
    k = (getattr(font, "path", None), getattr(font, "size", None), getattr(font, "index", 0))
    if k not in _BASIC:
        b = ImageFont.truetype(font.path, font.size, index=font.index, layout_engine=ImageFont.Layout.BASIC)
        try:                                     # variable font (Baloo2) ka wazan bhi wahi
            b.set_variation_by_axes(list(font.get_variation_axes() and [a.get("default", 0) for a in font.get_variation_axes()]))
        except Exception:
            pass
        if len(_BASIC) > 200:
            _BASIC.clear()
        _BASIC[k] = b
    return _BASIC[k]


def _wrap(name):
    from PIL import ImageFont
    orig = getattr(ImageFont.FreeTypeFont, name)

    def f(self, text, *a, **kw):
        try:
            return orig(self, text, *a, **kw)
        except OSError as e:
            if "raqm" not in str(e).lower() and "layout" not in str(e).lower():
                raise
            try:
                return orig(self, clean(text), *a, **kw)
            except OSError:
                kw.pop("features", None)
                kw.pop("language", None)
                kw.pop("direction", None)
                return orig(_basic(self), clean(text), *a, **kw)
    f.__name__ = name
    f._raqmsafe = True
    setattr(ImageFont.FreeTypeFont, name, f)


def install():
    global _DONE
    if _DONE:
        return
    try:
        from PIL import ImageFont
        for n in ("getmask2", "getbbox", "getlength"):
            if hasattr(ImageFont.FreeTypeFont, n) and not getattr(getattr(ImageFont.FreeTypeFont, n), "_raqmsafe", False):
                _wrap(n)
        _DONE = True
    except Exception:
        pass
