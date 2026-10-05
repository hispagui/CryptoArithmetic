"""
Loris De Vos
Polynomial rings and polynomials; input should be in the form of a dict as follow,
    {(2,1,0):3, (0,2,0):-5, (0,0,0):7} which encods 3*x^2*y - 5*y^2 + 7 
    if order is not None (i.e. not in Z); a,b,c should be FieldElement(a,order), FieldElement(b,order), FieldElement(c,order)

handles polynomials over Z (default) and over finite fiedls of order p^n            
"""

from collections import defaultdict
from arithmetic import FieldElement

def monomial_divides(a : int, b : int):
    return all(x <= y for x, y in zip(a, b))

def monomial_div(a : int, b : int):
    return tuple(x - y for x, y in zip(a, b))






class PolynomialRing :

    def __init__(self, *variables : str, order = None):
        if not variables:
            raise ValueError("At least one variable is required.")
        self.variables = variables
        self.n = len(variables)
        self.order = order # F_q[x,y,z] or Z[x,y,z] if prime is None
    def __call__(self, terms = None) :
        return Polynomial(self, terms or {})
    

class Polynomial :
    def __init__(self, ring : "PolynomialRing", terms : dict):
        # terms as above
        self.ring = ring
        self.terms = defaultdict(self._zero, terms)
        for key, val in list(self.terms.items()): # can also compute over F_q(x,y,z)
            self.terms[key] = self._coher(val)

    def _coher(self, coeff ):
        # makes sure coedd are of the form FieldElement
        if isinstance(self.ring.order, int) and not isinstance(coeff, FieldElement):
            return FieldElement(coeff, self.ring.order)
        return coeff
    
    def _zero(self):
        # type of default valuie for "missing keys"
        if isinstance(self.ring.order, int):
            return FieldElement(0, self.ring.order)
        return 0

    def is_zero(self, coeff) -> bool:
        if isinstance(coeff, FieldElement):
            return coeff.num == 0   # or whatever attribute holds the residue
        return coeff == 0

    def clean(self): # drops monomials who have coefficient 0
        self.terms = defaultdict(self._zero, {m: c for m, c in self.terms.items() if not self.is_zero(c)})
    
    def __repr__(self) -> str:
        # useful for display
        if not self.terms:
            return "0"
        vars = self.ring.variables
        pieces = []
        for mono in sorted(self.terms.keys(), reverse = True) :
            if isinstance(self.terms[mono], int):
                coeff = self.terms[mono]
            if isinstance(self.terms[mono], FieldElement):
                coeff = self.terms[mono].num
            part = ""
            if coeff == -1 and any(e != 0 for e in mono):
                part += "-"
            elif coeff != 1 or mono == (0,)*self.ring.n:
                part += str(coeff)
            for var, exp in zip(vars, mono):
                if exp == 0:
                    continue
                part += var
                if exp > 1:
                    part += "^" + str(exp)
            pieces.append(part)
        s = " + ".join(pieces)
        s = s.replace("+ -", "- ")
        return s
    
    def is_univariate(self) -> bool:
        self.clean()  # zero-coefficient monomials don't count
        return all(all(e == 0 for e in mono[1:]) for mono in self.terms.keys())
    
    def _require_univariate(self, op: str):
        if not self.is_univariate():
            raise ValueError(
                f"Polynomial.{op}: {self!r} has a nonzero exponent in a "
                f"variable other than '{self.ring.variables[0]}' - {op} is "
                "only defined for univariate polynomials"
            )

    # dunder methods

    def __add__(self, other : "Polynomial") -> "Polynomial":
        if self.ring is not other.ring:
            raise ValueError("Polynomials belong to different rings.")
        result = self.ring()
        for m, c in self.terms.items():
            result.terms[m] += c
        for m, c in other.terms.items():
            result.terms[m] += c
        result.clean()
        return result
    
    def __sub__(self, other : "Polynomial") -> "Polynomial":
        if self.ring is not other.ring:
            raise ValueError("Polynomials belong to different rings.")
        result = self.ring()
        for m, c in self.terms.items():
            result.terms[m] += c
        for m, c in other.terms.items():
            result.terms[m] -= c
        result.clean()
        return result
    
    def __mul__(self, other : "Polynomial") -> "Polynomial":
        if self.ring is not other.ring:
            raise ValueError("Polynomials belong to different rings.")
        result = self.ring()
        for m1, c1 in self.terms.items():
            for m2, c2 in other.terms.items():
                mono = tuple(a+b for a,b in zip(m1,m2))
                result.terms[mono] += c1*c2
        result.clean()
        return result

    def __pow__(self, n : int) -> "Polynomial":
        # repeated squarring like in FieldElement.__pow__ 
        if n < 0:
            raise ValueError("Negative exponents are not supported for polynomials")
        result = self.ring({(0,) * self.ring.n: 1})  # the constant polynomial 1
        base = self
        while n > 0:
            if n & 1:
                result = result * base
            base = base * base
            n >>= 1
        return result

    def __truediv__(self, other) -> list:
        # polynomial long division algo (with rest)
        if not other.terms:
            raise ZeroDivisionError("Division by zero polynomial")
        if self.ring is not other.ring:
            raise ValueError("Polynomials are in different rings.")   
        
        R = self.ring()
        R.terms.update(self.terms) # remainder set at numerator
        Q = self.ring() # quotient set at 0
        is_field = isinstance(self.ring.order, int)

        def leading_term(poly):
            keys = [m for m, c in poly.terms.items() if not poly.is_zero(c)]
            if not keys:
                return None
            m = max(keys)
            return m, poly.terms[m]
        
        lt_d = leading_term(other)
        if lt_d is None:
            raise ZeroDivisionError("Division by zero polynomial")
        lm_d, lc_d = lt_d

        while True:
            lt_r = leading_term(R)
            if lt_r is None:
                break
            lm_r, lc_r = lt_r
            if not monomial_divides(lm_d, lm_r):
                break
            if is_field:
                lc_q = lc_r * lc_d.inverse()
            else:
                if lc_r % lc_d != 0:
                    break
                lc_q = lc_r // lc_d
            lm_q = monomial_div(lm_r, lm_d)
            t = self.ring({lm_q: lc_q})
            Q = Q + t
            R = R - t * other
        R.clean()
        Q.clean()
        return Q, R

    
    
    # the following methods only work for univariate polynomials
    def degree(self) -> int:
        self._require_univariate()
        if not self.terms:
            return -1
        return max(mono[0] for mono in self.terms.keys())

    def mod(self, modpoly: "Polynomial") -> "Polynomial":
        # remainder of self divided by modpoly (self mod modpoly)
        # uses __truediv__
        self._require_univariate("mod")
        modpoly._require_univariate("mod")
        _, r = self / modpoly
        r.clean()
        return r

    def xgcd(self, other: "Polynomial") -> list:
        # Extended Euclidean algorithm, returns (gcd, u, v) with
        # u*self + v*other == gcd.
        self._require_univariate("xgcd")
        other._require_univariate("xgcd")
        R = self.ring
        zero_mono = (0,) * R.n
        zero = R({zero_mono: 0})
        one = R({zero_mono: 1})
        r0, r1 = self, other
        s0, s1 = one, zero
        t0, t1 = zero, one
 
        def is_zero_p(poly):
            poly.clean()
            return not poly.terms
 
        while not is_zero_p(r1):
            q, r = r0 / r1
            r0, r1 = r1, r
            s0, s1 = s1, s0 - q * s1
            t0, t1 = t1, t0 - q * t1
        return r0, s0, t0


    def modexp(self, exp: int, modpoly: "Polynomial") -> "Polynomial":
        # (self**exp mod modpoly), via square-and-multiply, O(log exp)
        # polynomial multiplications instead of `exp` of them
        self._require_univariate("modexp")
        modpoly._require_univariate("modexp")
        R = self.ring
        zero_mono = (0,) * R.n
        result = R({zero_mono: 1})
        b = self.mod(modpoly)
        e = exp
        while e > 0:
            if e & 1:
                result = (result * b).mod(modpoly)
            b = (b * b).mod(modpoly)
            e >>= 1
        return result
 



