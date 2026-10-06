"""
Sha224, 256, 384 and 512 hashing algorithms
    SHA object : (P, var)
    P : plaintext to hash (of any bit size)
    var : what variant of sha from the 4 above
    .hash() -> str of hash in hexadecimal
"""


K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]

K64 = [
    0x428a2f98d728ae22, 0x7137449123ef65cd, 0xb5c0fbcfec4d3b2f, 0xe9b5dba58189dbbc,
    0x3956c25bf348b538, 0x59f111f1b605d019, 0x923f82a4af194f9b, 0xab1c5ed5da6d8118,
    0xd807aa98a3030242, 0x12835b0145706fbe, 0x243185be4ee4b28c, 0x550c7dc3d5ffb4e2,
    0x72be5d74f27b896f, 0x80deb1fe3b1696b1, 0x9bdc06a725c71235, 0xc19bf174cf692694,
    0xe49b69c19ef14ad2, 0xefbe4786384f25e3, 0x0fc19dc68b8cd5b5, 0x240ca1cc77ac9c65,
    0x2de92c6f592b0275, 0x4a7484aa6ea6e483, 0x5cb0a9dcbd41fbd4, 0x76f988da831153b5,
    0x983e5152ee66dfab, 0xa831c66d2db43210, 0xb00327c898fb213f, 0xbf597fc7beef0ee4,
    0xc6e00bf33da88fc2, 0xd5a79147930aa725, 0x06ca6351e003826f, 0x142929670a0e6e70,
    0x27b70a8546d22ffc, 0x2e1b21385c26c926, 0x4d2c6dfc5ac42aed, 0x53380d139d95b3df,
    0x650a73548baf63de, 0x766a0abb3c77b2a8, 0x81c2c92e47edaee6, 0x92722c851482353b,
    0xa2bfe8a14cf10364, 0xa81a664bbc423001, 0xc24b8b70d0f89791, 0xc76c51a30654be30,
    0xd192e819d6ef5218, 0xd69906245565a910, 0xf40e35855771202a, 0x106aa07032bbd1b8,
    0x19a4c116b8d2d0c8, 0x1e376c085141ab53, 0x2748774cdf8eeb99, 0x34b0bcb5e19b48a8,
    0x391c0cb3c5c95a63, 0x4ed8aa4ae3418acb, 0x5b9cca4f7763e373, 0x682e6ff3d6b2b8a3,
    0x748f82ee5defb2fc, 0x78a5636f43172f60, 0x84c87814a1f0ab72, 0x8cc702081a6439ec,
    0x90befffa23631e28, 0xa4506cebde82bde9, 0xbef9a3f7b2c67915, 0xc67178f2e372532b,
    0xca273eceea26619c, 0xd186b8c721c0c207, 0xeada7dd6cde0eb1e, 0xf57d4f7fee6ed178,
    0x06f067aa72176fba, 0x0a637dc5a2c898a6, 0x113f9804bef90dae, 0x1b710b35131c471b,
    0x28db77f523047d84, 0x32caab7b40c72493, 0x3c9ebe0a15c9bebc, 0x431d67c49c100d4c,
    0x4cc5d4becb3e42b6, 0x597f299cfc657e2a, 0x5fcb6fab3ad6faec, 0x6c44198c4a475817,
]

IV256 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,]
IV224 = [0xc1059ed8, 0x367cd507, 0x3070dd17, 0xf70e5939, 0xffc00b31, 0x68581511, 0x64f98fa7, 0xbefa4fa4]
IV512 = [0x6a09e667f3bcc908, 0xbb67ae8584caa73b, 0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1,
          0x510e527fade682d1, 0x9b05688c2b3e6c1f, 0x1f83d9abfb41bd6b, 0x5be0cd19137e2179]
IV384 = [0xcbbb9d5dc1059ed8, 0x629a292a367cd507, 0x9159015a3070dd17, 0x152fecd8f70e5939,
          0x67332667ffc00b31, 0x8eb44a8768581511, 0xdb0c2e0d64f98fa7, 0x47b5481dbefa4fa4]


def ROTR(x : int, n : int, w : int) -> int: 
    mask = (1 << w) - 1
    return ((x >> n) | (x << (w - n))) & mask
def SHR(x : int, n : int) -> int:
    return x >> n
def Ch(x : int,y : int ,z : int) -> int:
    return (x & y) ^ (~x & z)
def Maj(x : int,y : int ,z : int) -> int:
    return (x & y) ^ (x & z) ^ (y & z)
def add_mod32(*args: int, w : int) -> int:
    mask = (1 << w) - 1
    total = 0
    for a in args:
        total += a
    return total & mask


VARIANTS = {
    "sha224": dict(w=32, rounds=64, K=K32, IV=IV224, block_bytes=64,  len_bytes=8,  out_words=7,
                   sigma0=(7, 18, 3), sigma1=(17, 19, 10), Sigma0=(2, 13, 22), Sigma1=(6, 11, 25)),
    "sha256": dict(w=32, rounds=64, K=K32, IV=IV256, block_bytes=64,  len_bytes=8,  out_words=8,
                   sigma0=(7, 18, 3), sigma1=(17, 19, 10), Sigma0=(2, 13, 22), Sigma1=(6, 11, 25)),
    "sha384": dict(w=64, rounds=80, K=K64, IV=IV384, block_bytes=128, len_bytes=16, out_words=6,
                   sigma0=(1, 8, 7),  sigma1=(19, 61, 6), Sigma0=(28, 34, 39), Sigma1=(14, 18, 41)),
    "sha512": dict(w=64, rounds=80, K=K64, IV=IV512, block_bytes=128, len_bytes=16, out_words=8,
                   sigma0=(1, 8, 7),  sigma1=(19, 61, 6), Sigma0=(28, 34, 39), Sigma1=(14, 18, 41)),
}

class SHA:
    def __init__(self, plaintext, variant : str = "sha256"):
        if not (isinstance(plaintext, bytes)):
            self.plaintext = plaintext.encode(encoding="utf-8")
        else :
            self.plaintext = plaintext
        self.variant = VARIANTS[variant]
        self.var = variant

    def __repr__(self):
        return f'("{self.var}",{self.plaintext.hex()}")'
    
    def _sigma0(self, x : bytes) -> bytes: 
        r1, r2, s = self.variant["sigma0"]
        w = self.variant["w"]
        return ROTR(x, r1, w) ^ ROTR(x, r2, w) ^ SHR(x, s)
    def _sigma1(self, x : bytes) -> bytes: 
        r1, r2, s = self.variant["sigma1"]
        w = self.variant["w"]
        return ROTR(x, r1, w) ^ ROTR(x, r2, w) ^ SHR(x, s)
    def _Sigma0(self, x : bytes) -> bytes:
        r1, r2, r3 = self.variant["Sigma0"]
        w = self.variant["w"]
        return ROTR(x, r1, w) ^ ROTR(x, r2, w) ^ ROTR(x, r3, w)
    def _Sigma1(self, x : bytes) -> bytes: 
        r1, r2, r3 = self.variant["Sigma1"]
        w = self.variant["w"]
        return ROTR(x, r1, w) ^ ROTR(x, r2, w) ^ ROTR(x, r3, w)



    def hash(self) -> str:
        w = self.variant["w"]
        word_bytes = w // 8
        block_bytes = self.variant["block_bytes"]
        padded = self._padding()
        state = list(self.variant["IV"])

        for mult in range(0, len(padded), block_bytes):
            bloc = padded[mult : mult + block_bytes]
            message_sched = self._message_scheduele(bloc)
            state = self._compresssion(state, message_sched)

        kept = state[: self.variant["out_words"]]
        hash = b''.join(w.to_bytes(word_bytes, byteorder='big') for w in kept)
        return hash.hex()


    def _padding(self) -> bytes:
        # Take any sized plaintext and pads to multiple of 512 (sha256)
        # Add 10000000 and 0's until 64 bits remain to add 64 bits encoding bitsize of message
        block_bytes = self.variant["block_bytes"]
        len_bytes = self.variant["len_bytes"]
        reserve = block_bytes - len_bytes
        original_bit_length = len(self.plaintext) * 8
        message = self.plaintext + b"\x80" # add 10000000
        while len(message) % block_bytes != reserve :
            message += b"\x00"
        message += original_bit_length.to_bytes(len_bytes, "big")
        return message


    def _message_scheduele(self, block : bytes) -> list:
        # Shuffles plaintext with padding : 512 bits
        w = self.variant["w"]
        word_bytes = w // 8
        words_per_block = self.variant["block_bytes"] // word_bytes  # 16, always
        W = [int.from_bytes(block[i:i + word_bytes], "big")
             for i in range(0, self.variant["block_bytes"], word_bytes)]

        for t in range(words_per_block, self.variant["rounds"]):
            val = add_mod32(self._sigma1(W[t-2]), W[t-7], self._sigma0(W[t-15]), W[t-16], w=w)
            W.append(val)
        return W
    

    def _compresssion(self, IV : bytes, mess_sched : list) -> list:
        w = self.variant["w"]
        K = self.variant["K"]
        a, b, c, d, e, f, g, h = IV
        for t in range(self.variant["rounds"]):
            temp1 = add_mod32(h, self._Sigma1(e), Ch(e,f,g), K[t], mess_sched[t], w=w)
            temp2 = add_mod32(self._Sigma0(a), Maj(a,b,c), w=w)
            a, b, c, d, e, f, g, h = (add_mod32(temp1, temp2, w=w), a, b, c, add_mod32(d, temp1, w=w), e, f, g)
        return [add_mod32(a, IV[0], w=w), add_mod32(b, IV[1], w=w), add_mod32(c, IV[2], w=w), add_mod32(d, IV[3], w=w), add_mod32(e, IV[4], w=w), add_mod32(f, IV[5], w=w), add_mod32(g, IV[6], w=w), add_mod32(h, IV[7], w=w)]
