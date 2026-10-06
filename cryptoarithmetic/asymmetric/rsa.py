"""
RSA key generation, encryption and signatures
    public, private = generate_keypair(bits=2048, e=65537)

    RSAPublicKey(n, e)
        .encrypt(message, scheme="oaep", hash="sha256", label=b"")               -> ciphertext bytes
        .verify(message, signature, scheme="pss", hash="sha256", salt_len=None)  -> bool
        .raw_encrypt(m)                     textbook RSA, on integers

    RSAPrivateKey(p, q, e=65537)
        .decrypt(ciphertext, scheme="oaep", hash="sha256", label=b"")    -> message bytes
        .sign(message, scheme="pss", hash="sha256", salt_len=None)      -> signature bytes
        .public_key()                                                     -> RSAPublicKey
        .raw_decrypt(c)                     textbook RSA, on integers

    schemes for encryption: "oaep" (recommended), "pkcs1v15"
    schemes for signatures: "pss" (recommended), "pkcs1v15"
    hash: any of sha224 sha256 sha384 sha512 sha3_224 sha3_256 sha3_384 sha3_512

The raw functions are textbook RSA and are NOT secure on their own: always use one of the padded schemes
"""

from math import gcd

from ..algebra.primality import generate_prime, mod_inverse
from ..hashing import get_hash
from ..utils import constant_time_equal, random_bytes, xor_bytes


# ----------------------------------------------------------------------------
#  Integer <-> byte string, and the mask generation function
# ----------------------------------------------------------------------------

def i2osp(x: int, length: int) -> bytes:
    # integer to octet string of exactly length bytes
    if x < 0 or x >> (8 * length):
        raise ValueError("integer too large")
    return x.to_bytes(length, "big")


def os2ip(octets: bytes) -> int:
    return int.from_bytes(octets, "big")


def mgf1(seed: bytes, length: int, hash: str = "sha256") -> bytes:
    # MGF1: a hash-based mask of length bytes derived from seed
    H = get_hash(hash)
    out = b""
    counter = 0
    while len(out) < length:
        out += H.digest(seed + i2osp(counter, 4))
        counter += 1
    return out[:length]


# -------------------------- Keys --------------------------

class RSAPublicKey:
    def __init__(self, n: int, e: int):
        self.n = n
        self.e = e
        self.byte_length = (n.bit_length() + 7) // 8          # k in RFC 8017

    def __repr__(self):
        return f"RSAPublicKey({self.n.bit_length()} bits, e={self.e})"

    def raw_encrypt(self, m: int) -> int:
        if not 0 <= m < self.n:
            raise ValueError("message representative out of range")
        return pow(m, self.e, self.n)

    def encrypt(self, message: bytes, scheme: str = "oaep", hash: str = "sha256", label: bytes = b"") -> bytes:
        if scheme == "oaep":
            return oaep_encrypt(self, message, hash, label)
        if scheme == "pkcs1v15":
            return pkcs1v15_encrypt(self, message)
        raise ValueError("scheme must be 'oaep' or 'pkcs1v15'")

    def verify(self, message: bytes, signature: bytes, scheme: str = "pss", hash: str = "sha256",
               salt_len: int = None) -> bool:
        if scheme == "pss":
            return pss_verify(self, message, signature, hash, salt_len)
        if scheme == "pkcs1v15":
            return pkcs1v15_verify(self, message, signature, hash)
        raise ValueError("scheme must be 'pss' or 'pkcs1v15'")


class RSAPrivateKey:
    def __init__(self, p: int, q: int, e: int = 65537):
        if p == q:
            raise ValueError("p and q must be different")
        self.p, self.q, self.e = p, q, e
        self.n = p * q
        lam = (p - 1) * (q - 1) // gcd(p - 1, q - 1)          # Carmichael's lambda(n)
        if gcd(e, lam) != 1:
            raise ValueError("e is not invertible modulo lambda(n)")
        self.d = mod_inverse(e, lam)
        self.dp, self.dq = self.d % (p - 1), self.d % (q - 1)  # CRT exponents
        self.qinv = mod_inverse(q, p)
        self.byte_length = (self.n.bit_length() + 7) // 8

    def __repr__(self):
        return f"RSAPrivateKey({self.n.bit_length()} bits)"

    def public_key(self) -> RSAPublicKey:
        return RSAPublicKey(self.n, self.e)

    def raw_decrypt(self, c: int, blinding: bool = True) -> int:
        # c^d mod n by the Chinese remainder theorem, with base blinding
        if not 0 <= c < self.n:
            raise ValueError("ciphertext representative out of range")
        r = 1
        if blinding:               # decrypt c * r^e instead of c
            while True:
                r = 2 + int.from_bytes(random_bytes(self.byte_length + 8), "big") % (self.n - 3)
                if gcd(r, self.n) == 1:
                    break
            c = c * pow(r, self.e, self.n) % self.n
        m1, m2 = pow(c % self.p, self.dp, self.p), pow(c % self.q, self.dq, self.q)
        h = self.qinv * (m1 - m2) % self.p
        m = m2 + h * self.q
        if pow(m, self.e, self.n) != c:          # guards against faults in the CRT computation
            raise ValueError("private operation failed its self-check")
        return m * mod_inverse(r, self.n) % self.n if blinding else m

    def decrypt(self, ciphertext: bytes, scheme: str = "oaep", hash: str = "sha256", label: bytes = b"") -> bytes:
        if scheme == "oaep":
            return oaep_decrypt(self, ciphertext, hash, label)
        if scheme == "pkcs1v15":
            return pkcs1v15_decrypt(self, ciphertext)
        raise ValueError("scheme must be 'oaep' or 'pkcs1v15'")

    def sign(self, message: bytes, scheme: str = "pss", hash: str = "sha256", salt_len: int = None) -> bytes:
        if scheme == "pss":
            return pss_sign(self, message, hash, salt_len)
        if scheme == "pkcs1v15":
            return pkcs1v15_sign(self, message, hash)
        raise ValueError("scheme must be 'pss' or 'pkcs1v15'")






def generate_keypair(bits: int = 2048, e: int = 65537):
    """A fresh (public, private) key pair whose modulus has exactly `bits` bits."""
    if bits < 32:
        raise ValueError("bits must be at least 32")
    if e < 3 or e % 2 == 0:
        raise ValueError("e must be an odd integer >= 3")
    bits_p = (bits + 1) // 2
    while True:
        p, q = generate_prime(bits_p), generate_prime(bits - bits_p)
        if p == q or abs(p - q) >> max(0, bits // 2 - 100) == 0:     # p and q must not be close
            continue
        if gcd(e, (p - 1) * (q - 1)) != 1:
            continue
        private = RSAPrivateKey(p, q, e)
        return private.public_key(), private



# RSAES-OAEP (ENCRYPTION)

def oaep_encrypt(public: RSAPublicKey, message: bytes, hash: str = "sha256", label: bytes = b"") -> bytes:
    H = get_hash(hash)
    k, hlen = public.byte_length, H.digest_size
    if len(message) > k - 2 * hlen - 2:
        raise ValueError("message too long for this key and hash")
    db = H.digest(label) + bytes(k - len(message) - 2 * hlen - 2) + b"\x01" + message
    seed = random_bytes(hlen)
    masked_db = xor_bytes(db, mgf1(seed, k - hlen - 1, hash))
    masked_seed = xor_bytes(seed, mgf1(masked_db, hlen, hash))
    em = b"\x00" + masked_seed + masked_db
    return i2osp(public.raw_encrypt(os2ip(em)), k)

def oaep_decrypt(private: RSAPrivateKey, ciphertext: bytes, hash: str = "sha256", label: bytes = b"") -> bytes:
    H = get_hash(hash)
    k, hlen = private.byte_length, H.digest_size
    if len(ciphertext) != k or k < 2 * hlen + 2 or os2ip(ciphertext) >= private.n:
        raise ValueError("decryption error")
    em = i2osp(private.raw_decrypt(os2ip(ciphertext)), k)
    masked_seed, masked_db = em[1:1 + hlen], em[1 + hlen:]
    seed = xor_bytes(masked_seed, mgf1(masked_db, hlen, hash))
    db = xor_bytes(masked_db, mgf1(seed, k - hlen - 1, hash))
    bad = em[0] != 0
    bad |= not constant_time_equal(db[:hlen], H.digest(label))
    # find the 0x01 separator after the zero padding, scanning the whole string every time
    sep, found = 0, False
    for i, b in enumerate(db[hlen:]):
        if not found and b == 1:
            sep, found = i, True
        elif not found and b != 0:
            bad = True
    if bad or not found:
        raise ValueError("decryption error")
    return db[hlen + sep + 1:]





#  RSAES-PKCS#1 v1_5 (ENCRYPTION)

def pkcs1v15_encrypt(public: RSAPublicKey, message: bytes) -> bytes:
    k = public.byte_length
    if len(message) > k - 11:
        raise ValueError("message too long for this key")
    ps = b""
    while len(ps) < k - len(message) - 3:                   # non-zero random padding, at least 8 bytes
        ps += random_bytes(k - len(message) - 3 - len(ps)).replace(b"\x00", b"")
    em = b"\x00\x02" + ps + b"\x00" + message
    return i2osp(public.raw_encrypt(os2ip(em)), k)

def pkcs1v15_decrypt(private: RSAPrivateKey, ciphertext: bytes) -> bytes:
    k = private.byte_length
    if len(ciphertext) != k or k < 11 or os2ip(ciphertext) >= private.n:
        raise ValueError("decryption error")
    em = i2osp(private.raw_decrypt(os2ip(ciphertext)), k)
    sep = em.find(b"\x00", 2)
    if em[0] != 0 or em[1] != 2 or sep < 10:                # sep < 10: fewer than 8 padding bytes (or none)
        raise ValueError("decryption error")
    return em[sep + 1:]



#  RSASSA-PKCS#1 v1_5 (DIG SIGNATURE)

# last byte of the OID 2.16.840.1.101.3.4.2.x of each hash
_HASH_OID = {"sha256": 0x01, "sha384": 0x02, "sha512": 0x03, "sha224": 0x04,
             "sha3_224": 0x07, "sha3_256": 0x08, "sha3_384": 0x09, "sha3_512": 0x0A}

def _digest_info(hash: str, digest: bytes) -> bytes:
    # DER of DigestInfo ::= SEQUENCE { AlgorithmIdentifier, OCTET STRING digest }
    prefix = bytes([0x30, 17 + len(digest), 0x30, 0x0D, 0x06, 0x09, 0x60, 0x86, 0x48, 0x01,
                    0x65, 0x03, 0x04, 0x02, _HASH_OID[hash], 0x05, 0x00, 0x04, len(digest)])
    return prefix + digest

def _emsa_pkcs1v15(message: bytes, k: int, hash: str) -> bytes:
    t = _digest_info(hash, get_hash(hash).digest(message))
    if k < len(t) + 11:
        raise ValueError("key too short for this hash")
    return b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t

def pkcs1v15_sign(private: RSAPrivateKey, message: bytes, hash: str = "sha256") -> bytes:
    em = _emsa_pkcs1v15(message, private.byte_length, hash)
    return i2osp(private.raw_decrypt(os2ip(em)), private.byte_length)

def pkcs1v15_verify(public: RSAPublicKey, message: bytes, signature: bytes, hash: str = "sha256") -> bool:
    k = public.byte_length
    if len(signature) != k or os2ip(signature) >= public.n:
        return False
    try:
        expected = _emsa_pkcs1v15(message, k, hash)
    except ValueError:
        return False
    return constant_time_equal(i2osp(public.raw_encrypt(os2ip(signature)), k), expected)





# RSASSA-PSS (DIG SIGNATURE) 

def _emsa_pss_encode(message: bytes, em_bits: int, hash: str, salt_len: int) -> bytes:
    H = get_hash(hash)
    hlen, em_len = H.digest_size, (em_bits + 7) // 8
    if em_len < hlen + salt_len + 2:
        raise ValueError("key too short for this hash and salt length")
    salt = random_bytes(salt_len)
    h = H.digest(bytes(8) + H.digest(message) + salt)
    db = bytes(em_len - salt_len - hlen - 2) + b"\x01" + salt
    masked_db = bytearray(xor_bytes(db, mgf1(h, em_len - hlen - 1, hash)))
    masked_db[0] &= 0xFF >> (8 * em_len - em_bits)          # clear the unused leftmost bits
    return bytes(masked_db) + h + b"\xbc"

def _emsa_pss_verify(message: bytes, em: bytes, em_bits: int, hash: str, salt_len: int) -> bool:
    H = get_hash(hash)
    hlen, em_len = H.digest_size, (em_bits + 7) // 8
    if em_len < hlen + salt_len + 2 or em[-1] != 0xBC:
        return False
    masked_db, h = em[:em_len - hlen - 1], em[em_len - hlen - 1:-1]
    top_mask = 0xFF >> (8 * em_len - em_bits)
    if masked_db[0] & ~top_mask & 0xFF:
        return False
    db = bytearray(xor_bytes(masked_db, mgf1(h, em_len - hlen - 1, hash)))
    db[0] &= top_mask
    zeros = em_len - hlen - salt_len - 2
    if any(db[:zeros]) or db[zeros] != 1:
        return False
    salt = bytes(db[len(db) - salt_len:])
    return constant_time_equal(H.digest(bytes(8) + H.digest(message) + salt), h)

def pss_sign(private: RSAPrivateKey, message: bytes, hash: str = "sha256", salt_len: int = None) -> bytes:
    salt_len = get_hash(hash).digest_size if salt_len is None else salt_len
    em_bits = private.n.bit_length() - 1
    em = _emsa_pss_encode(message, em_bits, hash, salt_len)
    return i2osp(private.raw_decrypt(os2ip(em)), private.byte_length)

def pss_verify(public: RSAPublicKey, message: bytes, signature: bytes, hash: str = "sha256",
               salt_len: int = None) -> bool:
    salt_len = get_hash(hash).digest_size if salt_len is None else salt_len
    if len(signature) != public.byte_length or os2ip(signature) >= public.n:
        return False
    em_bits = public.n.bit_length() - 1
    try:
        em = i2osp(public.raw_encrypt(os2ip(signature)), (em_bits + 7) // 8)
    except ValueError:
        return False
    return _emsa_pss_verify(message, em, em_bits, hash, salt_len)
