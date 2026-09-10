"""
Finite Field arithmetic
Groups derived from elliptic curve
"""


class FieldElement:
    # an element of a group GF(p) is an integer mod a prime p
    # some arithmetic operations (mod p)
    def __init__(self, num:int, prime:int):
        num = num % prime 
        self.num = num
        self.prime = prime

    def _check_same_field(self, other: "FieldElement"):
        if self.prime != other.prime:
            raise TypeError("Cannot operate on elements from different fields")
        
    def __repr__(self): # print(self)
        return f"FieldElement_{self.prime}({self.num})"
    
    # dunder methods for arithmetic operations
    def __eq__(self, other): # self = other
        if other is None:
            return False
        return self.num == other.num and self.prime == other.prime
    
    def __add__(self, other: "FieldElement") -> "FieldElement": # self+other
        self._check_same_field(other)
        return FieldElement((self.num + other.num) % self.prime, self.prime)

    def __sub__(self, other : "FieldElement") -> "FieldElement": # self-other
        self._check_same_field(other)
        return FieldElement((self.num - other.num) % self.prime, self.prime)
    
    def __mul__(self, other : "FieldElement") -> "FieldElement": # self*other
        self._check_same_field(other)
        return FieldElement((self.num * other.num) % self.prime, self.prime)
    
    def __rmul__(self, const : int) -> "FieldElement": # self*constant
        return FieldElement((self.num * const) % self.prime, self.prime)

    def __pow__(self, exp : int) -> "FieldElement": # self**exp
        # this is basically the pow(a,b,modulo) function in python3 : Exponentiation by squarring
        # fast computation in O(log exp)    fermat little theorem : a^p-1 ≡ 1 (mod p)
        # we can reduce a^n ≡ a^{n mod p-1} (mod p)
        n = exp % (self.prime - 1)
        result = 1
        a = self.num
        while n > 0: # exponentiation by squarring
            if n % 2 == 1:
                result = (result * a) % self.prime
            a = (a*a) % self.prime
            n = n // 2 # division with remainder (discards rest)
        return FieldElement(result, self.prime)
    
    def inverse(self) -> "FieldElement": # self^-1
        # from Fermat little theorem : a^-1 ≡ a^p-2 (mod p)
        return self.__pow__(self.prime - 2)
    
    def __neg__(self) -> "FieldElement": # -self
        # returns -a (mod p)
        return FieldElement((-self.num) % self.prime, self.prime)
    
    def __truediv__(self, other : "FieldElement") -> "FieldElement": # self/other
        # returns a/b (mod p) for a,b in GF(p)
        self._check_same_field(other)
        return self * other.inverse()
    




class Point:
    """
    Keeps track of points on elliptic curves defined by y^2 = x^3 + ax + b (mod p)
    Some elliptic curve operation between them

    ADD POINT COUNTING ALGO from SCHOOF (in O(log p))

    MONTGOMERY CURVES ?

    EDWARD CURVES ?
    """
    __slots__ = ("x", "y", "a", "b") # restricts Point to only have these attributes

    def __init__(self, x: "FieldElement", y: "FieldElement", a: "FieldElement", b: "FieldElement"):
        # a,b are parameters for the curve
        # x,y are parameters for the point
        # and (x,y) = (None, None) is the point at infinity (above), the identity
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        q = self.a.prime
        if x is None and y is None:
            return
        if y * y != (x * x * x) + (a * x) + b:
            raise ValueError(f"({x.num}, {y.num}) is not on the curve")
        
    def __eq__(self, other):
        return (
            self.x == other.x
            and self.y == other.y
            and self.a == other.a
            and self.b == other.b
        )
    
    def __repr__(self):
        if self.x is None:
            return "Point(infinity)"
        return f"Point({self.x.num},{self.y.num})"

    def is_infinity(self) -> bool:
        return self.x is None
        
    def __add__(self, other: "Point") -> "Point":
        if self.a != other.a or self.b != other.b:
            raise TypeError("Points are not on the same curve")
        # P + infinity = P
        if self.is_infinity():
            return other
        # infinity + P = P
        if other.is_infinity():
            return self
        # P + (-P) = infinity  (same x, opposite y, third point must be infinity by symmetry)
        if self.x == other.x and self.y != other.y: 
            return Point(None, None, self.a, self.b)
        # P + Q = R (PQ slope)
        if self.x != other.x:
            slope = (other.y - self.y) / (other.x - self.x)
            x3 = slope * slope - self.x - other.x
            y3 = slope * (self.x - x3) - self.y    # -self.y because we need to mirror !
            return Point(x3, y3, self.a, self.b)
        # P + P = 2P (tangent at P slope)
        if self == other:
            if self.y.num == 0: # tangent is a vertical line
                return Point(None, None, self.a, self.b) # so 
            slope = (3 * self.x * self.x + self.a) / (2 * self.y) # implicit differentiation of curve
            x3 = slope * slope - 2 * self.x
            y3 = slope * (self.x - x3) - self.y
            return Point(x3, y3, self.a, self.b)
        raise RuntimeError("Unhandled point addition case")
    
    def inverse(self) -> "Point":
        if self.is_infinity():
            return self
        else:
            return Point(self.x, - self.y, self.a, self.b)


    def trace_frobenius(self, prime) -> "FieldElement":
        return None
    
    """
    def schoof_algo(self) -> int:
        M = 1, t = 1
        while M <= 4*sqrt(self.q):
            for prime in primes.prime_liste :
                if not (prime % self.q == 0):
                    t_prime

        return None
    """
    
    def order_point(self):
        # METHOD CALLS SCHOOF ALGO
        return None
        
def scalar_mul(k: int, point: "Point") -> "Point":
    # uses double-and-add method (runes in O(log k) instead of O(k))
    # this uses bit representation of integers
    # exemple : k = 1,000,000 < 2^20, algo performs roughly 30 operations (20 doublings, and 10 additions) instead of 1,000,000
    if k < 0:
        return scalar_mul(-k, point).inverse()
    
    res = Point(None, None, point.a, point.b)
    addend = point
    while k:
        if k & 1:          # if the current bit is 1, add current power of two
            res = res + addend
        addend = addend + addend  # double
        k >>= 1 # right bit shift
    return res
    
    

def extended_gcd(a:int, b:int) -> tuple:
    # extended Euclidean algorithm
    # returns gcd(a,b), x, y such that ax + by = gcd(a,b)
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return old_r, old_s, old_t

def crt(residues: list, moduli: list) -> list:
    # Chinese Remainder Theorem
    # given residues [r1, r2, ...] and pairwise coprime moduli [m1, m2, ...]
    # returns   (x, M) with M = product(moduli) and x is the unique solution to x ≡ r_i (mod m_i) for every i
    if len(residues) != len(moduli):
        raise ValueError("residues and moduli must have the same length")
    if not residues or not moduli:
        raise ValueError("residues and moduli must be non-empty")
    x, M = residues[0] % moduli[0], moduli[0]
    for r_i, m_i in zip(residues[1:], moduli[1:]):
        g, p, _q ! extended_gcd(M, m_i)
        if (r_i - x_i) % g != 0:
            raise ValueError("moduli are not pairwise coprime")
        lcm = M // g * m_i
        x = (x +(r_i - x_i) // g * p % (m_i // g) * M) % lcm
        M = lcm
    return x % M, M