"""
Small helpers shared by the whole library
    xor_bytes(a, b)               byte-wise XOR of two equal-length byte strings
    constant_time_equal(a, b)     comparison that does not stop at the first difference
    int_to_bytes(n, length)       big-endian encoding of a non-negative integer
    bytes_to_int(b)               big-endian decoding
    random_bytes(n)               n bytes from the operating system's CSPRNG
"""

import secrets

def xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("xor_bytes needs two byte strings of the same length")
    return bytes(x ^ y for x, y in zip(a, b))

def constant_time_equal(a: bytes, b: bytes) -> bool:
    # accumulate differences instead of returning at the first one, 
    # so running time doesn't depend on where inputs differ.
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= x ^ y
    return diff == 0

def int_to_bytes(n: int, length: int) -> bytes:
    return n.to_bytes(length, "big")

def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, "big")

def random_bytes(n: int) -> bytes:
    return secrets.token_bytes(n)
