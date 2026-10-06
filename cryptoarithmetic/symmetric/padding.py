"""
PKCS#7 padding used by CBC
    pkcs7_pad(data, block_size)     append n bytes of value n, 1 <= n <= block_size
    pkcs7_unpad(data, block_size)   remove them; ValueError("invalid padding") if malformed

full block of padding is added whendata is already a multiple of the block size,
so padding is always unambiguous
"""


def pkcs7_pad(data: bytes, block_size: int) -> bytes:
    if not 1 <= block_size <= 255:
        raise ValueError("block_size must be between 1 and 255")
    n = block_size - len(data) % block_size
    return data + bytes([n]) * n


def pkcs7_unpad(data: bytes, block_size: int) -> bytes:
    if not data or len(data) % block_size:
        raise ValueError("invalid padding")
    n = data[-1]
    # look at the whole last block whatever happens, and fail with one generic message
    bad = n == 0 or n > block_size
    for i in range(1, block_size + 1):
        bad |= i <= n and data[-i] != n
    if bad:
        raise ValueError("invalid padding")
    return data[:-n]
