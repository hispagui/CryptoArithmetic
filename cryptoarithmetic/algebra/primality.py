"""
Primality testing and prime generation (needed by RSA)
    is_probable_prime(n, rounds=40)   trial division + Miller-Rabin
    generate_prime(bits)              random prime of exact bits
    mod_inverse(a, m)                 a^-1 mod m

Miller-Rabin: write n - 1 = 2^s * d with d odd. For a base a, n is declared
"probably prime" if a^d = 1 or a^(2^r d) = -1 (mod n) for some 0 <= r < s. A composite
number passes for at most 1/4 of the bases, so `rounds` random bases give an error
probability below 4^-rounds. See THEORY.md.
"""

import secrets

from .arithmetic import extended_gcd
from .primes import prime_liste

_SMALL_PRIMES = prime_liste[:200]          # trial division by the primes below 1223


def mod_inverse(a: int, m: int) -> int:
    # inverse of a mod m (error if gcd(a, m) != 1)
    g, s, _ = extended_gcd(a % m, m)
    if g != 1:
        raise ValueError("a is not invertible modulo m")
    return s % m


def is_probable_prime(n: int, rounds: int = 40) -> bool:
    if n < 2:
        return False
    for q in _SMALL_PRIMES:
        if n == q:
            return True
        if n % q == 0:
            return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = 2 + secrets.randbelow(n - 3)    # a in [2, n-2]
        x = pow(a, d, n)  # x = a^d mod n
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False             # a is a witness: n is composite
    return True


def generate_prime(bits: int, rounds: int = 40) -> int:
    # a random prime with exact nb of bits
    if bits < 8:
        raise ValueError("bits must be at least 8")
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if is_probable_prime(candidate, rounds):
            return candidate
