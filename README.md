# CryptoArithmetic

This project contains implementations of arithmetic used in
elliptic-curve cryptography and point counting. The main modules are
`arithmetic.py` and `polynomial.py`.

## `arithmetic.py`

### Prime field elements

`FieldElement` represents an element of the finite field $\mathbb{F}_p$ as
an integer reduced modulo $p$.

Supported operations include:

- addition, subtraction, multiplication, and division;
- multiplication by an integer;
- exponentiation by square-and-multiply;
- additive negation and multiplicative inversion;
- equality checks between elements of the same field.

Elements from different fields cannot be combined. For example:

The implementation uses Fermat's little theorem for inverses:
```math
a^{-1} = a^{p-2} \pmod p.
```
This assumes that $p$ is prime and that the element being inverted is
nonzero.

### Elliptic curves

An elliptic curve is an abelian variety; it has a group law which is abelian, where elements of the group are points on the curve.

`Point` models points on a short Weierstrass curve

```math
y^2 = x^3 + ax + b \pmod p.
```

The constructor validates that finite points lie on the curve. The point at
infinity is represented by `Point(None, None, a, b)` and acts as the identity
element of the elliptic-curve group.

Implemented operations are:

- point equality and display;
- point addition, including the identity, inverse, doubling, and vertical-line
	cases;
- `Point.inverse()` for the additive inverse;
- `scalar_mul(k, point)` using double-and-add in $O(\log k)$ operations.

## `polynomial.py`

### Polynomial rings

`PolynomialRing(*variables, order=None)` creates a polynomial ring over the
integers by default. When `order=p` is supplied, coefficients are coerced to
`FieldElement` values in $\mathbb{F}_p$.

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
- `mod()` for polynomial remainders;
- `xgcd()` for the extended Euclidean algorithm;
- `modexp()` for modular exponentiation by repeated squaring.

Division, remainders, the extended Euclidean algorithm, and modular
exponentiation require univariate polynomials. Polynomial operations also
require both operands to belong to the same `PolynomialRing` instance.

## `schoof.py`

For short Weierstrass curve $y^2 = x^3 + ax + b$, schoof's algo computes the number of points on that curve over a field F_q (we denote the curve by $E$).

This is the classic Frobenius map : $\pi : (x,y) \rightarrow (x^q, y^q)$ over $\widebar{E}$ where $\widebar{E}$ is the initial curve extended over $\widebar{\mathbb{F}_q}$ is an endomorphism.

The trick now is that the Frobenius map satisfies the characteristic equation $\pi^2 - t \pi + q = 0$, where $t = q + 1 - \mid E \mid$.
For a proof see [???]

We want to comput $t$ in order to obtain the $\mid E \mid$, the number of points on $E$.




## Hashings

This projet also contains a few famous hashing algorithms such as the SHA 224, 256, 384 and 512 algorithms.

## Public key crypto

And also a classical implementation of Elliptic Curve Digital Signature Algorithm, (an application of `Points` in `arithmetic.py`).