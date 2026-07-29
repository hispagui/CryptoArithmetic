"""
Loris De Vos

terms should be a dic {(2,1,0):3, (0,2,0):-5, (0,0,0):7}
encods 3*x^2*y - 5*y^2 + 7 
if order is not None, a,b,c should be FieldElement(a,order), FieldElement(b,order), FieldElement(c,order)

handles polynomials over Z (default) and over finite fiedls of order p^n            
"""

from collections import defaultdict
from arithmetic import FieldElement

def monomial_divides(a, b):
    return all(x <= y for x, y in zip(a, b))
def monomial_div(a, b):
    return tuple(y - x for x, y in zip(a, b))






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
        self.ring = ring
        self.terms = defaultdict(self._zero, terms)
        for key, val in list(self.terms.items()): # can also compute over F_q(x,y,z)
            self.terms[key] = self._coher(val)

    def _coher(self, coeff ):
        if isinstance(self.ring.order, int) and not isinstance(coeff, FieldElement):
            return FieldElement(coeff, self.ring.order)
        return coeff
    
    def _zero(self):
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
            result.terms[m] -= c
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
        #Repeated squarring like in FieldElement.__pow__ 
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
        # polynomial long division algo
        # actually this is division with rest
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

    
    
    # Following methods only work for univariate polynomials
    def poly_degree(self) -> int:
        self.clean()
        if not self.terms:
            return -1
        return max(ex for (ex, _ey) in self.terms.keys())
    
    def reduce_mod(poly: "Polynomial", modpoly: "Polynomial") -> "Polynomial":
    """Remainder of poly divided by modpoly (poly mod modpoly)."""
    _, r = poly / modpoly
    r.clean()
    return r


#---------------------------------------------------
# Division polynomial
#---------------------------------------------------

def reduce_mod_curve(poly : "Polynomial", a : int, b:int) -> "Polynomial":
    """
    Each monomial c * x^ex * y^ey is rewritten as 
    c * x^ex * y^ey = c * x^ex * (y^2)^k * y^r
    with y^2 = (x^3 + a*x + b), k = ey//2 and r = ey % 2
    making every monomial in y have exponent 0 or 1 (since y^r)
    """
    R = poly.ring
    g = Polynomial(R, {(3, 0): 1, (1, 0): a, (0, 0): b})  # x^3 + a*x + b
    result = R()
    for (ex, ey), coeff in poly.terms.items(): # as in dictionnary
        if poly.is_zero(coeff):
            continue
        k, r = divmod(ey, 2)
        gk = g ** k  # (x^3+ax+b)^k ; g**0 is the identity polynomial "1"
        term = Polynomial(R, {(ex, r): coeff}) * gk
        result = result + term
    result.clean()
    return result

def div_poly_schoof(n : int, a : int , b : int, order_field = None) -> "Polynomial":
    '''
    Builds [psi_0, psi_1, ..., psi_n] for y^2 = x^3+ax+b over F_p
    (following https://en.wikipedia.org/wiki/Division_polynomials)
    '''
    R = PolynomialRing("x", "y", order = order_field)
    size = max(n +1, 5)
    psi = [None] * size
    psi[0]= Polynomial(R, {(0,0) : 0})  #0
    psi[1] = Polynomial(R, {(0,0) : 1})  #1
    psi[2] = Polynomial(R, {(0,1) : 2})  #2y
    psi[3] = Polynomial(R, {(4,0):3, (2,0):(6*a), (1,0):(12*b), (0,0):(-a)})
    psi[4] = Polynomial(R, {(0,1) : 4}) * Polynomial(R, {(6,0):1, (4,0):(5*a), (3,0):(20*b), (2,0):((-5)*a*a), (1,0):((-4)*a*b), (0,0): (-8*b*b - a*a*a)})  #4y*...

    for m in range(5, n+1):
        count += 1
        if m % 2 == 1:
            k = (m-1)//2
            raw = (psi[k +2] * psi[k] * psi[k] * psi[k] - psi[k -1] * psi[k +1] * psi[k +1] * psi[k +1])
            psi[m] = raw
        else:
            k = m // 2
            raw = psi[k] * (psi[k+2] * psi[k-1] * psi[k-1] -psi[k-2] * psi[k+1] * psi[k+1])
            dividend = reduce_mod_curve(raw, a, b)   # now y has exponents only 1
            # so div = 2y * y*f(x) = 2y^2 * f(x), we can use the fact that y^2 = x^3+ax+b
            diviseur = Polynomial({(3, 0): 2, (1, 0): 2 * a, (0, 0): 2 * b}) # 2*(x^3+a*x+b)
            quot, rem = dividend / diviseur
            rem.clean()
            if rem.terms:
                raise ArithmeticError(
                    f"division_polynomials: psi_{m} computation had nonzero remainder "
                    "(unexpected - check curve parameters / characteristic)"
                )
            psi[m] = Polynomial({(ex, 1) : c for (ex, ey), c in quot.terms.items()})
            
    return psi[:n+1]










def frobenius_trace_mod_l(prime : int, a : int, b : int): # from Schoof
    h = div_poly_schoof(prime, a, b)
    pi_l = 


# thm : the frobenius endomorphism allows one to compute nb. of points on curve over F_q
# over F_q, the frob. endo. satisfies phi^2 + t*phi + q = 0
# where t = q + 1 - #E(F_q) 