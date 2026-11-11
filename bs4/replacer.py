"""Tag transformation rules applied while a document is being parsed."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from bs4.element import Tag


def _check_name(name: Any) -> str:
    if not isinstance(name, str):
        raise TypeError("Tag names must be strings.")
    if not name or any(c.isspace() or c in "<>/" for c in name):
        raise ValueError("Tag names must be nonempty names without whitespace or <>/.")
    return name


class SoupReplacer:
    """Change tags while the document is being parsed.

    Milestone 2 form, renames every ``og_tag`` to ``alt_tag``::

        SoupReplacer("b", "blockquote")

    Milestone 3 form, takes functions that are called with each tag::

        SoupReplacer(name_xformer=lambda tag: "blockquote" if tag.name == "b" else tag.name)

    :param name_xformer: takes a tag, returns the name it should have.
    :param attrs_xformer: takes a tag, returns the attributes it should have.
    :param xformer: takes a tag and changes it in place. Returns nothing.

    The functions run when the parser closes a tag, so the tag already has
    its attributes and children. The two forms can't be mixed.
    """

    def __init__(
        self,
        og_tag: Optional[str] = None,
        alt_tag: Optional[str] = None,
        *,
        name_xformer: Optional[Callable[[Tag], str]] = None,
        attrs_xformer: Optional[Callable[[Tag], Mapping[str, Any]]] = None,
        xformer: Optional[Callable[[Tag], None]] = None,
    ):
        functions = {
            "name_xformer": name_xformer,
            "attrs_xformer": attrs_xformer,
            "xformer": xformer,
        }
        for keyword, function in functions.items():
            if function is not None and not callable(function):
                raise TypeError(f"{keyword} must be a function or None.")

        if og_tag is not None or alt_tag is not None:
            if any(f is not None for f in functions.values()):
                raise TypeError("Use either a tag pair or xformer functions, not both.")
            _check_name(og_tag)
            _check_name(alt_tag)

        self.og_tag = og_tag
        self.alt_tag = alt_tag
        self.name_xformer = name_xformer
        self.attrs_xformer = attrs_xformer
        self.xformer = xformer

    def transform(self, tag: Tag) -> None:
        """Apply the rules to one tag. Called from BeautifulSoup.popTag().

        :meta private:
        """
        if self.og_tag is not None:
            if tag.name == self.og_tag:
                tag.name = self.alt_tag
            return

        # Call both functions first and apply afterwards, so attrs_xformer
        # still sees the original tag name.
        new_name = None
        new_attrs = None
        if self.name_xformer is not None:
            new_name = _check_name(self.name_xformer(tag))
        if self.attrs_xformer is not None:
            new_attrs = self.attrs_xformer(tag)
            if not isinstance(new_attrs, Mapping):
                raise TypeError("attrs_xformer must return a dictionary.")

        if new_name is not None:
            tag.name = new_name
        if new_attrs is not None and new_attrs is not tag.attrs:
            tag.attrs = dict(new_attrs)
        if self.xformer is not None:
            self.xformer(tag)
