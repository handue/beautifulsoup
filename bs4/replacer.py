"""Tag renaming rules applied while a document is being parsed."""


class SoupReplacer:
    """Rename each completed ``og_tag`` to ``alt_tag`` during parsing.

    Names are matched exactly against the parser's normalized local tag name.
    The rule changes only the name, preserving the original parser semantics.
    """

    og_tag: str
    alt_tag: str

    def __init__(self, og_tag: str, alt_tag: str):
        for name in (og_tag, alt_tag):
            if not isinstance(name, str):
                raise TypeError("Tag names must be strings.")
            if not name or any(c.isspace() or c in "<>/" for c in name):
                raise ValueError(
                    "Tag names must be nonempty names without whitespace or <>/."
                )
        self.og_tag = og_tag
        self.alt_tag = alt_tag
