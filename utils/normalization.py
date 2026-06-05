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

def strip_country_prefix(col, country):
    col_norm = normalize_text(col)
    country_norm = normalize_text(country)

    if col_norm.startswith(country_norm + " "):
        return col_norm[len(country_norm) + 1:]
    return col_norm

def clean_html(html: str) -> str:
    """
    Cleans Wikipedia HTML before parsing:
    - Removes reference markers like [3], [12], [a], etc.
    - Removes [citation needed], [edit], [note X]
    - Normalizes unicode
    - Removes superscript reference tags
    """

    # Normalize unicode (important for weird spaces)
    html = unicodedata.normalize("NFKC", html)

    # Remove [3], [12], [a], [note 4], etc.
    html = re.sub(r"\[[^\]]+\]", "", html)

    # Remove superscript reference tags: <sup class="reference">...</sup>
    html = re.sub(r"<sup[^>]*>.*?</sup>", "", html, flags=re.DOTALL)

    # Remove edit links: <span class="mw-editsection">...</span>
    html = re.sub(r"<span class=\"mw-editsection\">.*?</span>", "", html, flags=re.DOTALL)

    # Remove leftover HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    # Remove stray whitespace
    html = re.sub(r"\s+", " ", html)

    return html.strip()