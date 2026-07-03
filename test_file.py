from ff_ec_arithmetic import FieldElement, Point, scalar_mul

'''
# Toy curve y^2 = x^3 + 2x + 2 (mod 17)
p = 17
a = FieldElement(2, p)
b = FieldElement(2, p)

# (5,1) is a known point of toy curve, and 19 is its group order
x = FieldElement(5, p)
y = FieldElement(1, p)
P = Point(x, y, a, b)
print("Base point P =", P)


pt = Point(None, None, a, b)
for k in range(20):
    via_scalar_mul = scalar_mul(k, P)
    assert pt == via_scalar_mul, f"mismatch at k={k}"
    print(f"{k:2d} * P = {via_scalar_mul}")
    pt = pt + P

 


 # In hexadecimals

'''
print("secp256k1 (the Bitcoin curve)")

P = 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFE_FFFFFC2F
A = FieldElement(0, P)
B = FieldElement(7, P)
Gx = FieldElement(
    0x79BE667E_F9DCBBAC_55A06295_CE870B07_029BFCDB_2DCE28D9_59F2815B_16F81798, P
    )
Gy = FieldElement(
        0x483ADA77_26A3C465_5DA4FBFC_0E1108A8_FD17B448_A6855419_9C47D08F_FB10D4B8, P
    )
N = 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFE_BAAEDCE6_AF48A03B_BFD25E8C_D0364141
 
G_secp = Point(Gx, Gy, A, B)

print(G_secp)

identity = scalar_mul(N, G_secp)
print("N * G is point at infinity:", identity.is_infinity())
