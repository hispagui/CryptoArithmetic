"""
Two classes
"""

class FieldElement:
    """
    An element of a group GF(p) is an integer mod a prime p
    Some arithmetic operations (mod p)
    """
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
        # This is basically the pow(a,b,modulo) function in python3 : Exponentiation by squarring
        # Fast computation in O(log exp)
        # From Fermat little theorem : a^p-1 ≡ 1 (mod p)
        # We can reduce a^n ≡ a^{n mod p-1} (mod p)
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
        # From Fermat little theorem : a^-1 ≡ a^p-2 (mod p)
        return FieldElement(self.num ** (self.prime - 2), self.prime)
    
    def __neg__(self) -> "FieldElement": # -self
        # Returns -a (mod p)
        return FieldElement((-self.num) % self.prime, self.prime)
    
    def __truediv__(self, other : "FieldElement") -> "FieldElement": # self/other
        # Returns a/b (mod p) for a,b in GF(p)
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
        
def scalar_mul(k: int, point: "Point") -> "Point":
    '''
    Uses double-and-add method (runes in O(log k) instead of O(k))
    This uses bit representation of integers
        Exemple : k = 1,000,000 < 2^20
        The algo performs roughly 30 operations (20 doublings, and 10 additions)
        Instead of 1,000,000
    '''
    if k < 0:
        return scalar_mul(-k, point).inverse()
    
    res = Point(None, None, point.a, point.b)
    addend = point
    while k:
        if k & 1:               # if the current bit is 1, add current power of two
            res = res + addend
        addend = addend + addend  # double
        k >>= 1 # right bit shift
    return res
    
    

