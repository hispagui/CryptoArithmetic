"""
Elliptic Curve Digital Signature Algorithm, uses existing finite field and elliptic curve arithmetic, as well as SHA for hashing

ECDSA object : (P, n)
P : point on an elliptic curve F that generates a subgroup G of E(F) of order n
n : order of G, should be prime

sign(message, private_key) -> signature
verify(message, signature, public_key) -> bool
"""

from arithmetic import Point, scalar_mul
from SHA2 import SHA
from random import randint

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
    Plays Alice, who works with Bob
    Alice has received public key from Bob
    Bob should also use this class
    """

    def __init__(self, point : "Point", n : int):
        self.n = n # The order of the group (is it possible to compute it directly from E(F(p) ?)
        self.point = point # This is the generating point

    def __repr__(self):
        return f"(Curve, Gen.point, Grp.order) = (y^2=x^3+{self.point.a.num}*x+{self.point.b.num}, {self.point}, {self.n})"

    def generate_key_pair(self) -> list: 
        private = randint(1, self.n - 1)    
        public = scalar_mul(private, self.point)
        return (private, public)

    def ecdh_key_exchange(self, private_key : int, public_key : "Point") -> "Point":
        # ECDH public key generation
        public_exchange = scalar_mul(private_key, public_key)
        return public_exchange
    
    def sign(self, message : bytes, private_key : int) -> list:
        """ 
        Alice wantrs to sign a message
        Can check algo on wikipedia of ECDSA
        """
        hash = SHA(message, "sha256")
        e = hash.hash()
        e = int(e, 16)
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
        
    def verify(self, message : bytes, signature, public_key : "Point") -> bool:
        '''
        Bob wants to verify Alice's signature
        '''
        (r,s) = signature
        n = self.n
        if not (1 <= r <= n-1 and 1 <= s <= n-1):
            return False
        s_inv = inv_mod(s, n)
        hash = SHA(message, "sha256")
        e = hash.hash()
        e = int(e, 16)
        u1 = e * s_inv
        u2 = r * s_inv
        R = scalar_mul(u1, self.point) + scalar_mul(u2, public_key)
        if R.is_infinity():
            return False
        if not(R.x.num % n == r):
            return False
        return True