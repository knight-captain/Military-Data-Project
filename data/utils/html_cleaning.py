import re
import unicodedata

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
