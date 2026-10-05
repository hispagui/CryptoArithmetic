# CryptoArithmetic
 
Implementations, from scratch and in pure Python, of the arithmetic used in
elliptic-curve cryptography and point counting: finite fields, elliptic curves,
polynomials, Schoof's point-counting algorithm, the SHA-2 hash functions and ECDSA.
 
This README explains **how to call the code**. The mathematics (group law,
Schoof's algorithm, SHA-2, ECDSA, correctness checks) is in
[`THEORY.md`](THEORY.md).
 
## Contents
 
1. [Files and requirements](#1-files-and-requirements)
2. [Quick start](#2-quick-start)
3. [`arithmetic.py`](#3-arithmeticpy)
4. [`polynomial.py`](#4-polynomialpy)
5. [`schoof.py`](#5-schoofpy)
6. [`SHA2.py`](#6-sha2py)
7. [`ECDSA.py`](#7-ecdsapy)
8. [End to end: from a curve to a signature](#8-end-to-end-from-a-curve-to-a-signature)
9. [Troubleshooting](#9-troubleshooting)
---
 
## 1. Files and requirements
 
| File | Provides | Imports |
|---|---|---|
| `arithmetic.py` | `FieldElement`, `Point`, `scalar_mul`, `extended_gcd`, `crt` | – |
| `polynomial.py` | `PolynomialRing`, `Polynomial` | `arithmetic` |
| `schoof.py` | `schoof`, `frobenius_trace_mod_l`, division polynomials | `polynomial`, `arithmetic`, `primes` |
| `primes.py` | `prime_liste` (a list of primes) | – |
| `SHA2.py` | `SHA` (SHA-224/256/384/512) | – |
| `ECDSA.py` | `ECDSA` (keys, sign, verify, ECDH) | `arithmetic`, `SHA2` |

  
---
 
## 2. Quick start
 
```python
from arithmetic import FieldElement, Point, scalar_mul
from schoof import schoof
from SHA2 import SHA
 
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
 
# 4. a hash
print(SHA("abc").hash())          # ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
```
 
---
 
## 3. `arithmetic.py`
 
### 3.1 `FieldElement` — an element of F_p
 
```text
FieldElement(num: int, prime: int)
```
 
`num` is reduced modulo `prime` on construction. `prime` **must be prime** (not
checked).
 
Expressions/operations supported : addition, substraction, multiplication, division, scalar mulltiplication, exponentiation, additive inverse, multiplicative inverse and equality modulo a prime `p`

 
**Things to know**
 
- `x * 2` and `x + 1` raise `AttributeError`: write `2 * x` or `x + FieldElement(1, p)`.
- `x == 3` raises `AttributeError`: compare two `FieldElement`s.
- `FieldElement(0, p).inverse()` silently returns `0`.
- `FieldElement(0, 17) ** 16` returns `1` instead of `0` (see [`THEORY.md` §2](THEORY.md#2-finite-fields)).

### 3.2 `Point` — a point on `y² = x³ + ax + b (mod p)`
 
```text
Point(x: FieldElement, y: FieldElement, a: FieldElement, b: FieldElement)
Point(None, None, a, b)          # the point at infinity (group identity)
```
 
The constructor raises `ValueError` if `(x, y)` is not on the curve. It does not
check that the curve is non-singular.
 
Group operations supported : addition `P+Q`, inverse `-P`, point at infinity check, equality and scalar multiplication.

### 3.3 `extended_gcd` and `crt`
 
```text
extended_gcd(a: int, b: int) -> (g, s, t)      # s*a + t*b == g == gcd(a, b)
crt(residues: list, moduli: list) -> (x, M)    # x ≡ residues[i] (mod moduli[i]) for all i
```
 
`crt` returns the smallest non-negative solution `x` and the modulus `M` (the
lcm of the moduli, i.e. their product when they are pairwise coprime). It raises
`ValueError` if the lists differ in length, are empty, or the system has no
solution.
 
---
 
## 4. `polynomial.py`
 
### 4.1 Rings and polynomials
 
```text
PolynomialRing(*variables: str, order: int | None = None)
ring(terms: dict) -> Polynomial        # ring() or ring({}) is the zero polynomial
```
 
- `order=None`: integer coefficients (the ring `Z[x, y, ...]`).
- `order=p`: coefficients are coerced to `FieldElement(., p)` (the ring `F_p[x, y, ...]`).
- `terms` maps an **exponent tuple** (one entry per variable) to a coefficient: in
  `PolynomialRing("x", "y")`, `{(2, 1): 3}` is `3x²y`.
- Two polynomials can only be combined if they come from the **same
  `PolynomialRing` object**. Two separate calls to `PolynomialRing("x", order=97)`
  give incompatible rings.
- Over `F_p`, coefficients are displayed as residues in `[0, p)` (so `-1` shows as
`96` over `F_97`).
 
### 4.2 Operators and methods
 
Operations and expression supported: 
- addition `+`, substraction `-`, multiplication `*`, quotient with remainder `/` of polynomials, raising power `**`, equality `==`, scalling (scalar multiplication) `.scale(c)`, zero coefficient check `.is_zero(c)`, zero polynomial check `.is_zero_poly()` and univariate check `.is_univariate()`.


These need **univariate** polynomials over a field (`ValueError` otherwise; both
operands from the same ring):
- degree `.degree()`, remainder of division by m `.mod(m)`, gcd `.xgcd(g)`, exponent modulo m `.modexp(e, m)` and inverse modulo m `.inverse_mod(m)` (the last operations require the polynom to be univariate.)

**Things to know**
 
- There is no `Polynomial + int`; use `scale`, or build a constant polynomial with `ring({(0,)*n: c})`.
- The exponent tuples must have exactly one entry per variable.
- `mod`, `xgcd`, `modexp` and `inverse_mod` are only meaningful over a field (`order=p`).
---
 
## 5. `schoof.py`
 
Counts the points of `y² = x³ + ax + b` over `F_p`. Requirements: `p` an odd
prime with `p >= 5` (primality is **not** checked), a non-singular curve, and
`primes.py` (see [§1](#1-files-and-requirements)).
 
### 5.1 `schoof` — the point count
 
```text
schoof(a: int, b: int, p: int, verbose: bool = False) -> int
```
 
Returns `#E(F_p)`, the number of points **including the point at infinity**.
`a` and `b` may be negative or larger than `p` (they are reduced mod `p`).
 
| Raises | When |
|---|---|
| `ValueError` | `p < 5`, or the curve is singular (`4a³ + 27b² ≡ 0 mod p`) |
| `RuntimeError` | the 30 primes of `prime_liste` are not enough (not a realistic case) |
 
`verbose=True` prints, for each small prime `ℓ` tried, either `t mod ℓ` or that
`ℓ` was skipped.
 
Everything runs on the generic `Polynomial` class, so this is a teaching
implementation: from a fraction of a second for `p ≈ 100` to some tens of seconds
for `p ≈ 10⁵` (timings in [`THEORY.md` §5.12](THEORY.md#512-complexity-and-limits)).
 
### 5.2 `frobenius_trace_mod_l` — one residue
 
```text
frobenius_trace_mod_l(a: int, b: int, prime: int, l: int) -> int
```
 
Returns `t mod l` (in `[0, l)`) for a prime `l != prime`; `t` is the trace of
Frobenius, `t = p + 1 - #E(F_p)`. It raises `ZeroDivisionError` or `RuntimeError`
for a degenerate `(curve, l)` pair, which `schoof` catches.
 
 
### 5.3 Division polynomials
 
```text
div_poly_schoof(n: int, a: int, b: int, order_field: int | None = None) -> Polynomial
division_poly_AB(l: int, a: int, b: int, prime: int) -> (A, B)
division_poly_odd(l: int, a: int, b: int, prime: int) -> Polynomial
curve_poly(a: int, b: int, ring: PolynomialRing) -> Polynomial
reduce_curve(poly: Polynomial, a: int, b: int) -> Polynomial
```
 
- `div_poly_schoof(n, a, b)`: the `n`-th division polynomial `ψₙ(x, y)` in
  `PolynomialRing("x", "y")`, over `Z` (`order_field=None`) or `F_p`
  (`order_field=p`), in the form `A(x) + B(x)·y`.
- `division_poly_AB(l, a, b, p)`: `(A, B)` as univariate polynomials over `F_p`
  with `ψₗ = A + B·y`. For odd `l`, `B = 0`; for even `l`, `A = 0`.
- `division_poly_odd(l, a, b, p)`: `A` for odd `l` (`ValueError` for even `l`);
  its degree is `(l² - 1) / 2`.
- `curve_poly(a, b, ring)`: `x³ + ax + b` in any ring whose first variable is `x`.
- `reduce_curve(poly, a, b)`: rewrites a polynomial in `x, y` using
  `y² = x³ + ax + b` so that the `y`-degree is at most 1.

 
---
 
## 6. `SHA2.py`
 
```text
SHA(plaintext: str | bytes, variant: str = "sha256")
SHA.hash() -> str          # lowercase hexadecimal digest
```
 
| `variant` | digest size | hex length |
|---|---|---|
| `"sha224"` | 224 bits | 56 |
| `"sha256"` | 256 bits | 64 |
| `"sha384"` | 384 bits | 96 |
| `"sha512"` | 512 bits | 128 |
 
A `str` is encoded as UTF-8 first; `bytes` are hashed as they are.
 
```python
from SHA2 import SHA
 
print(SHA("abc").hash())
# ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
print(SHA("abc", "sha224").hash())
# 23097d223405d8228642a477bda255b32aadbce4bda0b3f7e36c9da7
print(SHA(b"abc", "sha512").hash()[:32])        # ddaf35a193617abacc417349ae204131
print(SHA("").hash())
# e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```
 
**Things to know**
 
- An unknown variant raises `KeyError` (`SHA("x", "md5")`).
- Only `str` and `bytes` are accepted; `bytearray` or `int` raise `AttributeError`
  (use `bytes(data)`).
- The whole message is hashed at once (no `update()`).
- `repr(SHA("abc"))` prints a stray quote: `("sha256",616263")`.
---
 
## 7. `ECDSA.py`
 
```text
ECDSA(point: Point, n: int)
```
 
- `point`: the generator `G` (a finite `Point`).
- `n`: the order of `G`. It **must be prime** and be the true order of `G`;
  neither is checked.
One `ECDSA` object holds the domain parameters (curve, `G`, `n`); both parties
build the same one and pass their keys to the methods.
 
Methods:
- `generate_key_pair()`
- `sign(message, private_key)`, hashed with SHA-256
- `verify(message, signature, public_key)`
- `ecdh_key_exchange(private_key, public_key)`, the shared point `private_key · public_key`
 
`repr(ecdsa)` shows the curve, the generator and `n`.
 
### 7.1 A complete example on a small curve
 
The curve `y² = x³ + 1290x + 1258` over `F_2003` has 2053 points (a prime, found
with `schoof(1290, 1258, 2003)`), so every point other than the identity
generates the whole group and `n = 2053`.
 
```python
import random
from arithmetic import FieldElement, Point
from ECDSA import ECDSA
 
p, a, b, n = 2003, 1290, 1258, 2053
G = Point(FieldElement(1, p), FieldElement(584, p), FieldElement(a, p), FieldElement(b, p))
 
ec = ECDSA(G, n)
print(ec)       # (Curve, Gen.point, Grp.order) = (y^2=x^3+1290*x+1258, Point(1,584), 2053)
 
random.seed(1)                           # only to make this example reproducible
d, Q = ec.generate_key_pair()
print(d, Q)                              # 551 Point(1723,1944)
 
sig = ec.sign(b"hello", d)
print(sig)                               # (1303, 1002)
 
print(ec.verify(b"hello", sig, Q))                       # True
print(ec.verify(b"hellp", sig, Q))                       # False   other message
print(ec.verify(b"hello", (sig[0], sig[1] % n + 1), Q))  # False   modified s
d2, Q2 = ec.generate_key_pair()
print(ec.verify(b"hello", sig, Q2))                      # False   wrong public key
print(ec.verify(b"hello", (0, sig[1]), Q))               # False   r out of range
 
# ECDH: both sides get the same point
da, Qa = ec.generate_key_pair()
db, Qb = ec.generate_key_pair()
print(ec.ecdh_key_exchange(da, Qb) == ec.ecdh_key_exchange(db, Qa))   # True
```
 
### 7.2 Building your own parameters with `schoof`
 
`schoof` gives `N = #E(F_p)`. Take `n` = a large prime factor of `N` and a
generator `G = (N/n)·P` for a random point `P` (why this works: [`THEORY.md`](THEORY.md#78-choosing-n-and-g-with-schoof)).
 
```python
import random
from arithmetic import FieldElement, Point, scalar_mul
from schoof import schoof
 
def random_point(a, b, p):
    """Toy sizes only: the square root is found by brute force."""
    A, B = FieldElement(a, p), FieldElement(b, p)
    while True:
        x = random.randrange(p)
        r = (x**3 + a*x + b) % p
        if r and pow(r, (p - 1) // 2, p) == 1:          # r is a non-zero square
            y = next(y for y in range(p) if y * y % p == r)
            return Point(FieldElement(x, p), FieldElement(y, p), A, B)
 
def prime_factors(m):
    f, d = [], 2
    while d * d <= m:
        while m % d == 0:
            f.append(d)
            m //= d
        d += 1
    if m > 1:
        f.append(m)
    return f
 
def find_generator(a, b, p):
    """Returns (G, n): n = largest prime factor of #E(F_p), G a point of order n."""
    N = schoof(a, b, p)
    n = max(prime_factors(N))
    h = N // n                                           # cofactor
    while True:
        G = scalar_mul(h, random_point(a, b, p))
        if not G.is_infinity():
            return G, n
 
random.seed(0)
G, n = find_generator(1290, 1258, 2003)
print(n, scalar_mul(n, G).is_infinity())     # 2053 True
 
G, n = find_generator(2, 3, 97)              # N = 100 = 2^2 * 5^2  ->  n = 5
print(n, scalar_mul(n, G).is_infinity())     # 5 True
```
 
### 7.3 Warning
 
This is educational code. In particular:
 
- **Randomness.** `generate_key_pair` and `sign` use `random.randint`, which is
  predictable, and a predictable or repeated nonce reveals the private key.
 
## 8. End to end: from a curve to a signature
 
```python
import random
from arithmetic import FieldElement, Point, scalar_mul
from schoof import schoof
from ECDSA import ECDSA
 
# 1. choose a curve and count its points
p, a, b = 2003, 1290, 1258
N = schoof(a, b, p)                              # 2053
assert all(N % q for q in range(2, int(N**0.5) + 1)), "N is prime, so n = N"
 
# 2. a generator (any non-identity point, since the group has prime order)
G = Point(FieldElement(1, p), FieldElement(584, p), FieldElement(a, p), FieldElement(b, p))
assert scalar_mul(N, G).is_infinity()
 
# 3. sign and verify
ec = ECDSA(G, N)
d, Q = ec.generate_key_pair()
message = b"pay 10 euros to Bob"
signature = ec.sign(message, d)
print(ec.verify(message, signature, Q))          # True
print(ec.verify(b"pay 99 euros to Bob", signature, Q))   # False
```