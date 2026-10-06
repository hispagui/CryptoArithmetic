"""
DES and Triple-DES

    DES(key)            key: 8 bytes (the 8 parity bits are ignored: 56 effective bits)
    TripleDES(key)      key: 16 bytes (K1, K2, K1) or 24 bytes (K1, K2, K3); EDE order
        .block_size            8
        .encrypt_block(block)  8 bytes -> 8 bytes
        .decrypt_block(block)  8 bytes -> 8 bytes

Both are raw block transformations; use them with CBC (cbc.py), CTR (ctr.py) or CMAC
(mac/cmac.py).

SECURITY!   DES has only a 56-bit key and can be brute-forced,
            Triple-DES has 64-bit blocks and vulnerable to birthday attacks on long messages, deprecated by NIST
Use AES in anycase
"""

# fmt: off
_IP = [58, 50, 42, 34, 26, 18, 10, 2, 60, 52, 44, 36, 28, 20, 12, 4,
       62, 54, 46, 38, 30, 22, 14, 6, 64, 56, 48, 40, 32, 24, 16, 8,
       57, 49, 41, 33, 25, 17, 9, 1, 59, 51, 43, 35, 27, 19, 11, 3,
       61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7]

_E = [32, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9, 8, 9, 10, 11, 12, 13,
      12, 13, 14, 15, 16, 17, 16, 17, 18, 19, 20, 21, 20, 21, 22, 23, 24, 25,
      24, 25, 26, 27, 28, 29, 28, 29, 30, 31, 32, 1]

_P = [16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31, 10,
      2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25]

_PC1 = [57, 49, 41, 33, 25, 17, 9, 1, 58, 50, 42, 34, 26, 18,
        10, 2, 59, 51, 43, 35, 27, 19, 11, 3, 60, 52, 44, 36,
        63, 55, 47, 39, 31, 23, 15, 7, 62, 54, 46, 38, 30, 22,
        14, 6, 61, 53, 45, 37, 29, 21, 13, 5, 28, 20, 12, 4]

_PC2 = [14, 17, 11, 24, 1, 5, 3, 28, 15, 6, 21, 10,
        23, 19, 12, 4, 26, 8, 16, 7, 27, 20, 13, 2,
        41, 52, 31, 37, 47, 55, 30, 40, 51, 45, 33, 48,
        44, 49, 39, 56, 34, 53, 46, 42, 50, 36, 29, 32]

_SHIFTS = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]

_SBOXES = [
    [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7,
     0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8,
     4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0,
     15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],
    [15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10,
     3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5,
     0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15,
     13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9],
    [10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8,
     13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1,
     13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7,
     1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12],
    [7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15,
     13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9,
     10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4,
     3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14],
    [2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9,
     14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6,
     4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14,
     11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3],
    [12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11,
     10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8,
     9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6,
     4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13],
    [4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1,
     13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6,
     1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2,
     6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12],
    [13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7,
     1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2,
     7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8,
     2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11],
]
# fmt: on

_FP = [0] * 64                                   # the final permutation is the inverse of IP
for _i, _p in enumerate(_IP):
    _FP[_p - 1] = _i + 1


def _permute(value: int, table: list, in_bits: int) -> int:
    # output bit i is bit table[i] (1 = most significant) of the in_bits-bit input
    out = 0
    for pos in table:
        out = (out << 1) | ((value >> (in_bits - pos)) & 1)
    return out


def _sbox_lookup(box: list, six_bits: int) -> int:
    row = ((six_bits >> 4) & 0b10) | (six_bits & 1)              # outer bits choose the row
    col = (six_bits >> 1) & 0b1111                               # inner four bits the column
    return box[16 * row + col]


# S-box layer followed by the P permutation: _SP[i][six bits] is a 32-bit word
_SP = [[_permute(_sbox_lookup(_SBOXES[i], v) << (28 - 4 * i), _P, 32) for v in range(64)]
       for i in range(8)]


def _key_schedule(key: bytes) -> list:
    # the sixteen 48-bit round keys
    k = _permute(int.from_bytes(key, "big"), _PC1, 64)           # 56 bits
    c, d = k >> 28, k & 0xFFFFFFF
    subkeys = []
    for shift in _SHIFTS:
        c = ((c << shift) | (c >> (28 - shift))) & 0xFFFFFFF
        d = ((d << shift) | (d >> (28 - shift))) & 0xFFFFFFF
        subkeys.append(_permute((c << 28) | d, _PC2, 56))
    return subkeys


def _feistel(r: int, subkey: int) -> int:
    x = _permute(r, _E, 32) ^ subkey                              # expand to 48 bits, mix the key
    out = 0
    for i in range(8):
        out ^= _SP[i][(x >> (42 - 6 * i)) & 0x3F]
    return out


def _crypt_block(block: int, subkeys: list) -> int:
    block = _permute(block, _IP, 64)
    left, right = block >> 32, block & 0xFFFFFFFF
    for k in subkeys:
        left, right = right, left ^ _feistel(right, k)
    return _permute((right << 32) | left, _FP, 64)                # note the final swap


class DES:
    block_size = 8

    def __init__(self, key: bytes):
        if len(key) != 8:
            raise ValueError("DES key must be 8 bytes long")
        self.key = bytes(key)
        self._enc = _key_schedule(self.key)
        self._dec = self._enc[::-1]                                # decryption: same network, keys reversed

    def encrypt_block(self, block: bytes) -> bytes:
        if len(block) != 8:
            raise ValueError("DES works on blocks of exactly 8 bytes")
        return _crypt_block(int.from_bytes(block, "big"), self._enc).to_bytes(8, "big")

    def decrypt_block(self, block: bytes) -> bytes:
        if len(block) != 8:
            raise ValueError("DES works on blocks of exactly 8 bytes")
        return _crypt_block(int.from_bytes(block, "big"), self._dec).to_bytes(8, "big")


class TripleDES:
    # 3DES in encrypt-decrypt-encrypt order: C = E_K3(D_K2(E_K1(P)))
    block_size = 8

    def __init__(self, key: bytes):
        if len(key) == 16:
            key = key + key[:8]                                    # two-key variant: K3 = K1
        elif len(key) != 24:
            raise ValueError("Triple-DES key must be 16 or 24 bytes long")
        self.key = bytes(key)
        self._k1, self._k2, self._k3 = DES(key[:8]), DES(key[8:16]), DES(key[16:])

    def encrypt_block(self, block: bytes) -> bytes:
        return self._k3.encrypt_block(self._k2.decrypt_block(self._k1.encrypt_block(block)))

    def decrypt_block(self, block: bytes) -> bytes:
        return self._k1.decrypt_block(self._k2.encrypt_block(self._k3.decrypt_block(block)))
