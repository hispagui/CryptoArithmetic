"""
KMAC, native MAC of SHA-3, built on cSHAKE

    KMAC(key, variant="kmac128", out_len=None, customization=b"", xof=False)
        variants: kmac128 (default output 32 bytes), kmac256 (default output 64 bytes)
        .mac(message)           -> bytes of out_len bytes
        .verify(message, tag)  -> bool

    KMAC128(K, X, L, S) = cSHAKE128( bytepad(encode_string(K), 168) || X || right_encode(L), L, "KMAC", S)
"""

from ..hashing.sha3 import CSHAKE, bytepad, encode_string, right_encode
from ..utils import constant_time_equal

# name: (cSHAKE variant, rate, default output length in bytes)
KMAC_VARIANTS = {"kmac128": ("cshake128", 168, 32), "kmac256": ("cshake256", 136, 64)}


class KMAC:
    def __init__(self, key: bytes, variant: str = "kmac128", out_len: int = None,
                 customization: bytes = b"", xof: bool = False):
        self.cshake, self.rate, default_len = KMAC_VARIANTS[variant]       # KeyError if unknown
        self.var = variant
        self.key = key
        self.out_len = default_len if out_len is None else out_len
        self.customization = customization
        self.xof = xof

    def mac(self, message: bytes) -> bytes:
        length_field = right_encode(0 if self.xof else 8 * self.out_len)
        data = bytepad(encode_string(self.key), self.rate) + message + length_field
        return CSHAKE(data, self.cshake, b"KMAC", self.customization).digest(self.out_len)

    def verify(self, message: bytes, tag: bytes) -> bool:
        return constant_time_equal(self.mac(message), tag)
