"""
HMAC, the MAC of the hash functions.
    HMAC(key, hash="sha256")
        .mac(message)            -> bytes (the tag, of the hash's digest size)
        .verify(message, tag)    -> bool  (constant-time comparison)

(works with every hash of hashing.get_hash)

    HMAC(K, m) = H( (K' xor opad) || H( (K' xor ipad) || m ) )
"""

from ..hashing import get_hash
from ..utils import constant_time_equal


class HMAC:
    def __init__(self, key: bytes, hash: str = "sha256"):
        self.hash = get_hash(hash)
        if len(key) > self.hash.block_size:
            key = self.hash.digest(key)
        key = key.ljust(self.hash.block_size, b"\x00")
        self._inner = bytes(b ^ 0x36 for b in key)
        self._outer = bytes(b ^ 0x5C for b in key)

    def mac(self, message: bytes) -> bytes:
        inner = self.hash.digest(self._inner + message)
        return self.hash.digest(self._outer + inner)

    def verify(self, message: bytes, tag: bytes) -> bool:
        return constant_time_equal(self.mac(message), tag)
