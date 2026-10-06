"""
Block-cipher MACs: CMAC and raw CBC-MAC.
    CMAC(cipher)                      cipher: AES, DES or TripleDES (64- or 128-bit blocks)
        .mac(message, tag_len=None)   -> bytes (tag_len leading bytes, default a full block)
        .verify(message, tag)         -> bool  (constant-time comparison)

    CBCMAC(cipher)
        .mac(message) / .verify(message, tag)
        message length must be a non-zero multiple of the block size.

CMAC is the secure, variable-length version of CBC-MAC:
derives two subkeys K1, K2 from E_K(0) and xors K1 or K2 into the last block before the final CBC step
Plain CBC-MAC only secure when all messages have same length; with variable lengths an attacker can forge tags by concatenation
"""

from ..utils import constant_time_equal, xor_bytes

_RB = {16: 0x87, 8: 0x1B}             # the reduction constant of GF(2^128) and GF(2^64)


class CMAC:
    def __init__(self, cipher):
        bs = cipher.block_size
        if bs not in _RB:
            raise ValueError("CMAC supports 64-bit and 128-bit block ciphers")
        self.cipher = cipher
        self.block_size = bs
        mask, msb = (1 << (8 * bs)) - 1, 1 << (8 * bs - 1)

        def dbl(x: int) -> int:                       # multiplication by x in GF(2^(8*bs))
            return ((x << 1) & mask) ^ (_RB[bs] if x & msb else 0)

        l = int.from_bytes(cipher.encrypt_block(bytes(bs)), "big")
        self._k1 = dbl(l).to_bytes(bs, "big")
        self._k2 = dbl(dbl(l)).to_bytes(bs, "big")

    def mac(self, message: bytes, tag_len: int = None) -> bytes:
        bs = self.block_size
        n_blocks = max(1, -(-len(message) // bs))
        complete = bool(message) and len(message) % bs == 0
        last = message[(n_blocks - 1) * bs:]
        if complete:
            last = xor_bytes(last, self._k1)
        else:
            last = xor_bytes(last + b"\x80" + bytes(bs - len(last) - 1), self._k2)
        x = bytes(bs)
        for i in range(n_blocks - 1):
            x = self.cipher.encrypt_block(xor_bytes(x, message[i * bs:(i + 1) * bs]))
        tag = self.cipher.encrypt_block(xor_bytes(x, last))
        if tag_len is None:
            return tag
        if not 1 <= tag_len <= bs:
            raise ValueError("tag_len must be between 1 and the block size")
        return tag[:tag_len]

    def verify(self, message: bytes, tag: bytes) -> bool:
        return constant_time_equal(self.mac(message, len(tag)), tag)


class CBCMAC:
    def __init__(self, cipher):
        self.cipher = cipher
        self.block_size = cipher.block_size

    def mac(self, message: bytes) -> bytes:
        bs = self.block_size
        if not message or len(message) % bs:
            raise ValueError("CBC-MAC needs a non-empty message whose length is a multiple of the block size")
        x = bytes(bs)
        for i in range(0, len(message), bs):
            x = self.cipher.encrypt_block(xor_bytes(x, message[i:i + bs]))
        return x

    def verify(self, message: bytes, tag: bytes) -> bool:
        return constant_time_equal(self.mac(message), tag)
