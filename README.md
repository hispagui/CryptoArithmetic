# CryptoArithmetic

This project contains implementations of arithmetic used in
elliptic-curve cryptography and point counting. The main modules are
`arithmetic.py` and `polynomial.py`.

## `arithmetic.py`

### Prime field elements

`FieldElement` represents an element of the finite field \(\mathbb{F}_p\) as
an integer reduced modulo `p`.

Supported operations include:

- addition, subtraction, multiplication, and division;
- multiplication by an integer;
- exponentiation by square-and-multiply;
- additive negation and multiplicative inversion;
- equality checks between elements of the same field.

Elements from different fields cannot be combined. For example:

The implementation uses Fermat's little theorem for inverses:
\[
a^{-1} = a^{p-2} \pmod p.
\]
This assumes that `p` is prime and that the element being inverted is
nonzero.

### Elliptic curves

An elliptic curve is an abelian variety; it has a group law which is abelian, where elements of the group are points on the curve.

`Point` models points on a short Weierstrass curve

\[
y^2 = x^3 + ax + b \pmod p.
\]

The constructor validates that finite points lie on the curve. The point at
infinity is represented by `Point(None, None, a, b)` and acts as the identity
element of the elliptic-curve group.

Implemented operations are:

- point equality and display;
- point addition, including the identity, inverse, doubling, and vertical-line
	cases;
- `Point.inverse()` for the additive inverse;
- `scalar_mul(k, point)` using double-and-add in \(O(\log k)\) operations.

## `polynomial.py`

### Polynomial rings

`PolynomialRing(*variables, order=None)` creates a polynomial ring over the
integers by default. When `order=p` is supplied, coefficients are coerced to
`FieldElement` values in \(\mathbb{F}_p\).

Polynomials are represented by dictionaries whose keys are exponent tuples.
For example, in `PolynomialRing("x", "y")`,

```python
from polynomial import PolynomialRing

R = PolynomialRing("x", "y")
f = R({(2, 1): 3, (0, 2): -5, (0, 0): 7})
print(f)  # 3x^2y - 5y^2 + 7
```

`Polynomial` supports:

- addition, subtraction, multiplication, and nonnegative powers;
- polynomial long division, returning `(quotient, remainder)`;
- zero-term cleanup with `clean()` and zero testing with `is_zero()`;
- `degree()` for univariate polynomials;
- `mod()` for polynomial remainders;
- `xgcd()` for the extended Euclidean algorithm;
- `modexp()` for modular exponentiation by repeated squaring.

Division, remainders, the extended Euclidean algorithm, and modular
exponentiation require univariate polynomials. Polynomial operations also
require both operands to belong to the same `PolynomialRing` instance.

### Elliptic curves and Schoof support

The module also contains helpers for the curve

\[
y^2 = x^3 + ax + b.
\]

`reduce_mod_curve()` rewrites powers of `y` using
`y^2 = x^3 + ax + b`, reducing the exponent of `y` to zero or one. This is
useful when working in the coordinate ring of the curve.

`div_poly_schoof()` is intended to construct the division polynomials
\(\psi_0, \ldots, \psi_n\), which are used by Schoof's algorithm to study
the action of multiplication and Frobenius on elliptic-curve torsion points.



## Hashings

This projet also contains a few famous hashing algorithms such as the SHA 224, 256, 384 and 512 algorithms.

## Public key crypto

Classical implementation of Elliptic Curve Digital Signature Algorithm, application of `Points` in `arithmetic.py`.