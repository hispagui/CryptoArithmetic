"""
AES block cipher           
    AES(key)                 key: 16, 24 or 32 bytes
        .block_size            16
        .encrypt_block(block)  16 bytes -> 16 bytes
        .decrypt_block(block)  16 bytes -> 16 bytes

This is only the raw block transformation. 
To encrypt messages use a mode of operation: CBC (cbc.py), CTR (ctr.py) or GCM (gcm.py).

arithmetic is done in GF(2^8) = F_2[x]/(x^8 + x^4 + x^3 + x + 1). 
S-box is computed from its definition rather than typed in
"""

# ----------------------------------------------------------------------------
#  GF(2^8) and the tables derived from it
# ----------------------------------------------------------------------------

def _xtime(a: int) -> int:
    # mult by x (that is, by 2) in GF(2^8)
    a <<= 1
    return (a ^ 0x11B) & 0xFF if a & 0x100 else a


def _gmul(a: int, b: int) -> int:
    # prod in GF(2^8), by shift-and-add
    result = 0
    while b:
        if b & 1:
            result ^= a
        a = _xtime(a)
        b >>= 1
    return result


def _ginv(a: int) -> int:
    # mult inverse in GF(2^8): a^254 (and 0 for 0)
    result, base, e = 1, a, 254
    while e:
        if e & 1:
            result = _gmul(result, base)
        base = _gmul(base, base)
        e >>= 1
    return result if a else 0


def _build_sbox() -> list:
    sbox = []
    for x in range(256):
        inv = _ginv(x)
        s = inv
        for shift in (1, 2, 3, 4):                   # b ^ rotl(b,1) ^ ... ^ rotl(b,4)
            s ^= ((inv << shift) | (inv >> (8 - shift))) & 0xFF
        sbox.append(s ^ 0x63)
    return sbox


SBOX = _build_sbox()
INV_SBOX = [0] * 256
for _i, _s in enumerate(SBOX):
    INV_SBOX[_s] = _i

_M2 = [_gmul(x, 2) for x in range(256)]
_M3 = [_gmul(x, 3) for x in range(256)]
_M9 = [_gmul(x, 9) for x in range(256)]
_M11 = [_gmul(x, 11) for x in range(256)]
_M13 = [_gmul(x, 13) for x in range(256)]
_M14 = [_gmul(x, 14) for x in range(256)]

# ShiftRows moves the byte at (row r, column c) to column c - r; as an index map:
_SHIFT = [r + 4 * ((c + r) % 4) for c in range(4) for r in range(4)]       # new[i] = old[_SHIFT[i]]
_INV_SHIFT = [r + 4 * ((c - r) % 4) for c in range(4) for r in range(4)]


# --------------------------
#  Key expansion
# --------------------------

def _expand_key(key: bytes) -> list:
    # returns round keys: a list of Nr + 1 lists of 16 bytes
    nk = len(key) // 4                               # key length in 32-bit words: 4, 6 or 8
    nr = nk + 6                                      # number of rounds: 10, 12 or 14
    w = [list(key[4 * i: 4 * i + 4]) for i in range(nk)]
    rcon = 1
    for i in range(nk, 4 * (nr + 1)):
        t = list(w[i - 1])
        if i % nk == 0:
            t = [SBOX[b] for b in t[1:] + t[:1]]     # RotWord then SubWord
            t[0] ^= rcon
            rcon = _xtime(rcon)
        elif nk > 6 and i % nk == 4:                 # AES-256 only
            t = [SBOX[b] for b in t]
        w.append([a ^ b for a, b in zip(w[i - nk], t)])
    return [sum(w[4 * r: 4 * r + 4], []) for r in range(nr + 1)]


# ----------------------------------------------------------------------------
#  The cipher
# ----------------------------------------------------------------------------

class AES:
    block_size = 16

    def __init__(self, key: bytes):
        if len(key) not in (16, 24, 32):
            raise ValueError("AES key must be 16, 24 or 32 bytes long")
        self.key = bytes(key)
        self._round_keys = _expand_key(self.key)
        self._rounds = len(self._round_keys) - 1

    def __repr__(self):
        return f"AES-{8 * len(self.key)}"

    def encrypt_block(self, block: bytes) -> bytes:
        if len(block) != 16:
            raise ValueError("AES works on blocks of exactly 16 bytes")
        rk = self._round_keys
        state = [b ^ k for b, k in zip(block, rk[0])]
        for r in range(1, self._rounds):
            state = [SBOX[state[i]] for i in _SHIFT]                     # SubBytes + ShiftRows
            mixed = []
            for c in range(0, 16, 4):                                    # MixColumns
                a0, a1, a2, a3 = state[c: c + 4]
                mixed += [_M2[a0] ^ _M3[a1] ^ a2 ^ a3,
                          a0 ^ _M2[a1] ^ _M3[a2] ^ a3,
                          a0 ^ a1 ^ _M2[a2] ^ _M3[a3],
                          _M3[a0] ^ a1 ^ a2 ^ _M2[a3]]
            state = [s ^ k for s, k in zip(mixed, rk[r])]                # AddRoundKey
        state = [SBOX[state[i]] for i in _SHIFT]                         # last round: no MixColumns
        return bytes(s ^ k for s, k in zip(state, rk[self._rounds]))

    def decrypt_block(self, block: bytes) -> bytes:
        if len(block) != 16:
            raise ValueError("AES works on blocks of exactly 16 bytes")
        rk = self._round_keys
        state = [b ^ k for b, k in zip(block, rk[self._rounds])]
        for r in range(self._rounds - 1, 0, -1):
            state = [INV_SBOX[state[i]] for i in _INV_SHIFT]             # InvShiftRows + InvSubBytes
            state = [s ^ k for s, k in zip(state, rk[r])]                # AddRoundKey
            mixed = []
            for c in range(0, 16, 4):                                    # InvMixColumns
                a0, a1, a2, a3 = state[c: c + 4]
                mixed += [_M14[a0] ^ _M11[a1] ^ _M13[a2] ^ _M9[a3],
                          _M9[a0] ^ _M14[a1] ^ _M11[a2] ^ _M13[a3],
                          _M13[a0] ^ _M9[a1] ^ _M14[a2] ^ _M11[a3],
                          _M11[a0] ^ _M13[a1] ^ _M9[a2] ^ _M14[a3]]
            state = mixed
        state = [INV_SBOX[state[i]] for i in _INV_SHIFT]
        return bytes(s ^ k for s, k in zip(state, rk[0]))
