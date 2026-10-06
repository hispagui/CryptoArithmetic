# CryptoArithmetic

Cryptography written from scratch in pure Python, for study: finite fields, elliptic
curves, polynomials, Schoof's point counting, SHA-2 / SHA-3, HMAC / KMAC / CMAC, AES, DES
and Triple-DES with CBC / CTR / GCM, RSA and ECDSA.

This README says **how to call things**. 
Educational code: not constant-time, not audited, slow. Do not protect real secrets with it.

## Contents

1. [Layout and installation](#1-layout-and-installation)
2. [Quick start](#2-quick-start)
3. [`algebra/arithmetic.py`](#3-algebraarithmeticpy)
4. [`algebra/polynomial.py`](#4-algebrapolynomialpy)
5. [`elliptic/schoof.py`](#5-ellipticschoofpy)
6. [Hash functions](#6-hash-functions)
7. [Message authentication codes](#7-message-authentication-codes)
8. [Symmetric encryption](#8-symmetric-encryption)
9. [Public-key cryptography](#9-public-key-cryptography)
10. [Common errors](#10-common-errors)

---

## 1. Layout and installation

One protocol, or one family, per file:

```text
cryptoarithmetic/
├── algebra/     arithmetic.py  polynomial.py  primality.py  primes.py
├── elliptic/    schoof.py
├── hashing/     sha2.py  sha3.py
├── mac/         hmac.py  kmac.py  cmac.py
├── symmetric/   aes.py  des.py  padding.py  cbc.py  ctr.py  gcm.py
├── asymmetric/  rsa.py  ecdsa.py
└── utils.py
```

Python 3.8+, standard library only. Run from the folder containing `cryptoarithmetic/`
(or `pip install -e .`), see https://pypi.org/project/cryptoarithmetic/0.1.0/. Each subpackage re-exports its classes, so both
`from cryptoarithmetic.symmetric import AES` and `from cryptoarithmetic.symmetric.aes import AES` work.

**Which MAC goes with which primitive**

- SHA-2: HMAC. SHA-3: HMAC, or its native KMAC.
- AES, DES, Triple-DES: CMAC (CBC-MAC only for fixed-length messages).
- CBC mode: CMAC, or encrypt-then-HMAC. CTR mode: GCM, whose authentication-only form is GMAC.
- RSA, ECDSA: no MAC (a MAC needs a secret shared by both sides); their counterpart is the signature.

---

## 2. Quick start

```python
from cryptoarithmetic.algebra import FieldElement, Point, scalar_mul
from cryptoarithmetic.elliptic import schoof
from cryptoarithmetic.hashing import SHA, SHA3
from cryptoarithmetic.mac import HMAC
from cryptoarithmetic.symmetric import AES, GCM
from cryptoarithmetic.asymmetric import generate_keypair, ECDSA

# 1. arithmetic in F_17
x, y = FieldElement(6, 17), FieldElement(3, 17)
print(x + y, x * y, x / y)        # FieldElement_17(9) FieldElement_17(1) FieldElement_17(2)

# 2. a point on y^2 = x^3 + 2x + 3 over F_97, and its multiples
p = 97
a, b = FieldElement(2, p), FieldElement(3, p)
P = Point(FieldElement(3, p), FieldElement(6, p), a, b)
print(P + P, scalar_mul(5, P))    # Point(80,10) Point(infinity)

# 3. how many points does that curve have? (Schoof's algorithm)
print(schoof(2, 3, 97))           # 100

# 4. hashes and a MAC
print(SHA("abc").hash())          # ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
print(SHA3("abc").hash())         # 3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532
print(HMAC(b"Jefe", "sha256").mac(b"what do ya want for nothing?").hex())
# 5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843

# 5. authenticated encryption with AES-GCM
ciphertext, tag = GCM(AES(bytes(range(16)))).encrypt(b"secret", bytes(12), b"header")
print(ciphertext.hex(), tag.hex())      # 3ab3e421fcef 5eecaa10c9d47dfdd06efce31967e254

# 6. RSA
public, private = generate_keypair(1024)
print(private.decrypt(public.encrypt(b"hello", "oaep"), "oaep"))      # b'hello'

# 7. ECDSA on a small curve; its 2053 points (a prime) were counted with schoof(1290, 1258, 2003)
q = 2003
G = Point(FieldElement(1, q), FieldElement(584, q), FieldElement(1290, q), FieldElement(1258, q))
ecdsa = ECDSA(G, 2053)
d, Q = ecdsa.generate_key_pair()
signature = ecdsa.sign(b"hello", d)
print(ecdsa.verify(b"hello", signature, Q), ecdsa.verify(b"hellp", signature, Q))   # True False
```

---

## 3. `algebra/arithmetic.py`

**`FieldElement(num, prime)`** — an element of F_p, `prime` must be prime.
Operations supported: addition, subtraction, multiplication, division, multiplication by an
integer (`3 * x`), exponentiation, additive inverse, multiplicative inverse (`.inverse()`)
and equality, modulo a prime `p`. Attributes `.num`, `.prime`.

**`Point(x, y, a, b)`** — a point on `y² = x³ + ax + b (mod p)` with `FieldElement`
coordinates; `Point(None, None, a, b)` is the point at infinity. A point that is not on the
curve raises `ValueError`.
Operations supported: addition (all cases: identity, opposite points, doubling), additive
inverse (`.inverse()`), equality and `.is_infinity()`.

**`scalar_mul(k, point)`** — `k·P` by double-and-add; `k` may be zero or negative.

**`extended_gcd(a, b)`** returns `(g, s, t)` with `s·a + t·b = g = gcd(a, b)`.
**`crt(residues, moduli)`** returns `(x, M)`, the solution of the congruences modulo `M`.

---

## 4. `algebra/polynomial.py`

**`PolynomialRing(*variables, order=None)`** — polynomials with integer coefficients, or
with coefficients in F_p when `order=p`. `ring({(2, 1): 3})` builds `3x²y` in
`PolynomialRing("x", "y")` (keys are exponent tuples). Polynomials combine only if they come
from the same ring object.

Operations supported: addition, subtraction, multiplication, exponentiation by a
non-negative integer, division with remainder (`f / g` returns `(quotient, remainder)`),
equality, scaling by a constant (`.scale(c)`) and `.is_zero_poly()`.

For univariate polynomials over F_p: `.degree()`, `.mod(m)`, `.xgcd(g)` (extended Euclid,
returns `(gcd, u, v)`), `.modexp(e, m)` (`f**e mod m`) and `.inverse_mod(m)` (`None` if not
invertible).

---

## 5. `elliptic/schoof.py`

**`schoof(a, b, p, verbose=False)`** — the number of points (including infinity) of
`y² = x³ + ax + b` over F_p, by Schoof's algorithm. `p` must be an odd prime `≥ 5` and the
curve non-singular, otherwise `ValueError`. `verbose=True` prints each small prime used or
skipped. It is a teaching implementation: from a fraction of a second at `p ≈ 100` to tens
of seconds at `p ≈ 10⁵`.

**`frobenius_trace_mod_l(a, b, p, l)`** — `t mod l`, where `t = p + 1 − #E(F_p)` is the trace
of Frobenius. A prime `l` that cannot be used for this curve is skipped by `schoof`.

**Division polynomials:** `div_poly_schoof(n, a, b, order_field=None)` gives `ψₙ(x, y)`;
`division_poly_AB(l, a, b, p)` returns `(A, B)` with `ψₗ = A(x) + B(x)·y`;
`division_poly_odd(l, a, b, p)` returns the polynomial in `x` for odd `l`;
`curve_poly(a, b, ring)` builds `x³ + ax + b`; `reduce_curve(poly, a, b)` applies `y² = x³ + ax + b`.

---

## 6. Hash functions

All take `bytes` or `str` (UTF-8). `.hash()` returns a hexadecimal string.

**`SHA(plaintext, variant="sha256")`** (`hashing/sha2.py`). Variants: `sha224`, `sha256`,
`sha384`, `sha512` (digests of 224, 256, 384, 512 bits).

**`SHA3(plaintext, variant="sha3_256")`** (`hashing/sha3.py`), also `.digest()` for bytes.
Variants: `sha3_224`, `sha3_256`, `sha3_384`, `sha3_512` (28, 32, 48, 64 bytes), and
`keccak_224`, `keccak_256`, `keccak_384`, `keccak_512` (the original Keccak padding).

**`SHAKE(plaintext, variant="shake128")`** — extendable output: `.hash(out_len=32)`,
`.digest(out_len=32)`. Variants: `shake128`, `shake256`.

**`CSHAKE(plaintext, variant="cshake128", function_name=b"", customization=b"")`** —
customizable SHAKE, same methods. Variants: `cshake128`, `cshake256`.

**`get_hash(name)`** — a uniform description of a fixed-output hash (`.digest(data)`,
`.digest_size`, `.block_size`). `HASH_NAMES` lists the names accepted by HMAC and RSA:
`sha224`, `sha256`, `sha384`, `sha512`, `sha3_224`, `sha3_256`, `sha3_384`, `sha3_512`.

---

## 7. Message authentication codes

Every MAC has `.mac(message)` (bytes) and `.verify(message, tag)` (constant-time).

**`HMAC(key, hash="sha256")`** (`mac/hmac.py`) — any hash name above, any key length.

**`KMAC(key, variant="kmac128", out_len=None, customization=b"", xof=False)`** (`mac/kmac.py`).
Variants: `kmac128` (default output 32 bytes), `kmac256` (64 bytes); `out_len` is in bytes;
`xof=True` gives KMACXOF.

**`CMAC(cipher)`** (`mac/cmac.py`) — `cipher` is an `AES`, `DES` or `TripleDES` object;
`.mac(message, tag_len=None)` accepts any message length and can truncate the tag.
**`CBCMAC(cipher)`** — the raw CBC-MAC: non-empty messages whose length is a multiple of the
block size, all of the same length.

GMAC is in [§8](#8-symmetric-encryption).

---

## 8. Symmetric encryption

**Block ciphers** (`symmetric/aes.py`, `des.py`): `AES(key)` with a 16-, 24- or 32-byte key;
`DES(key)` with 8 bytes; `TripleDES(key)` with 16 or 24 bytes. Each has `.block_size`,
`.encrypt_block(block)` and `.decrypt_block(block)` on exactly one block.

**`pkcs7_pad(data, block_size)`, `pkcs7_unpad(data, block_size)`** (`symmetric/padding.py`).

**`CBC(cipher)`** (`symmetric/cbc.py`): `.encrypt(plaintext, iv, padding=True)` and
`.decrypt(ciphertext, iv, padding=True)`; `iv` is one random block.

**`CTR(cipher, counter_bits=None)`** (`symmetric/ctr.py`): `.crypt(data, counter_block)`
(also `.encrypt` / `.decrypt`, which are the same operation); `counter_block` is one full block
whose low `counter_bits` bits are the counter.

**`GCM(cipher)`** (`symmetric/gcm.py`, AES only):
`.encrypt(plaintext, iv, aad=b"", tag_len=16)` returns `(ciphertext, tag)`;
`.decrypt(ciphertext, iv, tag, aad=b"")` returns the plaintext or raises
`ValueError("authentication failed")`; `.gmac(iv, aad, tag_len=16)` authenticates data
without encrypting.

Use a fresh random IV or nonce for every message (`os.urandom`). CBC and CTR do not detect
tampering: add a MAC, or use GCM.

---

## 9. Public-key cryptography

**RSA** (`asymmetric/rsa.py`). `generate_keypair(bits=2048, e=65537)` returns
`(public, private)`; `RSAPrivateKey(p, q, e)` rebuilds a key from two primes.

- `public.encrypt(message, scheme="oaep", hash="sha256", label=b"")` and
  `private.decrypt(ciphertext, scheme="oaep", hash="sha256", label=b"")`; schemes `oaep`
  (recommended) or `pkcs1v15`. Every decryption failure raises the same `ValueError("decryption error")`.
- `private.sign(message, scheme="pss", hash="sha256", salt_len=None)` and
  `public.verify(message, signature, scheme="pss", hash="sha256", salt_len=None)` (returns a
  `bool`); schemes `pss` (recommended) or `pkcs1v15`.
- `hash` is any name in `HASH_NAMES`. OAEP carries at most `key_bytes − 2·hash_size − 2`
  bytes: to encrypt more, encrypt a random AES key with RSA and the data with AES-GCM.
- `public.raw_encrypt(m)` / `private.raw_decrypt(c)`: the bare operation on integers (study only).

**ECDSA** (`asymmetric/ecdsa.py`). `ECDSA(point, n)` where `point` is a generator `G` of the
curve and `n` is its **prime** order. Methods: `.generate_key_pair()` returns `(d, Q)`;
`.sign(message, d)` returns `(r, s)` (SHA-256); `.verify(message, (r, s), Q)` returns a
`bool`; `.ecdh_key_exchange(d, Q)` returns the shared point. Use `schoof` to count the
points and find a suitable `n`.
This class draws its randomness from Python's `random`: for study only.

---

## 10. Common errors

- `ModuleNotFoundError: cryptoarithmetic`: run from the project folder, or `pip install -e .`.
- `AttributeError ... 'prime'`: write `3 * x`, not `x * 3`, for a `FieldElement`.
- `ValueError: Polynomials belong to different rings`: build the `PolynomialRing` once and reuse it.
- `ValueError: invalid padding` / `authentication failed` / `decryption error`: wrong key, IV or, nonce, or modified data (the exact reason is not revealed on purpose).
- `ValueError: key too short for this hash`: RSA-PSS with SHA-512 needs a key larger than 1024 bits.
- `schoof` slow: run with `verbose=True`; a skipped small prime forces a larger, costlier one.