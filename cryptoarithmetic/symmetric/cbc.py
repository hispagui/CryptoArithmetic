"""
CBC, cipher block chaining
    CBC(cipher)     cipher can be AES, DES, TripleDES, ... (anything with block_size, encrypt_block, decrypt_block)
        .encrypt(plaintext, iv, padding=True)    -> ciphertext
        .decrypt(ciphertext, iv, padding=True)   -> plaintext

    C_i = E_K(P_i xor C_{i-1}),   C_0 = IV        P_i = D_K(C_i) xor C_{i-1}

IV must have exactly one block and be unpredictable and must not be reused with same key. 
CBC gives confidentiality only.
Authenticate the ciphertext (encrypt-then-MAC with HMAC / CMAC, or use GCM).
"""

from ..utils import xor_bytes
from .padding import pkcs7_pad, pkcs7_unpad


class CBC:
    def __init__(self, cipher):
        self.cipher = cipher
        self.block_size = cipher.block_size

    def _check_iv(self, iv: bytes):
        if len(iv) != self.block_size:
            raise ValueError(f"the IV must be exactly {self.block_size} bytes long")

    def encrypt(self, plaintext: bytes, iv: bytes, padding: bool = True) -> bytes:
        self._check_iv(iv)
        bs = self.block_size
        if padding:
            plaintext = pkcs7_pad(plaintext, bs)
        elif len(plaintext) % bs:
            raise ValueError("without padding the plaintext length must be a multiple of the block size")
        out, prev = [], iv
        for i in range(0, len(plaintext), bs):
            prev = self.cipher.encrypt_block(xor_bytes(plaintext[i:i + bs], prev))
            out.append(prev)
        return b"".join(out)

    def decrypt(self, ciphertext: bytes, iv: bytes, padding: bool = True) -> bytes:
        self._check_iv(iv)
        bs = self.block_size
        if len(ciphertext) % bs:
            raise ValueError("the ciphertext length must be a multiple of the block size")
        out, prev = [], iv
        for i in range(0, len(ciphertext), bs):
            block = ciphertext[i:i + bs]
            out.append(xor_bytes(self.cipher.decrypt_block(block), prev))
            prev = block
        plaintext = b"".join(out)
        return pkcs7_unpad(plaintext, bs) if padding else plaintext
