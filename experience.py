"""Compact experience evidence from public listing text."""
import html
import re


YEAR_REQUIREMENT = re.compile(
    r"(?<![\w.])(?P<low>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"(?:\s*(?:[-–—]|to)\s*(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten))?"
    r"\s*\+?\s*(?:years?|yrs?)\s*[’']?\s*"
    r"(?:[\w+#/-]+\s+){0,6}experience\b",
    re.I,
)
YEAR_WORDS = dict(zip("one two three four five six seven eight nine ten".split(), range(1, 11)))


def experience_years(text):
    """Extract compact minimum-year signals; never retain whole descriptions.

    Range lower bounds count (2–4 years asks for at least two). Conflicting
    requirements remain visible so a two-year skill cannot mask five overall.
    """
    plain = re.sub(r"<[^>]+>", " ", html.unescape(html.unescape(text or "")))
    plain = " ".join(plain.split())
    return sorted({YEAR_WORDS.get(m["low"].lower(), int(m["low"]) if m["low"].isdigit() else 0)
                   for m in YEAR_REQUIREMENT.finditer(plain)})
