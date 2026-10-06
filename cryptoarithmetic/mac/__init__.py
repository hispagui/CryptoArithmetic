"""
Message authentication codes
    hmac.py   HMAC over any SHA-2 / SHA-3 hash
    kmac.py   KMAC128 / KMAC256, the native MAC of SHA-3
    cmac.py   CMAC (and raw CBC-MAC) over any block cipher: AES, DES, Triple-DES
GCM / GMAC, the authenticated version of CTR, lives in symmetric/gcm.py
"""

from .hmac import HMAC
from .kmac import KMAC
from .cmac import CMAC, CBCMAC
