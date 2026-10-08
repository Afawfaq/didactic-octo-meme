from __future__ import annotations

import random

DICTIONARY_TOKENS = [b"{}", b"[]", b"\"a\"", b"true", b"false", b"null", b"{\"__boom__\":1337}"]
MUTATORS = ["bit_flip", "insert", "delete", "splice", "dictionary_insert"]


def mutate(seed: bytes, op: str, focus: int | None, corpus: list[bytes], rnd: random.Random) -> bytes:
    data = bytearray(seed)
    if not data:
        data = bytearray(b"{}")

    idx = focus if focus is not None else rnd.randrange(len(data))
    idx = max(0, min(idx, len(data) - 1))

    if op == "bit_flip":
        data[idx] ^= 1 << rnd.randrange(8)
    elif op == "insert":
        data[idx:idx] = bytes([rnd.randrange(256)])
    elif op == "delete" and len(data) > 1:
        del data[idx]
    elif op == "splice" and corpus:
        other = rnd.choice(corpus)
        cut_a = rnd.randrange(len(data))
        cut_b = rnd.randrange(max(len(other), 1))
        data = bytearray(data[:cut_a] + other[cut_b:])
    elif op == "dictionary_insert":
        token = rnd.choice(DICTIONARY_TOKENS)
        data[idx:idx] = token

    if len(data) > 4096:
        data = data[:4096]
    return bytes(data)
