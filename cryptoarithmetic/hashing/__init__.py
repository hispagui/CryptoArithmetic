"""
Hash functions.
    sha2.py   SHA-224, SHA-256, SHA-384, SHA-512        class SHA
    sha3.py   SHA3-*, Keccak-*, SHAKE, cSHAKE           classes SHA3, SHAKE, CSHAKE

get_hash(name) returns a HashSpec describing fixed-output hash in uniform way (digest function on bytes, digest size, block size)
HMAC, RSA-OAEP, RSA-PSS and RSA-PKCS use it, so every one of these names works there:
sha224 sha256 sha384 sha512 sha3_224 sha3_256 sha3_384 sha3_512
"""

from collections import namedtuple

from .sha2 import SHA, VARIANTS as _SHA2_VARIANTS
from .sha3 import SHA3, SHAKE, CSHAKE, SHA3_VARIANTS

# digest(data: bytes) -> bytes ; digest_size and block_size in bytes
HashSpec = namedtuple("HashSpec", "name digest digest_size block_size")


def _sha2_spec(name):
    v = _SHA2_VARIANTS[name]
    return HashSpec(name,
                    lambda data: bytes.fromhex(SHA(data, name).hash()),
                    v["out_words"] * (v["w"] // 8),
                    v["block_bytes"])

def _sha3_spec(name):
    rate, out_len, _ = SHA3_VARIANTS[name]
    return HashSpec(name, lambda data: SHA3(data, name).digest(), out_len, rate)

_SPECS = {name: _sha2_spec(name) for name in _SHA2_VARIANTS}
_SPECS.update({name: _sha3_spec(name) for name in SHA3_VARIANTS if name.startswith("sha3_")})
HASH_NAMES = tuple(_SPECS)

def get_hash(name: str) -> HashSpec:
    try:
        return _SPECS[name]
    except KeyError:
        raise ValueError(f"unknown hash {name!r}; choose one of {', '.join(HASH_NAMES)}") from None
