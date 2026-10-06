"""
SHA-3 family built on Keccak sponge 
    SHA3(plaintext, variant="sha3_256")  fixed-length hashes    (224, 256,384 and 512 variants)
        .hash()   -> lowercase hexadecimal str
        .digest() -> bytes

    SHAKE(plaintext, variant="shake128")   XOF (variants, 128 and 256)
        .hash(out_len=32)   -> hex str of out_len bytes
        .digest(out_len=32) -> bytes

    CSHAKE(plaintext, variant="cshake128", function_name=b"", customization=b"")
        customizable SHAKE (SP 800-185); the building block of KMAC (mac/kmac.py).
        .digest(out_len=32) -> bytes

Rotation offsets and round constants are computed from their definitions (not typed in)
"""

_MASK = (1 << 64) - 1


# ----------------------------------------------------------------------------
#  Keccak-f[1600]
# ----------------------------------------------------------------------------

def _rotation_offsets() -> list:
    #r [x][y]: rho rotation amounts, from the (x, y) -> (y, 2x + 3y) walk
    r = [[0] * 5 for _ in range(5)]
    x, y = 1, 0
    for t in range(24):
        r[x][y] = ((t + 1) * (t + 2) // 2) % 64
        x, y = y, (2 * x + 3 * y) % 5
    return r


def _round_constants() -> list:
    # 24 iota constants, from degree-8 LFSR x^8 + x^6 + x^5 + x^4 + 1
    def rc_bit(t: int) -> int:
        if t % 255 == 0:
            return 1
        R = 1
        for _ in range(t % 255):
            R <<= 1
            if R & 0x100:
                R ^= 0x171
        return R & 1

    constants = []
    for ir in range(24):
        c = 0
        for j in range(7):
            if rc_bit(j + 7 * ir):
                c |= 1 << ((1 << j) - 1)
        constants.append(c)
    return constants


_RHO = _rotation_offsets()
_RC = _round_constants()

# rho and pi together: lane (x, y) rotated by _RHO[x][y] and moved to (y, 2x + 3y)
_RHO_PI = [(x + 5 * y, y + 5 * ((2 * x + 3 * y) % 5), _RHO[x][y])
           for x in range(5) for y in range(5)]


def keccak_f1600(A: list) -> list:
    # Keccak-f[1600] permutation on a list of 25 * 64-bit lanes
    for rc in _RC:
        # theta: xor each lane with the parities of two neighbouring columns
        C = [A[x] ^ A[x + 5] ^ A[x + 10] ^ A[x + 15] ^ A[x + 20] for x in range(5)]
        D = [C[(x - 1) % 5] ^ (((C[(x + 1) % 5] << 1) | (C[(x + 1) % 5] >> 63)) & _MASK)
             for x in range(5)]
        A = [A[i] ^ D[i % 5] for i in range(25)]
        # rho + pi: rotate every lane and permute the positions
        B = [0] * 25
        for src, dst, r in _RHO_PI:
            v = A[src]
            B[dst] = ((v << r) | (v >> (64 - r))) & _MASK if r else v
        # chi: the only non-linear step, row by row
        A = [B[x + 5 * y] ^ ((~B[(x + 1) % 5 + 5 * y]) & B[(x + 2) % 5 + 5 * y])
             for y in range(5) for x in range(5)]
        # iota: break the symmetry between rounds
        A[0] ^= rc
    return A


# ---------------- The sponge -------------------------------------

def keccak_sponge(data: bytes, rate: int, suffix: int, out_len: int) -> bytes:
    # keccak sponge function (absorb -> squeez)
    # absorbs data at rate bytes per block, then squeeze out_len bytes
    # suffix is domain-separation byte appended before padding: 0x06 SHA-3, 0x1F SHAKE, 0x04 cSHAKE, 0x01 original Keccak
    padded = bytearray(data)
    padded.append(suffix)
    while len(padded) % rate:
        padded.append(0)
    padded[-1] ^= 0x80                               # the closing "1" of pad10*1

    state = [0] * 25
    lanes = rate // 8
    for off in range(0, len(padded), rate):          # absorbing
        for i in range(lanes):
            state[i] ^= int.from_bytes(padded[off + 8 * i: off + 8 * i + 8], "little")
        state = keccak_f1600(state)

    out = bytearray()                                # squeezing
    while True:
        for i in range(lanes):
            out += state[i].to_bytes(8, "little")
        if len(out) >= out_len:
            return bytes(out[:out_len])
        state = keccak_f1600(state)


def _to_bytes(plaintext) -> bytes:
    return plaintext if isinstance(plaintext, bytes) else plaintext.encode("utf-8")




# name: (rate in bytes, output length in bytes, domain-separation suffix)
SHA3_VARIANTS = {
    "sha3_224":   (144, 28, 0x06),
    "sha3_256":   (136, 32, 0x06),
    "sha3_384":   (104, 48, 0x06),
    "sha3_512":   (72,  64, 0x06),
    "keccak_224": (144, 28, 0x01),
    "keccak_256": (136, 32, 0x01),
    "keccak_384": (104, 48, 0x01),
    "keccak_512": (72,  64, 0x01),
}
class SHA3:
    def __init__(self, plaintext, variant: str = "sha3_256"):
        self.plaintext = _to_bytes(plaintext)
        self.var = variant
        self.rate, self.out_len, self.suffix = SHA3_VARIANTS[variant]     # KeyError if unknown

    def __repr__(self):
        return f'("{self.var}",{self.plaintext.hex()})'

    def digest(self) -> bytes:
        return keccak_sponge(self.plaintext, self.rate, self.suffix, self.out_len)

    def hash(self) -> str:
        return self.digest().hex()



SHAKE_VARIANTS = {"shake128": 168, "shake256": 136}        # name: rate in bytes
class SHAKE:
    def __init__(self, plaintext, variant: str = "shake128"):
        self.plaintext = _to_bytes(plaintext)
        self.var = variant
        self.rate = SHAKE_VARIANTS[variant]

    def __repr__(self):
        return f'("{self.var}",{self.plaintext.hex()})'

    def digest(self, out_len: int = 32) -> bytes:
        return keccak_sponge(self.plaintext, self.rate, 0x1F, out_len)

    def hash(self, out_len: int = 32) -> str:
        return self.digest(out_len).hex()




def left_encode(x: int) -> bytes:
    # returns byte length n of x (1 byte), followed by x on n bytes
    n = max(1, (x.bit_length() + 7) // 8)
    return bytes([n]) + x.to_bytes(n, "big")

def right_encode(x: int) -> bytes:
    # x on n bytes, followed by n (1 byte)
    n = max(1, (x.bit_length() + 7) // 8)
    return x.to_bytes(n, "big") + bytes([n])

def encode_string(s: bytes) -> bytes:
    # bit length of s (left_encode), followed by s
    return left_encode(8 * len(s)) + s

def bytepad(x: bytes, w: int) -> bytes:
    # left_encode(w) || x, padded with zero bytes to a multiple of w
    z = left_encode(w) + x
    return z + b"\x00" * (-len(z) % w)

CSHAKE_VARIANTS = {"cshake128": 168, "cshake256": 136}     # name: rate in bytes
class CSHAKE:
    #cSHAKE(X, L, N, S),  With N = S = "" it is exactly SHAKE."""
    def __init__(self, plaintext, variant: str = "cshake128",
                 function_name: bytes = b"", customization: bytes = b""):
        self.plaintext = _to_bytes(plaintext)
        self.var = variant
        self.rate = CSHAKE_VARIANTS[variant]
        self.N = _to_bytes(function_name)
        self.S = _to_bytes(customization)

    def digest(self, out_len: int = 32) -> bytes:
        if not self.N and not self.S:
            return keccak_sponge(self.plaintext, self.rate, 0x1F, out_len)
        prefix = bytepad(encode_string(self.N) + encode_string(self.S), self.rate)
        return keccak_sponge(prefix + self.plaintext, self.rate, 0x04, out_len)

    def hash(self, out_len: int = 32) -> str:
        return self.digest(out_len).hex()
