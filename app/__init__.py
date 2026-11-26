"""Sabhisaab Network bot."""
try:                                   # v3.9.6: raqm_layout() failed se video kabhi na ruke
    from . import raqmsafe as _rs
    _rs.install()
except Exception:
    pass
