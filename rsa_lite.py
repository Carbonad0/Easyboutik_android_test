"""
rsa_lite.py — Signature/vérification RSA "Full Domain Hash" (FDH), 100% Python
standard (hashlib + entiers natifs), sans dépendance externe.

Pourquoi ne pas utiliser `cryptography` ou `rsa` (PyPI) ?
- `cryptography` compile des bindings natifs (OpenSSL/Rust) : ça complique
  significativement une compilation Buildozer/Android (temps de build, taille,
  risques d'échec selon l'environnement du CI).
- Ce module est volontairement minimal et n'est utilisé QUE pour signer/vérifier
  de courtes chaînes de licence (pas pour du chiffrement général) : le schéma
  "Full Domain Hash" (RSA-FDH, Bellare-Rogaway) est un schéma de signature
  standard et éprouvé (sécurité prouvée dans le modèle de l'oracle aléatoire).

Séparation des responsabilités :
- `verify()` est utilisé côté application (licence.py) : ne nécessite que la
  clé PUBLIQUE. Aucune donnée secrète n'est présente dans l'app.
- `sign()` et `generate_keypair()` ne doivent JAMAIS être appelés que sur la
  machine de l'admin (outil `admin_tool/`), jamais embarqués dans l'APK.
"""

import hashlib
import random


# ---------------------------------------------------------------------------
# Génération de clés (ADMIN UNIQUEMENT — ne pas utiliser côté app)
# ---------------------------------------------------------------------------

def _is_probable_prime(n, k=24):
    if n < 2:
        return False
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _gen_prime(bits):
    while True:
        n = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if _is_probable_prime(n):
            return n


def generate_keypair(bits=2048):
    """Génère une paire de clés RSA. À exécuter UNE SEULE FOIS, sur la machine
    de l'admin. Retourne (public, private) sous forme de dicts sérialisables."""
    e = 65537
    while True:
        p = _gen_prime(bits // 2)
        q = _gen_prime(bits // 2)
        if p == q:
            continue
        n = p * q
        phi = (p - 1) * (q - 1)
        if phi % e == 0:
            continue
        d = pow(e, -1, phi)
        return {"n": n, "e": e}, {"n": n, "d": d}


# ---------------------------------------------------------------------------
# Signature "Full Domain Hash" — cœur de l'algorithme (partagé sign/verify)
# ---------------------------------------------------------------------------

def _mgf1(seed: bytes, length: int) -> bytes:
    """Mask Generation Function (SHA-256) : étend un condensé court en un
    grand nombre pseudo-aléatoire de `length` octets."""
    out = b""
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:length]


def _fdh(message: bytes, n_bytes: int) -> int:
    digest = hashlib.sha256(message).digest()
    expanded = bytearray(_mgf1(digest, n_bytes))
    expanded[0] &= 0x7F  # garantit une valeur strictement inférieure au module n
    return int.from_bytes(bytes(expanded), "big")


def sign(message: bytes, private_key: dict) -> bytes:
    """ADMIN UNIQUEMENT. Nécessite la clé privée (n, d)."""
    n, d = private_key["n"], private_key["d"]
    n_bytes = (n.bit_length() + 7) // 8
    m = _fdh(message, n_bytes)
    s = pow(m, d, n)
    return s.to_bytes(n_bytes, "big")


def verify(message: bytes, signature: bytes, public_key: dict) -> bool:
    """Utilisable côté app. Nécessite seulement la clé PUBLIQUE (n, e)."""
    n, e = public_key["n"], public_key["e"]
    n_bytes = (n.bit_length() + 7) // 8
    if len(signature) != n_bytes:
        return False
    s = int.from_bytes(signature, "big")
    m_check = pow(s, e, n)
    m_expected = _fdh(message, n_bytes)
    return m_check == m_expected
