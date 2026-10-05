# CryptoArithmetic — Theory

The mathematics behind the code, and how each piece maps to it. For how to
*call* the code see the [`README.md`](README.md).

## 1. Notation
 
| Symbol | Meaning |
|---|---|
| $p$ | an odd prime, $p \ge 5$ |
| $\mathbb{F}_p$ | the field $\mathbb{Z}/p\mathbb{Z}$ |
| $E$ | the curve $y^2 = x^3 + ax + b$, with $g(x) = x^3 + ax + b$ |
| $E(\mathbb{F}_p)$ | the points of $E$ with coordinates in $\mathbb{F}_p$, plus the point at infinity $O$ |
| $N$ | $\#E(\mathbb{F}_p)$ |
| $t$ | trace of Frobenius, $t = p + 1 - N$ |
| $\pi$ | the Frobenius map $(x, y) \mapsto (x^p, y^p)$ |
| $\ell$ | a small prime, $\ell \ne p$ |
| $E[\ell]$ | the points $P$ of $E$ over $\overline{\mathbb{F}}_p$ with $\ell P = O$ |
| $[k]P$ | $k$ times $P$ in the group law |


## 2. Finite fields
 
`FieldElement(num, p)` is an element of $\mathbb{F}_p$, stored as the residue
$0 \le \text{num} < p$. Every non-zero $a$ has an inverse. By Fermat's little theorem
$a^{p-1} = 1$, so
 
```math
a^{-1} = a^{p-2} \pmod p .
```
 
**Exponentiation by squaring.** Writing $e$ in binary, $a^e$ is computed with
$\lfloor \log_2 e \rfloor$ squarings and one multiplication per set bit, i.e.
$O(\log e)$ multiplications instead of $e$.
 
**Reducing the exponent.** For $a \ne 0$, $a^e = a^{e \bmod (p-1)}$, which
`__pow__` uses (it also makes negative exponents work). For $a = 0$ it is wrong
when $e > 0$ and $(p-1) \mid e$, $\:0^{p-1} = 0$ but the code computes $0^0 = 1$.



## 3. Elliptic curves over F_p
 
### 3.1 The curve
 
```math
E:\; y^2 = x^3 + ax + b, \qquad 4a^3 + 27b^2 \not\equiv 0 \pmod p .
```
 
The condition says $g(x)$ has no repeated root, i.e. the curve has no singular
point. For $p \ge 5$ every elliptic curve can be put in this *short Weierstrass
form*.

### 3.2 The group law
 
Points are added by the chord-and-tangent rule. For $P = (x_1, y_1)$ and
$Q = (x_2, y_2)$:
 
- $O$ is the identity, and $-P = (x_1, -y_1)$.
- If $x_1 = x_2$ and $y_1 = -y_2$, then $P + Q = O$.
- Otherwise let
```math
\lambda =
\begin{cases}
\dfrac{y_2 - y_1}{x_2 - x_1} & P \ne Q \\[3mm]
\dfrac{3x_1^2 + a}{2y_1} & P = Q,\ y_1 \ne 0
\end{cases}
\qquad
x_3 = \lambda^2 - x_1 - x_2, \qquad y_3 = \lambda (x_1 - x_3) - y_1 ,
```
 
  and $P + Q = (x_3, y_3)$. If $P = Q$ and $y_1 = 0$ (a point of order 2, vertical
  tangent) then $2P = O$.
 
That the result is an abelian group (in particular associativity) is a theorem,
not something the code checks. `Point.__add__` follows exactly the case
distinction above: identity, $P + (-P)$, generic addition, doubling.

### 3.3 Scalar multiplication
 
$[k]P$ is computed by double-and-add on the binary expansion of $k$.

This uses $\lfloor \log_2 k \rfloor$ doublings and at most as many additions, so for
$k \approx 10^6$ about 30 group operations instead of $10^6$. A negative $k$ is
handled as $-[|k|]P$.

### 3.4 Size and structure of the group
 
**Hasse's theorem.** $N = p + 1 - t$ with $\lvert t \rvert \le 2\sqrt{p}$.
 
The group is $E(\mathbb{F}_p) \cong \mathbb{Z}/n_1 \times \mathbb{Z}/n_2$ with
$n_1 \mid n_2$ and $n_1 \mid p - 1$ (so it is cyclic or "almost" cyclic). By
Lagrange's theorem the order of any point divides $N$.
 

## 4. Polynomials over a field
 
A `Polynomial` is a dictionary `{exponent tuple: coefficient}` in a
`PolynomialRing` with a fixed list of variables; coefficients are integers or
`FieldElement`s of one prime. Terms are ordered lexicographically on the
exponent tuples (Python's tuple order); for one variable this is the usual order
by degree.
 
### 4.1 Division with remainder
 
In $\mathbb{F}_p[x]$, for $g \ne 0$ there are unique $q, r$ with $f = qg + r$ and
$\deg r < \deg g$. The algorithm (`Polynomial.__truediv__`) repeatedly cancels the leading term of the remainder.
It stops when no leading term of $r$ is divisible by the leading term of $g$. Over $\mathbb{Z}$ the same loop also needs the leading coefficient of $r$ to be divisible by that of $g$, and stops otherwise, so
$3x^2 + 1$ divided by $2x$ gives quotient $0$ and remainder $3x^2 + 1$.
 
### 4.2 Euclid and Bézout
 
$\gcd(f, g)$ is obtained by repeating $(f, g) \to (g, f \bmod g)$. 








## 5. Schoof's algorithm
 
The goal is to compute $N = \#E(\mathbb{F}_p)$ for large $p$ without enumerating $x \in \mathbb{F}_p$
(which costs $O(p)$). Schoof gives an algo polynomial in $\log p$.
 
### 5.1 The Frobenius endomorphism
 
Let $\overline{\mathbb{F}}_p$ be an algebraic closure and consider $E$ over it. The map
 
```math
\pi : E \to E, \qquad (x, y) \mapsto (x^p, y^p), \qquad O \mapsto O
```
 
is an endomorphism of the group $E$. A point is fixed by $\pi$ exactly when its
coordinates satisfy $c^p = c$, i.e. lie in $\mathbb{F}_p$. Hence
 
```math
E(\mathbb{F}_p) = \ker(1 - \pi) .
```
 
The key fact is the *characteristic equation* of Frobenius, valid in the
endomorphism ring of $E$:
 
```math
\pi^2 - t\,\pi + p = 0, \qquad t = p + 1 - N .
```
 
(The degree of $1 - \pi$ is $p + 1 - t$ and equals $\#\ker(1-\pi) = N$, which is
how $t$ and $N$ are linked. So computing $N$ is equivalent to computing the integer $t$, and Hasse's bound says $t$ lies in a short interval.
 
### 5.2 Strategy: $t$ modulo small primes, then the CRT
 
Compute $t \bmod \ell$ for several small primes $\ell$, and combine with the
Chinese remainder theorem.

Let $H = \lfloor 2\sqrt{p} \rfloor$. By Hasse, $t$ is one of the
$2H + 1$ integers in $[-H, H]$. If $M = \prod \ell_i$ satisfies $M > 2H$ (that is
$M \ge 2H + 1$), then no two of them are congruent mod $M$, so the residue
$t \bmod M$ determines $t$: take the representative in $(-M/2, M/2]$.
The code requires
 
```math
M > 4\sqrt{p} \iff M^2 > 16p
```
 
(`while prod * prod <= 16 * p`), which implies $M > 2H$ because $4\sqrt{p} \ge 2H$.
The decoding is `if 2*t > M: t -= M`.

### 5.3 How $\pi$ acts on $E[\ell]$
 
For $\ell \ne p$, $E[\ell] \cong (\mathbb{Z}/\ell)^2$, and $\pi$ maps $E[\ell]$ to
itself, so it acts on it as a $2 \times 2$ matrix over $\mathbb{Z}/\ell$ whose
characteristic polynomial is $X^2 - tX + p \bmod \ell$. The characteristic equation
therefore holds on $E[\ell]$, and since $\ell P = O$ for $P \in E[\ell]$ we may
reduce scalars mod $\ell$:
 
```math
\pi^2(P) + [\bar q]\,P \;=\; [\tau]\,\pi(P) \qquad \forall P \in E[\ell],
\qquad \bar q = p \bmod \ell, \quad \tau = t \bmod \ell .
```
 
**Uniqueness.** If two values $\tau, \tau' \in [0, \ell)$ both satisfied this for
some $P \ne O$, then $[\tau - \tau']\pi(P) = O$; $\pi(P) \ne O$ has order $\ell$, so
$\tau \equiv \tau' \pmod \ell$. Hence trying $\tau = 0, 1, \dots, \ell - 1$ finds
exactly one match, and it is $t \bmod \ell$.
 
### 5.4 Division polynomials
 
We cannot list the points of $E[\ell]$ (they live in an unknown extension field),
but their $x$-coordinates are the roots of a polynomial over $\mathbb{F}_p$.
The division polynomials $\psi_n \in \mathbb{Z}[a, b, x, y]$ are defined by
 
```math
\begin{aligned}
\psi_0 &= 0, \\
\psi_1 = 1, \\
\psi_2 = 2y, \\
\psi_3 = 3x^4 + 6ax^2 + 12bx - a^2,\\
\psi_4 &= 4y\,(x^6 + 5ax^4 + 20bx^3 - 5a^2x^2 - 4abx - 8b^2 - a^3),\\
\psi_{2m+1} &= \psi_{m+2}\,\psi_m^3 - \psi_{m-1}\,\psi_{m+1}^3 \qquad (m \ge 2),\\
\psi_{2m} &= \frac{\psi_m}{2y}\left(\psi_{m+2}\,\psi_{m-1}^2 - \psi_{m-2}\,\psi_{m+1}^2\right) \qquad (m \ge 3).
\end{aligned}
```
 
Working modulo the curve equation $y^2 = g(x)$:
 
- for **odd** $n$, $\psi_n$ is a polynomial in $x$ alone, of degree $(n^2 - 1)/2$ and
  leading coefficient $n$;
- for **even** $n$, $\psi_n = y \cdot (\text{polynomial in } x)$.


### 5.5 The ring $S$ and the generic torsion point
 
Fix an odd prime $\ell \ne p$ and put $f = f_\ell$. Define
 
```math
S = \bigl(\mathbb{F}_p[x]/(f)\bigr)[y]\,/\,(y^2 - g(x)),
```
 
whose elements are $A(x) + B(x)\,y$ with $A, B$ reduced mod $f$ (`RingS`).
 
The two generators $(x, y)$ form a point $P_{\text{gen}} \in E(S)$ ("the generic
$\ell$-torsion point"). Specialising it into each factor gives a point of
$E[\ell] \setminus \{O\}$, and every such point arises this way. Therefore, an identity between points built from $P_{\text{gen}}$ with the group law holds in $S$ iff it holds for every $P \in E[\ell] \setminus \{O\}$.

`SymbolicPoint` is a `Point` whose coordinates are `RingS` elements; its `__add__`
is the same case analysis as `Point.__add__`, with "divide" meaning "invert in $S$"
(`RingS.inverse`, via $(A + By)^{-1} = (A - By)/(A^2 - B^2 g)$) and
"is $x_1 = x_2$" meaning "equal in $S$".
 
### 5.6 Frobenius and scalar multiples inside $S$
 
At a torsion point $(x_0, y_0)$, $\pi$ gives $(x_0^p, y_0^p)$. As elements of $S$,
$x^p \bmod f$ evaluates to $x_0^p$ at every root, and since $p$ is odd
 
```math
y^p = y\,(y^2)^{(p-1)/2} = y\,g(x)^{(p-1)/2} .
```
 
So
 
```math
\pi(P_{\text{gen}}) = \Bigl(x^{p} \bmod f,\;\; \bigl(g^{(p-1)/2} \bmod f\bigr)\,y\Bigr),
\qquad
\pi^2(P_{\text{gen}}) = \Bigl(x^{p^2} \bmod f,\;\; \bigl(g^{(p^2-1)/2} \bmod f\bigr)\,y\Bigr),
```
 
each computed with `modexp` ($O(\log p)$ polynomial multiplications mod $f$). No separate
"apply $\pi$ to a general element" is needed: applying $(x, y) \mapsto (x^p, y^p)$ twice is
the map with exponent $p^2$.
 
The scalar multiples $[\bar q]P_{\text{gen}}$ and $[\tau]\pi(P_{\text{gen}})$ use
double-and-add (`symbolic_scalar_mul`). Because the points have order $\ell$, the
scalars are taken mod $\ell$ ($\bar q = p \bmod \ell$, $0 \le \tau < \ell$), so these
cost $O(\log \ell)$ group operations whatever the size of $p$.
 
### 5.7 Finding $\tau$
 
`frobenius_trace_mod_l(a, b, p, l)` for odd $\ell$:
 
```text
f    = f_l(x) mod p                           # division_poly_odd
P    = (x, y)                                 # generic point in S
lhs  = pi^2(P) + [p mod l] P                  # SymbolicPoint addition
for tau in 0 .. l-1:
    if lhs == [tau] pi(P):  return tau        # equality in S = equality at all of E[l]
```
 
Special case $\tau = 0$: $[0]\pi(P) = O$, and `lhs` is $O$ exactly when
$\pi^2 = -\bar q$ on $E[\ell]$, i.e. when $t \equiv 0 \pmod \ell$ (e.g. for
supersingular curves, where $t = 0$).
 

### 5.8 Degenerate primes
 
If $x(\pi^2 P) - x([\bar q]P)$ is zero at some roots of $f$ and non-zero at
others, it is a zero divisor in $S$, `RingS.inverse` raises `ZeroDivisionError`,
and `schoof` simply continues with the next prime. This is sound: the algorithm
only needs *some* set of distinct primes with $M^2 > 16p$, not a particular one.
 
When does it happen? [...]


### 5.9 The prime $\ell = 2$
 
$\psi_2 = 2y$ does not give a useful modulus. Instead use the parity of $N$.
Since $p$ is odd, $N = p + 1 - t$ is even iff $t$ is even. $N$ is even iff $E(\mathbb{F}_p)$
has a point of order 2 (Cauchy), i.e. a point $(x_0, 0)$, i.e. iff $g(x)$ has a root
in $\mathbb{F}_p$. Since
 
```math
x^p - x = \prod_{c \in \mathbb{F}_p} (x - c),
```
 
$\gcd(x^p - x,\, g)$ is the product of $(x - c)$ over the roots $c \in \mathbb{F}_p$ of
$g$. Therefore
 
```math
t \equiv 0 \pmod 2 \iff \deg \gcd(x^p - x,\; g) \ge 1 ,
```
 
computed as $x^p \bmod g$ (`modexp`), then `xgcd` (`_trace_mod_2`).
 
### 5.10 Worked example
 
$E:\ y^2 = x^3 + 2x + 3$ over $\mathbb{F}_{97}$.
 
- Hasse: $\lvert t \rvert \le 2\sqrt{97} \approx 19.7$, so $t \in [-19, 19]$.
- Need $M^2 > 16 \cdot 97 = 1552$, i.e. $M \ge 40$.
- $\ell = 2$: $x^3 + 2x + 3$ has roots $30, 68, 96$ mod 97 → $t \equiv 0 \pmod 2$ (and $4 \mid N$, as three roots mean full 2-torsion).
- $\ell = 3$: degenerate, skipped (as computed in §5.9).
- $\ell = 5$: $\tau = 3$. $\ell = 7$: $\tau = 5$. Now $M = 2 \cdot 5 \cdot 7 = 70$ and $70^2 = 4900 > 1552$: stop.
- CRT: $t \equiv 0 \ (2),\ 3 \ (5),\ 5 \ (7)$ gives $t \equiv 68 \pmod{70}$.
- Recentre: $2 \cdot 68 = 136 > 70$, so $t = 68 - 70 = -2$.
- $N = 97 + 1 - (-2) = 100$.
A direct count confirms $N = 100$, and the point $(3, 6)$ has order 5, dividing 100.