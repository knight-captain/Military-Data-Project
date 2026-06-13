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

    # Remove zero-width and control characters
    s = re.sub(r"[\u200b\u200c\u200d\uFEFF\u00ad]", "", s)
    s = re.sub(r"[\x00-\x1f\x7f]", "", s)

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
    
    #enforce that clean_html() always returns a string
    if not isinstance(html, str):
        html = str(html)

    # Normalize unicode (important for weird spaces)
    html = unicodedata.normalize("NFKC", html)

    # Remove [3], [12], [a], [note 4], etc.
    # Remove bracketed references, but ONLY if they are short
    html = re.sub(r"\[[0-9a-zA-Z ]{1,10}\]", "", html)

    # Remove superscript reference tags: <sup class="reference">...</sup>
    html = re.sub(r"<sup[^>]*>.*?</sup>", "", html, flags=re.DOTALL)

    # Remove edit links: <span class="mw-editsection">...</span>
    html = re.sub(r"<span class=\"mw-editsection\">.*?</span>", "", html, flags=re.DOTALL)

    # Remove leftover HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    # Remove stray whitespace
    html = re.sub(r"\s+", " ", html)

    html = html or ""  # ensure non-None
    return html.strip()