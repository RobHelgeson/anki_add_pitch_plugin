import re

from anki.utils import strip_html


_re_ja_patt = re.compile(
    r"["
    r"\u3041-\u3096"  # hiragana
    r"\u30A0-\u30FF"  # katakana
    r"\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A"  # kanji
    r"\u3005"  # 々
    # r'\u2026\u301C'  # …〜 (might be used to indicate affixes)
    #                        (disabled — causes more problems than benefits)
    r"]+"
)
_re_variation_selectors_patt = re.compile(
    r"["
    r"\U000E0100-\U000E013D"  # variation selectors [1]
    r"]+"
)
# [1] https://en.wikipedia.org/wiki/Variation_Selectors_Supplement
_re_bracketed_content_patt = re.compile(r"[\[\(\{][^\]\)\}]*[\]\)\}]")
_re_all_hira_patt = re.compile(
    r"^["
    r"\u3041-\u3096"  # hiragana
    r"]+$"
)

ruby_regex = re.compile(r" ?([^ >]+?)\[(.+?)\]", flags=re.IGNORECASE)


def _remove_bracketed_content(dirty):
    """Remove brackets and their contents."""

    clean = _re_bracketed_content_patt.sub("", dirty)
    return clean


def _remove_variation_selectors(dirty):
    """Remove brackets and their contents."""

    clean = _re_variation_selectors_patt.sub("", dirty)
    return clean


def _clean_japanese_from_note_field(dirty):
    """Perform heuristic cleaning of an note field and return
    - the first consecutive string of Japanese if present
    - None otherwise
    """

    # heuristic cleaning
    no_html = strip_html(dirty)
    no_brack_html = _remove_bracketed_content(no_html)
    no_varsel_brack_html = _remove_variation_selectors(no_brack_html)
    # look for Japanese writing in expression field
    ja_match = _re_ja_patt.search(no_varsel_brack_html)
    if ja_match:
        # return rist consecutive match
        return ja_match.group(0)
    # no Japanese text in field
    return None


def get_field_and_reading(field):
    field = strip_html(field)
    reading = ""

    for match in reversed(list(re.finditer(ruby_regex, field))):
        field = field[: match.start()] + match.group(1) + field[match.end() :]
        reading = match.group(2) + reading

    field = _clean_japanese_from_note_field(field)
    if not field:
        reading = None

    return (field, reading)


def just_hiragana(field):
    all_hira_match = _re_all_hira_patt.search(field)
    return all_hira_match.group(0) if all_hira_match else None
