"""
Loris De Vos
everything that leeds to schoof's algo (computes number of points on elliptic curves y^2=x^3+ax+b), contains:
    division polynomial 
    trace of Frobnius endomorphism
built entirely on top of polynomial.py (PolynomialRing, Polynomial) and arithmetic.py (FieldElement, crt),
this file adds the coordinate ring S and a curve-point class over that ring S
"""

import math 
from polynomial import PolynomialRing, Polynomial
from arithmetic import FieldElement, crt
from primes import prime_liste



# ----------------------- Division Polynomial -----------------------

def curve_poly(a: int, b: int, ring: "PolynomialRing") -> "Polynomial":
    # builds g = x^3 + ax + b in wathever polynomial ring. 
    zeros = (0,) * (ring.n - 1)
    return Polynomial(ring, {(3,) + zeros: 1, (1,) + zeros: a, (0,) + zeros: b})

def reduce_curve(poly: "Polynomial", a: int, b: int) -> "Polynomial":
    # rewrites poly. using the fact that y^2 = g = x^3+ax+b
    # eliminates every y-power above 1
    # this keeps div_poly_schoof's monomial count low, when used to compute psi_l for large l.
    ring = poly.ring
    g = curve_poly(a, b, ring)
    result = ring()
    for (ex, ey), coeff in poly.terms.items():
        if poly.is_zero(coeff):
            continue
        k, r = divmod(ey, 2)
        term = Polynomial(ring, {(ex, r): coeff})
        if k:
            term = term * g.pow(k)
        result = result + term
    result.clean()
    return result

def div_poly_schoof(n : int, a : int , b : int, order_field = None) -> "Polynomial":
    # builds [psi_0, psi_1, ..., psi_n] for y^2 = x^3+ax+b over F_p (or Z)
    # following https://en.wikipedia.org/wiki/Division_polynomials
    # also every psi_m is passed through reduce_curve() as soon as it's computed

    R = PolynomialRing("x", "y", order = order_field)
    psi0 = Polynomial(R, {(0,0) : 0})  #0
    psi1 = Polynomial(R, {(0,0) : 1})  #1
    psi2 = Polynomial(R, {(0,1) : 2})  #2y
    psi3 = Polynomial(R, {(4,0):3, (2,0):(6*a), (1,0):(12*b), (0,0):(-a*a)})
    psi4 = Polynomial(R, {(0,1) : 4}) * Polynomial(R, {(6,0):1, (4,0):(5*a), (3,0):(20*b), (2,0):((-5)*a*a), (1,0):((-4)*a*b), (0,0): (-8*b*b - a*a*a)})  #4y*...
    psi_liste = [psi0, psi1, psi2, psi3, psi4]
    if n < 5:
        return psi_liste[n]
    for m in range(5, n + 1):
        if m % 2 == 1:
            k = (m - 1) // 2
            #  psi_{2k+1} = psi_{k+2} psi_k^3 - psi_{k-1} psi_{k+1}^3
            psi_m = (psi_liste[k+2] * psi_liste[k] * psi_liste[k] * psi_liste[k]
                      - psi_liste[k-1] * psi_liste[k+1] * psi_liste[k+1] * psi_liste[k+1])
        else:
            k = m // 2
            #  psi_{2k} = (psi_k / 2y) * (psi_{k+2} psi_{k-1}^2 - psi_{k-2} psi_{k+1}^2)
            bracket = (psi_liste[k+2] * psi_liste[k-1] * psi_liste[k-1]
                       - psi_liste[k-2] * psi_liste[k+1] * psi_liste[k+1])
            quotient, remainder = (psi_liste[k] * bracket) / psi2
            remainder.clean()
            assert not remainder.terms, (
                f"psi_{k} * bracket was not exactly divisible by 2y at m={m} "
                f"(remainder={remainder}); this should never happen mathematically"
            )
            psi_m = quotient
        psi_m = reduce_curve(psi_m, a, b)
        psi_liste.append(psi_m)
    return psi_liste[n]

def division_poly_AB(l: int, a: int, b: int, prime: int):
    # Returns A, B, univ. polys. such that psi_l(x, y) = A(x) + B(x)*y.
    # pairs with div_poly_schoof 

    bivariate = div_poly_schoof(l, a, b, order_field=prime)
    x_ring = PolynomialRing("x", order=prime)
    A_terms, B_terms = {}, {}
    for (ex, ey), coeff in bivariate.terms.items():
        if bivariate.is_zero(coeff):
            continue
        if ey == 0:
            A_terms[(ex,)] = coeff
        elif ey == 1:
            B_terms[(ex,)] = coeff
        else:
            raise AssertionError(
                f"psi_{l} has a y^{ey} term after reduce_curve -- "
                "div_poly_schoof should never leave y-degree above 1"
            )
    return Polynomial(x_ring, A_terms), Polynomial(x_ring, B_terms)

def division_poly_odd(l: int, a: int, b: int, prime: int) -> "Polynomial":
    """
    f_l(x) mod p for odd l: the (purely-x) l-th division polynomial, whose
    roots are exactly the x-coordinates of the l-torsion points of
    E: y^2 = x^3+ax+b over (an algebraic closure of) F_p.
    Degree is (l^2 - 1) / 2.
    """
    if l % 2 == 0:
        raise ValueError("division_poly_odd requires an odd l (even l has a y factor)")
    A, _B = division_poly_AB(l, a, b, prime)
    return A









# ----------------------- the ring S = F_p[x]/(f_l(x)) [y] / (y^2 - g(x)) -----------------------

class RingS:
    # class for ring S = F_p[x]/(f_l(x)) [y] / (y^2 - g(x))
    # keeps track of elements of the form A(x) + B(x)*y in S (reduced mod f)

    __slots__ = ("A", "B", "f", "g", "prime")
 
    def __init__(self, A: "Polynomial", B: "Polynomial", f: "Polynomial", g: "Polynomial", prime: int):
        self.f = f
        self.g = g
        self.prime = prime
        self.A = A.mod(f)
        self.B = B.mod(f)
 
    def _check_same_ring(self, other: "RingS"):
        if self.f is not other.f or self.g is not other.g:
            raise TypeError("elements from different copies of S")
 
    def __repr__(self):
        return f"RingS({self.A} + ({self.B})*y)"
 
    def __eq__(self, other: "RingS") -> bool:
        self._check_same_ring(other)
        return self.A == other.A and self.B == other.B
 
    def __add__(self, other: "RingS") -> "RingS":
        self._check_same_ring(other)
        return RingS(self.A + other.A, self.B + other.B, self.f, self.g, self.prime)
 
    def __sub__(self, other: "RingS") -> "RingS":
        self._check_same_ring(other)
        return RingS(self.A - other.A, self.B - other.B, self.f, self.g, self.prime)
 
    def __mul__(self, other: "RingS") -> "RingS":
        self._check_same_ring(other)
        # (A1+B1 y)(A2+B2 y) = (A1 A2 + B1 B2 g) + (A1 B2 + A2 B1) y
        A = self.A * other.A + self.B * other.B * self.g
        B = self.A * other.B + other.A * self.B
        return RingS(A, B, self.f, self.g, self.prime)
 
    def __rmul__(self, const) -> "RingS":
        return self.scale(const)
 
    def __neg__(self) -> "RingS":
        return self.scale(self.prime - 1)
 
    def scale(self, c) -> "RingS":
        return RingS(self.A.scale(c), self.B.scale(c), self.f, self.g, self.prime)
 
    def is_zero(self) -> bool:
        return self.A.is_zero_poly() and self.B.is_zero_poly()
 
    def inverse(self) -> "RingS":
        # (A+By)^-1 = (A-By) / (A^2 - B^2*g)
        denom = (self.A * self.A - self.B * self.B * self.g).mod(self.f)
        inv = denom.inverse_mod(self.f)
        if inv is None:
            # f_l(x) need not be irreducible mod p, so S isn't guaranteed to be a field 
            # sometimes element we need to invert might be a zero divisor for a pair (l, p) 
            # schoof() below handles it by simply trying a different small prime l instead
            raise ZeroDivisionError("element not invertible mod f_l (degenerate prime for this l)")
        neg_B = self.B.scale(self.prime - 1)
        return RingS((self.A * inv).mod(self.f), (neg_B * inv).mod(self.f), self.f, self.g, self.prime)
 
    def __truediv__(self, other: "RingS") -> "RingS":
        return self * other.inverse()



# ----------------------- elliptic-curve points with coordinates in S ---------------------------
 
class SymbolicPoint:
    # points on elliptic curves with coordinate rings S
    # used to represent l-torsion point (x,y) 
    # very similar to what was done in arithmetic.py

    __slots__ = ("x", "y", "a")
 
    def __init__(self, x, y, a: "RingS"):
        self.x = x
        self.y = y
        self.a = a
 
    def is_infinity(self) -> bool:
        return self.x is None
 
    def __eq__(self, other: "SymbolicPoint") -> bool:
        if self.is_infinity() or other.is_infinity():
            return self.is_infinity() and other.is_infinity()
        return self.x == other.x and self.y == other.y and self.a == other.a
 
    def __repr__(self):
        return "SymbolicPoint(infinity)" if self.is_infinity() else f"SymbolicPoint({self.x}, {self.y})"
 
    def __add__(self, other: "SymbolicPoint") -> "SymbolicPoint":
        if self.a != other.a:
            raise TypeError("points are not on the same curve")
        if self.is_infinity():
            return other
        if other.is_infinity():
            return self
        # P + (-P) = infinity  (same x, opposite y)
        if self.x == other.x and self.y != other.y:
            return SymbolicPoint(None, None, self.a)
        # P + Q = R  (P != Q)
        if self.x != other.x:
            slope = (other.y - self.y) / (other.x - self.x)
            x3 = slope * slope - self.x - other.x
            y3 = slope * (self.x - x3) - self.y
            return SymbolicPoint(x3, y3, self.a)
        # P + P = 2P  (tangent at P)
        if self == other:
            if self.y.is_zero():             # vertical tangent -> order-2 point
                return SymbolicPoint(None, None, self.a)
            slope = (3 * self.x * self.x + self.a) / (2 * self.y)
            x3 = slope * slope - 2 * self.x
            y3 = slope * (self.x - x3) - self.y
            return SymbolicPoint(x3, y3, self.a)
        raise RuntimeError("unhandled point addition case")
 
    def inverse(self) -> "SymbolicPoint":
        if self.is_infinity():
            return self
        return SymbolicPoint(self.x, -self.y, self.a)
 
 
def symbolic_scalar_mul(k: int, point: "SymbolicPoint") -> "SymbolicPoint":
    # double-and-add scalar multiplication as in arithmetic.scalar_mul
    if k < 0:
        return symbolic_scalar_mul(-k, point.inverse())
    res = SymbolicPoint(None, None, point.a)
    addend = point
    while k:
        if k & 1:
            res = res + addend
        addend = addend + addend
        k >>= 1
    return res



# ----------------------- trace of Frobenius mod l -----------------------


def _trace_mod_2(a: int, b: int, prime: int) -> int:
    # t mod 2 not computed via div poly
    # since #E(F_p) = p+1-t and p is odd, t is even iff #E(F_p) is even iff E has a point of order 2 iff x^3+ax+b has a root in F_p
    # can be tested via  gcd(x^p - x, x^3+ax+b) != 1
    ring = PolynomialRing("x", order=prime)
    g = curve_poly(a, b, ring)
    x_poly = ring({(1,): 1})
    xp = x_poly.mod_pow(prime, g)          # x^p mod g(x)
    diff = (xp - x_poly).mod(g)            # x^p - x
    gcd = diff.gcd(g)
    gcd.clean()
    degree = max((k[0] for k in gcd.terms), default=-1)
    return 0 if degree >= 1 else 1

def frobenius_trace_mod_l(a: int, b: int, prime: int, l: int) -> int:
    # computes t mod l, where t is Frob trace of E: y^2 = x^3 + ax + b over F_p, for prime l != p
    """
    Computes t mod l, where t is the trace of Frobenius of
    E: y^2 = x^3 + ax + b over F_p (`prime` = p), for a prime l != p.
 
    Looks, in the ring S = F_p[x]/(f_l(x))[y]/(y^2-g(x)), for the unique
    tau in [0, l) with
        phi_p^2(P) + (p mod l)*P  =  tau * phi_p(P)
    for the generic point P=(x,y), where phi_p(x,y)=(x^p, y^p) is
    Frobenius. That tau is t mod l.
    """
    if l == 2:
        return _trace_mod_2(a, b, prime)
 
    f = division_poly_odd(l, a, b, prime)
    x_ring = f.ring
    g = curve_poly(a, b, x_ring)
 
    zero, one, x_poly = x_ring({}), x_ring({(0,): 1}), x_ring({(1,): 1})
    a_elem = RingS(x_ring({(0,): a % prime}), zero, f, g, prime)
 
    q_l = prime % l
 
    P = SymbolicPoint(RingS(x_poly, zero, f, g, prime), RingS(zero, one, f, g, prime), a_elem)
 
    # phi_p(P) = (x^p mod f,  (g(x)^((p-1)/2) mod f) * y)
    Xq = x_poly.mod_pow(prime, f)
    Yq = g.mod_pow((prime - 1) // 2, f)
    phiP = SymbolicPoint(RingS(Xq, zero, f, g, prime), RingS(zero, Yq, f, g, prime), a_elem)
 
    # phi_p^2(P) = (x^(p^2) mod f, (g(x)^((p^2-1)/2) mod f) * y)   -- applying
    # Frobenius twice is the same map with exponent p^2 instead of p.
    Xq2 = x_poly.mod_pow(prime * prime, f)
    Yq2 = g.mod_pow((prime * prime - 1) // 2, f)
    phi2P = SymbolicPoint(RingS(Xq2, zero, f, g, prime), RingS(zero, Yq2, f, g, prime), a_elem)
 
    qP = symbolic_scalar_mul(q_l, P)
    lhs = phi2P + qP
 
    for tau in range(l):
        rhs = symbolic_scalar_mul(tau, phiP)
        if lhs == rhs:
            return tau
    raise RuntimeError(f"no matching tau found for l={l} (a={a}, b={b}, p={prime})")




_small_primes = prime_liste[0:30]

def schoof(a: int, b: int, p: int, verbose: bool = False) -> int:
    # computes #E(F_p) for E: y^2 = x^3 + ax + b, via Schoof's algorithm
    if (4 * a**3 + 27 * b * b) % p == 0:
        raise ValueError("singular curve: 4a^3 + 27b^2 = 0 (mod p)")
 
    bound = 4 * math.isqrt(p) + 1     # need prod(l_i) > this, by Hasse's bound
    residues, moduli, prod = [], [], 1
    idx = 0
    while prod <= bound:
        if idx >= len(_small_primes):
            raise RuntimeError("ran out of small primes, p is too large for this table")
        l = _small_primes[idx]
        idx += 1
        if l == p:
            continue
        try:
            t_l = frobenius_trace_mod_l(a, b, p, l)
        except (ZeroDivisionError, RuntimeError):
            # a "bad" (l, p) pair, f_l(x) happened to be non-squarefree
            # (or similar) mod p; just use a different small prime instead.
            if verbose:
                print(f"  l={l}: degenerate for this curve, skipping")
            continue
        if verbose:
            print(f"  l={l}: t mod l = {t_l}")
        residues.append(t_l)
        moduli.append(l)
        prod *= l
 
    t_mod_M, M = crt(residues, moduli)
    # t mod M represent any of t, t+M, t-M, t+2M, ... but Hasse bound guarantee exactly one in the interval
    # Hasse bound: |t| <= 2*sqrt(p) and M > 4*sqrt(p)

    t = t_mod_M
    if t > 2 * math.isqrt(p) + 1:
        t -= M
 
    return p + 1 - t