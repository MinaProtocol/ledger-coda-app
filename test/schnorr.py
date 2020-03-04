import hashlib
import binascii
import sys
from random import getrandbits
from codaledgercli import poseidon

a = 0
b = 7
a_coeff = a
b_coeff = b

p = 5543634365110765627805495722742127385843376434033820803590214255538854698464778703795540858859767700241957783601153
n = 5543634365110765627805495722742127385843376434033820803592568747918351978899288491582778380528407187068941959692289
G = [1, 1587713460471950740217388326193312024737041813752165827005856534245539019723616944862168333942330219466268138558982]
N = 382

field_bytes = 48

def next_bit():
    return getrandbits(1)

def legendre_symbol(a):
    ls = pow(a, (p - 1)//2, p)
    if ls == p - 1:
        return -1
    return ls

def prime_mod_sqrt(a):
    """
    Square root modulo prime number
    Solve the equation
        x^2 = a mod p
    and return list of x solution
    http://en.wikipedia.org/wiki/Tonelli-Shanks_algorithm
    """
    a %= p

    # Simple case
    if a == 0:
        return [0]
    if p == 2:
        return [a]

    # Check solution existence on odd prime
    if legendre_symbol(a) != 1:
        return []

    # Simple case
    if p % 4 == 3:
        x = pow(a, (p + 1)//4, p)
        return [x, p-x]

    # Factor p-1 on the form q * 2^s (with Q odd)
    q, s = p - 1, 0
    while q % 2 == 0:
        s += 1
        q //= 2

    # Select a z which is a quadratic non resudue modulo p
    z = 1
    while legendre_symbol(z) != -1:
        z += 1
    c = pow(z, q, p)

    # Search for a solution
    x = pow(a, (q + 1)//2, p)
    t = pow(a, q, p)
    m = s
    while t != 1:
        # Find the lowest i such that t^(2^i) = 1
        i, e = 0, 2
        for i in range(1, m):
            if pow(t, e, p) == 1:
                break
            e *= 2

        # Update next value to iterate
        b = pow(c, 2**(m - i - 1), p)
        x = (x * b) % p
        t = (t * b * b) % p
        c = (b * b) % p
        m = i

    return [x, p-x]

def random_field_elt():
    res = 0
    for i in range(N):
        res += next_bit() * (2 ** i)
    if res < p:
        return res
    else:
        return random_field_elt()

def both_sqrt(y2):
    [y, negy] = prime_mod_sqrt(y2)
    return (y, negy) if y < negy else (negy, y)

def is_square(x):
    return legendre_symbol(x) == 1

def is_curve_point(x):
    y2 = (x*x*x + a*x + b) % p
    return is_square(y2)

def is_on_curve(x, y):
    return (y*y) % p == (x*x*x + a*x + b) % p

def random_curve_point():
    x = random_field_elt()
    y2 = (x*x*x + a*x + b) % p

    if not is_square(y2):
        return random_curve_point()

    (y1, y2) = both_sqrt(y2)
    y = y1 if next_bit() else y2
    return (x, y)

def point_add(P1, P2):
    if (P1 is None):
        return P2
    if (P2 is None):
        return P1
    if (P1[0] == P2[0] and P1[1] != P2[1]):
        return None
    if (P1 == P2):
        lam = ((3 * P1[0] * P1[0] + a) * pow(2 * P1[1], p - 2, p)) % p
    else:
        lam = ((P2[1] - P1[1]) * pow(P2[0] - P1[0], p - 2, p)) % p
    x3 = (lam * lam - P1[0] - P2[0]) % p
    return (x3, (lam * (P1[0] - x3) - P1[1]) % p)

def point_neg(P):
    return (P[0], p - P[1])

def point_mul(P, n):
    R = None
    for i in range(N):
        if ((n >> i) & 1):
            R = point_add(R, P)
        P = point_add(P, P)
    return R

def bytes_from_int(x):
    return x.to_bytes(field_bytes, byteorder="little")

def bytes_from_point(P):
    return (b'\x03' if P[1] & 1 else b'\x02') + bytes_from_int(P[0])

def point_from_bytes(b):
    if b[0:1] in [b'\x02', b'\x03']:
        odd = b[0] - 0x02
    else:
        return None
    x = int_from_bytes(b[1:field_bytes])
    y_sq = (pow(x, 3, p) + a_coeff * x + b_coeff) % p
    if not is_square(y_sq):
        return None
    y0 = prime_mod_sqrt(y_sq)[0]
    y = p - y0 if y0 & 1 != odd else y0
    return [x, y]

def int_from_bytes(b):
    return int.from_bytes(b, byteorder="little")

def bits_from_int(x):
    return [ (x >> i) & 1 for i in range(N) ]

def hash_blake2s(x):
    return hashlib.blake2s(x).digest()

def bits_from_bytes(bs):
    def bits_from_byte(b):
        return [ (b >> i) & 1 for i in range(8) ]

    return [b for by in bs for b in bits_from_byte(by)]

def schnorr_hash(msg):
    sign_state = [0x103b9c65528d48ea197e4caac51d8fda9ab0f624f92e9b3f752b8022f91a3523600e459640f0b4066ebe4d568da58ea0,
    0x9d3b2798b0bdd9f80bd983f81fb4c7aaad12d82ba2af9c08e78b2716dc25b4fce20398e6c36420bac75c6efdbe2c887,
    0x80368c9b06f76e2b7257d37b16bb57c2443ef5bd19c182e5bf1623947952bca0e70461cbbc17382a75e444712547b0e]
    (x, px, py, r, m) = msg
    state = poseidon.poseidon([int_from_bytes(x), int(px)], state=sign_state)
    state = poseidon.poseidon([int(py), int(r)], state=state)
    state = poseidon.poseidon([int_from_bytes(m)], state=state)
    res = poseidon.poseidon_digest(state)
    # challenge length = 128 bits
    return int_from_bytes(bytes_from_int(res)[:17])

def schnorr_sign(msg, seckey):
    (x, m) = msg
    if not (1 <= seckey <= n - 1):
        raise ValueError('The secret key must be an integer in the range 1..n-1.')
    k0 = int_from_bytes(
            hash_blake2s(bytes_from_int(seckey) + x + m))
    if k0 == 0:
        raise RuntimeError('Failure. This happens only with negligible probability.')
    R = point_mul(G, k0)
    k = n - k0 if (R[1] % 2 != 0) else k0
    (px, py) = point_mul(G, seckey)
    e = schnorr_hash((x, px, py, R[0], m))
    return bytes_from_int(R[0]) + bytes_from_int((k + e * seckey) % n)

def schnorr_verify(msg, pubkey, sig):
    if len(pubkey) != field_bytes:
        raise ValueError('The public key must be a field size byte array.')
    if len(sig) != (field_bytes * 2):
        raise ValueError('The signature must be a field size + scalar size byte array.')
    P = point_from_bytes(pubkey)
    if (P is None):
        return False
    r = int_from_bytes(sig[0:field_bytes])
    s = int_from_bytes(sig[field_bytes:(field_bytes * 2)])
    if (r >= p or s >= n):
        return False
    # field elts = [x, px, py, r], bitstrings = m
    (x, m) = msg
    (px, py) = P
    e = schnorr_hash((x, px, py, r, m))
    (ex, ey) = point_mul(P, e)
    R = point_add(point_mul(G, s), (ex, p-ey))
    (rx, ry) = R
    if R is None or (R[1] % 2 != 0) or R[0] != r:
        return False
    return True

if __name__ == '__main__':
    print('point mul')
    msg = 240717916736854602989207148466022993262069182275
    assert is_on_curve(G[0], G[1])
    g2 = point_mul(G, msg)
    print(hex(g2[0]))
    print(hex(g2[1]))
    MSG = (b'this is a test', b'an excellent test')
    KEY = random_field_elt()
    SIG = schnorr_sign(MSG, KEY)
    if schnorr_verify(MSG, bytes_from_point(point_mul(G, KEY)), SIG):
        print('Signature 1 verified')
    else:
        print('Signature 1 failed to verify')
        sys.exit(1)

    pkpk = b'\x03' + bytes_from_int(xx)
    if schnorr_verify(msg, pkpk, ss):
        print("Signature 2 verified")
    else:
        print('Signature 2 failed to verify')
        sys.exit(1)
