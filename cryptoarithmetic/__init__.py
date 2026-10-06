"""
CryptoArithmetic: cryptography written from scratch in pure Python, for study.

    algebra      finite fields, elliptic-curve points, polynomials, primality testing
    elliptic     Schoof's point-counting algorithm
    hashing      SHA-2, SHA-3 (Keccak, SHAKE, cSHAKE)
    mac          HMAC, KMAC, CMAC, CBC-MAC
    symmetric    AES, DES, Triple-DES, and the modes CBC, CTR, GCM
    asymmetric   RSA (OAEP, PSS, PKCS#1 v1.5), ECDSA

Educational code: not constant-time, not audited. Do not protect real secrets with it.
"""

__version__ = "0.1.0"
