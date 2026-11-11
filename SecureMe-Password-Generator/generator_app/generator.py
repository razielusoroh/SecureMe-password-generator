"""
SecureMe Password Generator - core logic.

All randomness comes from Python's `secrets` module, which uses the
operating system's cryptographically secure random number generator.
Nothing in this module stores, prints or logs a password.
"""

import math
import secrets
import string

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/"

# Characters that are easy to confuse when reading or typing a password.
AMBIGUOUS = set("Il1|O0o`'\"")

MIN_LENGTH = 6
MAX_LENGTH = 128
MAX_WORDS = 6
MAX_WORD_LENGTH = 20

_rng = secrets.SystemRandom()


class PasswordError(ValueError):
    """Raised when the user's options cannot produce a valid password."""


def _strip_ambiguous(chars: str) -> str:
    return "".join(c for c in chars if c not in AMBIGUOUS)


def build_pools(upper=True, lower=True, digits=True, symbols=True,
                avoid_ambiguous=False):
    """Return the list of character groups the user has switched on."""
    pools = []
    if upper:
        pools.append(UPPERCASE)
    if lower:
        pools.append(LOWERCASE)
    if digits:
        pools.append(DIGITS)
    if symbols:
        pools.append(SYMBOLS)
    if avoid_ambiguous:
        pools = [_strip_ambiguous(p) for p in pools]
    return [p for p in pools if p]


def generate_random(length=16, upper=True, lower=True, digits=True,
                    symbols=True, avoid_ambiguous=False) -> str:
    """Generate a fully random password.

    Guarantees at least one character from every selected group, then
    fills the rest from the combined pool and shuffles the result.
    """
    if not isinstance(length, int) or not MIN_LENGTH <= length <= MAX_LENGTH:
        raise PasswordError(
            f"Length must be between {MIN_LENGTH} and {MAX_LENGTH}.")

    pools = build_pools(upper, lower, digits, symbols, avoid_ambiguous)
    if not pools:
        raise PasswordError("Select at least one character type.")

    chars = [secrets.choice(pool) for pool in pools]
    everything = "".join(pools)
    chars += [secrets.choice(everything) for _ in range(length - len(chars))]
    _rng.shuffle(chars)
    return "".join(chars)


def clean_words(raw):
    """Turn user input (a string or list) into a clean list of words."""
    if isinstance(raw, str):
        raw = raw.replace(",", " ").split()
    words = []
    for w in raw or []:
        w = "".join(ch for ch in str(w) if ch.isalnum())
        if w:
            words.append(w[:MAX_WORD_LENGTH])
    if not words:
        raise PasswordError("Enter at least one word.")
    if len(words) > MAX_WORDS:
        raise PasswordError(f"Use up to {MAX_WORDS} words.")
    return words


def generate_from_words(words, length=16, digits=True, symbols=True,
                        avoid_ambiguous=False) -> str:
    """Generate a memorable password built around the user's own words.

    Each word keeps its spelling so the user can recall it, but gets a
    random capitalisation style. Words are put in a random order and
    joined with random symbols/digits, then padded with random
    characters until the requested length is reached.
    """
    words = clean_words(words)
    if not isinstance(length, int) or not MIN_LENGTH <= length <= MAX_LENGTH:
        raise PasswordError(
            f"Length must be between {MIN_LENGTH} and {MAX_LENGTH}.")

    sep_pool = (SYMBOLS if symbols else "") + (DIGITS if digits else "")
    if avoid_ambiguous:
        sep_pool = _strip_ambiguous(sep_pool)
    if not sep_pool:
        # No digits or symbols chosen: join with random letters instead.
        sep_pool = _strip_ambiguous(UPPERCASE) if avoid_ambiguous else UPPERCASE

    styled = []
    for w in words:
        style = secrets.randbelow(3)
        if style == 0:
            styled.append(w.capitalize())
        elif style == 1:
            styled.append(w.upper())
        else:
            styled.append(w.lower())
    _rng.shuffle(styled)

    parts = []
    for i, w in enumerate(styled):
        parts.append(w)
        if i < len(styled) - 1:
            parts.append(secrets.choice(sep_pool))
    password = "".join(parts)

    # Make sure selected groups appear, then pad to the requested length.
    tail = []
    if digits:
        pool = _strip_ambiguous(DIGITS) if avoid_ambiguous else DIGITS
        tail.append(secrets.choice(pool))
    if symbols:
        tail.append(secrets.choice(SYMBOLS))
    while len(password) + len(tail) < length:
        tail.append(secrets.choice(sep_pool))
    return password + "".join(tail)


BITS_PER_KNOWN_WORD = 11  # a word from a ~2,000-word everyday vocabulary


def check_strength(password: str, known_words=None) -> dict:
    """Rate a password as weak, medium or strong.

    Uses an entropy estimate (length x log2 of the character pool size)
    combined with simple checks for variety.

    `known_words` are words the user typed in themselves. Real words are
    far easier to guess than random characters, so each one is counted
    as a single unit (about 11 bits) instead of letter by letter.
    """
    if not password:
        return {"label": "weak", "score": 0, "entropy": 0}

    if known_words:
        remaining = password
        word_bits = 0
        for w in known_words:
            idx = remaining.lower().find(w.lower())
            if idx != -1:
                remaining = remaining[:idx] + remaining[idx + len(w):]
                word_bits += BITS_PER_KNOWN_WORD + 1.6  # + capitalisation style
        result = check_strength(remaining) if remaining else {"entropy": 0}
        entropy = round(result["entropy"] + word_bits, 1)
        variety = _variety(password)
        return _rate(password, entropy, variety)

    pool = 0
    if any(c in LOWERCASE for c in password):
        pool += 26
    if any(c in UPPERCASE for c in password):
        pool += 26
    if any(c in DIGITS for c in password):
        pool += 10
    if any(not c.isalnum() for c in password):
        pool += len(SYMBOLS)

    entropy = round(len(password) * math.log2(pool), 1) if pool else 0
    return _rate(password, entropy, _variety(password))


def _variety(password: str) -> int:
    return sum([
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(not c.isalnum() for c in password),
    ])


def _rate(password: str, entropy: float, variety: int) -> dict:
    if entropy >= 75 and variety >= 3 and len(password) >= 12:
        label = "strong"
    elif entropy >= 45 and variety >= 2 and len(password) >= 8:
        label = "medium"
    else:
        label = "weak"

    score = min(100, int(entropy / 100 * 100))
    return {"label": label, "score": score, "entropy": entropy}
