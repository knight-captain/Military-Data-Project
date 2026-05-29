import unicodedata
import re

def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        return s

    # Unicode normalization
    s = unicodedata.normalize("NFKC", s)

    # Replace weird spaces with normal spaces
    s = s.replace("\u00A0", " ")  # NBSP
    s = s.replace("\u2009", " ")  # thin space
    s = s.replace("\u200A", " ")  # hair space
    s = s.replace("\u2002", " ")  # en space
    s = s.replace("\u2003", " ")  # em space
    s = s.replace("\u202F", " ")  # narrow NBSP

    # Strip whitespace
    s = s.strip()

    # Lowercase
    s = s.lower()

    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)

    return s
