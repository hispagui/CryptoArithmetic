"""
CTR, counter mode: turns a block cipher into a stream cipher
    CTR(cipher, counter_bits=None)
        .crypt(data, counter_block)   -> bytes   (encryption and decryption are the same)
        .encrypt / .decrypt           aliases of crypt

    keystream block i = E_K(counter_block + i)        output = data xor keystream

counter_block is a full block (16 bytes for AES, 8 for DES)
Its low counter_bits bits are incremented as a big-endian integer modulo 2^counter_bits;
the remaining high bits (the nonce) stay fixed. 
For example, a 96-bit nonce with a 32-bit counter starting at 1:
    CTR(aes, counter_bits=32).crypt(data, nonce + (1).to_bytes(4, "big"))
"""

from ..utils import xor_bytes


class CTR:
    def __init__(self, cipher, counter_bits: int = None):
        self.cipher = cipher
        self.block_size = cipher.block_size
        self.counter_bits = 8 * self.block_size if counter_bits is None else counter_bits
        if not 1 <= self.counter_bits <= 8 * self.block_size:
            raise ValueError("counter_bits must be between 1 and the block size in bits")

    def crypt(self, data: bytes, counter_block: bytes) -> bytes:
        bs = self.block_size
        if len(counter_block) != bs:
            raise ValueError(f"the counter block must be exactly {bs} bytes long")
        n_blocks = -(-len(data) // bs)
        if n_blocks > 1 << self.counter_bits:
            raise ValueError("message too long: the counter would wrap around and repeat")
        value = int.from_bytes(counter_block, "big")
        mask = (1 << self.counter_bits) - 1
        fixed, counter = value & ~mask, value & mask
        out = []
        for i in range(n_blocks):
            block = (fixed | ((counter + i) & mask)).to_bytes(bs, "big")
            keystream = self.cipher.encrypt_block(block)
            chunk = data[i * bs:(i + 1) * bs]
            out.append(xor_bytes(chunk, keystream[:len(chunk)]))
        return b"".join(out)

    encrypt = decrypt = crypt
