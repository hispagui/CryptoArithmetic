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
            m = max(poly.terms.keys())
            return m, poly.terms[m]
        
        while R.terms:
            lm_r, lc_r = leading_term(R)
            lm_d, lc_d = leading_term(other)
            if not monomial_divides(lm_d, lm_r):
                break

            if is_field:
                lc_q = lc_r * lc_d.invers()
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


def div_poly_schoof(n : int, a : int , b : int, order_field = None) -> "Polynomial":
    R = PolynomialRing("x", "y", order = order_field)
    psi0 = Polynomial(R, {(0,0) : 0})  #0
    psi1 = Polynomial(R, {(0,0) : 1})  #1
    psi2 = Polynomial(R, {(0,1) : 2})  #2y
    psi3 = Polynomial(R, {(4,0):3, (2,0):(6*a), (1,0):(12*b), (0,0):(-a)})
    psi4 = Polynomial(R, {(0,1) : 4}) * Polynomial(R, {(6,0):1, (4,0):(5*a), (3,0):(20*b), (2,0):((-5)*a*a), (1,0):((-4)*a*b), (0,0): (-8*b*b - a*a*a)})  #4y*...
    psi_liste = [psi0, psi1, psi2, psi3, psi4]
    count = len(psi_liste) -1
    if n < 5:
        return psi_liste[n]
    for m in range(4, n):
        count += 1
        if m % 2 == 1:
            psi2m = (psi_liste[((m-1)//2) +2] * psi_liste[(m-1)//2] * psi_liste[(m-1)//2] * psi_liste[(m-1)//2]) - (psi_liste[((m-1)//2) -1] * psi_liste[((m-1)//2) +1] * psi_liste[((m-1)//2) +1] * psi_liste[((m-1)//2) +1])
            psi_liste[(count%5)] = psi2m
            last = psi2m
        if m % 2 == 0:
            psi2m1 = ((psi_liste[m//2] / psi2)[0]) * (((psi_liste[(m//2)+2]) * psi_liste[(m//2)-1] * psi_liste[(m//2)-1]) -(psi_liste[(m//2)-2] * psi_liste[(m//2)+1] * psi_liste[(m//2)+1]))
            # above rest should always be zero
            # in every pair m, there is at least a factor 2y
            psi_liste[(count%5)] = psi2m1
            last = psi2m
    return last

def frobenius_trace_mod_l(prime : int, a : int, b : int): # from Schoof
    h = div_poly_schoof(prime, a, b)
    pi_l = 


# thm : the frobenius endomorphism allows one to compute nb. of points on curve over F_q
# over F_q, the frob. endo. satisfies phi^2 + t*phi + q = 0
# where t = q + 1 - #E(F_q) 