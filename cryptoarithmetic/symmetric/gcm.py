"""
GCM, Galois/Counter Mode: authenticated encryption (AEAD).
GMAC is GCM with an empty plaintext: a MAC of the associated data alone.

    GCM(cipher)          cipher can be a 128-bit block cipher, i.e. AES
        .encrypt(plaintext, iv, aad=b"", tag_len=16)  -> (ciphertext, tag)
        .decrypt(ciphertext, iv, tag, aad=b"")        -> plaintext (ValueError if wrong tag -> nothing returned)
        .gmac(iv, aad, tag_len=16)                    -> tag

iv is nonce; 12 bytes recommended length. 
aad is authenticated but not encrypted.
Tag is checked in constant time.
"""

from ..utils import constant_time_equal, xor_bytes

_R = 0xE1 << 120                      # x^128 = x^7 + x^2 + x + 1, in GCM's reflected bit order


class _GHash:
    """Multiplication by the fixed element H in GF(2^128), table driven."""

    def __init__(self, h: int):
        v, powers = h, []
        for _ in range(128):                              # powers[i] = H * x^i
            powers.append(v)
            v = (v >> 1) ^ _R if v & 1 else v >> 1
        # table[p][b]: product contribution of byte value b at byte position p (0 = most significant)
        self.table = []
        for p in range(16):
            row = [0] * 256
            for b in range(1, 256):
                low = b & -b                              # lowest set bit of b
                j = 7 - (low.bit_length() - 1)            # its bit index counted from the MSB of the byte
                row[b] = row[b ^ low] ^ powers[8 * p + j]
            self.table.append(row)

    def mult(self, x: int) -> int:
        z = 0
        for p in range(16):
            z ^= self.table[p][(x >> (120 - 8 * p)) & 0xFF]
        return z

    def ghash(self, data: bytes) -> int:
        """GHASH over `data` (a multiple of 16 bytes)."""
        y = 0
        for i in range(0, len(data), 16):
            y = self.mult(y ^ int.from_bytes(data[i:i + 16], "big"))
        return y


def _pad16(data: bytes) -> bytes:
    return data + b"\x00" * (-len(data) % 16)


class GCM:
    def __init__(self, cipher):
        if cipher.block_size != 16:
            raise ValueError("GCM needs a cipher with 128-bit blocks (AES)")
        self.cipher = cipher
        h = int.from_bytes(cipher.encrypt_block(bytes(16)), "big")
        self._ghash = _GHash(h)

    def _j0(self, iv: bytes) -> int:
        if not iv:
            raise ValueError("the IV must not be empty")
        if len(iv) == 12:
            return int.from_bytes(iv + b"\x00\x00\x00\x01", "big")
        data = _pad16(iv) + bytes(8) + (8 * len(iv)).to_bytes(8, "big")
        return self._ghash.ghash(data)

    def _ctr(self, data: bytes, counter: int) -> bytes:
        out = []
        for i in range(0, len(data), 16):
            counter = (counter & ~0xFFFFFFFF) | ((counter + 1) & 0xFFFFFFFF)   # inc32
            keystream = self.cipher.encrypt_block(counter.to_bytes(16, "big"))
            chunk = data[i:i + 16]
            out.append(xor_bytes(chunk, keystream[:len(chunk)]))
        return b"".join(out)

    def _tag(self, j0: int, aad: bytes, ciphertext: bytes, tag_len: int) -> bytes:
        lengths = (8 * len(aad)).to_bytes(8, "big") + (8 * len(ciphertext)).to_bytes(8, "big")
        s = self._ghash.ghash(_pad16(aad) + _pad16(ciphertext) + lengths)
        mask = int.from_bytes(self.cipher.encrypt_block(j0.to_bytes(16, "big")), "big")
        return (mask ^ s).to_bytes(16, "big")[:tag_len]

    @staticmethod
    def _check_tag_len(tag_len: int):
        if not 4 <= tag_len <= 16:
            raise ValueError("tag_len must be between 4 and 16 bytes")

    def encrypt(self, plaintext: bytes, iv: bytes, aad: bytes = b"", tag_len: int = 16):
        self._check_tag_len(tag_len)
        j0 = self._j0(iv)
        ciphertext = self._ctr(plaintext, j0)
        return ciphertext, self._tag(j0, aad, ciphertext, tag_len)

    def decrypt(self, ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes = b"") -> bytes:
        self._check_tag_len(len(tag))
        j0 = self._j0(iv)
        if not constant_time_equal(self._tag(j0, aad, ciphertext, len(tag)), tag):
            raise ValueError("authentication failed")
        return self._ctr(ciphertext, j0)

    def gmac(self, iv: bytes, aad: bytes, tag_len: int = 16) -> bytes:
        return self.encrypt(b"", iv, aad, tag_len)[1]
