from ff_ec_arithmetic import Point, scalar_mul
from random import randint

import hashlib

def pow_mod(num:int, exponent:int, prime:int):
    # This is basically pow function from python3
    # Fermat little theorem, we can reduce a^n ≡ a^{n mod p-1} (mod p)
    n = exponent % (prime - 1) 
    res = 1
    while n > 0: # exponentiation by squarring
        if n % 2 == 1:
            res = (res * num) % prime
        num = (num * num) % prime
        n = n // 2
    return res

def inv_mod(num : int, prime : int):
    # Fermat little theorem a^-1 ≡ a^p-2 (mod p)
    return pow_mod(num, prime-2, prime)


class ECDSA:
    """
    In this case I am Alice, and I work with Bob, who sent me his public key
    Bob also needs to use this class
    """

    def __init__(self, point : "Point", n : int):
        self.n = n # The order of the group (is it possible to ciolpute it directly from E(F(p) ?)
        self.point = point

    def generate_key_pair(self): 
        private = randint(1, self.n - 1)    
        public = scalar_mul(private, self.point)
        return (private, public)

    def ecdh_key_exchange(self, private_key : int, public_key : "Point") -> "Point":
        # ECDH public key generation
        public_exchange = scalar_mul(self.private_key, public_key)
        return public_exchange
    
    def _hash_message(self, message : bytes):
        # Hash message using SHA256
        digest = hashlib.sha256(message).digest()
        return int.from_bytes(digest, "big") % self.n

    def sign(self, message : bytes, private_key : int):
        """ 
        Alice wantrs to sign a message
        Can check algo on wikipedia of ECDSA
        """
        e = self._hash_message(message)
        n = self.n
 
        while True: # forces k to be a secure nonce !
            k = randint(1, self.n - 1)    
            R = scalar_mul(k, self.point) # Is a point
            r = R.x.num % n
            if r == 0:
                continue                              # unlucky k, retry
 
            k_inv = inv_mod(k, n)
            s = (k_inv * (e + r * private_key)) % n
            if s == 0:
                continue                              # unlucky k, retry
 
            return r, s
        
    def verify(self, message : bytes, signature, public_key : "Point"):
        '''
        Bob wants to verify Alice's signature
        '''
        (r,s) = signature
        n = self.n
        
        if not (1 <= r <= n-1 and 1 <= s <= n-1):
            return False
        
        s_inv = inv_mod(s, n)
        e = self._hash_message(message)
        u1 = e * s_inv
        u2 = r * s_inv
        R = scalar_mul(u1, self.point) + scalar_mul(u2, public_key)

        
        if R.is_infinity():
            return False
        if not(R.x.num % n == r):
            return False
        return True